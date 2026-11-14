#!/usr/bin/env python3
"""Analysis of run_audit.py --mode programs outputs: N5 (compensating edits) and N2 (cascading repair). Standard library.
Definitions fixed in research-log entry 11.

N5, per fact A with a `compensate` program (step 1 = after A, step 2 = after A~inv):
  edit_ok        o* at rank 1 on the edited question after A
  compensated    o at rank 1 on the edited question after A~inv
  overcomp       P(o) on the edited question after A~inv above its unedited value
  restored       share of A's valid (path, answer) reads whose rank-1 verdict equals the unedited verdict, after A~inv
  JS             median JS vs the unedited read over A's valid paths after A / after A~inv; neighbours (same-relation
                 controls) and sentinels separately; neighbour residue ratio = mean neighbour JS after A~inv / after A
  weight residue cumulative update norm after A~inv / after A
  late           compensate_late vs reference (commute.csv): median JS over A's paths, the X facts, the sentinels;
                 compensated after the late inverse edit
N2, per case A (S = swap__A, the repair s': o* -> o):
  states: A alone (cascade step 1), A then S (cascade step 2), S then A (cascade_rev), batch (cascade_batch)
  A holds / S holds (new object rank 1 on its edited question); FD violated = s' still answers o* (S's edited question
  has its old object o* at rank 1); reverse checks on valid paths: from o* -> s (A reverse_new subject rank 1),
  from o* not s' (A reverse_new alt not rank 1), from o -> s' (S reverse_new subject rank 1), from o not s (A reverse_old
  subject not rank 1); fully consistent = A and S hold and every reverse check passes.
Usage: python analyze_programs.py --out DIR --run METHOD=AUDIT_DIR [...]
"""
import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path

VERSION = "analyze_programs v1.0 (2026-11-05)"


def T(x):
    return x in ("True", True)


