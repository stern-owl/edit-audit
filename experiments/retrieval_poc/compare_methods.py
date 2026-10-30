"""Side-by-side audit of several editing methods on the same facts and probes (descriptive only).

Usage (repository root):
  python experiments/retrieval_poc/compare_methods.py \
     --method ROME  results/study_3462_seed{0,1,2}/deltas.csv results/study_3467_seed{0,1,2}/deltas.csv \
     --method MEMIT results/study_3574_MEMIT_seed{0,1,2}/deltas.csv \
     --out results/compare_methods
For ROME the v1 company rows (failed first-position edits) are dropped when v2 company rows are also given.
Every number is per fact and per route over seeds; aggregates are counts of routes, never averages over facts.
"""
import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from analyze_study import load, summarise  # noqa: E402

VERSION = "compare_methods v1 (2026-10-28)"


def parse():
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", nargs="+", action="append", required=True, metavar=("NAME", "DELTAS"))
    ap.add_argument("--out", required=True)
    return ap.parse_args()


def method_rows(files):
    rows = load(files)
    seeds_per_fact = defaultdict(set)
    for r in rows:
        seeds_per_fact[(r["fact_id"], r["route"])].add((r["seed"], r.get("_src", "")))
    # ROME main set: if a fact appears in several studies (v1 and v2 companies), keep the last file's study.
    by_fact_file = defaultdict(set)
    for f in files:
        for r in load([f]):
            by_fact_file[r["fact_id"]].add(Path(f).parent.name.rsplit("_seed", 1)[0])
    keep = {}
    for fact, studies in by_fact_file.items():
        keep[fact] = sorted(studies)[-1]
    out = []
    for f in files:
        study = Path(f).parent.name.rsplit("_seed", 1)[0]
        out += [r for r in load([f]) if keep[r["fact_id"]] == study]
    return out, keep


def fact_metrics(summary):
    by = defaultdict(list)
    for r in summary:
        by[r["fact_id"]].append(r)
    res = {}
    for fact, rs in by.items():
        v = [r for r in rs if r["route_valid"] == "True"]
        g = lambda k, l: [r for r in v if r["kind"] == k and r["answer_label"] == l]
        ep = [r for r in g("forward", "new_object") if r["route"] == "forward_edit_prompt"][0]
        para = [r for r in g("forward", "new_object") if r["route"] != "forward_edit_prompt"]
        oldf = [r for r in g("forward", "old_object") if r["route"] != "forward_edit_prompt"]
        ro, rn = g("reverse_old", "subject"), g("reverse_new", "subject")
        leak = [r for r in g("control", "edit_leak") if r["route"] == "control_same_relation"]
        own = [r for r in g("control", "edit_leak") if r["route"] == "control_new_object_own_fact"]
        ok = g("control", "correct")
        res[fact] = {
            "relation": rs[0]["relation"],
            "edit_new_rank_max": ep["post_rank_max"],
            "edit_new_logprob_mean": ep["post_sum_logprob_mean"],
            "q1_para_new_rank1": (sum(r["post_rank_max"] == 1 for r in para), len(para)),
            "q2_fwd_old_still_rank1": (sum(r["post_rank_min"] == 1 for r in oldf), len(oldf)),
            "q2_rev_old_subject_rank1": (sum(r["post_rank_max"] == 1 for r in ro), len(ro)),
            "q2_rev_old_delta": [r["delta_mean"] for r in ro],
            "q3_rev_new_delta": [r["delta_mean"] for r in rn],
            "q3_rev_new_rank": [(r["pre_rank"], r["post_rank_min"], r["post_rank_max"]) for r in rn],
            "q3_neighbour_leak_rank": [(r["pre_rank"], r["post_rank_min"], r["post_rank_max"]) for r in leak],
            "q3_neighbour_leak_delta": [r["delta_mean"] for r in leak],
            "ctl_correct_rank1": (sum(r["post_rank_max"] == 1 for r in ok), len(ok)),
            "ctl_correct_delta": [r["delta_mean"] for r in ok],
        }
    return res


