#!/usr/bin/env python3
"""Build the v3 candidate fact set (plan 2.2). Standard library only, deterministic, no model involved.

Sources
  draft       the 18 candidate edits of the draft (candidate_facts_v2.csv), copied verbatim so the v3 results on
              these facts are directly comparable with the paper;
  own         facts_v3/own_facts.csv: hand-written true facts (relation, subject, object), to be checked by a person;
  counterfact CounterFact (Meng et al., 2022) relation P36 (capital): subject, true object and counterfactual object
              exactly as published, from counterfact.json (md5 recorded in the output's manifest).

Rules (see relation_templates_v3.json "design_rules")
  * a fact is dropped if its old object's name occurs in its subject (forward read would test string copying);
  * within a relation each old object appears once (draft first, then own); CounterFact P36 lists several subjects for
    some capitals (Berlin: Nazi Germany, Weimar Republic, Germany, ...), so those are all kept with dup_group = the
    capital, and screening keeps at most one included fact per group (rule in relation_templates_v3.json);
  * own facts get their new object by a seeded cyclic shift within the relation: fact i takes the old object of fact
    i+1 in a shuffled order, so every new object is a real object of the same type, the "new object's own fact"
    control (new_alt = that fact's subject) always exists, and no two edits swap objects with each other;
  * CounterFact facts keep CounterFact's new object; new_alt is the kept P36 subject whose true capital it is, if any.

Output: --out (CSV with the columns of candidate_facts_v2.csv plus source, cf_case_id) and <out>.manifest.json.
"""
import argparse
import csv
import hashlib
import json
import random
import re
import unicodedata
from collections import Counter, OrderedDict
from pathlib import Path

VERSION = "build_candidates_v3 v1.0 (2026-10-31)"
FIELDS = ["fact_id", "relation", "subject", "target_old", "target_new", "old_alt", "new_alt", "notes", "source", "cf_case_id",
          "dup_group"]
PREFIX = {"novel_author": "nov", "company_founder": "com", "invention_inventor": "inv", "country_capital": "cap",
          "painting_painter": "pai", "character_creator": "chr", "country_currency": "cur"}


def slug(text):
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_")


def leaks(subject, obj):
    return obj.lower() in subject.lower()


def md5(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", default="experiments/retrieval_poc/candidate_facts_v2.csv")
    ap.add_argument("--own", default="experiments/retrieval_poc/facts_v3/own_facts.csv")
    ap.add_argument("--counterfact", required=True, help="path to counterfact.json")
    ap.add_argument("--templates", default="experiments/retrieval_poc/relation_templates_v3.json")
    ap.add_argument("--seed", default="v3-2026-10-31")
    ap.add_argument("--out", default="experiments/retrieval_poc/facts_v3/candidate_facts_v3.csv")
    a = ap.parse_args()

    relations = json.loads(Path(a.templates).read_text(encoding="utf-8"))["relations"]
    rows, dropped = [], []
    seen_obj = {r: set() for r in relations}
    seen_id = set()

    def add(row, why_not=None):
        if why_not:
            dropped.append({**row, "reason": why_not})
            return
        assert row["fact_id"] not in seen_id, row["fact_id"]
        assert row["source"] == "counterfact" or row["target_old"] not in seen_obj[row["relation"]], row
        seen_id.add(row["fact_id"])
        seen_obj[row["relation"]].add(row["target_old"])
        rows.append({k: row.get(k, "") for k in FIELDS})

    # draft facts, verbatim
    for r in csv.DictReader(open(a.draft, newline="", encoding="utf-8-sig")):
        add({**r, "source": "draft"})

    # own facts: filter, then cyclic shift within each relation
    own = list(csv.DictReader(open(a.own, newline="", encoding="utf-8")))
    by_rel = OrderedDict()
    for r in own:
        if r["relation"] not in relations:
            raise ValueError(f"unknown relation {r['relation']!r}")
        base = {"relation": r["relation"], "subject": r["subject"], "target_old": r["object"], "notes": r["notes"],
                "source": "own", "fact_id": f"{PREFIX[r['relation']]}_{slug(r['subject'])}"}
        if leaks(r["subject"], r["object"]):
            dropped.append({**base, "reason": "object name in subject"}); continue
        if r["object"] in seen_obj[r["relation"]] or any(x["target_old"] == r["object"] for x in by_rel.get(r["relation"], [])):
            dropped.append({**base, "reason": "duplicate object in relation"}); continue
        by_rel.setdefault(r["relation"], []).append(base)
    for rel, facts in by_rel.items():
        order = sorted(facts, key=lambda f: f["fact_id"])
        random.Random(f"{a.seed}:{rel}").shuffle(order)
        n = len(order)
        for i, f in enumerate(order):
            nxt = order[(i + 1) % n]
            f = {**f, "target_new": nxt["target_old"], "new_alt": nxt["subject"]}
            add(f, "new object name in subject" if leaks(f["subject"], f["target_new"]) else None)

    # CounterFact P36
    cf = json.loads(Path(a.counterfact).read_text(encoding="utf-8"))
    p36 = sorted((r for r in cf if r["requested_rewrite"]["relation_id"] == "P36"), key=lambda r: r["case_id"])
    kept = []
    for r in p36:
        rw = r["requested_rewrite"]
        base = {"relation": "country_capital", "subject": rw["subject"], "target_old": rw["target_true"]["str"],
                "target_new": rw["target_new"]["str"], "source": "counterfact", "cf_case_id": r["case_id"],
                "fact_id": f"cap_{slug(rw['subject'])}"}
        if leaks(rw["subject"], base["target_old"]) or leaks(rw["subject"], base["target_new"]):
            dropped.append({**base, "reason": "object name in subject"}); continue
        if base["fact_id"] in {k["fact_id"] for k in kept}:
            dropped.append({**base, "reason": "duplicate subject"}); continue
        kept.append(base)
    groups = Counter(k["target_old"] for k in kept)
    capital_of = {}
    for k in kept:                                   # lowest case_id first, so setdefault keeps the earliest
        capital_of.setdefault(k["target_old"], k["subject"])
    for k in kept:
        add({**k, "new_alt": capital_of.get(k["target_new"], ""),
             "dup_group": k["target_old"] if groups[k["target_old"]] > 1 else ""})

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    counts = Counter((r["relation"], r["source"]) for r in rows)
    manifest = {"version": VERSION, "seed": a.seed, "inputs": {p: md5(p) for p in (a.draft, a.own, a.counterfact, a.templates)},
                "n_candidates": len(rows), "by_relation_source": {f"{k[0]}/{k[1]}": v for k, v in sorted(counts.items())},
                "n_without_new_alt": sum(1 for r in rows if not r["new_alt"]),
                "n_dup_groups": len({r["dup_group"] for r in rows if r["dup_group"]}),
                "n_in_dup_groups": sum(1 for r in rows if r["dup_group"]),
                "dropped": dropped, "output_md5": md5(out)}
    Path(str(out) + ".manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print(VERSION, "|", len(rows), "candidates |", len(dropped), "dropped")
    for k, v in sorted(counts.items()):
        print(f"  {k[0]:20s} {k[1]:12s} {v}")
    print("  without new_alt:", manifest["n_without_new_alt"], "| dup groups:", manifest["n_dup_groups"],
          "covering", manifest["n_in_dup_groups"], "facts (resolved at screening)")
    for d in Counter(d["reason"] for d in dropped).items():
        print("  dropped:", d)
    print("wrote", out, manifest["output_md5"])


if __name__ == "__main__":
    main()
