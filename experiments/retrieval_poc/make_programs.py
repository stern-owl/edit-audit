#!/usr/bin/env python3
"""Edit programs for run_audit.py --mode programs: N5 (compensating edits) and N2 (cascading repair). Standard library.

A program is a list of steps applied from the unedited weights (each step = one edit call; a step with several edits is
one batch_edit call), reads after chosen steps, then an exact restore. Kinds:
  N5 compensate        [A], [A~inv]                      read A at steps 1 and 2 (A~inv: o* -> o, same prompt/subject)
  N5 compensate_late   [A], [X1] ... [X5], [A~inv]       read A, X1..X5 at the end; compared with the reference below
  N5 reference         [X1] ... [X5]                     read A, X1..X5 at the end (the state compensate_late should reach)
  N2 cascade           [A], [S]                          read A and S at steps 1 and 2 (step 1 = the edit alone)
  N2 cascade_rev       [S], [A]                          read A and S at the end
  N2 cascade_batch     [A + S] (one batch call)          read A and S at the end (skipped by the driver for ROME)
For N2, A is an admitted edit of a relation whose inverse is functional (one-to-one) whose new object o* already has a
subject s' that the unedited model knows (A's control_new_object_own_fact route, "<s'> -> o*", is valid; s' is A's
new_alt in the candidate file). A alone maps two subjects to o*. The repair S is the swap (s': o* -> o, A's old object):
after A and S the one-to-one relation holds again (s -> o*, s' -> o). S is a derived fact (fact_id swap__<A>); its probe
is built by the driver from the templates and judged on the unedited model.
Sentinels (from make_pairs.choose, never edited) are read after every program read. Deterministic.
Outputs: <out>/programs.jsonl, <out>/derived_facts.csv, <out>/sentinels.txt, <out>/programs_manifest.json
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import make_pairs as mp

VERSION = "make_programs v1.0 (2026-11-05)"
DERIVED_FIELDS = ["fact_id", "relation", "subject", "target_old", "target_new", "old_alt", "new_alt", "notes", "source",
                  "cf_case_id", "dup_group"]


def h(*parts):
    return hashlib.md5(":".join(parts).encode("utf-8")).hexdigest()


def ent(p):
    e = p["edit"]
    return {e["subject"], e["target_old"], e["target_new"]}


def build(facts, cardinality, sentinels, n_late, k_late, seed, new_alt):
    ids = [f for f in sorted(facts) if f not in sentinels]
    E = lambda f, d="fwd": {"fact": f, "dir": d}
    progs = []
    # N5
    for f in ids:
        progs.append({"program_id": f"comp:{f}", "experiment": "N5", "kind": "compensate", "steps": [[E(f)], [E(f, "inv")]],
                      "read": [f], "read_at": [1, 2], "compare_to": None})
    for f in sorted(ids, key=lambda x: h(seed, "late", x))[:n_late]:
        xs = []
        for x in sorted(ids, key=lambda x: h(seed, "late", f, x)):
            if x != f and not ent(facts[x]) & ent(facts[f]) and all(not ent(facts[x]) & ent(facts[y]) for y in xs):
                xs.append(x)
            if len(xs) == k_late:
                break
        progs.append({"program_id": f"ref:{f}", "experiment": "N5", "kind": "reference", "steps": [[E(x)] for x in xs],
                      "read": [f] + xs, "read_at": [len(xs)], "compare_to": None})
        progs.append({"program_id": f"late:{f}", "experiment": "N5", "kind": "compensate_late",
                      "steps": [[E(f)]] + [[E(x)] for x in xs] + [[E(f, "inv")]],
                      "read": [f] + xs, "read_at": [len(xs) + 2], "compare_to": f"ref:{f}"})
    # N2
    derived = []
    for a in ids:
        pa = facts[a]
        own = [r for r in pa["routes"] if r["route"] == "control_new_object_own_fact"]
        if cardinality.get(pa["relation"], {}).get("inverse") != "functional" or not own or not own[0]["valid"]:
            continue
        s, e = f"swap__{a}", pa["edit"]
        derived.append({"fact_id": s, "relation": pa["relation"], "subject": new_alt[a], "target_old": e["target_new"],
                        "target_new": e["target_old"], "old_alt": "", "new_alt": e["subject"],
                        "notes": f"N2 swap repair for {a}: {new_alt[a]} takes {e['subject']}'s old object",
                        "source": "derived", "cf_case_id": "", "dup_group": ""})
        for kind, steps, at in (("cascade", [[E(a)], [E(s)]], [1, 2]), ("cascade_rev", [[E(s)], [E(a)]], [2]),
                                ("cascade_batch", [[E(a), E(s)]], [1])):
            progs.append({"program_id": f"{kind}:{a}", "experiment": "N2", "kind": kind, "steps": steps,
                          "read": [a, s], "read_at": at, "compare_to": None, "repair_subject": new_alt[a]})
    return progs, derived


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probes-dir", required=True, nargs="+")
    ap.add_argument("--templates", required=True)
    ap.add_argument("--candidates", required=True, help="candidate_facts_v3.csv (for new_alt, the new object's own subject)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--sentinels", type=int, default=6)
    ap.add_argument("--late", type=int, default=20, help="facts with a compensate_late program")
    ap.add_argument("--late-k", type=int, default=5, help="unrelated edits between an edit and its compensation")
    ap.add_argument("--seed", default="0")
    a = ap.parse_args()
    facts = mp.load_admitted(a.probes_dir)
    card = {k: v.get("cardinality", {}) for k, v in json.loads(Path(a.templates).read_text(encoding="utf-8"))["relations"].items()}
    _, sentinels, _ = mp.choose(facts, {}, a.sentinels, a.seed)
    with open(a.candidates, newline="", encoding="utf-8-sig") as f:
        new_alt = {r["fact_id"]: (r["new_alt"] or "").strip() for r in csv.DictReader(f)}
    progs, derived = build(facts, card, sentinels, a.late, a.late_k, a.seed, new_alt)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    with open(out / "programs.jsonl", "w", encoding="utf-8") as f:
        for p in progs:
            f.write(json.dumps(p) + "\n")
    with open(out / "derived_facts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=DERIVED_FIELDS); w.writeheader(); w.writerows(derived)
    (out / "sentinels.txt").write_text("\n".join(sentinels) + "\n", encoding="utf-8")
    man = {"version": VERSION, "probes_dirs": a.probes_dir, "admitted": len(facts), "sentinels": sentinels, "seed": a.seed,
           "late": a.late, "late_k": a.late_k, "programs": dict(Counter(p["kind"] for p in progs)),
           "edit_calls": sum(len(p["steps"]) for p in progs), "derived": [d["fact_id"] for d in derived]}
    (out / "programs_manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    print(json.dumps(man, indent=1))


if __name__ == "__main__":
    main()
