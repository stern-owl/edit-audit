#!/usr/bin/env python3
"""Detailed tables for the results document, from run_audit.py outputs. Standard library only.

Usage:
  python report_details.py --root <dir with run folders> --out <dir>
Writes Markdown files:
  checks.md          per run: number of edit steps, worst check A / C, smallest check B, update-norm range
  quantiles.md       per run and route kind: JS / KL / TV quantiles of the post-edit read vs the unedited read
  per_fact_<run>.md  per fact (independent runs): edit success, paraphrases, stale reverse reads, reverse-from-new
                     subject rank, controls, largest rise of the new value on a control, median control JS
  leaks.md           per independent run: the 15 largest rises of the new value on control reads
  overlap.md         stale reverse reads across methods (same model) and across models (same facts, same method)
  sequential.md      per sequential run: order, held-out facts, cumulative update norm per step, the edits after
                     which the most untouched facts lost their correct answer
"""
import argparse
import csv
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

VERSION = "report_details v1.1 (2026-11-05)"


def rows(p):
    return list(csv.DictReader(open(p, newline="", encoding="utf-8")))


def T(x):
    return x in ("True", True)


def q(vals, ps=(0.5, 0.9, 0.99)):
    v = sorted(vals)
    if not v:
        return ["–"] * (len(ps) + 1)
    return [f"{v[min(len(v) - 1, int(p * len(v)))]:.4g}" for p in ps] + [f"{v[-1]:.4g}"]


def find_runs(root):
    out = {}
    for m in sorted(Path(root).glob("*/*/audit_*/manifest.json")):
        man = json.loads(m.read_text())
        name = f"{Path(man['model']).name}/{man['method']}/{man['mode']}/{m.parent.parent.parent.name.split('_')[0]}"
        out[name] = (m.parent, man)
    return out


def own_rows(d):
    """Rows of each fact read right after its own edit (independent: all rows)."""
    return [r for r in d if r["fact_id"] in r["edited_facts"].split("|")]


def checks_md(runs):
    L = ["# Verification checks and update norms per run", "",
         "| run | facts | edit steps | worst check A (repeat read) | smallest check B (weight change) | worst check C (restore) "
         "| update norm per step: min / median / max | final cumulative norm |", "|---|---|---|---|---|---|---|---|"]
    for name, (d, man) in runs.items():
        c = rows(d / "checks.csv")
        steps = [r for r in c if r["step"] != "final_restore"]
        a = max(float(r["check_A_repeat_max_diff"]) for r in c if r["check_A_repeat_max_diff"])
        b = min(float(r["check_B_weight_change_max_abs"]) for r in steps)
        cc = [float(r["check_C_restore_max_diff"]) for r in c if r.get("check_C_restore_max_diff")]
        nrm = [float(r["step_delta_frobenius_norm"]) for r in steps]
        cum = [float(r["cumulative_delta_frobenius_norm"]) for r in steps]
        L.append(f"| {name} | {len(man['order'])} | {len(steps)} | {a:.3g} | {b:.3g} | {max(cc):.3g} | "
                 f"{min(nrm):.3g} / {st.median(nrm):.3g} / {max(nrm):.3g} | {cum[-1]:.3g} |")
    return "\n".join(L) + "\n"


