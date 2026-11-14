"""Offline checks of run_audit.audit_programs (programs mode: N5 compensation, N2 cascade) and make_programs (CPU).
  1. An additive editor whose inverse edit subtracts exactly what the edit added: compensation returns the weights to
     the unedited ones (residual norm ~0, every read equal to the unedited read), and late compensation reaches the
     reference state (every compared read has JS ~0). Weights are restored after every program.
  2. A weight-dependent editor leaves a residue after compensation (residual norm > 0).
  3. Bookkeeping: reads only at read_at steps, edited_facts with ~inv, one check row per step (check C on the last),
     a multi-edit step reaches edit_fn as one call, derived facts get validity from the unedited reads.
  4. Failures: an edited sentinel is refused; a no-op editor is caught by check B.
  5. make_programs.build: N2 cases only for one-to-one relations with a valid own-fact control; swap targets.
"""
import json
import sys
from pathlib import Path

import torch
from transformers import GPT2Config, GPT2LMHeadModel

SP = Path(sys.argv[1]); sys.path.insert(0, str(SP)); sys.path.insert(0, str(Path(__file__).parent))
import make_programs as mk
import run_audit as ra
import screen_facts as sf
import screen_facts_v4 as sv
from toytok import ToyTok

facts_csv = sf.load_facts(str(SP / "candidate_facts_v2.csv")); T = json.load(open(SP / "relation_templates.json"))
T3 = json.load(open(SP / "relation_templates_v3.json", encoding="utf-8"))
torch.manual_seed(0)
m = GPT2LMHeadModel(GPT2Config(vocab_size=300, n_positions=256, n_embd=64, n_layer=2, n_head=2)).eval()
tok, dev = ToyTok(), torch.device("cpu")
facts = {p["fact_id"]: p for p, _ in sf.screen(m, tok, dev, facts_csv[:4], T)}
ids = sorted(facts)
row = {"fact_id": "swap__x", "relation": "country_capital", "subject": "Poland", "target_old": "Warsaw",
       "target_new": "Brussels", "old_alt": "", "new_alt": "Belgium", "notes": "", "source": "derived", "cf_case_id": "", "dup_group": ""}
facts["swap__x"] = sv.build_probes(row, sf.load_facts(str(SP / "facts_v3" / "candidate_facts_v3.csv")), T3)
assert all("valid" not in r for r in facts["swap__x"]["routes"])
params = ["transformer.h.1.mlp.c_proj.weight"]
W0 = m.get_parameter(params[0]).detach().clone()
D = {f: torch.randn(W0.shape, generator=torch.Generator().manual_seed(i)) * 0.3 for i, f in enumerate(sorted(facts))}
by_subj = {facts[f]["edit"]["subject"]: f for f in facts}
calls = []


def sign(e):
    f = by_subj[e["subject"]]
    return f, (1.0 if e["target_new"] == facts[f]["edit"]["target_new"] else -1.0)


def additive(edits):
    calls.append(len(edits))
    with torch.no_grad():
        for e in edits:
            f, sg = sign(e)
            m.get_parameter(params[0]).add_(sg * D[f])
    return {}, m, None


def dependent(edits):
    calls.append(len(edits))
    with torch.no_grad():
        w = m.get_parameter(params[0])
        for e in edits:
            f, sg = sign(e)
            w.add_(sg * D[f] + 0.3 * (w - W0) * float((w - W0).abs().mean()))
    return {}, m, None


a, b, c, s0 = ids[0], ids[1], ids[2], ids[3]
E = lambda f, d="fwd": {"fact": f, "dir": d}
programs = [
    {"program_id": f"comp:{a}", "kind": "compensate", "steps": [[E(a)], [E(a, "inv")]], "read": [a], "read_at": [1, 2], "compare_to": None},
    {"program_id": f"ref:{a}", "kind": "reference", "steps": [[E(b)], [E(c)]], "read": [a, b, c], "read_at": [2], "compare_to": None},
    {"program_id": f"late:{a}", "kind": "compensate_late", "steps": [[E(a)], [E(b)], [E(c)], [E(a, "inv")]],
     "read": [a, b, c], "read_at": [4], "compare_to": f"ref:{a}"},
    {"program_id": f"cascade_batch:{a}", "kind": "cascade_batch", "steps": [[E(a), E("swap__x")]], "read": [a, "swap__x"],
     "read_at": [1], "compare_to": None},
]


def run(fn, progs=programs, sents=(s0,)):
    rows = {k: [] for k in ("delta", "dist", "check", "commute", "pair")}
    calls.clear()
    ra.audit_programs(m, tok, dev, facts, progs, list(sents), fn, params, lambda k, r: rows[k].extend(r), seed=0,
                      derived=["swap__x"], rules=T3["validity_rules"], gen_tokens=3, reread_gen_tokens=0)
    assert torch.equal(m.get_parameter(params[0]), W0), "weights not restored"
    return rows


