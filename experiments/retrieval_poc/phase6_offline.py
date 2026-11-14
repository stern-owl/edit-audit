#!/usr/bin/env python3
"""Phase 6 offline analyses on logged run_audit.py outputs (no model, no GPU). Standard library only.

  N3  audit planning: which access paths (route types) to read under a question budget, how many inconsistent edits a
      plan detects, the CounterFact-style "standard plan" as a baseline, and transfer of plans across models;
  N2  admission control: (a) for one-to-one relations, how often a successful edit leaves the model in a state that
      violates the declared inverse functional dependency; (b) how well pre-edit signals predict violations (AUROC);
  E10 standard metrics on the same edits: CounterFact-style efficacy / paraphrase / neighbourhood scores, neighbourhood
      KL (CounterFact+) and a BAKE-like reverse efficacy, compared with the audit's verdicts.

Usage:
  python phase6_offline.py --templates relation_templates_v3.json --out <dir> --run MODEL/CONFIG=<audit dir> [...]
Definitions (violation types V0-V6, plans, costs) are fixed in research-log entry 09 and in the docstrings below.
"""
import argparse
import csv
import json
import math
import random
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

VERSION = "phase6_offline v1.1 (2026-11-05)"
HARD = ("V0", "V1", "V2", "V3", "V4", "V6")          # an edit with any of these is "inconsistent"; V5 (drift) is soft
NAMES = {"V0": "edit failed", "V1": "incomplete write", "V2": "stale read", "V3": "inverse inconsistency",
         "V4": "neighbour damage", "V5": "neighbour drift", "V6": "neighbour leak"}
ROUTES = ["forward_edit_prompt", "paraphrase_statement", "paraphrase_question", "contextual",
          "reverse_old_most_famous", "reverse_old_best_known", "reverse_new_most_famous", "reverse_new_best_known",
          "control_same_relation", "control_same_relation_2", "control_new_object_own_fact"]
STANDARD_PLAN = ("forward_edit_prompt", "paraphrase_statement", "paraphrase_question", "contextual",
                 "control_same_relation", "control_same_relation_2")
B, SEED = 2000, 0


def T(x):
    return x in ("True", True)