def quantiles_md(runs):
    L = ["# Distribution shift of reads (post-edit vs unedited), per run and route kind", "",
         "Independent runs: each fact's reads right after its own edit. Sequential runs: all reads at the last step.",
         "JS in bits (0 = identical, 1 = disjoint); KL(pre||post) in nats; TV = total variation. Columns: p50 / p90 / p99 / max.", "",
         "| run | route kind | reads | JS | KL(pre‖post) | TV | argmax changed | top-10 overlap (median) |",
         "|---|---|---|---|---|---|---|---|"]
    for name, (d, man) in runs.items():
        s = rows(d / "dist.csv")
        if man["mode"] == "independent":
            s = [r for r in s if r["fact_id"] in r["edited_facts"].split("|")]
        else:
            last = max(int(r["step"]) for r in s)
            s = [r for r in s if r["step"] == str(last)]
        groups = (("forward", lambda r: r["kind"] == "forward"), ("reverse_old", lambda r: r["kind"] == "reverse_old"),
                  ("reverse_new", lambda r: r["kind"] == "reverse_new"),
                  ("neighbour", lambda r: r["route"].startswith("control_same_relation")),
                  ("new object's own fact", lambda r: r["route"] == "control_new_object_own_fact"))
        for kind, sel in groups:
            ss = [r for r in s if sel(r) and T(r["route_valid"])]
            if not ss:
                continue
            js = [float(r["js_bits"]) for r in ss]
            kl = [float(r["kl_pre_post"]) for r in ss]
            tv = [float(r["tv"]) for r in ss]
            am = sum(T(r["argmax_changed"]) for r in ss)
            ov = st.median(float(r["top10_overlap"]) for r in ss)
            L.append(f"| {name} | {kind} | {len(ss)} | {' / '.join(q(js))} | {' / '.join(q(kl))} | {' / '.join(q(tv))} | "
                     f"{am}/{len(ss)} | {ov:.1f} |")
    return "\n".join(L) + "\n"


def per_fact(d):
    js = {(r["fact_id"], r["route"]): float(r["js_bits"]) for r in rows(d / "dist.csv")
          if r["fact_id"] in r["edited_facts"].split("|")}
    by = defaultdict(list)
    for r in own_rows(rows(d / "deltas.csv")):
        by[r["fact_id"]].append(r)
    out = {}
    for f, rs in sorted(by.items()):
        v = [r for r in rs if T(r["route_valid"])]
        g = lambda kind, lab: [r for r in v if r["kind"] == kind and r["answer_label"] == lab]
        ep = [r for r in g("forward", "new_object") if r["route"] == "forward_edit_prompt"]
        para = [r for r in g("forward", "new_object") if r["route"] != "forward_edit_prompt"]
        ro, rn = g("reverse_old", "subject"), g("reverse_new", "subject")
        ok = g("control", "correct")
        lk = [r for r in g("control", "edit_leak") if r["route"].startswith("control_same_relation")]   # o* only on neighbours
        best_leak = min(lk, key=lambda r: int(r["post_first_token_rank"]), default=None)
        cjs = [js[(f, r["route"])] for r in ok if (f, r["route"]) in js and r["route"].startswith("control_same_relation")]
        out[f] = {
            "relation": rs[0]["relation"],
            "edit": f"{int(ep[0]['post_first_token_rank']) == 1} (P={float(ep[0]['post_sequence_probability']):.2f})" if ep else "–",
            "para": f"{sum(int(r['post_first_token_rank']) == 1 for r in para)}/{len(para)}",
            "stale": (f"{sum(int(r['post_first_token_rank']) == 1 for r in ro)}/{len(ro)}"
                      if ep and int(ep[0]["post_first_token_rank"]) == 1 else f"n/a (edit failed; {sum(int(r['post_first_token_rank']) == 1 for r in ro)}/{len(ro)})"),
            "stale_n": (sum(int(r['post_first_token_rank']) == 1 for r in ro), len(ro)),
            "revnew": ", ".join(f"{r['pre_first_token_rank']}→{r['post_first_token_rank']}" for r in rn) or "–",
            "ctl": f"{sum(int(r['post_first_token_rank']) == 1 for r in ok if r['route'].startswith('control_same_relation'))}/"
                   f"{sum(1 for r in ok if r['route'].startswith('control_same_relation'))}",
            "leak": (f"{best_leak['pre_first_token_rank']}→{best_leak['post_first_token_rank']} ({best_leak['route'].replace('control_', '')})"
                     if best_leak else "–"),
            "js": f"{st.median(cjs):.4f}" if cjs else "–",
        }
    return out