r = run(additive)
assert all(isinstance(x["valid"], bool) for x in facts["swap__x"]["routes"]), "derived validity not set"
chk = {x["step"]: x for x in r["check"]}
assert set(chk) == {f"comp:{a}:1", f"comp:{a}:2", f"ref:{a}:1", f"ref:{a}:2", f"late:{a}:1", f"late:{a}:2", f"late:{a}:3",
                    f"late:{a}:4", f"cascade_batch:{a}:1"}, sorted(chk)
assert chk[f"comp:{a}:2"]["cumulative_delta_frobenius_norm"] < 1e-4 < chk[f"comp:{a}:1"]["cumulative_delta_frobenius_norm"]
assert "check_C_restore_max_diff" in chk[f"comp:{a}:2"] and "check_C_restore_max_diff" not in chk[f"comp:{a}:1"]
assert chk[f"comp:{a}:2"]["edited_facts"] == f"{a}|{a}~inv"
d2 = [x for x in r["dist"] if x["step"] == f"comp:{a}:2"]
assert d2 and max(x["js_bits"] for x in d2) < 1e-9, "exact compensation must give the unedited reads"
assert {x["step"] for x in r["dist"]} == {f"comp:{a}:1", f"comp:{a}:2", f"ref:{a}:2", f"late:{a}:4", f"cascade_batch:{a}:1"}
assert {x["fact_id"] for x in r["dist"] if x["step"] == f"late:{a}:4"} == {a, b, c, s0}
assert r["commute"] and max(x["js_bits"] for x in r["commute"]) < 1e-9 and {x["pair_id"] for x in r["commute"]} == {f"late:{a}"}
assert calls.count(2) == 1, calls                                   # the batch step is one call with two edits
assert {x["fact_id"] for x in r["delta"] if x["step"] == f"cascade_batch:{a}:1"} == {a, "swap__x", s0}
r2 = run(dependent, progs=programs[:1])
assert [x for x in r2["check"] if x["step"] == f"comp:{a}:2"][0]["cumulative_delta_frobenius_norm"] > 1e-3
try:
    run(additive, sents=(b,)); raise SystemExit("edited sentinel not refused")
except ValueError as e:
    assert "sentinel" in str(e)
try:
    run(lambda edits: ({}, m, None), progs=programs[:1]); raise SystemExit("check B missed a no-op editor")
except RuntimeError as e:
    assert "check B" in str(e)
assert ra.program_edit(facts, E(a, "inv"))["target_new"] == facts[a]["edit"]["target_old"]
# make_programs.build
own = lambda valid: [{"route": "control_new_object_own_fact", "valid": valid}]
F = {"cap_be": {"fact_id": "cap_be", "relation": "country_capital", "routes": own(True),
                "edit": {"subject": "Belgium", "target_old": "Brussels", "target_new": "Warsaw"}},
     "cap_cl": {"fact_id": "cap_cl", "relation": "country_capital", "routes": own(False),
                "edit": {"subject": "Chile", "target_old": "Santiago", "target_new": "Kabul"}},
     "nov_x": {"fact_id": "nov_x", "relation": "novel_author", "routes": own(True),
               "edit": {"subject": "Emma", "target_old": "Jane Austen", "target_new": "Leo Tolstoy"}},
     "nov_y": {"fact_id": "nov_y", "relation": "novel_author", "routes": own(True),
               "edit": {"subject": "Dracula", "target_old": "Bram Stoker", "target_new": "Mary Shelley"}}}
card = {"country_capital": {"inverse": "functional"}, "novel_author": {"inverse": "non-functional"}}
progs, derived = mk.build(F, card, [], 1, 1, "0", {"cap_be": "Poland", "cap_cl": "Afghanistan", "nov_x": "War and Peace", "nov_y": "x"})
assert [d["fact_id"] for d in derived] == ["swap__cap_be"]
d = derived[0]
assert (d["subject"], d["target_old"], d["target_new"], d["new_alt"]) == ("Poland", "Warsaw", "Brussels", "Belgium")
kinds = sorted(p["kind"] for p in progs)
assert kinds == sorted(["compensate"] * 4 + ["reference", "compensate_late"] + ["cascade", "cascade_rev", "cascade_batch"]), kinds
late = [p for p in progs if p["kind"] == "compensate_late"][0]
assert late["steps"][0] == [E(late["read"][0])] and late["steps"][-1] == [E(late["read"][0], "inv")]
print("PROGRAMS TESTS PASSED | exact and residual compensation, late compensation vs reference, batch step, derived validity, make_programs")
