"""Offline checks of analyze_audit.py (CPU, no downloads).
  1. Contract logic on hand-made rows: for an inverse-functional relation a reverse-from-new read is a violation unless
     the subject is rank 1; for a non-functional relation it is a violation unless the subject's log-probability rises.
     Invalid paths are ignored; stale reverse reads count for every relation.
  2. End to end on real run_audit outputs of a tiny model (independent and sequential): report and summary are written,
     every rate lies in [0, 1], the bootstrap interval contains the point estimate, sequential steps are listed.
"""
import json
import sys
import tempfile
from pathlib import Path

import torch
from transformers import GPT2Config, GPT2LMHeadModel

SP = Path(sys.argv[1]); sys.path.insert(0, str(SP)); sys.path.insert(0, str(Path(__file__).parent))
import analyze_audit as aa
import run_audit as ra
import screen_facts_v4 as sv
from screen_facts import load_facts
from toytok import ToyTok

card = {"country_capital": {"inverse": "functional"}, "novel_author": {"inverse": "non-functional"}}


def row(fact, rel, kind, route, label, post_rank, delta, valid=True, answer="x", pre_rank=1):
    return {"fact_id": fact, "relation": rel, "kind": kind, "route": route, "answer_label": label, "route_valid": str(valid),
            "post_first_token_rank": str(post_rank), "pre_first_token_rank": str(pre_rank), "delta_sum_logprob": str(delta),
            "step": "1", "edited_facts": fact, "fact_edited": "True", "answer": answer}


ep = lambda f, rel, r, new: row(f, rel, "forward", "forward_edit_prompt", "new_object", r, 5.0, answer=new)
d = [ep("cap", "country_capital", 1, "Rome"), ep("nov", "novel_author", 1, "Bram Stoker"), ep("bad", "novel_author", 7, "Jane Austen"),
     row("cap", "country_capital", "reverse_new", "reverse_new_best_known", "subject", 1, -0.5),   # rank 1: no violation
     row("cap", "country_capital", "reverse_new", "reverse_new_most_famous", "subject", 4, +2.0),  # rises, not rank 1: violation
     row("nov", "novel_author", "reverse_new", "reverse_new_best_known", "subject", 30, +0.3),     # rises: no violation
     row("nov", "novel_author", "reverse_new", "reverse_new_most_famous", "subject", 3, -0.1),     # falls: violation
     row("nov", "novel_author", "reverse_new", "reverse_new_extra", "subject", 1, -9.0, valid=False),  # invalid: ignored
     row("nov", "novel_author", "reverse_old", "reverse_old_best_known", "subject", 1, -0.1),      # stale (was rank 1 before)
     row("nov", "novel_author", "reverse_old", "reverse_old_most_famous", "subject", 2, -0.1, pre_rank=3),  # not stale
     row("cap", "country_capital", "reverse_old", "reverse_old_best_known", "subject", 2, -3.0),   # not stale
     row("bad", "novel_author", "reverse_old", "reverse_old_best_known", "subject", 1, 0.0),       # failed edit: excluded
     # controls of 'nov': own fact (correct = new object), a passing neighbour, a failing neighbour, an o*-equal neighbour
     row("nov", "novel_author", "control", "control_new_object_own_fact", "correct", 1, 0.0, answer="Bram Stoker"),
     row("nov", "novel_author", "control", "control_new_object_own_fact", "edit_leak", 1, 0.0, answer="Mary Shelley"),
     row("nov", "novel_author", "control", "control_same_relation", "correct", 1, 0.0, answer="Jane Austen"),
     row("nov", "novel_author", "control", "control_same_relation", "edit_leak", 3, 0.0, answer="Bram Stoker"),
     row("nov", "novel_author", "control", "control_same_relation_2", "correct", 4, 0.0, answer="Herman Melville"),
     row("nov", "novel_author", "control", "control_same_relation_3", "correct", 1, 0.0, answer="Bram Stoker")]
dist = [{"fact_id": "nov", "step": "1", "route": rt, "js_bits": str(j)} for rt, j in
        (("control_same_relation", 0.05), ("control_same_relation_2", 0.30), ("control_same_relation_3", 0.0), ("control_new_object_own_fact", 0.2))]
