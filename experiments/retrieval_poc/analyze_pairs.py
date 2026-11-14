#!/usr/bin/env python3
"""Analysis of run_audit.py --mode pairs outputs (N1, commutativity of edit pairs). Standard library only.

Per pair (definitions fixed in research-log entry 10):
  read gap            median JS(AB || BA) over the valid paths of A and B (commute.csv); sentinel gap: same over sentinels
  order-dependent     a (path, answer) read of A or B whose rank-1 verdict differs between the AB and BA states (deltas.csv)
  rel. weight gap     ||dAB - dBA|| / mean(||dAB||, ||dBA||)                    (pairs.csv)
  rel. additivity gap mean over orders of ||dXY - (dA + dB)|| / ||dXY||
  first-edit retention in order XY, X's edited question still answers o*_X at rank 1 after Y's edit, among X that hold
                      after their own edit in the independent run (--independent METHOD=DIR)
  second-edit success in order XY, Y's edited question answers o*_Y at rank 1, among Y that succeed independently
Usage: python analyze_pairs.py --out DIR --run METHOD=PAIRS_AUDIT_DIR [...] [--independent METHOD=AUDIT_DIR ...]
"""
import argparse
import csv
import random
import statistics
from collections import defaultdict
from pathlib import Path

VERSION = "analyze_pairs v1.0 (2026-11-05)"
CLASSES = ("disjoint", "same_relation", "neighbour", "shared_object", "same_new", "chained", "other_shared")


def T(x):
    return x in ("True", True)


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def independent_ok(d):
    """fact_id -> edit succeeded (new object rank 1 on the edited question) in an independent run."""
    return {r["fact_id"]: r["post_first_token_rank"] == "1" for r in rows(Path(d) / "deltas.csv")
            if r["route"] == "forward_edit_prompt" and r["answer_label"] == "new_object" and r["fact_id"] in r["edited_facts"].split("|")}


def load(d, ind_ok):
    d = Path(d)
    pairs = {r["pair_id"]: dict(r) for r in rows(d / "pairs.csv")}
    js = defaultdict(list); sjs = defaultdict(list)
    for r in rows(d / "commute.csv"):
        if T(r["route_valid"]):
            (sjs if r["role"] == "sentinel" else js)[r["pair_id"]].append(float(r["js_bits"]))
    verdict = defaultdict(dict)          # pair -> order -> {(fact, route, label): rank1}
    edit_rank1 = defaultdict(dict)       # (pair, order) -> {fact: new object rank 1 on its edited question}
    for r in rows(d / "deltas.csv"):
        pid, order = r["step"].split(":")
        if r["fact_id"] not in r["edited_facts"].split("|"):
            continue                     # sentinels: reported via the sentinel gap
        if T(r["route_valid"]):
            verdict[pid].setdefault(order, {})[(r["fact_id"], r["route"], r["answer_label"])] = r["post_first_token_rank"] == "1"
        if r["route"] == "forward_edit_prompt" and r["answer_label"] == "new_object":
            edit_rank1[(pid, order)][r["fact_id"]] = r["post_first_token_rank"] == "1"
    out = {}
    for pid, p in pairs.items():
        a, b = p["fact_a"], p["fact_b"]
        v = verdict[pid]
        keys = sorted(set(v.get("AB", {})) & set(v.get("BA", {})))
        dep = sum(v["AB"][k] != v["BA"][k] for k in keys)
        f = lambda k: float(p[k])
        rel_w = f("gap_AB_BA") / ((f("norm_dAB") + f("norm_dBA")) / 2)
        rel_add = (f("add_gap_AB") / f("norm_dAB") + f("add_gap_BA") / f("norm_dBA")) / 2
        first, second = [], []
        for order, (x, y) in (("AB", (a, b)), ("BA", (b, a))):
            e = edit_rank1[(pid, order)]
            if ind_ok is None or ind_ok.get(x):
                first.append(e[x])
            if ind_ok is None or ind_ok.get(y):
                second.append(e[y])
        out[pid] = {"class": p["pair_class"], "a": a, "b": b, "read_gap": statistics.median(js[pid]),
                    "sent_gap": statistics.median(sjs[pid]) if sjs[pid] else None, "dep": dep, "n_paths": len(keys),
                    "rel_w": rel_w, "rel_add": rel_add, "key_cos": float(p["key_cos_mean"]) if p.get("key_cos_mean") else None,
                    "cos_upd": f("cos_dA_dB"), "first": first, "second": second,
                    "check_B_min": f("check_B_min"), "check_C_max": f("check_C_max")}
    return out