def agg(m, rel=None):
    f = {k: v for k, v in m.items() if rel is None or (v["relation"] == "company_founder") == (rel == "company")}
    s = lambda key: (sum(v[key][0] for v in f.values()), sum(v[key][1] for v in f.values()))
    rn = [d for v in f.values() for d in v["q3_rev_new_delta"]]
    lk = [x for v in f.values() for x in v["q3_neighbour_leak_rank"]]
    return {
        "facts": len(f),
        "edit_prompt_rank1_all_seeds": sum(v["edit_new_rank_max"] == 1 for v in f.values()),
        "edit_prompt_P_range": (round(min(math.exp(v["edit_new_logprob_mean"]) for v in f.values()), 3),
                                round(max(math.exp(v["edit_new_logprob_mean"]) for v in f.values()), 3)),
        "q1_para_new_rank1": s("q1_para_new_rank1"),
        "q2_fwd_old_still_rank1_some_seed": s("q2_fwd_old_still_rank1"),
        "q2_rev_old_subject_rank1": s("q2_rev_old_subject_rank1"),
        "q3_rev_new_decreases": (sum(d < 0 for d in rn), len(rn)),
        "q3_neighbour_leak_reaches_top5": (sum(x[2] <= 5 for x in lk), len(lk)),
        "q3_neighbour_leak_rises": (sum(x[2] < x[0] for x in lk), len(lk)),
        "ctl_correct_rank1": s("ctl_correct_rank1"),
    }


def main():
    a = parse()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    metrics, studies = {}, {}
    for spec in a.method:
        name, files = spec[0], spec[1:]
        rows, keep = method_rows(files)
        metrics[name] = fact_metrics(summarise(rows))
        studies[name] = keep
    names = list(metrics)
    facts = sorted(set.intersection(*[set(m) for m in metrics.values()]),
                   key=lambda f: (metrics[names[0]][f]["relation"], f))

    print(VERSION)
    for n in names:
        print(f"{n}: studies used per fact -> {sorted(set(studies[n].values()))}")
    lines = []
    for scope in (None, "noncompany", "company"):
        label = {None: "ALL 12 FACTS", "noncompany": "NOVELS + INVENTION", "company": "COMPANIES"}[scope]
        print(f"\n== {label}")
        for n in names:
            g = agg({f: metrics[n][f] for f in facts}, scope)
            print(f"{n:10s}", json.dumps(g))
            lines.append({"scope": label, "method": n, **{k: str(v) for k, v in g.items()}})

    print("\n== PER FACT (valid routes; ranks = first-token ranks; min-max over 3 seeds)")
    hdr = ["fact", "method", "edit P", "Q1 para new@1", "Q2 rev-old subj@1", "Q2 rev-old d", "Q3 rev-new d",
           "Q3 neighbour rank pre->post", "ctl ok@1"]
    print(" | ".join(hdr))
    per = []
    for f in facts:
        for n in names:
            v = metrics[n][f]
            row = [f, n, f"{math.exp(v['edit_new_logprob_mean']):.2f}",
                   "%d/%d" % v["q1_para_new_rank1"], "%d/%d" % v["q2_rev_old_subject_rank1"],
                   " ".join(f"{d:+.2f}" for d in v["q2_rev_old_delta"]),
                   " ".join(f"{d:+.2f}" for d in v["q3_rev_new_delta"]),
                   " ".join(f"{p}->{lo}-{hi}" if lo != hi else f"{p}->{lo}" for p, lo, hi in v["q3_neighbour_leak_rank"]),
                   "%d/%d" % v["ctl_correct_rank1"]]
            print(" | ".join(row))
            per.append(dict(zip(hdr, row)))
    for name, data in (("aggregate.csv", lines), ("per_fact.csv", per)):
        with open(out / name, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0].keys()))
            w.writeheader(); w.writerows(data)
    (out / "manifest.json").write_text(json.dumps({"version": VERSION, "inputs": {s[0]: s[1:] for s in a.method}}, indent=1))
    print(f"\nWrote {out}/aggregate.csv and per_fact.csv")


if __name__ == "__main__":
    main()
