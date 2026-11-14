"""Offline checks of screen_facts_v4 and the v3 fact set (CPU, no downloads).
  1. Every v3 candidate builds valid probes: 4 forward + 4 reverse routes, the edit prompt contains the subject and does
     not start with it, neighbours are distinct same-relation facts sharing no answer with the edit, choice is stable.
  2. Screening runs end to end on a tiny random GPT-2.
  3. dup_group resolution keeps exactly one included fact per group: highest reverse_old subject log-probability,
     ties broken by the lowest CounterFact case_id.
"""
import json
import sys
from collections import Counter
from pathlib import Path

import torch
from transformers import GPT2Config, GPT2LMHeadModel

SP = Path(sys.argv[1]); sys.path.insert(0, str(SP)); sys.path.insert(0, str(Path(__file__).parent))
import screen_facts_v4 as sv
from screen_facts import load_facts
from toytok import ToyTok

facts = load_facts(str(SP / "facts_v3" / "candidate_facts_v3.csv"))
T = json.load(open(SP / "relation_templates_v3.json", encoding="utf-8"))
assert len(facts) == len({f["fact_id"] for f in facts})
kinds = Counter()
for f in facts:
    p = sv.build_probes(f, facts, T)
    k = Counter(r["kind"] for r in p["routes"])
    assert k["forward"] == 4 and k["reverse_old"] == 2 and k["reverse_new"] == 2, (f["fact_id"], k)
    assert not p["edit"]["prompt"].startswith(f["subject"]), f["fact_id"]
    nb = [r for r in p["routes"] if r["route"].startswith("control_same_relation")]
    ids = [r["control_fact"] for r in nb]
    assert len(set(ids)) == len(ids) and f["fact_id"] not in ids
    for r in nb:
        assert r["answers"]["correct"] not in (f["target_old"], f["target_new"]), (f["fact_id"], r)
    assert [r["control_fact"] for r in sv.build_probes(f, facts, T)["routes"] if "control_fact" in r] == ids, "not stable"
    kinds[(f["relation"], len(nb), "own" if f["new_alt"] else "no_own")] += 1
print("probe structure OK for", len(facts), "facts:", dict(sorted(kinds.items())))

torch.manual_seed(0)
m = GPT2LMHeadModel(GPT2Config(vocab_size=400, n_positions=256, n_embd=64, n_layer=2, n_head=2)).eval()
sample = [f for f in facts if f["relation"] == "country_capital"][:5] + [f for f in facts if f["source"] == "draft"][:3]
res = list(sv.screen(m, ToyTok(), torch.device("cpu"), sample, T))
assert all("included" in p["screening"] for p, _ in res)
json.dumps([p for p, _ in res])


def fake(fid, group, case, lp, included=True):
    p = {"fact_id": fid, "dup_group": group, "cf_case_id": str(case), "screening": {"included": included},
         "routes": [{"route": "reverse_old_best_known", "kind": "reverse_old", "valid": True},
                    {"route": "reverse_old_most_famous", "kind": "reverse_old", "valid": False}]}
    sc = {"reverse_old_best_known": {"answers": {"subject": {"sum_logprob": lp}}},
          "reverse_old_most_famous": {"answers": {"subject": {"sum_logprob": 0.0}}}}   # invalid route must be ignored
    return p, sc


rs = [fake("a", "Berlin", 10, -3.0), fake("b", "Berlin", 5, -1.0), fake("c", "Berlin", 1, -2.0),
      fake("d", "Paris", 7, -1.5), fake("e", "Paris", 3, -1.5), fake("f", "Paris", 1, -0.1, included=False),
      fake("g", "", 2, -9.0)]
w = sv.resolve_dup_groups(rs)
assert w == {"Berlin": "b", "Paris": "e"}, w
inc = {p["fact_id"]: p["screening"]["included"] for p, _ in rs}
assert inc == {"a": False, "b": True, "c": False, "d": False, "e": True, "f": False, "g": True}, inc
assert rs[0][0]["screening"]["excluded_by_dup_group"] == "b"
print("SCREEN V4 TESTS PASSED | candidates", len(facts), "| tiny-model screen", [(p["fact_id"], p["screening"]["included"]) for p, _ in res][:4],
      "| dup groups", w)
