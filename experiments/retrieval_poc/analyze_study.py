"""Descriptive analysis of run_fact_study outputs (one deltas.csv per seed).

Usage:
  python experiments/retrieval_poc/analyze_study.py \
      experiments/retrieval_poc/results/study_3462_seed0/deltas.csv \
      experiments/retrieval_poc/results/study_3462_seed1/deltas.csv \
      experiments/retrieval_poc/results/study_3462_seed2/deltas.csv \
      --out experiments/retrieval_poc/results/analysis_3462

CPU only, standard library only. Nothing is averaged across facts: every
number is per fact and per route, summarised across seeds (min / max / mean).

The three questions are reported separately:
  Q1 acquisition   - does the NEW object win on forward routes?
  Q2 persistence   - is the OLD fact still reachable (forward old rank,
                     and reverse-from-old-object routes)?
  Q3 access profile- which routes changed (reverse-from-new-object, controls)?

One rule here was added AFTER seeing the data and is labelled as such:
  "edit took" = new object is rank 1 on the edit prompt in every seed.
Facts where the edit did not take are reported in their own section and are
NOT used for Q2/Q3, because persistence is meaningless if nothing was learned.
"""
import argparse, csv, json, statistics as st
from collections import defaultdict
from pathlib import Path

VERSION = "analyze_study v1 (2026-10-24)"


def load(paths):
    rows = []
    for p in paths:
        with open(p, newline="") as f:
            for r in csv.DictReader(f):
                if r["answer_label"].startswith("MARGIN"):
                    r["pre_first_token_rank"] = r["post_first_token_rank"] = ""
                rows.append(r)
    return rows


def num(x):
    return None if x in ("", None) else float(x)


def summarise(rows):
    g = defaultdict(list)
    for r in rows:
        g[(r["fact_id"], r["route"], r["answer_label"])].append(r)
    out = []
    for (fact, route, label), rs in g.items():
        d = [num(r["delta_sum_logprob"]) for r in rs]
        post = [num(r["post_first_token_rank"]) for r in rs]
        post = [int(x) for x in post if x is not None]
        pre = num(rs[0]["pre_first_token_rank"])
        out.append({
            "fact_id": fact, "relation": rs[0]["relation"], "route": route,
            "kind": rs[0]["kind"], "route_valid": rs[0]["route_valid"],
            "answer_label": label, "answer": rs[0]["answer"],
            "n_seeds": len(rs), "seeds": ",".join(sorted(r["seed"] for r in rs)),
            "pre_rank": "" if pre is None else int(pre),
            "post_rank_min": min(post) if post else "",
            "post_rank_max": max(post) if post else "",
            "pre_sum_logprob": round(num(rs[0]["pre_sum_logprob"]), 3),
            "post_sum_logprob_mean": round(st.mean(num(r["post_sum_logprob"]) for r in rs), 3),
            "delta_mean": round(st.mean(d), 3), "delta_min": round(min(d), 3),
            "delta_max": round(max(d), 3),
            "post_greedy_seed0": rs[0]["post_greedy"].replace("\n", "\\n"),
        })
    out.sort(key=lambda r: (r["fact_id"], r["kind"], r["route"], r["answer_label"]))
    return out


def rank_str(r):
    a, b = r["post_rank_min"], r["post_rank_max"]
    return f"{a}" if a == b else f"{a}-{b}"


