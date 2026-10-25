import json, sys, csv, io
from pathlib import Path
import torch
from transformers import GPT2Config, GPT2LMHeadModel
SP = Path(sys.argv[1]); sys.path.insert(0, str(SP)); sys.path.insert(0, str(Path(__file__).parent))
import screen_facts as sf
from toytok import ToyTok
facts = sf.load_facts(str(SP / "candidate_facts_v2.csv"))
T = json.load(open(SP / "relation_templates.json"))
for f in facts:
    p = sf.build_probes(f, facts, T)
    ctrl = [r for r in p["routes"] if r["kind"] == "control"]
    for c in ctrl:
        assert c["answers"]["correct"] != c["answers"]["edit_leak"], (f["fact_id"], c)
    assert len(ctrl) >= 1, f["fact_id"]
    n = len(p["routes"])
    print(f"{f['fact_id']:16s} routes={n:2d} edit={p['edit']['prompt']!r}  ctrl={[c.get('control_fact', 'own') for c in ctrl]}")
p = sf.build_probes(facts[4], facts, T)
for r in p["routes"]: print("   ", r["kind"], "|", r["prompt"], "|", list(r["answers"].values()))
torch.manual_seed(0)
m = GPT2LMHeadModel(GPT2Config(vocab_size=300, n_positions=256, n_embd=64, n_layer=2, n_head=2)).eval()
res = list(sf.screen(m, ToyTok(), torch.device("cpu"), facts[:5], T))
assert all("included" in pr["screening"] for pr, _ in res)
json.dumps([pr for pr, _ in res])
print("SCREEN TESTS PASSED:", [(pr["fact_id"], pr["screening"]["included"]) for pr, _ in res])
