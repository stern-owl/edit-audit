#!/usr/bin/env python3
"""Analysis of run_audit.py outputs (deltas.csv + dist.csv). Standard library only.

Usage:
  python analyze_audit.py --templates relation_templates_v3.json --out <dir> --run METHOD=<audit output dir> [--run ...]

Independent runs (one edit, read, restore per fact) -> per method x relation, valid paths only:
  Q1  edit_ok            new object rank 1 on the edited question                                   (facts)
      para_new1          new object rank 1 on the other forward paths                               (paths)
  Q2  fwd_old1           old object still rank 1 on a forward path                                  (paths)
      rev_old_stale      subject still rank 1 on a reverse path naming o, SUCCESSFUL edits only     (paths)
      rev_old_survival   of those reverse paths that returned the subject at rank 1 before the edit, the share still
                         doing so after it (successful edits only)                                  (paths)
      rev_old_stale_all  the same over all edits, failed ones included (for comparison)
  Q3  rev_new_rank1 / rev_new_rises / rev_new_violation   reverse path naming o*, successful edits only; violation
                         applies the relation contract (inverse functional -> subject must be rank 1; otherwise its
                         log-probability must rise)                                                 (paths)
      nb_correct1        same-relation neighbours keep their correct answer at rank 1                (paths)
      nb_leak_top5       o* enters a same-relation neighbour's top 5                                (paths)
      nb_pass_shift      among neighbour reads that PASS the rank-1 check, share with JS > 0.01 bit  (passing reads)
      own_correct1       the new object's own fact keeps the new object at rank 1 (a separate check: its correct
                         answer is the new object, so it is not a side-effect read)                 (paths)
      nb JS median       median full-vocabulary JS (bits) on same-relation neighbour reads
  Every rate has a 95% percentile bootstrap interval over FACTS (2000 resamples, seed 0): facts are resampled, the
  path-level rate is recomputed on the resampled facts. Nothing is averaged across seeds as if they were facts.

Sequential / batch runs -> per step at which every fact was read:
  edited facts:   edit_ok; rev_old_stale among edits that still hold at that step
  unedited facts: retention (old object still rank 1 on the edit prompt), separately for held-out facts never edited
  neighbours:     correct@1 and median JS only over same-relation neighbours whose own fact was not edited by step k
  persistence:    per edited fact, edit_ok right after its own edit vs at the last step.
"""
import argparse
import csv
import json
import random
import statistics as st
from collections import defaultdict
from pathlib import Path

VERSION = "analyze_audit v1.2 (2026-11-05)"
B, ALPHA = 2000, 0.05


def load(run_dir):
    run_dir = Path(run_dir)
    d = list(csv.DictReader(open(run_dir / "deltas.csv", newline="", encoding="utf-8")))
    s = list(csv.DictReader(open(run_dir / "dist.csv", newline="", encoding="utf-8")))
    m = json.loads((run_dir / "manifest.json").read_text()) if (run_dir / "manifest.json").exists() else {}
    return d, s, m


def T(x):
    return x in (True, "True")


def rank(r, k="post_first_token_rank"):
    return int(r[k])