def per_fact_md(name, pf):
    L = [f"# Per-fact audit: {name}", "",
         "Valid paths only. edit = new object rank 1 on the edited question (full-answer probability); para = other forward "
         "paths with the new object at rank 1; stale = reverse-from-old paths still returning the subject at rank 1; "
         "rev-new = subject rank before→after on reverse-from-new paths; ctl = same-relation neighbours keeping their correct "
         "answer at rank 1; leak = best rank of the new value on a neighbour, before→after; JS = median neighbour JS (bits). "
         "Stale reads are not counted for failed edits.", "",
         "| fact | relation | edit | para | stale | rev-new subject rank | ctl | leak | JS |", "|---|---|---|---|---|---|---|---|---|"]
    for f, x in pf.items():
        L.append(f"| {f} | {x['relation']} | {x['edit']} | {x['para']} | {x['stale']} | {x['revnew']} | {x['ctl']} | {x['leak']} | {x['js']} |")
    return "\n".join(L) + "\n"


def leaks_md(runs):
    L = ["# Largest rises of the new value o* on same-relation neighbour reads (independent runs)", "",
         "Each row: the edited fact, the neighbour route, the control fact (empty for runs before run_audit v1.2), the new "
         "value o*, its first-token rank on the neighbour's question before → after, and whether the neighbour's correct "
         "answer stayed rank 1. Sorted by rank after the edit.", ""]
    for name, (d, man) in runs.items():
        if man["mode"] != "independent":
            continue
        rs = own_rows(rows(d / "deltas.csv"))
        okk = {(r["fact_id"], r["route"]): int(r["post_first_token_rank"]) == 1 for r in rs
               if r["kind"] == "control" and r["answer_label"] == "correct"}
        # same-relation neighbours only: there the leak answer is the new value o*; on the new object's own fact it is o
        lk = [r for r in rs if r["route"].startswith("control_same_relation") and r["answer_label"] == "edit_leak"
              and T(r["route_valid"])]
        lk.sort(key=lambda r: (int(r["post_first_token_rank"]), -int(r["pre_first_token_rank"])))
        L += [f"## {name}", "", "| edited fact | control route | control fact | o* | rank before → after | correct answer still rank 1 |",
              "|---|---|---|---|---|---|"]
        for r in lk[:15]:
            L.append(f"| {r['fact_id']} | {r['route'].replace('control_', '')} | {r.get('control_fact', '')} | {r['answer']} | "
                     f"{r['pre_first_token_rank']} → {r['post_first_token_rank']} | {okk.get((r['fact_id'], r['route']))} |")
        n5 = sum(int(r["post_first_token_rank"]) <= 5 for r in lk)
        nw = sum(int(r["post_first_token_rank"]) == 1 and not okk.get((r["fact_id"], r["route"])) for r in lk)
        n2 = sum(int(r["post_first_token_rank"]) <= 2 for r in lk)
        L += ["", f"New value in a neighbour's top 5: {n5}/{len(lk)}; at rank ≤ 2: {n2}/{len(lk)}; "
                  f"new value displaces the neighbour's correct answer (rank 1): {nw}/{len(lk)}.", ""]
    return "\n".join(L) + "\n"


