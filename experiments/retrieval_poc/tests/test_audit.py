"""Offline checks of run_audit.audit on a tiny random GPT-2 (CPU, no downloads).
  independent: every fact is read after its own edit and the weights are restored after each one;
  sequential:  edits accumulate, every fact is re-read at checkpoints, one exact restore at the end;
  batch:       facts are edited in chunks; every fact is read after every chunk;
  failures:    an editor that undoes its own edit is caught by check B, and an edit outside the snapshotted
               weights (which restore cannot undo) is caught by check C.
"""
import json
import sys
import tempfile
from pathlib import Path

import torch
from transformers import GPT2Config, GPT2LMHeadModel

SP = Path(sys.argv[1]); sys.path.insert(0, str(SP)); sys.path.insert(0, str(Path(__file__).parent))
import run_audit as ra
import screen_facts as sf
from toytok import ToyTok

facts_csv = sf.load_facts(str(SP / "candidate_facts_v2.csv")); T = json.load(open(SP / "relation_templates.json"))
torch.manual_seed(0)
m = GPT2LMHeadModel(GPT2Config(vocab_size=300, n_positions=256, n_embd=64, n_layer=2, n_head=2)).eval()
tok, dev = ToyTok(), torch.device("cpu")
facts = [p for p, _ in sf.screen(m, tok, dev, facts_csv[:4], T)]
params = ["transformer.h.1.mlp.c_proj.weight"]
base = m.get_parameter(params[0]).detach().clone()
calls = []


def live(edits):
    calls.append([e["subject"] for e in edits])
    with torch.no_grad():
        m.get_parameter(params[0]).add_(torch.randn_like(base) * 0.2)
    return {}, m, None


def run(mode, edit_fn=live, **kw):
    rows = {"delta": [], "dist": [], "check": []}
    calls.clear()
    steps = ra.make_steps(len(facts), mode, kw.pop("batch_size", 2))
    ra.audit(m, tok, dev, facts, steps, edit_fn, params, mode, lambda k, r: rows[k].extend(r), gen_tokens=3,
             reread_gen_tokens=kw.pop("reread_gen_tokens", 3), **kw)
    assert torch.equal(m.get_parameter(params[0]), base), f"{mode}: weights not restored"
    return rows, steps


n = len(facts)
routes = {p["fact_id"]: len(p["routes"]) for p in facts}
# independent
r, steps = run("independent")
assert len(steps) == n and len(calls) == n and all(len(c) == 1 for c in calls)
assert {x["fact_id"] for x in r["dist"]} == set(routes) and len(r["dist"]) == sum(routes.values())
assert all(c["check_C_restore_max_diff"] <= 1e-4 and c["check_B_weight_change_max_abs"] > 0 for c in r["check"])
assert all(x["edited_facts"] == x["fact_id"] for x in r["delta"])
# sequential, all facts re-read at every step
r, steps = run("sequential")
reads = [(x["step"], x["fact_id"]) for x in r["dist"]]
assert len(set(reads)) == n * n, "every fact should be read after every step"
last = [x for x in r["dist"] if x["step"] == n]
assert all(x["fact_edited"] for x in last) and len(last) == sum(routes.values())
step1 = {x["fact_id"]: x["fact_edited"] for x in r["dist"] if x["step"] == 1}
assert sum(step1.values()) == 1, step1
untouched = [x for x in r["dist"] if x["step"] == 1 and not x["fact_edited"]]
assert any(x["js_bits"] > 0 for x in untouched), "side effects on untouched facts should be visible"
cum = [c["cumulative_delta_frobenius_norm"] for c in r["check"] if c["step"] != "final_restore"]
assert cum[-1] > cum[0] and r["check"][-1]["step"] == "final_restore" and r["check"][-1]["check_C_restore_max_diff"] <= 1e-4
# sequential with checkpoints and no greedy re-reads: step 1 reads only the edited fact
r, _ = run("sequential", checkpoints={2}, reread_gen_tokens=0)
by_step = {}
for x in r["dist"]:
    by_step.setdefault(x["step"], set()).add(x["fact_id"])
assert len(by_step[1]) == 1 and len(by_step[2]) == n and len(by_step[n]) == n and len(by_step[3]) == 1
assert all(x["post_greedy"] == "" and x["pre_greedy"] == "" for x in r["delta"] if x["fact_id"] not in x["edited_facts"].split("|"))
# batch
r, steps = run("batch", batch_size=3)
assert [len(s) for s in steps] == [3, n - 3] and [len(c) for c in calls] == [3, n - 3]
assert len({(x["step"], x["fact_id"]) for x in r["dist"]}) == 2 * n
with tempfile.TemporaryDirectory() as d:
    sink = ra.CsvSink(Path(d)); sink("delta", r["delta"]); sink("dist", r["dist"]); sink("check", r["check"]); sink.close()
    assert sum(1 for _ in open(Path(d) / "dist.csv")) == len(r["dist"]) + 1


# failures
def undoing(edits):
    return {}, m, None


def outside(edits):   # changes a weight that is not snapshotted, so restore cannot undo it
    # Random, not constant: a constant added to every entry of c_proj shifts all hidden dimensions equally, which
    # the following LayerNorms remove exactly, so the outputs would not change and check C would rightly pass.
    with torch.no_grad():
        m.get_parameter(params[0]).add_(0.1)
        w = m.get_parameter("transformer.h.0.mlp.c_proj.weight")
        w.add_(torch.randn_like(w) * 0.5)
    return {}, m, None


for mode, fn, check in (("sequential", undoing, "check B"), ("independent", outside, "check C"), ("sequential", outside, "Check C")):
    saved = {k: v.clone() for k, v in m.state_dict().items()}
    try:
        run(mode, edit_fn=fn)
        raise SystemExit(f"{check} missed a failure in {mode} mode")
    except (RuntimeError, AssertionError) as e:
        assert check in str(e), (mode, check, str(e)[:120])
        print(f"{mode}: {check} correctly caught:", str(e)[:70])
    m.load_state_dict(saved)
# alphaedit_reset: right cache shape for Linear (GPT-J/Llama style, weight (out, in)) and Conv1D (GPT-2, weight (in, out))
import types
from transformers.pytorch_utils import Conv1D
holder = types.SimpleNamespace()
lin = torch.nn.Sequential(); lin.add_module("fc_out", torch.nn.Linear(16, 4))
ra.alphaedit_reset(holder, lin, types.SimpleNamespace(rewrite_module_tmp="fc_out", layers=[3, 4, 5]))
assert holder.cache_c.shape == (3, 16, 16) and holder.cache_c_new and not holder.cache_c.any()
ra.alphaedit_reset(holder, m, types.SimpleNamespace(rewrite_module_tmp="transformer.h.{}.mlp.c_proj", layers=[0, 1]))
assert isinstance(m.get_submodule("transformer.h.1.mlp.c_proj"), Conv1D) and holder.cache_c.shape == (2, 256, 256), holder.cache_c.shape
print("AUDIT TESTS PASSED | facts", n, "| modes independent, sequential (+checkpoints), batch | alphaedit_reset shapes OK")