def fact_records(deltas, dists, cardinality, step=None, edit_step=None):
    """Per fact: lists of 0/1 outcomes per metric (paths), from the reads at `step` (default: each fact's own step).

    Conventions (v1.2, after review):
      * Reverse-path metrics (rev_old_stale, rev_new_*) count only facts whose edit succeeded, i.e. the new object is
        rank 1 on the edited question in the same read (sequential: the edit still holds at `step`). A failed edit leaves
        the reverse path unchanged trivially. The unconditional versions are kept as *_all.
      * Control reads are split by role. Same-relation neighbours (nb_*) measure side effects on other facts; the new
        object's own fact (own_*) is a different check, because its correct answer IS the new object. Neighbours whose
        correct answer equals the new object are excluded from nb_* (screening already prevents them; asserted here).
      * nb_pass_shift: among neighbour reads that PASS the rank-1 specificity check, the share whose next-token
        distribution moved by JS > 0.01 bit (denominator = passing reads).
      * With edit_step (fact -> step at which it was edited), sequential runs also give nbU_*: neighbours whose own fact
        was not edited by `step` (an edited neighbour is expected to change). Rows without a control_fact column (runs
        before run_audit v1.2) give no nbU_* values."""
    by = defaultdict(lambda: defaultdict(list))
    js = defaultdict(dict)
    for r in dists:
        if step is None or r["step"] == str(step):
            js[(r["fact_id"], r["step"], r["route"])] = float(r["js_bits"])
    new_obj = {}
    for r in deltas:
        if r["route"] == "forward_edit_prompt" and r["answer_label"] == "new_object":
            new_obj[r["fact_id"]] = r["answer"]
    for r in deltas:
        if step is not None and r["step"] != str(step):
            continue
        if step is None and r["fact_id"] not in r["edited_facts"].split("|"):
            continue
        if not T(r["route_valid"]):
            continue
        f, kind, lab, route = r["fact_id"], r["kind"], r["answer_label"], r["route"]
        rec = by[f]
        rec["_relation"] = r["relation"]
        rec["_edited"] = T(r["fact_edited"])
        inv_fun = cardinality.get(r["relation"], {}).get("inverse") == "functional"
        if kind == "forward":
            if route == "forward_edit_prompt":
                if lab == "new_object":
                    rec["edit_ok"].append(rank(r) == 1)
                if lab == "old_object":
                    rec["retention"].append(rank(r) == 1)
            else:
                if lab == "new_object":
                    rec["para_new1"].append(rank(r) == 1)
            if lab == "old_object":
                rec["fwd_old1"].append(rank(r) == 1)
        elif kind == "reverse_old" and lab == "subject":
            rec["rev_old_stale_all"].append(rank(r) == 1)
            rec["_rev_old_pre1"].append(r["pre_first_token_rank"] == "1")
        elif kind == "reverse_new" and lab == "subject":
            r1, rises = rank(r) == 1, float(r["delta_sum_logprob"]) > 0
            rec["rev_new_rank1_all"].append(r1)
            rec["rev_new_rises_all"].append(rises)
            rec["rev_new_violation_all"].append((not r1) if inv_fun else (not rises))
        elif kind == "control":
            j = js.get((f, r["step"], route))
            own = route == "control_new_object_own_fact"
            if lab == "correct":
                ok = rank(r) == 1
                if own:
                    rec["own_correct1"].append(ok)
                    continue
                if r["answer"] == new_obj.get(f):
                    continue                     # a neighbour whose correct answer is the new object: not a side-effect read
                rec["nb_correct1"].append(ok)
                if j is not None:
                    rec["nb_js"].append(j)
                    if ok:
                        rec["nb_pass_shift"].append(j > 0.01)
                cf = r.get("control_fact")
                if edit_step is not None and step is not None and cf is not None:
                    if (not cf) or cf not in edit_step or edit_step[cf] > step:
                        rec["nbU_correct1"].append(ok)
                        if j is not None:
                            rec["nbU_js"].append(j)
            elif lab == "edit_leak" and not own:
                rec["nb_leak_top5"].append(rank(r) <= 5)
    for rec in by.values():
        ok = bool(rec["edit_ok"]) and rec["edit_ok"][0]
        for m in ("rev_old_stale", "rev_new_rank1", "rev_new_rises", "rev_new_violation"):
            rec[m] = list(rec[m + "_all"]) if ok else []
        # survival: of the reverse-from-old reads returning the subject at rank 1 BEFORE the edit, still rank 1 after
        rec["rev_old_survival"] = [st_ for st_, p1 in zip(rec["rev_old_stale_all"], rec["_rev_old_pre1"]) if p1] if ok else []
    return by


METRICS = ["edit_ok", "para_new1", "fwd_old1", "rev_old_stale", "rev_old_survival", "rev_old_stale_all", "rev_new_rank1",
           "rev_new_rises", "rev_new_violation", "nb_correct1", "nb_leak_top5", "nb_pass_shift", "own_correct1", "retention"]


def rate(recs, metric):
    num = sum(sum(r[metric]) for r in recs)
    den = sum(len(r[metric]) for r in recs)
    return num, den


def boot(recs, metric, seed=0):
    recs = [r for r in recs if r[metric]]
    if not recs:
        return None
    rnd = random.Random(seed)
    vals = []
    for _ in range(B):
        sample = [recs[rnd.randrange(len(recs))] for _ in recs]
        n, d = rate(sample, metric)
        vals.append(n / d)
    vals.sort()
    return vals[int(ALPHA / 2 * B)], vals[int((1 - ALPHA / 2) * B) - 1]


def fmt(recs, metric):
    n, d = rate(recs, metric)
    if d == 0:
        return "–"
    ci = boot(recs, metric)
    return f"{n}/{d} = {n / d:.0%} [{ci[0]:.0%}, {ci[1]:.0%}]"


def table(groups, metrics, title):
    lines = [f"### {title}", "", "| group | facts | " + " | ".join(metrics) + " | nb JS median |",
             "|---|---|" + "---|" * len(metrics) + "---|"]
    rows = []
    for name, recs in groups:
        js = [j for r in recs for j in r["nb_js"]]
        lines.append(f"| {name} | {len(recs)} | " + " | ".join(fmt(recs, m) for m in metrics) +
                     f" | {st.median(js):.4f} |" if js else f"| {name} | {len(recs)} | " + " | ".join(fmt(recs, m) for m in metrics) + " | – |")
        for m in metrics:
            n, d = rate(recs, m)
            ci = boot(recs, m) if d else None
            rows.append({"table": title, "group": name, "facts": len(recs), "metric": m, "num": n, "den": d,
                         "rate": n / d if d else "", "ci_low": ci[0] if ci else "", "ci_high": ci[1] if ci else ""})
    return lines + [""], rows


