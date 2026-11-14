"""Offline checks of phase6_offline.py (CPU, standard library only).
  1. Violation logic on hand-made rows: V0 for a failed edit (and no reverse violations for it), V2 stale / V3 contract on
     reverse paths of successful edits, V4/V5/V6 on same-relation neighbours, a neighbour whose correct answer is the new
     object is dropped, the FD-state check on the new object's own fact, invalid paths ignored.
  2. Plans: the standard plan misses a stale-only edit; detection rates and the greedy choice on these rows.
  3. Rank-based AUROC equals the brute-force pairwise count (with ties) on random scores.
"""
import csv
import random
import sys
import tempfile
from pathlib import Path

SP = Path(sys.argv[1]); sys.path.insert(0, str(SP))
import phase6_offline as p6

card = {"country_capital": {"inverse": "functional"}, "novel_author": {"inverse": "non-functional"}}
D_COLS = ["fact_id", "edited_facts", "relation", "route", "route_valid", "answer_label", "answer", "pre_sum_logprob",
          "post_sum_logprob", "delta_sum_logprob", "pre_first_token_rank", "post_first_token_rank"]


def row(f, rel, route, label, pre_rank, post_rank, pre_lp=-2.0, post_lp=-2.0, answer="x", valid=True):
    return [f, f, rel, route, str(valid), label, answer, pre_lp, post_lp, post_lp - pre_lp, pre_rank, post_rank]


C, N = "country_capital", "novel_author"
rows = [
    # cap: successful 1:1 edit; stale reverse-old (V2), reverse-new not rank 1 (V3), neighbour passes but drifts (V5) and
    # leaks o* into its top 5 (V6); second neighbour's correct answer is o* (dropped); own fact still answered by o*
    row("cap", C, "forward_edit_prompt", "new_object", 900, 1, -9, -0.5, "Rome"),
    row("cap", C, "forward_edit_prompt", "old_object", 1, 50, -0.3, -8, "Paris"),
    row("cap", C, "paraphrase_question", "new_object", 700, 1, -9, -0.6, "Rome"),
    row("cap", C, "paraphrase_question", "old_object", 1, 40, -0.4, -7, "Paris"),
    row("cap", C, "reverse_old_best_known", "subject", 1, 1, -0.7, -0.9),
    row("cap", C, "reverse_new_best_known", "subject", 800, 4, -9, -3),
    row("cap", C, "reverse_new_best_known", "alt:Italy", 1, 1, -0.2, -0.4),
    row("cap", C, "control_same_relation", "correct", 1, 1, -0.5, -0.6, "Berlin"),
    row("cap", C, "control_same_relation", "edit_leak", 30, 3, -6, -2, "Rome"),
    row("cap", C, "control_same_relation_2", "correct", 1, 9, -0.5, -5, "Rome"),          # correct == o*: dropped
    row("cap", C, "control_new_object_own_fact", "correct", 1, 1, -0.2, -0.2, "Rome"),
    row("cap", C, "contextual", "new_object", 1, 9, -9, -9, "Rome", valid=False),            # invalid: ignored
    # nov: failed edit (V0); its stale reverse read is not counted; neighbour loses its answer (V4)
    row("nov", N, "forward_edit_prompt", "new_object", 500, 7, -9, -5, "Bram Stoker"),
    row("nov", N, "forward_edit_prompt", "old_object", 1, 1, -0.3, -0.5, "Mary Shelley"),
    row("nov", N, "reverse_old_best_known", "subject", 1, 1, -0.5, -0.5),
    row("nov", N, "control_same_relation", "correct", 1, 2, -0.5, -3, "Jane Austen"),
    # st: successful non-functional edit whose only violation is a stale reverse read (subject rises on reverse-new)
    row("st", N, "forward_edit_prompt", "new_object", 600, 1, -9, -0.5, "Jane Austen"),
    row("st", N, "forward_edit_prompt", "old_object", 1, 30, -0.3, -6, "Herman Melville"),
    row("st", N, "reverse_old_most_famous", "subject", 1, 1, -1.5, -1.6),
    row("st", N, "reverse_new_most_famous", "subject", 400, 300, -9, -8),
    row("st", N, "control_same_relation", "correct", 1, 1, -0.5, -0.5, "Leo Tolstoy"),
    row("st", N, "control_same_relation", "edit_leak", 90, 80, -7, -7, "Jane Austen"),
]
dist = [("cap", "control_same_relation", 0.05, 0.2), ("cap", "control_same_relation_2", 0.4, 1.0),
        ("st", "control_same_relation", 0.001, 0.003), ("nov", "control_same_relation", 0.3, 0.9)]
with tempfile.TemporaryDirectory() as tmp:
    with open(Path(tmp) / "deltas.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(D_COLS); w.writerows(rows)
    with open(Path(tmp) / "dist.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["fact_id", "edited_facts", "route", "js_bits", "kl_pre_post"])
        w.writerows([(f, f, r, j, k) for f, r, j, k in dist])
    E = p6.load_edits(tmp, card)

cap, nov, st = E["cap"], E["nov"], E["st"]
assert cap["viol"] == ["V2", "V3", "V5", "V6"], cap["viol"]
assert cap["det"]["reverse_old_best_known"] == ["V2"] and cap["det"]["reverse_new_best_known"] == ["V3"]
assert "control_same_relation_2" not in cap["routes"], "neighbour whose correct answer is o* must be dropped"
assert "contextual" not in cap["routes"], "invalid path must be ignored"
assert cap["fd_state_violation"] is True and cap["rev_old_pre1"] is True
assert cap["es"] is True and cap["ps"] is True and cap["ns"] is True and cap["bake_rev"] == 0.0
assert abs(cap["nkl"] - 0.2) < 1e-12
assert nov["viol"] == ["V0", "V4"], nov["viol"]                       # stale read of a failed edit not counted
assert nov["es"] is False and nov["fd_state_violation"] is None
assert st["viol"] == ["V2"], st["viol"]                              # rising subject on reverse-new: no V3 (non-functional)
assert abs(st["feat"]["rev_old_strength"] + 1.5) < 1e-12

std = list(p6.STANDARD_PLAN)
assert p6.rate(E, std) == (2, 3), p6.rate(E, std)                    # cap via V6, nov via V0/V4; st (stale only) missed
assert p6.rate(E, ["reverse_old_best_known", "reverse_old_most_famous"]) == (2, 3)
assert p6.rate(E, p6.ROUTES) == (3, 3)
assert p6.rate(E, std, ("V5",)) == (1, 1)                            # drift is visible to the standard plan, but soft
g = p6.greedy(E, 2)
assert p6.rate(E, g) == (3, 3), (g, p6.rate(E, g))

rnd = random.Random(1)
for _ in range(200):
    pos = [rnd.choice(range(6)) for _ in range(rnd.randint(1, 8))]
    neg = [rnd.choice(range(6)) for _ in range(rnd.randint(1, 8))]
    brute = sum(1.0 if a > b else 0.5 if a == b else 0.0 for a in pos for b in neg) / (len(pos) * len(neg))
    assert abs(p6.auroc(pos, neg) - brute) < 1e-12, (pos, neg)
assert p6.auroc([], [1]) is None
print("test_phase6_offline: all checks passed")