def load_edits(run_dir, cardinality):
    """One record per edited fact: per-route reads after its own edit, violations, detection map, features, scores."""
    deltas = [r for r in csv.DictReader(open(Path(run_dir) / "deltas.csv", newline="", encoding="utf-8"))
              if r["fact_id"] in r["edited_facts"].split("|")]
    dist = {(r["fact_id"], r["route"]): r for r in csv.DictReader(open(Path(run_dir) / "dist.csv", newline="", encoding="utf-8"))
            if r["fact_id"] in r["edited_facts"].split("|")}
    by = defaultdict(lambda: defaultdict(dict))
    rel = {}
    for r in deltas:
        rel[r["fact_id"]] = r["relation"]
        if T(r["route_valid"]):
            lab = "alt" if r["answer_label"].startswith("alt:") else r["answer_label"]
            by[r["fact_id"]][r["route"]][lab] = r
    new_obj = {r["fact_id"]: r["answer"] for r in deltas if r["route"] == "forward_edit_prompt" and r["answer_label"] == "new_object"}
    for f, routes in by.items():                      # analysis v1.2: a neighbour whose correct answer is o* is not a side-effect read
        for n in [n for n, a in routes.items() if n.startswith("control_same_relation") and "correct" in a]:
            if routes[n]["correct"]["answer"] == new_obj.get(f):
                del routes[n]
    out = {}
    for f, routes in by.items():
        inv_fun = cardinality.get(rel[f], {}).get("inverse") == "functional"
        ep = routes.get("forward_edit_prompt", {})
        if "new_object" not in ep:
            continue
        rk = lambda row: int(row["post_first_token_rank"])
        ok = rk(ep["new_object"]) == 1
        det = defaultdict(set)                         # route -> violation types it reveals for this edit
        if not ok:
            det["forward_edit_prompt"].add("V0")
        for name, a in routes.items():
            if name.startswith("paraphrase") or name == "contextual":
                if "new_object" in a and rk(a["new_object"]) != 1:
                    det[name].add("V1")
            elif name.startswith("reverse_old") and ok and "subject" in a:
                if rk(a["subject"]) == 1:
                    det[name].add("V2")
            elif name.startswith("reverse_new") and ok and "subject" in a:
                r1, rises = rk(a["subject"]) == 1, float(a["subject"]["delta_sum_logprob"]) > 0
                if (not r1) if inv_fun else (not rises):
                    det[name].add("V3")
            elif name.startswith("control_same_relation") and "correct" in a:
                passed = rk(a["correct"]) == 1
                if not passed:
                    det[name].add("V4")
                if "edit_leak" in a and rk(a["edit_leak"]) <= 5:
                    det[name].add("V6")
                d = dist.get((f, name))
                if passed and d is not None and float(d["js_bits"]) > 0.01:
                    det[name].add("V5")
        viol = set().union(*det.values()) if det else set()
        # pre-edit features (unedited model only)
        lp = lambda row, k="pre_sum_logprob": float(row[k])
        rev_old = [a["subject"] for n, a in routes.items() if n.startswith("reverse_old") and "subject" in a]
        rev_new = [a["subject"] for n, a in routes.items() if n.startswith("reverse_new") and "subject" in a]
        nb = [a for n, a in routes.items() if n.startswith("control_same_relation") and "correct" in a]
        own = routes.get("control_new_object_own_fact", {})
        feat = {
            "pre_logp_new": lp(ep["new_object"]),                       # -perplexingness of the new fact
            "pre_rank_new": -int(ep["new_object"]["pre_first_token_rank"]),
            "pre_logp_old": lp(ep["old_object"]) if "old_object" in ep else None,
            "rev_old_strength": max((lp(x) for x in rev_old), default=None),
            "rev_new_closeness": max((lp(x) for x in rev_new), default=None),
        }
        # standard metrics (CounterFact-style, full-answer probabilities after the edit)
        post = lambda row: float(row["post_sum_logprob"])
        es = post(ep["new_object"]) > post(ep["old_object"]) if "old_object" in ep else None
        para = [a for n, a in routes.items() if (n.startswith("paraphrase") or n == "contextual") and {"new_object", "old_object"} <= set(a)]
        ps = all(post(a["new_object"]) > post(a["old_object"]) for a in para) if para else None
        ns = all(post(a["correct"]) > post(a["edit_leak"]) for a in nb if "edit_leak" in a) if nb else None
        nkl = [float(dist[(f, n)]["kl_pre_post"]) for n in routes if n.startswith("control_same_relation") and (f, n) in dist]
        # BAKE-like reverse efficacy: on reverse-from-new paths, is the edited subject preferred over o*'s own subject?
        bake = []
        for n, a in routes.items():
            if n.startswith("reverse_new") and "subject" in a:
                if "alt" in a:
                    bake.append(post(a["subject"]) > post(a["alt"]))
        fd_state = None
        if inv_fun and ok and "correct" in own:
            fd_state = int(own["correct"]["post_first_token_rank"]) == 1   # o* still answers its own subject s'
        out[f] = {"relation": rel[f], "inv_fun": inv_fun, "ok": ok, "det": {k: sorted(v) for k, v in det.items()},
                  "viol": sorted(viol), "routes": sorted(routes), "feat": feat, "es": es, "ps": ps, "ns": ns,
                  "nkl": (sum(nkl) / len(nkl)) if nkl else None, "bake_rev": (sum(bake) / len(bake)) if bake else None,
                  "fd_state_violation": fd_state, "rev_old_pre1": any(x["pre_first_token_rank"] == "1" for x in rev_old)}
    return out


def is_local(name):
    """Local configurations = ROME+stats, MEMIT, AlphaEdit; ROME without statistics (".../ROME") is the ablation."""
    return name.split("/")[-1] in ("ROME+stats", "MEMIT", "AlphaEdit")


def inconsistent(e, types=HARD):
    return any(v in types for v in e["viol"])


def detected(e, plan, types=HARD):
    return any(v in types for r in plan for v in e["det"].get(r, []))


