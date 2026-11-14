#!/usr/bin/env python3
"""Choose the edit pairs and sentinel facts for the commutativity experiment (N1; run_audit.py --mode pairs).

Every unordered pair of admitted facts gets exactly one class, tested in this order (first match wins):
  same_new       both edits write the same new object (o*_A = o*_B);
  shared_object  one edit's new object is the other's old object (o*_A = o_B or o_A = o*_B);
  chained        one edit's old or new object is the other's subject;
  neighbour      B is one of A's same-relation control facts or vice versa (the audit reads one from the other);
  other_shared   any other shared entity (subject, old or new object);
  same_relation  same relation, no shared entity;
  disjoint       different relations, no shared entity.
Sentinels (facts read after every pair, never edited) are chosen first, by hash, among facts that are in no
same_new / shared_object / chained pair, spread over relations; pairs are then drawn among the remaining facts.
Within a class, pairs are ordered by md5(seed:fact_a|fact_b) and the first --per-class are kept (all if fewer).
Deterministic: same probes and arguments -> same output. Standard library only.
Outputs: <out>/pairs.csv (pair_id, pair_class, fact_a, fact_b), <out>/sentinels.txt, <out>/pairs_manifest.json
"""
import argparse
import csv
import hashlib
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

VERSION = "make_pairs v1.0 (2026-11-05)"
CLASSES = ("same_new", "shared_object", "chained", "neighbour", "other_shared", "same_relation", "disjoint")


def h(*parts):
    return hashlib.md5(":".join(parts).encode("utf-8")).hexdigest()


def pair_class(a, b):
    ea, eb = a["edit"], b["edit"]
    if ea["target_new"] == eb["target_new"]:
        return "same_new"
    if ea["target_new"] == eb["target_old"] or ea["target_old"] == eb["target_new"]:
        return "shared_object"
    if {ea["target_old"], ea["target_new"]} & {eb["subject"]} or {eb["target_old"], eb["target_new"]} & {ea["subject"]}:
        return "chained"
    ctl = lambda p: {r.get("control_fact") for r in p["routes"] if r["route"].startswith("control_same_relation")}
    if b["fact_id"] in ctl(a) or a["fact_id"] in ctl(b):
        return "neighbour"
    ent = lambda e: {e["subject"], e["target_old"], e["target_new"]}
    if ent(ea) & ent(eb):
        return "other_shared"
    return "same_relation" if a["relation"] == b["relation"] else "disjoint"


def load_admitted(dirs):
    facts = {}
    for d in dirs:
        for f in sorted(Path(d).glob("*.json")):
            p = json.loads(f.read_text(encoding="utf-8"))
            if p.get("screening", {}).get("included"):
                facts[p["fact_id"]] = p
    return facts


def choose(facts, per_class, n_sentinels, seed):
    ids = sorted(facts)
    cls = {(a, b): pair_class(facts[a], facts[b]) for a, b in itertools.combinations(ids, 2)}
    risky = {x for (a, b), c in cls.items() if c in ("same_new", "shared_object", "chained") for x in (a, b)}
    by_rel = defaultdict(list)
    for f in ids:
        if f not in risky:
            by_rel[facts[f]["relation"]].append(f)
    for r in by_rel:
        by_rel[r].sort(key=lambda f: h(seed, "sentinel", f))
    sentinels = []
    while len(sentinels) < n_sentinels and any(by_rel.values()):
        for r in sorted(by_rel):                         # round-robin over relations
            if by_rel[r] and len(sentinels) < n_sentinels:
                sentinels.append(by_rel[r].pop(0))
    pool = defaultdict(list)
    for (a, b), c in cls.items():
        if a not in sentinels and b not in sentinels:
            pool[c].append((a, b))
    pairs = []
    for c in CLASSES:
        for a, b in sorted(pool[c], key=lambda ab: h(seed, *ab))[:per_class.get(c, 0)]:
            pairs.append({"pair_id": f"p{len(pairs) + 1:03d}", "pair_class": c, "fact_a": a, "fact_b": b})
    return pairs, sentinels, Counter(cls.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probes-dir", required=True, nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--per-class", default="same_new=all,shared_object=all,chained=all,neighbour=30,same_relation=30,disjoint=30",
                    help="class=N or class=all, comma separated; classes not named get 0")
    ap.add_argument("--sentinels", type=int, default=6)
    ap.add_argument("--seed", default="0")
    a = ap.parse_args()
    per = {k: (10 ** 9 if v == "all" else int(v)) for k, v in (x.split("=") for x in a.per_class.split(","))}
    if set(per) - set(CLASSES):
        raise ValueError(f"unknown class in --per-class: {set(per) - set(CLASSES)}")
    facts = load_admitted(a.probes_dir)
    pairs, sentinels, available = choose(facts, per, a.sentinels, a.seed)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    with open(out / "pairs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["pair_id", "pair_class", "fact_a", "fact_b"]); w.writeheader(); w.writerows(pairs)
    (out / "sentinels.txt").write_text("\n".join(sentinels) + "\n", encoding="utf-8")
    man = {"version": VERSION, "probes_dirs": a.probes_dir, "admitted": len(facts), "per_class": a.per_class,
           "seed": a.seed, "available_pairs": dict(available), "chosen": dict(Counter(p["pair_class"] for p in pairs)),
           "sentinels": sentinels}
    (out / "pairs_manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    print(json.dumps(man, indent=1))


if __name__ == "__main__":
    main()