def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs); i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x, y):
    rx, ry = ranks(x), ranks(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")


def boot_spearman(x, y, seed=0, n=1000):
    rnd = random.Random(seed); vals = []
    for _ in range(n):
        idx = [rnd.randrange(len(x)) for _ in x]
        s = spearman([x[i] for i in idx], [y[i] for i in idx])
        if s == s:
            vals.append(s)
    vals.sort()
    return vals[int(.025 * len(vals))], vals[int(.975 * len(vals)) - 1]


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def q(xs, p):
    xs = sorted(x for x in xs if x is not None)
    return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else None


def fmt(x, nd=4):
    return "–" if x is None else f"{x:.{nd}f}"


def pct(n, d):
    return f"{n}/{d} = {n / d:.0%}" if d else "–"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", required=True, metavar="METHOD=DIR")
    ap.add_argument("--independent", action="append", default=[], metavar="METHOD=DIR")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ind = dict(s.split("=", 1) for s in a.independent)
    runs = {}
    for s in a.run:
        name, d = s.split("=", 1)
        runs[name] = load(d, independent_ok(ind[name]) if name in ind else None)
    L = [f"# N1 commutativity of edit pairs ({VERSION})", "",
         "Definitions: research-log entry 10. Read gap = median JS(AB‖BA) over the valid paths of A and B (bits); "
         "order-dependent = share of (path, answer) reads of A and B whose rank-1 verdict differs between orders.", ""]
    L += ["## Checks", "", "| method | pairs | min check B | max check C |", "|---|---|---|---|"]
    for name, P in runs.items():
        L.append(f"| {name} | {len(P)} | {min(p['check_B_min'] for p in P.values()):.3g} | {max(p['check_C_max'] for p in P.values()):.3g} |")
    L += ["", "## By pair class", "",
          "| method | class | pairs | read gap median [q25, q75] | order-dependent verdicts | rel. weight gap median | rel. additivity gap median | update cosine median | key cosine median | first-edit retention | second-edit success | sentinel gap median |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    ratio_lines = []
    for name, P in runs.items():
        disj = med([p["read_gap"] for p in P.values() if p["class"] == "disjoint"])
        for c in CLASSES:
            S = [p for p in P.values() if p["class"] == c]
            if not S:
                continue
            rg = [p["read_gap"] for p in S]
            dep, npth = sum(p["dep"] for p in S), sum(p["n_paths"] for p in S)
            fr = [x for p in S for x in p["first"]]; sc = [x for p in S for x in p["second"]]
            L.append(f"| {name} | {c} | {len(S)} | {fmt(med(rg))} [{fmt(q(rg, .25))}, {fmt(q(rg, .75))}] | {pct(dep, npth)} | "
                     f"{fmt(med([p['rel_w'] for p in S]), 3)} | {fmt(med([p['rel_add'] for p in S]), 3)} | "
                     f"{fmt(med([p['cos_upd'] for p in S]), 3)} | {fmt(med([p['key_cos'] for p in S]), 3)} | "
                     f"{pct(sum(fr), len(fr))} | {pct(sum(sc), len(sc))} | {fmt(med([p['sent_gap'] for p in S]))} |")
            if c != "disjoint" and disj:
                ratio_lines.append(f"| {name} | {c} | {med(rg) / disj:.1f}× |")
    L += ["", "Read gap relative to disjoint pairs (median / median):", "", "| method | class | ratio |", "|---|---|---|"] + ratio_lines
    L += ["", "## Conflict predictors (all pairs; Spearman ρ with 95% bootstrap interval)", "",
          "| method | key cosine vs rel. weight gap | key cosine vs read gap | update cosine vs read gap | rel. weight gap vs read gap |",
          "|---|---|---|---|---|"]
    for name, P in runs.items():
        V = [p for p in P.values() if p["key_cos"] is not None]
        cell = lambda x, y: (lambda s, ci: f"{s:.2f} [{ci[0]:.2f}, {ci[1]:.2f}]")(spearman(x, y), boot_spearman(x, y))
        kc, rw, rg, cu = [p["key_cos"] for p in V], [p["rel_w"] for p in V], [p["read_gap"] for p in V], [abs(p["cos_upd"]) for p in V]
        L.append(f"| {name} | {cell(kc, rw)} | {cell(kc, rg)} | {cell(cu, rg)} | {cell(rw, rg)} |")
    L += ["", "## Pairs with the largest read gap (per method, top 8)", ""]
    for name, P in runs.items():
        L += [f"**{name}**", "", "| pair | class | A | B | read gap | order-dependent | rel. weight gap | key cosine | first edit held (AB, BA) |", "|---|---|---|---|---|---|---|---|---|"]
        for pid, p in sorted(P.items(), key=lambda kv: -kv[1]["read_gap"])[:8]:
            L.append(f"| {pid} | {p['class']} | {p['a']} | {p['b']} | {p['read_gap']:.4f} | {p['dep']}/{p['n_paths']} | "
                     f"{p['rel_w']:.3f} | {fmt(p['key_cos'], 3)} | {p['first']} |")
        L.append("")
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    with open(out / "pairs_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["method", "pair_id", "class", "fact_a", "fact_b", "read_gap", "sent_gap", "dep", "n_paths", "rel_w",
                    "rel_add", "cos_upd", "key_cos", "first_held", "second_ok"])
        for name, P in runs.items():
            for pid, p in P.items():
                w.writerow([name, pid, p["class"], p["a"], p["b"], p["read_gap"], p["sent_gap"], p["dep"], p["n_paths"],
                            p["rel_w"], p["rel_add"], p["cos_upd"], p["key_cos"], "|".join(map(str, p["first"])),
                            "|".join(map(str, p["second"]))])
    print("\n".join(L).encode("ascii", "replace").decode())


if __name__ == "__main__":
    main()
