"""Recompute every number reported in the paper (Table 2 and findings F1-F5) from the raw deltas.csv files.

CPU only, standard library only. Run from the repository root:
    python experiments/retrieval_poc/check_paper_numbers.py
Pass --results <dir> to check a fresh re-run instead of the shipped outputs
(it expects study_<A>_seed{0,1,2}/deltas.csv for --study-v1 and --study-v2).

Which runs feed the paper:
  * study 3462 (templates v1): novels and the invention -> main results;
    the three company facts -> finding F5 (failed edits, subject in first position).
  * study 3467 (templates v2): the five company facts -> main results.
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from analyze_study import load, summarise  # noqa: E402

V1_COMPANY_FAILED = {"apple", "facebook", "microsoft"}


def rank_rng(r):
    a, b = r["post_rank_min"], r["post_rank_max"]
    return f"{a}" if a == b else f"{a}-{b}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="experiments/retrieval_poc/results")
    ap.add_argument("--study-v1", default="3462")
    ap.add_argument("--study-v2", default="3467")
    a = ap.parse_args()
    res = Path(a.results)
    v1 = summarise(load([res / f"study_{a.study_v1}_seed{s}/deltas.csv" for s in range(3)]))
    v2 = summarise(load([res / f"study_{a.study_v2}_seed{s}/deltas.csv" for s in range(3)]))
    v1_rows = load([res / f"study_{a.study_v1}_seed{s}/deltas.csv" for s in range(3)])
    v2_rows = load([res / f"study_{a.study_v2}_seed{s}/deltas.csv" for s in range(3)])

    main_rows = [r for r in v1 if r["relation"] != "company_founder"] + v2
    raw_main = [r for r in v1_rows if r["relation"] != "company_founder"] + v2_rows
    facts = sorted({r["fact_id"] for r in main_rows},
                   key=lambda f: ({"novel_author": 0, "company_founder": 1, "invention_inventor": 2}[
                       next(r["relation"] for r in main_rows if r["fact_id"] == f)], f))

    def sel(fact, kind, label, valid=True, route=None):
        return [r for r in main_rows if r["fact_id"] == fact and r["kind"] == kind and r["answer_label"] == label
                and (not valid or r["route_valid"] == "True") and (route is None or r["route"] == route)]

    print("TABLE 2 (per fact; valid routes only; 3 seeds)")
    print(f"{'fact':16s} {'Q1':>5s} {'Q2':>5s}  {'Q3 rev-new delta':18s} Q3 neighbour")
    agg = {"q1_nc": [0, 0], "q1_co": [0, 0], "q2": [0, 0], "q3_neg": [0, 0], "co_leak_max": 0}
    for f in facts:
        rel = next(r["relation"] for r in main_rows if r["fact_id"] == f)
        para = [r for r in sel(f, "forward", "new_object") if r["route"] != "forward_edit_prompt"]
        q1 = sum(r["post_rank_max"] == 1 for r in para)
        ro = sel(f, "reverse_old", "subject")
        q2 = sum(r["post_rank_max"] == 1 for r in ro)
        rn = sel(f, "reverse_new", "subject")
        leak = sel(f, "control", "edit_leak", route="control_same_relation")
        key = "q1_co" if rel == "company_founder" else "q1_nc"
        agg[key][0] += q1; agg[key][1] += len(para)
        agg["q2"][0] += q2; agg["q2"][1] += len(ro)
        agg["q3_neg"][0] += sum(r["delta_mean"] < 0 for r in rn); agg["q3_neg"][1] += len(rn)
        if rel == "company_founder":
            agg["co_leak_max"] = max(agg["co_leak_max"], max(r["post_rank_max"] for r in leak))
        print(f"{f:16s} {q1}/{len(para):<3d} {q2}/{len(ro):<3d}  "
              f"{', '.join(f'{r[chr(100)+'elta_mean']:+.2f}' for r in rn):18s} "
              f"{', '.join(f'{r['pre_rank']}->{rank_rng(r)}' for r in leak)}")

    ep = [r for r in raw_main if r["route"] == "forward_edit_prompt" and r["answer_label"] == "new_object"]
    ep_ranks = {int(r["post_first_token_rank"]) for r in ep}
    ep_p = [math.exp(float(r["post_sum_logprob"])) for r in ep]
    ctl = [r for r in main_rows if r["kind"] == "control" and r["answer_label"] == "correct" and r["route_valid"] == "True"]

    print("\nHEADLINE NUMBERS")
    print(f"F1 edit prompt: new answer rank(s) {sorted(ep_ranks)} over {len(ep)} runs; "
          f"full-answer probability {min(ep_p):.3f}-{max(ep_p):.3f}")
    print(f"F1 paraphrase/context new@1 every seed: novels+invention {agg['q1_nc'][0]}/{agg['q1_nc'][1]}, "
          f"companies {agg['q1_co'][0]}/{agg['q1_co'][1]}")
    print(f"F2 reverse-from-old subject still rank 1 every seed: {agg['q2'][0]}/{agg['q2'][1]}")
    print(f"F3 reverse-from-new subject log-prob decreases (mean over seeds): {agg['q3_neg'][0]}/{agg['q3_neg'][1]}")
    print(f"F4 neighbour correct answer rank 1 every seed: {sum(r['post_rank_max'] == 1 for r in ctl)}/{len(ctl)}; "
          f"company neighbour: new value worst rank {agg['co_leak_max']}")

    fail = [r for r in v1_rows if r["fact_id"] in V1_COMPANY_FAILED and r["route"] == "forward_edit_prompt"
            and r["answer_label"] == "new_object"]
    fr = [int(r["post_first_token_rank"]) for r in fail]
    nb = [int(r["post_first_token_rank"]) for r in v1_rows if r["fact_id"] == "apple"
          and r["route"] == "control_new_object_own_fact" and r["answer_label"] == "correct"]
    print(f"F5 v1 company edits (subject first): new answer rank {min(fr)}-{max(fr)}; "
          f"'Microsoft ... Bill Gates' neighbour after Apple edit: rank {min(nb)}-{max(nb)}")


if __name__ == "__main__":
    main()