def rate(edits, plan, types=HARD):
    bad = [e for e in edits.values() if inconsistent(e, types)]
    return (sum(detected(e, plan, types) for e in bad), len(bad))


def greedy(edits, budget, types=HARD):
    plan = []
    for _ in range(budget):
        best = max((r for r in ROUTES if r not in plan), key=lambda r: (rate(edits, plan + [r], types)[0], -ROUTES.index(r)))
        plan.append(best)
    return plan


def auroc(pos, neg):
    """Mann-Whitney AUROC of score for positives vs negatives (ties count 1/2), via mid-ranks."""
    if not pos or not neg:
        return None
    xs = sorted([(v, 1) for v in pos] + [(v, 0) for v in neg])
    rsum, i = 0.0, 0
    while i < len(xs):
        j = i
        while j < len(xs) and xs[j][0] == xs[i][0]:
            j += 1
        mid = (i + j + 1) / 2                            # mid-rank of the tie block (1-based)
        rsum += mid * sum(y for _, y in xs[i:j])
        i = j
    n1, n0 = len(pos), len(neg)
    return (rsum - n1 * (n1 + 1) / 2) / (n1 * n0)


def boot_auroc(pairs, seed=SEED):
    rnd = random.Random(seed)
    vals = []
    for _ in range(500):
        smp = [pairs[rnd.randrange(len(pairs))] for _ in pairs]
        a = auroc([s for s, y in smp if y], [s for s, y in smp if not y])
        if a is not None:
            vals.append(a)
    vals.sort()
    return (vals[int(.025 * len(vals))], vals[int(.975 * len(vals)) - 1]) if vals else (None, None)