def overlap_md(runs, pfs):
    L = ["# Stale reverse reads across methods and models", ""]
    by_model = defaultdict(dict)
    for name, (d, man) in runs.items():
        if man["mode"] == "independent" and name in pfs:
            by_model[Path(man["model"]).name][man["method"]] = pfs[name]
    for model, ms in by_model.items():
        common = set.intersection(*(set(p) for p in ms.values()))
        allstale = [f for f in sorted(common) if all(ms[m][f]["stale_n"][0] == ms[m][f]["stale_n"][1] > 0 for m in ms)]
        nostale = [f for f in sorted(common) if all(ms[m][f]["stale_n"][0] == 0 and ms[m][f]["stale_n"][1] > 0 for m in ms)]
        L += [f"## {model}: {len(common)} facts, methods {sorted(ms)}", "",
              f"- Every valid reverse-from-old path stale under **every** method: {len(allstale)} facts: {', '.join(allstale)}",
              f"- No stale reverse-from-old path under any method: {len(nostale)} facts: {', '.join(nostale)}", ""]
    models = sorted(by_model)
    if len(models) == 2:
        a, b = models
        for m in sorted(set(by_model[a]) & set(by_model[b])):
            pa, pb = by_model[a][m], by_model[b][m]
            common = sorted(set(pa) & set(pb))
            sa = sum(pa[f]["stale_n"][0] for f in common); na = sum(pa[f]["stale_n"][1] for f in common)
            sb = sum(pb[f]["stale_n"][0] for f in common); nb = sum(pb[f]["stale_n"][1] for f in common)
            L.append(f"- {m}, facts admitted by both models ({len(common)}): stale {a} {sa}/{na}, {b} {sb}/{nb}")
        L.append("")
    return "\n".join(L) + "\n"


def sequential_md(runs):
    L = ["# Sequential runs: order, held-out facts, update norms, damaging edits", ""]
    for name, (d, man) in runs.items():
        if man["mode"] == "independent":
            continue
        c = [r for r in rows(d / "checks.csv") if r["step"] != "final_restore"]
        dd = rows(d / "deltas.csv")
        L += [f"## {name}", "", f"- order (first 15 of {len(man['order'])}): {', '.join(man['order'][:15])}",
              f"- held out (never edited): {', '.join(man.get('holdout', [])) or 'none'}",
              f"- checkpoints with a full re-read: {man.get('checkpoints') or 'every step'} (+ last step)", "",
              "| step | edited fact | update norm | cumulative norm |", "|---|---|---|---|"]
        for r in c:
            if int(r["step"]) in (1, 2, 3, 4, 5, 10, 20, 30, 40, 50, 60, 70, 78) or int(r["step"]) == len(c):
                L.append(f"| {r['step']} | {r['edited_facts']} | {float(r['step_delta_frobenius_norm']):.3g} | "
                         f"{float(r['cumulative_delta_frobenius_norm']):.3g} |")
        # step 1 damage: untouched facts that lost their old answer on the edit prompt after the first edit
        s1 = [r for r in dd if r["step"] == "1" and not T(r["fact_edited"]) and r["route"] == "forward_edit_prompt"
              and r["answer_label"] == "old_object" and T(r["route_valid"])]
        lost = [r["fact_id"] for r in s1 if int(r["post_first_token_rank"]) != 1 and int(r["pre_first_token_rank"]) == 1]
        L += ["", f"- after the first edit ({c[0]['edited_facts']}): {len(lost)}/{len(s1)} untouched facts no longer give their "
                  f"correct answer at rank 1 on the edited question{': ' + ', '.join(lost[:20]) if lost else ''}", ""]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    runs = find_runs(a.root)
    (out / "checks.md").write_text(checks_md(runs), encoding="utf-8")
    (out / "quantiles.md").write_text(quantiles_md(runs), encoding="utf-8")
    pfs = {}
    for name, (d, man) in runs.items():
        if man["mode"] == "independent":
            pfs[name] = per_fact(d)
            (out / f"per_fact_{name.replace('/', '_')}.md").write_text(per_fact_md(name, pfs[name]), encoding="utf-8")
    (out / "leaks.md").write_text(leaks_md(runs), encoding="utf-8")
    (out / "overlap.md").write_text(overlap_md(runs, pfs), encoding="utf-8")
    (out / "sequential.md").write_text(sequential_md(runs), encoding="utf-8")
    print(VERSION, "|", len(runs), "runs:", list(runs))
    print("wrote", sorted(p.name for p in out.iterdir()))


if __name__ == "__main__":
    main()
