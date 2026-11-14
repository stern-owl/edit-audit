"""Offline checks of run_audit.audit_pairs (pairs mode, N1) and make_pairs on a tiny random GPT-2 (CPU, no downloads).
  1. An editor whose updates are fixed per fact and additive commutes exactly: AB and BA weights are identical (order
     gap 0, additivity gap 0) and every AB/BA read pair has JS 0; weights are restored after the run.
  2. An editor whose update depends on the current weights does not commute: order gap > 0 and some reads differ.
  3. Row bookkeeping: steps <pair>:AB / <pair>:BA, application order in edited_facts, fact_edit_step = position,
     sentinels read and never edited, one check row per order and one pair row per pair, reset_fn before each order.
  4. subject_keys returns the rewrite module's input at the subject's last token (checked against a manual forward pass).
  5. Failures: a sentinel inside a pair is refused; an editor that does nothing is caught by check B.
  6. make_pairs: class rules on hand-made facts; sentinels avoid shared-object facts; deterministic output.
"""
import json
import sys
from pathlib import Path

import torch
from transformers import GPT2Config, GPT2LMHeadModel

SP = Path(sys.argv[1]); sys.path.insert(0, str(SP)); sys.path.insert(0, str(Path(__file__).parent))
import make_pairs as mp
import probe_scoring_v4 as ps
import run_audit as ra
import screen_facts as sf
from toytok import ToyTok

facts_csv = sf.load_facts(str(SP / "candidate_facts_v2.csv")); T = json.load(open(SP / "relation_templates.json"))
torch.manual_seed(0)
m = GPT2LMHeadModel(GPT2Config(vocab_size=300, n_positions=256, n_embd=64, n_layer=2, n_head=2)).eval()
tok, dev = ToyTok(), torch.device("cpu")
facts = {p["fact_id"]: p for p, _ in sf.screen(m, tok, dev, facts_csv[:4], T)}
ids = sorted(facts)
params = ["transformer.h.0.mlp.c_proj.weight", "transformer.h.1.mlp.c_proj.weight"]
modules = [n[:-len(".weight")] for n in params]
base_w = {n: m.get_parameter(n).detach().clone() for n in params}
pairs = [{"pair_id": "p001", "pair_class": "same_relation", "fact_a": ids[0], "fact_b": ids[1]},
         {"pair_id": "p002", "pair_class": "disjoint", "fact_a": ids[1], "fact_b": ids[2]}]
sentinels = [ids[3]]
fixed = {f: {n: torch.randn(base_w[n].shape, generator=torch.Generator().manual_seed(i * 10 + j)) * 0.3
             for j, n in enumerate(params)} for i, f in enumerate(ids)}
subj2fact = {facts[f]["edit"]["subject"]: f for f in ids}
resets = []


def additive(edits):
    with torch.no_grad():
        for n in params:
            m.get_parameter(n).add_(fixed[subj2fact[edits[0]["subject"]]][n])
    return {}, m, None


def dependent(edits):   # update depends on the current weights: does not commute
    with torch.no_grad():
        for n in params:
            w = m.get_parameter(n)
            w.add_(fixed[subj2fact[edits[0]["subject"]]][n] + 0.5 * (w - base_w[n]) * w.abs().mean())
    return {}, m, None


def run(edit_fn, prs=pairs, sents=sentinels):
    rows = {"delta": [], "dist": [], "check": [], "commute": [], "pair": []}
    resets.clear()
    ra.audit_pairs(m, tok, dev, facts, prs, sents, edit_fn, params, lambda k, r: rows[k].extend(r), seed=0,
                   reset_fn=lambda: resets.append(1), key_modules=modules, gen_tokens=3, reread_gen_tokens=0)
    assert all(torch.equal(m.get_parameter(n), base_w[n]) for n in params), "weights not restored"
    return rows


# 1. additive editor commutes exactly
r = run(additive)
assert len(r["pair"]) == 2 and len(r["check"]) == 4 and len(resets) == 4
for p in r["pair"]:
    assert p["gap_AB_BA"] < 1e-5 and p["add_gap_AB"] < 1e-5 and p["add_gap_BA"] < 1e-5, p
    assert abs(p["norm_dAB"] - p["norm_dBA"]) < 1e-5 and p["check_C_max"] <= 1e-4 and p["check_B_min"] > 0
    assert -1 <= p["key_cos_mean"] <= 1 and -1 <= p["key_cos_last_layer"] <= 1