def fact_report(summary):
    by_fact = defaultdict(list)
    for r in summary:
        by_fact[r["fact_id"]].append(r)

    took, failed = [], []
    for fact, rs in sorted(by_fact.items()):
        ep = [r for r in rs if r["route"] == "forward_edit_prompt" and r["answer_label"] == "new_object"][0]
        (took if ep["post_rank_max"] == 1 else failed).append(fact)

    L = [f"# Fact study analysis ({VERSION})", "",
         "Descriptive only. Ranks are first-token ranks (1 = top). "
         "Ranges are min-max over seeds. Δ = change in full-answer log-probability, mean over seeds. "
         "Only routes marked valid at screening are used; invalid ones are listed but excluded.", "",
         f"**Edit took (post-hoc rule: new object rank 1 on edit prompt in every seed):** {', '.join(took)}",
         f"**Edit did not take:** {', '.join(failed) or 'none'}", ""]

    def line(r):
        flag = "" if r["route_valid"] == "True" else "  _(invalid route, excluded)_"
        return (f"| {r['route']} | {r['answer_label']} ({r['answer']}) | {r['pre_rank']} → {rank_str(r)} "
                f"| {r['delta_mean']:+.2f} [{r['delta_min']:+.2f}, {r['delta_max']:+.2f}] |{flag}")

    hdr = ["| route | answer | rank pre → post | Δ logprob mean [min, max] |", "|---|---|---|---|"]
    for fact in took + failed:
        rs = by_fact[fact]
        L += [f"## {fact} ({rs[0]['relation']})" + ("" if fact in took else " — EDIT DID NOT TAKE"), ""]
        sections = [
            ("Q1 acquisition – new object on forward routes", lambda r: r["kind"] == "forward" and r["answer_label"] == "new_object"),
            ("Q2 persistence – old object on forward routes", lambda r: r["kind"] == "forward" and r["answer_label"] == "old_object"),
            ("Q2 persistence – reverse from OLD object (subject should stay if old fact persists)", lambda r: r["kind"] == "reverse_old"),
            ("Q3 access – reverse from NEW object (subject rises only if edit propagates backwards)", lambda r: r["kind"] == "reverse_new"),
            ("Locality controls", lambda r: r["kind"] == "control"),
        ]
        for title, pred in sections:
            sel = [r for r in rs if pred(r)]
            if sel:
                L += [f"**{title}**", ""] + hdr + [line(r) for r in sel] + [""]
    return "\n".join(L), took, failed


def overview(summary, took):
    """One row per included fact: the headline number for each question, valid routes only."""
    rows = []
    for fact in took:
        rs = [r for r in summary if r["fact_id"] == fact and r["route_valid"] == "True"]
        fwd_new = [r for r in rs if r["kind"] == "forward" and r["answer_label"] == "new_object"]
        fwd_old = [r for r in rs if r["kind"] == "forward" and r["answer_label"] == "old_object"]
        rev_old = [r for r in rs if r["kind"] == "reverse_old" and r["answer_label"] == "subject"]
        rev_new = [r for r in rs if r["kind"] == "reverse_new" and r["answer_label"] == "subject"]
        ctl_ok = [r for r in rs if r["kind"] == "control" and r["answer_label"] == "correct"]
        ctl_leak = [r for r in rs if r["kind"] == "control" and r["answer_label"] == "edit_leak"]
        rows.append({
            "fact_id": fact,
            "Q1_fwd_routes_new_rank1_all_seeds": f"{sum(r['post_rank_max']==1 for r in fwd_new)}/{len(fwd_new)}",
            "Q2_fwd_old_best_post_rank": min(r["post_rank_min"] for r in fwd_old),
            "Q2_rev_old_subject_rank1_all_seeds": f"{sum(r['post_rank_max']==1 for r in rev_old)}/{len(rev_old)}",
            "Q2_rev_old_subject_delta_means": " ".join(f"{r['delta_mean']:+.2f}" for r in rev_old),
            "Q3_rev_new_subject_rank_pre_to_post": " ".join(f"{r['pre_rank']}→{rank_str(r)}" for r in rev_new),
            "Q3_rev_new_subject_delta_means": " ".join(f"{r['delta_mean']:+.2f}" for r in rev_new),
            "ctl_correct_still_rank1": f"{sum(r['post_rank_max']==1 for r in ctl_ok)}/{len(ctl_ok)}",
            "ctl_leak_rank_pre_to_post": " ".join(f"{r['pre_rank']}→{rank_str(r)}" for r in ctl_leak),
        })
    return rows


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deltas", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rows = load(a.deltas)
    summary = summarise(rows)
    report, took, failed = fact_report(summary)
    ov = overview(summary, took)
    write_csv(out / "route_summary.csv", summary)
    write_csv(out / "overview.csv", ov)
    (out / "fact_report.md").write_text(report)
    (out / "manifest.json").write_text(json.dumps(
        {"version": VERSION, "inputs": a.deltas, "edit_took": took, "edit_did_not_take": failed}, indent=2))
    print(VERSION)
    print(f"edit took: {took}\nedit did not take: {failed}\n")
    for r in ov:
        print(json.dumps(r))
    print(f"\nWrote {out}/route_summary.csv, overview.csv, fact_report.md")


if __name__ == "__main__":
    main()
