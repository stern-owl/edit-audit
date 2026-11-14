#!/usr/bin/env python3
"""Compare a re-run's CSV outputs with the shipped ones, row by row. Standard library only.

Usage:
  python compare_to_shipped.py --pair NAME SHIPPED.csv RERUN.csv [--pair ...] [--out report.md]

Rows are matched on whichever of scope, fact, fact_id, method, seed, route, answer_label are present in both
files; the key must be unique.
For every matched row it reports
  * the largest absolute difference of every numeric column (log-probabilities, probabilities),
  * how many rows differ in any rank column (exact integer comparison),
  * how many rows differ in any other text column (greedy continuations, validity flags),
and lists every rank or validity difference so it can be inspected. Nothing is averaged away.
"""
import argparse
import csv
import math

KEY_CANDIDATES = ["scope", "fact", "fact_id", "method", "seed", "route", "answer_label"]
IGNORE = {"method"}   # in deltas.csv: absent from ROME runs, constant otherwise (still a key where both files have it)


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def as_float(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def compare(name, shipped_path, rerun_path, drop_margin=False):
    a, b = load(shipped_path), load(rerun_path)
    if drop_margin:   # derived "MARGIN new_minus_old" rows exist only in the draft's deltas.csv format
        a = [r for r in a if not r.get("answer_label", "").startswith("MARGIN")]
        b = [r for r in b if not r.get("answer_label", "").startswith("MARGIN")]
    keys = [k for k in KEY_CANDIDATES if k in a[0] and k in b[0]]
    if not keys:
        raise ValueError(f"{name}: no key columns among {KEY_CANDIDATES}")
    cols = [c for c in a[0] if c in b[0] and c not in keys and c not in IGNORE]
    if len({tuple(r[k] for k in keys) for r in a}) != len(a):
        raise ValueError(f"{name}: key {keys} is not unique in {shipped_path}")
    ia = {tuple(r[k] for k in keys): r for r in a}
    ib = {tuple(r[k] for k in keys): r for r in b}
    only_a, only_b = sorted(set(ia) - set(ib)), sorted(set(ib) - set(ia))
    max_abs = {}
    rank_diffs, text_diffs = [], []
    for key in sorted(set(ia) & set(ib)):
        ra, rb = ia[key], ib[key]
        for c in cols:
            if ra[c] == rb[c]:
                continue
            fa, fb = as_float(ra[c]), as_float(rb[c])
            if "rank" in c:
                rank_diffs.append((key, c, ra[c], rb[c]))
            elif fa is not None and fb is not None:
                max_abs[c] = max(max_abs.get(c, 0.0), abs(fa - fb))
            else:
                text_diffs.append((key, c, ra[c], rb[c]))
    lines = [f"## {name}", f"- shipped: `{shipped_path}` ({len(a)} rows)", f"- re-run: `{rerun_path}` ({len(b)} rows)",
             f"- matched on {keys}: {len(set(ia) & set(ib))} rows; only shipped {len(only_a)}; only re-run {len(only_b)}"]
    num_cols = [c for c in cols if "rank" not in c and any(as_float(r[c]) is not None for r in a[:50])]
    for c in num_cols:
        lines.append(f"- max |diff| `{c}`: {max_abs.get(c, 0.0):.3g}")
    lines.append(f"- rank differences: {len(rank_diffs)}")
    lines += [f"  - {dict(zip(keys, k))} `{c}`: {x} -> {y}" for k, c, x, y in rank_diffs]
    lines.append(f"- text differences: {len(text_diffs)}")
    lines += [f"  - {dict(zip(keys, k))} `{c}`: {x!r} -> {y!r}" for k, c, x, y in text_diffs[:200]]
    if len(text_diffs) > 200:
        lines.append(f"  - ... {len(text_diffs) - 200} more")
    for k in only_a[:20]:
        lines.append(f"  - only shipped: {dict(zip(keys, k))}")
    for k in only_b[:20]:
        lines.append(f"  - only re-run: {dict(zip(keys, k))}")
    verdict = "IDENTICAL" if not (max_abs or rank_diffs or text_diffs or only_a or only_b) else (
        "SAME RANKS AND TEXT, numeric drift only" if not (rank_diffs or text_diffs or only_a or only_b) else "DIFFERS")
    lines.insert(1, f"**Verdict: {verdict}**")
    return "\n".join(lines) + "\n", verdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", nargs=3, action="append", metavar=("NAME", "SHIPPED", "RERUN"), required=True)
    ap.add_argument("--out")
    ap.add_argument("--drop-margin", action="store_true", help="ignore MARGIN rows (compare old-format vs run_audit deltas)")
    args = ap.parse_args()
    parts, verdicts = [], []
    for name, s, r in args.pair:
        text, v = compare(name, s, r, args.drop_margin)
        parts.append(text)
        verdicts.append((name, v))
    summary = "# Re-run vs shipped\n\n" + "\n".join(f"- {n}: **{v}**" for n, v in verdicts) + "\n\n"
    report = summary + "\n".join(parts)
    print(report)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)


if __name__ == "__main__":
    main()