assert max(c["js_bits"] for c in r["commute"]) < 1e-9, max(c["js_bits"] for c in r["commute"])
n_routes = lambda fs: sum(len(facts[f]["routes"]) for f in fs)
assert len(r["commute"]) == n_routes([ids[0], ids[1], ids[3]]) + n_routes([ids[1], ids[2], ids[3]])
# 3. bookkeeping
steps = {(x["step"], x["fact_id"]): x for x in r["dist"]}
assert {s for s, _ in steps} == {"p001:AB", "p001:BA", "p002:AB", "p002:BA"}
d = [x for x in r["delta"] if x["step"] == "p001:BA"]
assert all(x["edited_facts"] == f"{ids[1]}|{ids[0]}" for x in d)
assert {x["fact_id"]: x["fact_edit_step"] for x in d} == {ids[1]: 1, ids[0]: 2, ids[3]: ""}
assert all(not x["fact_edited"] and x["post_greedy"] == "" for x in d if x["fact_id"] == ids[3])
assert {c["role"] for c in r["commute"] if c["pair_id"] == "p002" and c["fact_id"] == ids[1]} == {"A"}
# 2. weight-dependent editor does not commute
r2 = run(dependent)
assert all(p["gap_AB_BA"] > 1e-3 for p in r2["pair"]), [p["gap_AB_BA"] for p in r2["pair"]]
assert max(c["js_bits"] for c in r2["commute"]) > 1e-6
# 4. subject keys equal a manual forward pass
f0 = facts[ids[0]]
k = ra.subject_keys(m, tok, dev, f0, modules)
prompt, subj = f0["edit"]["prompt"], f0["edit"]["subject"]
idx = len(ps.encode_prompt(tok, prompt[:prompt.index(subj) + len(subj)])) - 1
with torch.no_grad():
    hs = m(torch.tensor([ps.encode_prompt(tok, prompt)]), output_hidden_states=True).hidden_states
    blk = m.transformer.h[1]
    manual = blk.mlp.act(blk.mlp.c_fc(blk.ln_2(hs[1] + blk.attn(blk.ln_1(hs[1]))[0])))[0, idx]
assert k[1].shape == (256,) and torch.allclose(k[1], manual, atol=1e-5), (k[1] - manual).abs().max()
# 5. failures
try:
    run(additive, sents=[ids[0]]); raise SystemExit("sentinel inside a pair not refused")
except ValueError as e:
    assert "sentinel" in str(e)
try:
    run(lambda edits: ({}, m, None)); raise SystemExit("check B missed a no-op editor")
except RuntimeError as e:
    assert "check B" in str(e), str(e)
assert all(torch.equal(m.get_parameter(n), base_w[n]) for n in params)
# 6. make_pairs rules
mk = lambda f, rel, s, o, n, ctl=(): {"fact_id": f, "relation": rel, "edit": {"subject": s, "target_old": o, "target_new": n},
                                      "routes": [{"route": "control_same_relation", "control_fact": c} for c in ctl]}
F = {"amazon": mk("amazon", "founder", "Amazon", "Jeff Bezos", "Mark Zuckerberg"),
     "facebook": mk("facebook", "founder", "Facebook", "Mark Zuckerberg", "Jeff Bezos"),
     "apple": mk("apple", "founder", "Apple", "Steve Jobs", "Bill Gates", ctl=("tesla",)),
     "tesla": mk("tesla", "founder", "Tesla", "Elon Musk", "Larry Page"),
     "google": mk("google", "founder", "Google", "Larry Page", "Bill Gates"),
     "dracula": mk("dracula", "author", "Dracula", "Bram Stoker", "Mary Shelley"),
     "emma": mk("emma", "author", "Emma", "Jane Austen", "Leo Tolstoy"),
     "bezos_bio": mk("bezos_bio", "author", "Jeff Bezos", "Brad Stone", "Walter Isaacson")}
pc = lambda a, b: mp.pair_class(F[a], F[b])
assert pc("amazon", "facebook") == "shared_object" and pc("apple", "google") == "same_new"
assert pc("apple", "tesla") == "neighbour" and pc("tesla", "google") == "shared_object"
assert pc("amazon", "bezos_bio") == "chained" and pc("dracula", "emma") == "same_relation" and pc("amazon", "emma") == "disjoint"
pr1, s1, avail = mp.choose(F, {c: 10 ** 9 for c in mp.CLASSES}, 2, "0")
pr2, s2, _ = mp.choose(F, {c: 10 ** 9 for c in mp.CLASSES}, 2, "0")
assert pr1 == pr2 and s1 == s2 and sum(avail.values()) == len(F) * (len(F) - 1) // 2
risky = {"amazon", "facebook", "apple", "google", "tesla", "bezos_bio"}
assert not set(s1) & risky and not {x for p in pr1 for x in (p["fact_a"], p["fact_b"])} & set(s1), (s1, pr1)
# 7. CLI flag check (v1.3.1; jobs 18781-18784 failed because the old guard also fired in pairs mode)
from argparse import Namespace
A = lambda mode, **kw: Namespace(mode=mode, **{**dict(pairs="", programs="", sentinels_file="", derived_facts=""), **kw})
ra.check_mode_args(A("pairs", pairs="p.csv", sentinels_file="s.txt"))
ra.check_mode_args(A("pairs", pairs="p.csv"))
ra.check_mode_args(A("programs", programs="g.jsonl", sentinels_file="s.txt", derived_facts="d.csv"))
for m in ("independent", "sequential", "batch"):
    ra.check_mode_args(A(m))
bad = [A("pairs"), A("programs"), A("pairs", pairs="p.csv", programs="g.jsonl"), A("programs", programs="g.jsonl", pairs="p.csv"),
       A("pairs", pairs="p.csv", derived_facts="d.csv")] +       [A(m, **{k: "x"}) for m in ("independent", "sequential", "batch") for k in ("pairs", "programs", "sentinels_file", "derived_facts")]
for a in bad:
    try:
        ra.check_mode_args(a)
    except ValueError:
        continue
    raise AssertionError(f"check_mode_args accepted {a}")
print("PAIRS TESTS PASSED | commuting and non-commuting editors, bookkeeping, keys, failures, make_pairs rules, CLI flags")