def independent_report(runs, cardinality):
    lines, rows = [], []
    for method, (deltas, dists, man) in runs.items():
        recs = fact_records(deltas, dists, cardinality)
        by_rel = defaultdict(list)
        for f, r in sorted(recs.items()):
            by_rel[r["_relation"]].append(r)
        groups = [("ALL", list(recs.values()))] + sorted(by_rel.items())
        groups += [("inverse functional", [r for r in recs.values()
                                           if cardinality.get(r["_relation"], {}).get("inverse") == "functional"]),
                   ("inverse non-functional", [r for r in recs.values()
                                               if cardinality.get(r["_relation"], {}).get("inverse") != "functional"])]
        l, rr = table(groups, METRICS[:-1], f"{method} ({man.get('mode', '?')}, model {Path(man.get('model', '?')).name}, seed {man.get('seed', '?')})")
        lines += l
        rows += [{"method": method, **x} for x in rr]
    return lines, rows


def sequential_report(runs, cardinality):
    lines, rows = [], []
    for method, (deltas, dists, man) in runs.items():
        n_facts = len({r["fact_id"] for r in deltas})
        reads = defaultdict(set)
        for r in deltas:
            reads[r["step"]].add(r["fact_id"])
        full = sorted((int(s) for s, fs in reads.items() if len(fs) == n_facts and s.isdigit()))
        lines += [f"### {method} ({man.get('mode', '?')}, model {Path(man.get('model', '?')).name}, {n_facts} facts, "
                  f"full re-reads at steps {full})", "",
                  "| step k | edited | edit_ok (edited) | rev_old_stale (edits holding) | retention (not yet edited) | retention (held out) | "
                  "untouched neighbours correct@1 | JS median (untouched neighbours) |",
                  "|---|---|---|---|---|---|---|---|"]
        edit_step = {}
        for r in deltas:
            if T(r["fact_edited"]) and r.get("fact_edit_step"):
                edit_step[r["fact_id"]] = int(r["fact_edit_step"])
        for k in full:
            recs = fact_records(deltas, dists, cardinality, step=k, edit_step=edit_step)
            ed = [r for r in recs.values() if r["_edited"]]
            un = [r for r in recs.values() if not r["_edited"]]
            ho = [r for f, r in recs.items() if f not in edit_step]
            js = [j for r in recs.values() for j in r["nbU_js"]]
            lines.append(f"| {k} | {len(ed)} | {fmt(ed, 'edit_ok')} | {fmt(ed, 'rev_old_stale')} | {fmt(un, 'retention')} | "
                         f"{fmt(ho, 'retention')} | {fmt(list(recs.values()), 'nbU_correct1')} | "
                         + (f"{st.median(js):.4f} |" if js else "– |"))
            for grp, rr, ms in (("edited", ed, ("edit_ok", "rev_old_stale")), ("unedited", un, ("retention",)),
                                ("held_out", ho, ("retention",)), ("all", list(recs.values()), ("nbU_correct1",))):
                for m in ms:
                    n, d = rate(rr, m)
                    rows.append({"method": method, "table": "sequential", "group": grp, "step": k, "facts": len(rr),
                                 "metric": m, "num": n, "den": d, "rate": n / d if d else ""})
        # persistence: own-step read vs last step
        own = fact_records(deltas, dists, cardinality)
        last = fact_records(deltas, dists, cardinality, step=full[-1]) if full else {}
        both = [f for f in own if f in last and own[f]["edit_ok"] and last[f]["edit_ok"]]
        kept = sum(own[f]["edit_ok"][0] and last[f]["edit_ok"][0] for f in both)
        lost = sum(own[f]["edit_ok"][0] and not last[f]["edit_ok"][0] for f in both)
        took = sum(own[f]["edit_ok"][0] for f in both)
        lines += ["", f"Persistence of the edited question: {took}/{len(both)} edits took at their own step; of those, "
                      f"{kept} still hold at step {full[-1] if full else '?'} and {lost} were lost.", ""]
        rows.append({"method": method, "table": "persistence", "group": "edited", "step": full[-1] if full else "",
                     "facts": len(both), "metric": "edit_ok kept / took", "num": kept, "den": took,
                     "rate": kept / took if took else ""})
    return lines, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", required=True, metavar="NAME=DIR")
    ap.add_argument("--templates", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rel = json.loads(Path(a.templates).read_text(encoding="utf-8"))["relations"]
    cardinality = {k: v.get("cardinality", {}) for k, v in rel.items()}
    runs = {}
    for spec in a.run:
        name, d = spec.split("=", 1)
        runs[name] = load(d)
    ind = {k: v for k, v in runs.items() if v[2].get("mode", "independent") == "independent"}
    seq = {k: v for k, v in runs.items() if k not in ind}
    lines = [f"# Audit report ({VERSION})", "",
             "Rates are over valid paths; brackets are 95% bootstrap intervals over facts. "
             "rev_new_violation applies the relation contract of the templates file.", ""]
    rows = []
    if ind:
        l, r = independent_report(ind, cardinality); lines += ["## Independent edits", ""] + l; rows += r
    if seq:
        l, r = sequential_report(seq, cardinality); lines += ["## Sequential / batch edits", ""] + l; rows += r
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with open(out / "summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, restval="")
        w.writeheader()
        w.writerows(rows)
    print("\n".join(lines))
    print("wrote", out / "report.md", out / "summary.csv")


if __name__ == "__main__":
    main()