def rows(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def pct(n, d):
    return f"{n}/{d} = {n / d:.0%}" if d else "–"


def fmt(x, nd=4):
    return "–" if x is None else f"{x:.{nd}f}"


def load(d):
    d = Path(d)
    D = defaultdict(lambda: defaultdict(dict))          # step -> fact -> {(route, label): row}
    for r in rows(d / "deltas.csv"):
        D[r["step"]][r["fact_id"]][(r["route"], r["answer_label"].split(":")[0])] = r
    J = defaultdict(lambda: defaultdict(dict))          # step -> fact -> route -> (valid, js)
    for r in rows(d / "dist.csv"):
        J[r["step"]][r["fact_id"]][r["route"]] = (T(r["route_valid"]), float(r["js_bits"]))
    C = {r["step"]: r for r in rows(d / "checks.csv")}
    M = rows(d / "commute.csv") if (d / "commute.csv").exists() else []
    return D, J, C, M


def rank1(row):
    return row["post_first_token_rank"] == "1"


def js_of(J, step, f, pred):
    return [js for route, (v, js) in J[step][f].items() if v and pred(route)]


def n5(D, J, C, M):
    facts = sorted(s.split(":", 1)[1][:-2] for s in D if s.startswith("comp:") and s.endswith(":1"))
    sent = None
    recs = {}
    for f in facts:
        s1, s2 = f"comp:{f}:1", f"comp:{f}:2"
        a1, a2 = D[s1][f], D[s2][f]
        if sent is None:
            sent = [x for x in D[s1] if x != f]
        ep_new1, ep_old2 = a1[("forward_edit_prompt", "new_object")], a2[("forward_edit_prompt", "old_object")]
        valid = [k for k, r in a2.items() if T(r["route_valid"])]
        restored = sum((a2[k]["post_first_token_rank"] == "1") == (a2[k]["pre_first_token_rank"] == "1") for k in valid)
        nb = lambda r: r.startswith("control_same_relation")
        own = lambda r: not r.startswith("control")
        nb1, nb2 = mean(js_of(J, s1, f, nb)), mean(js_of(J, s2, f, nb))
        c1, c2 = float(C[s1]["cumulative_delta_frobenius_norm"]), float(C[s2]["cumulative_delta_frobenius_norm"])
        recs[f] = {"edit_ok": rank1(ep_new1), "comp": rank1(ep_old2),
                   "overcomp": float(ep_old2["post_sum_logprob"]) > float(ep_old2["pre_sum_logprob"]),
                   "d_logp_o": float(ep_old2["post_sum_logprob"]) - float(ep_old2["pre_sum_logprob"]),
                   "restored": (restored, len(valid)), "js1": med(js_of(J, s1, f, own)), "js2": med(js_of(J, s2, f, own)),
                   "nb1": nb1, "nb2": nb2, "nb_ratio": (nb2 / nb1) if nb1 else None,
                   "sent2": med([js for x in sent for js in js_of(J, s2, x, lambda r: True)]),
                   "w_res": c2 / c1 if c1 else None, "check_C": float(C[s2]["check_C_restore_max_diff"])}
    late = {}
    for s in D:
        if s.startswith("late:"):
            f = s.split(":")[1]
            rr = [r for r in M if r["pair_id"] == f"late:{f}" and T(r["route_valid"])]
            last = D[s][f][("forward_edit_prompt", "old_object")]
            late[f] = {"A": med([float(r["js_bits"]) for r in rr if r["fact_id"] == f and not r["route"].startswith("control")]),
                       "X": med([float(r["js_bits"]) for r in rr if r["fact_id"] != f and r["role"] == "read"]),
                       "sent": med([float(r["js_bits"]) for r in rr if r["role"] == "sentinel"]), "comp": rank1(last)}
    return recs, late


def n2(D, J):
    cases = sorted(s.split(":")[1] for s in D if s.startswith("cascade:") and s.endswith(":1"))
    states = {"A alone": lambda a: f"cascade:{a}:1", "A then S": lambda a: f"cascade:{a}:2",
              "S then A": lambda a: f"cascade_rev:{a}:2", "batch A+S": lambda a: f"cascade_batch:{a}:1"}
    out = defaultdict(dict)
    for a in cases:
        s = f"swap__{a}"
        for name, st in states.items():
            step = st(a)
            if step not in D:
                continue
            A, S = D[step][a], D[step][s]
            v = lambda R, route_prefix, lab: [R[k] for k in R if k[0].startswith(route_prefix) and k[1] == lab and T(R[k]["route_valid"])]
            a_holds = rank1(A[("forward_edit_prompt", "new_object")])
            s_holds = rank1(S[("forward_edit_prompt", "new_object")])
            fd_viol = rank1(S[("forward_edit_prompt", "old_object")])
            chk = {"o*->s": [rank1(r) for r in v(A, "reverse_new", "subject")],
                   "o*-/->s'": [not rank1(r) for r in v(A, "reverse_new", "alt")],
                   "o->s'": [rank1(r) for r in v(S, "reverse_new", "subject")],
                   "o-/->s": [not rank1(r) for r in v(A, "reverse_old", "subject")]}
            nbjs = mean(js_of(J, step, a, lambda r: r.startswith("control_same_relation")) +
                        js_of(J, step, s, lambda r: r.startswith("control_same_relation")))
            out[a][name] = {"A": a_holds, "S": s_holds, "fd": fd_viol, "chk": chk,
                            "full": a_holds and s_holds and all(all(x) for x in chk.values()), "nbjs": nbjs}
    return cases, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", required=True, metavar="METHOD=DIR")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    runs = {s.split("=", 1)[0]: load(s.split("=", 1)[1]) for s in a.run}
    L = [f"# N5 compensation and N2 cascade ({VERSION})", "", "Definitions: research-log entry 11.", "",
         "## Checks", "", "| method | program steps | min check B | max check C |", "|---|---|---|---|"]
    for name, (D, J, C, M) in runs.items():
        L.append(f"| {name} | {len(C)} | {min(float(c['check_B_weight_change_max_abs']) for c in C.values()):.3g} | "
                 f"{max(float(c['check_C_restore_max_diff']) for c in C.values() if c.get('check_C_restore_max_diff')):.3g} |")
    L += ["", "## N5 compensating edits", "",
          "| method | facts | edit ok | compensated (of edit ok) | over-compensated (of compensated) | median Δlog P(o) | verdicts restored | median JS A after edit → after undo | neighbour JS after edit → after undo | median neighbour residue ratio | sentinel JS after undo | median weight residue |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    late_lines = []
    for name, (D, J, C, M) in runs.items():
        R, late = n5(D, J, C, M)
        ok = [r for r in R.values() if r["edit_ok"]]
        cp = [r for r in ok if r["comp"]]
        rs = (sum(r["restored"][0] for r in ok), sum(r["restored"][1] for r in ok))
        L.append(f"| {name} | {len(R)} | {pct(len(ok), len(R))} | {pct(len(cp), len(ok))} | "
                 f"{pct(sum(r['overcomp'] for r in cp), len(cp))} | {fmt(med([r['d_logp_o'] for r in cp]), 2)} | {pct(*rs)} | "
                 f"{fmt(med([r['js1'] for r in ok]))} → {fmt(med([r['js2'] for r in ok]))} | "
                 f"{fmt(med([r['nb1'] for r in ok]))} → {fmt(med([r['nb2'] for r in ok]))} | {fmt(med([r['nb_ratio'] for r in ok]), 2)} | "
                 f"{fmt(med([r['sent2'] for r in ok]))} | {fmt(med([r['w_res'] for r in ok]), 3)} |")
        if late:
            same = [f for f in late if f in R and R[f]["edit_ok"]]
            late_lines.append(f"| {name} | {len(late)} | {pct(sum(l['comp'] for l in late.values()), len(late))} | "
                              f"{fmt(med([late[f]['A'] for f in same]))} | {fmt(med([R[f]['js2'] for f in same]))} | "
                              f"{fmt(med([l['X'] for l in late.values()]))} | {fmt(med([l['sent'] for l in late.values()]))} |")
    L += ["", "Late compensation (5 unrelated edits between the edit and its compensation), compared with the reference state "
          "(the 5 edits alone):", "",
          "| method | facts | compensated | median JS A's paths: late vs reference | same facts: immediate undo vs unedited | median JS X facts | median JS sentinels |",
          "|---|---|---|---|---|---|---|"] + late_lines
    L += ["", "## N2 cascading repair (swap)", "",
          "| method | state | cases | A holds | S holds | both hold | s' still answers o* (FD violated) | o*→s | o*↛s' | o→s' | o↛s | fully consistent | median neighbour JS |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    detail = []
    for name, (D, J, C, M) in runs.items():
        cases, out = n2(D, J)
        for st in ("A alone", "A then S", "S then A", "batch A+S"):
            X = [out[c][st] for c in cases if st in out[c]]
            if not X:
                continue
            ck = lambda k: (sum(sum(x["chk"][k]) for x in X), sum(len(x["chk"][k]) for x in X))
            L.append(f"| {name} | {st} | {len(X)} | {pct(sum(x['A'] for x in X), len(X))} | {pct(sum(x['S'] for x in X), len(X))} | "
                     f"{pct(sum(x['A'] and x['S'] for x in X), len(X))} | {pct(sum(x['fd'] for x in X), len(X))} | "
                     + " | ".join(pct(*ck(k)) for k in ("o*->s", "o*-/->s'", "o->s'", "o-/->s")) +
                     f" | {pct(sum(x['full'] for x in X), len(X))} | {fmt(med([x['nbjs'] for x in X]))} |")
        for c in cases:
            detail.append(f"| {name} | {c} | " + " | ".join(
                ("A" if out[c][st]["A"] else "-") + ("S" if out[c][st]["S"] else "-") + ("!" if out[c][st]["fd"] else "")
                if st in out[c] else "n/a" for st in ("A alone", "A then S", "S then A", "batch A+S")) + " |")
    L += ["", "Per case (A / S = that edit holds; ! = s' still answers o*):", "",
          "| method | case | A alone | A then S | S then A | batch |", "|---|---|---|---|---|---|"] + detail
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L).encode("ascii", "replace").decode())


if __name__ == "__main__":
    main()