def pct(n, d):
    return f"{n}/{d} = {n / d:.0%}" if d else "–"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", required=True, metavar="MODEL/CONFIG=DIR")
    ap.add_argument("--templates", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    card = {k: v.get("cardinality", {}) for k, v in json.loads(Path(a.templates).read_text(encoding="utf-8"))["relations"].items()}
    runs = {}
    for spec in a.run:
        name, d = spec.split("=", 1)
        runs[name] = load_edits(d, card)
    for model in sorted({n.split("/")[0] for n in runs}):   # pooled local configurations, per model and overall
        runs[f"{model}/local"] = {f"{n}:{f}": e for n, E in list(runs.items()) if n.startswith(model + "/") and is_local(n) for f, e in E.items()}
    runs["all/local"] = {k: e for n, E in list(runs.items()) if n.endswith("/local") for k, e in E.items()}
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    L = [f"# Phase 6 offline analyses ({VERSION})", ""]

    # ---------------- N3 ----------------
    L += ["## N3. Audit planning", "",
          "Detection rate = share of inconsistent edits (any of " + ", ".join(f"{k} {NAMES[k]}" for k in HARD) +
          ") that the plan reveals. Cost = questions asked per edit.", "",
          "| run | edits | inconsistent | full catalogue (11) | standard plan (6) | 1 reverse-old + 1 neighbour (2) | greedy 1 | greedy 2 | greedy 3 | greedy plan (order) |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    n3rows = []
    for name, E in runs.items():
        bad = sum(inconsistent(e) for e in E.values())
        full = rate(E, ROUTES); std = rate(E, list(STANDARD_PLAN)); two = rate(E, ["reverse_old_best_known", "control_same_relation"])
        g = greedy(E, 3)
        gs = [rate(E, g[:k]) for k in (1, 2, 3)]
        L.append(f"| {name} | {len(E)} | {bad} | {pct(*full)} | {pct(*std)} | {pct(*two)} | {pct(*gs[0])} | {pct(*gs[1])} | {pct(*gs[2])} | {', '.join(g)} |")
        n3rows.append({"run": name, "edits": len(E), "inconsistent": bad, "full": full[0], "standard": std[0], "two": two[0],
                       "g1": gs[0][0], "g2": gs[1][0], "g3": gs[2][0], "plan": "|".join(g)})
    # same, without V3: the reverse-from-new failure is near-universal (and known, BAKE), so it dominates the table above
    NO3 = tuple(k for k in HARD if k != "V3")
    L += ["", "Same, **excluding V3** (inverse inconsistency; near-universal and already known from BAKE): inconsistent = any "
          "of " + ", ".join(NO3) + ".", "",
          "| run | inconsistent | standard plan (6) | 1 reverse-old + 1 neighbour (2) | greedy 1 | greedy 2 | greedy 3 | greedy plan (order) |",
          "|---|---|---|---|---|---|---|---|"]
    for name, E in runs.items():
        g = greedy(E, 3, NO3)
        L.append(f"| {name} | {sum(inconsistent(e, NO3) for e in E.values())} | {pct(*rate(E, list(STANDARD_PLAN), NO3))} | "
                 f"{pct(*rate(E, ['reverse_old_best_known', 'control_same_relation'], NO3))} | "
                 + " | ".join(pct(*rate(E, g[:k], NO3)) for k in (1, 2, 3)) + f" | {', '.join(g)} |")
    # what the standard plan misses, by violation type
    L += ["", "Violation types per run (edits with the type) and how many of those the standard plan reveals:", "",
          "| run | " + " | ".join(f"{k} {NAMES[k]}" for k in ("V0", "V1", "V2", "V3", "V4", "V5", "V6")) + " |", "|---|" + "---|" * 7]
    for name, E in runs.items():
        cells = []
        for k in ("V0", "V1", "V2", "V3", "V4", "V5", "V6"):
            n = sum(k in e["viol"] for e in E.values())
            s = sum(detected(e, STANDARD_PLAN, (k,)) for e in E.values() if k in e["viol"])
            cells.append(f"{n} ({s} by standard)")
        L.append(f"| {name} | " + " | ".join(cells) + " |")
    # transfer: plan chosen on one model's local configurations, applied to the other model's
    pools = [n for n in runs if n.endswith("/local") and not n.startswith("all/")]
    L += ["", "Transfer of greedy plans across models (local configurations pooled per model): rows = pool the plan was chosen "
          "on, columns = pool it is applied to (detection rate).", "",
          "| chosen on \\ applied to | " + " | ".join(pools) + " |", "|---|" + "---|" * len(pools)]
    for src in pools:
        for b in (1, 2, 3):
            p = greedy(runs[src], b)
            L.append(f"| {src}, budget {b} ({' + '.join(p)}) | " + " | ".join(
                (lambda r: f"{r[0] / r[1]:.0%}" if r[1] else "–")(rate(runs[t], p)) for t in pools) + " |")
    # adaptive plan: read routes in the greedy order, stop at the first violation
    L += ["", "Adaptive audit (read routes in greedy order of the pooled local configurations, stop at the first violation): "
          "mean questions until an inconsistent edit is flagged, and questions spent on consistent edits (all routes).", ""]
    pooled = {f"{n}:{f}": e for n, E in runs.items() if is_local(n) for f, e in E.items()}
    order = greedy(pooled, len(ROUTES))
    L += [f"Pooled greedy order: {', '.join(order)}", "", "| run | mean questions to flag an inconsistent edit | consistent edits (cost 11 each) | mean cost per edit vs 11 |", "|---|---|---|---|"]
    for name, E in runs.items():
        costs, cons = [], 0
        for e in E.values():
            if inconsistent(e):
                k = next(i + 1 for i, r in enumerate(order) if any(v in HARD for v in e["det"].get(r, [])))
                costs.append(k)
            else:
                cons += 1
        mean_all = (sum(costs) + 11 * cons) / max(1, len(E))
        L.append(f"| {name} | {sum(costs) / len(costs):.2f} | {cons} | {mean_all:.2f} |" if costs else f"| {name} | – | {cons} | – |")

    # ---------------- N2 ----------------
    L += ["", "## N2. Admission control", "",
          "### Functional-dependency state violations (one-to-one relations)",
          "Successful edits of capital/currency facts whose new object has its own fact in the set: does the new object still "
          "answer its original subject (so two subjects now map to it, violating the declared inverse FD)?", "",
          "| run | edits checked | state violates the inverse FD |", "|---|---|---|"]
    for name, E in runs.items():
        xs = [e["fd_state_violation"] for e in E.values() if e["fd_state_violation"] is not None]
        L.append(f"| {name} | {len(xs)} | {pct(sum(xs), len(xs))} |")
    L += ["", "### Pre-edit predictors of violations (AUROC, 95% bootstrap interval over edits; successful edits for V2/V3)",
          "Features use only reads of the unedited model. AUROC > 0.5: higher feature value -> violation more likely.", "",
          "| run | target | positives / n | " + " | ".join(("pre_logp_new", "pre_rank_new", "pre_logp_old", "rev_old_strength", "rev_new_closeness")) + " |",
          "|---|---|---|" + "---|" * 5]
    for name, E in runs.items():
        for tgt in ("V2", "V2|pre1", "V4", "V6"):
            # V2|pre1: only successful edits with some reverse-from-old read at rank 1 before the edit (otherwise the read
            # cannot stay stale, and reverse strength would trivially separate the two groups)
            pool = [e for e in E.values() if (e["ok"] or tgt[:2] not in ("V2", "V3")) and (tgt != "V2|pre1" or e["rev_old_pre1"])]
            ys = [tgt[:2] in e["viol"] for e in pool]
            cells = []
            for fn in ("pre_logp_new", "pre_rank_new", "pre_logp_old", "rev_old_strength", "rev_new_closeness"):
                pairs = [(e["feat"][fn], y) for e, y in zip(pool, ys) if e["feat"][fn] is not None]
                au = auroc([s for s, y in pairs if y], [s for s, y in pairs if not y])
                if au is None:
                    cells.append("–"); continue
                lo, hi = boot_auroc(pairs)
                cells.append(f"{au:.2f} [{lo:.2f}, {hi:.2f}]")
            L.append(f"| {name} | {tgt} {NAMES[tgt[:2]]} | {sum(ys)}/{len(ys)} | " + " | ".join(cells) + " |")

    # ---------------- E10 ----------------
    L += ["", "## E10. Standard metrics vs the audit on the same edits", "",
          "ES = P(o*) > P(o) on the edited question; PS = the same on every paraphrase/context path; NS = P(correct) > P(o*) on "
          "every same-relation neighbour (CounterFact-style, full-answer probabilities). NKL = mean neighbour KL(pre‖post) "
          "(CounterFact+). BAKE-like = share of reverse-from-new paths preferring the edited subject over o*'s own subject.", "",
          "| run | ES pass | PS pass | NS pass | pass all three | of those: audit flags inconsistent | … stale (V2) | … inverse (V3) | … damage/leak (V4/V6) | … drift (V5) | mean BAKE-like | AUROC of NKL for V2 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, E in runs.items():
        es = [e for e in E.values() if e["es"]]; ps = [e for e in E.values() if e["ps"]]; ns = [e for e in E.values() if e["ns"]]
        allp = [e for e in E.values() if e["es"] and e["ps"] is not False and e["ns"] is not False]
        flag = lambda ts: sum(any(v in ts for v in e["viol"]) for e in allp)
        bk = [e["bake_rev"] for e in E.values() if e["bake_rev"] is not None]
        pairs = [(e["nkl"], "V2" in e["viol"]) for e in E.values() if e["ok"] and e["nkl"] is not None]
        au = auroc([s for s, y in pairs if y], [s for s, y in pairs if not y])
        L.append(f"| {name} | {pct(len(es), len(E))} | {pct(len(ps), len(E))} | {pct(len(ns), len(E))} | {pct(len(allp), len(E))} | "
                 f"{pct(flag(HARD), len(allp))} | {pct(flag(('V2',)), len(allp))} | {pct(flag(('V3',)), len(allp))} | "
                 f"{pct(flag(('V4', 'V6')), len(allp))} | {pct(flag(('V5',)), len(allp))} | "
                 f"{sum(bk) / len(bk):.0%} | " + (f"{au:.2f} [{boot_auroc(pairs)[0]:.2f}, {boot_auroc(pairs)[1]:.2f}]" if au is not None else "–") + " |")
    (out / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    with open(out / "edits.jsonl", "w", encoding="utf-8") as f:
        for name, E in runs.items():
            for fid, e in E.items():
                f.write(json.dumps({"run": name, "fact_id": fid, **e}) + "\n")
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