recs = aa.fact_records(d, dist, card)
assert recs["cap"]["rev_new_violation"] == [False, True], recs["cap"]["rev_new_violation"]
assert recs["nov"]["rev_new_violation"] == [False, True], recs["nov"]["rev_new_violation"]
assert recs["nov"]["rev_old_stale"] == [True, False] and recs["cap"]["rev_old_stale"] == [False]
assert recs["bad"]["rev_old_stale"] == [] and recs["bad"]["rev_old_stale_all"] == [True], "failed edit must be excluded"
assert recs["nov"]["rev_old_survival"] == [True], recs["nov"]["rev_old_survival"]     # only the pre-edit rank-1 path
assert aa.rate(list(recs.values()), "rev_new_violation") == (2, 4)
n = recs["nov"]
assert n["own_correct1"] == [True] and n["nb_correct1"] == [True, False], (n["own_correct1"], n["nb_correct1"])  # o*-equal neighbour dropped
assert n["nb_leak_top5"] == [True], n["nb_leak_top5"]                                 # own-fact leak row not a neighbour leak
assert n["nb_pass_shift"] == [True], n["nb_pass_shift"]                               # denominator: passing neighbour reads only
assert sorted(n["nb_js"]) == [0.05, 0.30], n["nb_js"]

facts_csv = load_facts(str(SP / "facts_v3" / "candidate_facts_v3.csv"))
T3 = json.load(open(SP / "relation_templates_v3.json", encoding="utf-8"))
torch.manual_seed(0)
m = GPT2LMHeadModel(GPT2Config(vocab_size=400, n_positions=256, n_embd=64, n_layer=2, n_head=2)).eval()
tok, dev = ToyTok(), torch.device("cpu")
sample = [f for f in facts_csv if f["source"] == "draft"][:4] + [f for f in facts_csv if f["relation"] == "country_capital"][:2]
probes = []
for f in sample:
    p = sv.build_probes(f, facts_csv, T3)
    for r in p["routes"]:
        r["valid"] = True
    probes.append(p)
params = ["transformer.h.1.mlp.c_proj.weight"]


def live(edits):
    with torch.no_grad():
        m.get_parameter(params[0]).add_(torch.randn_like(m.get_parameter(params[0])) * 0.2)
    return {}, m, None


tmp = Path(tempfile.mkdtemp())
for mode in ("independent", "sequential"):
    out = tmp / mode
    out.mkdir()
    sink = ra.CsvSink(out)
    steps = ra.make_steps(len(probes) - (2 if mode == "sequential" else 0), mode, 0)   # sequential: last 2 held out
    ra.audit(m, tok, dev, probes, steps, live, params, mode, sink, gen_tokens=2, reread_gen_tokens=0, checkpoints={1, 3})
    sink.close()
    (out / "manifest.json").write_text(json.dumps({"mode": mode, "model": "tiny", "seed": 0}))
sys.argv = ["analyze_audit.py", "--templates", str(SP / "relation_templates_v3.json"), "--out", str(tmp / "report"),
            "--run", f"IND={tmp / 'independent'}", "--run", f"SEQ={tmp / 'sequential'}"]
aa.main()
rep = (tmp / "report" / "report.md").read_text(encoding="utf-8")
assert "## Independent edits" in rep and "## Sequential / batch edits" in rep and "Persistence" in rep
import csv
rows = list(csv.DictReader(open(tmp / "report" / "summary.csv", encoding="utf-8")))
for r in rows:
    if r["rate"] != "":
        assert 0 <= float(r["rate"]) <= 1, r
    if r.get("ci_low"):
        assert float(r["ci_low"]) - 1e-9 <= float(r["rate"]) <= float(r["ci_high"]) + 1e-9, r
steps = sorted({int(r["step"]) for r in rows if r["table"] == "sequential"})
assert steps == [1, 3, len(probes) - 2], steps
held = [r for r in rows if r["table"] == "sequential" and r["group"] == "held_out"]
assert held and all(int(r["facts"]) == 2 for r in held), held
# controls whose fact was edited are excluded: a neighbour edited at step 1 must not count at step 3
es = {"a": 1}
d2 = [dict(row("x", "novel_author", "control", "control_same_relation", "correct", 1, 0.0), step="3", control_fact="a", fact_edited="False"),
      dict(row("x", "novel_author", "control", "control_same_relation_2", "correct", 7, 0.0), step="3", control_fact="b", fact_edited="False")]
rx = aa.fact_records(d2, [], card, step=3, edit_step=es)["x"]
assert rx["nbU_correct1"] == [False], rx["nbU_correct1"]
print("ANALYZE AUDIT TESTS PASSED | summary rows", len(rows), "| sequential full-read steps", steps)
