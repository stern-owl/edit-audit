import json, sys, tempfile
from pathlib import Path
import torch
from transformers import GPT2Config, GPT2LMHeadModel
SP = Path(sys.argv[1]); sys.path.insert(0, str(SP)); sys.path.insert(0, str(Path(__file__).parent))
import screen_facts as sf, run_fact_study as st
from toytok import ToyTok
facts = sf.load_facts(str(SP / "candidate_facts_v2.csv")); T = json.load(open(SP / "relation_templates.json"))
torch.manual_seed(0)
m = GPT2LMHeadModel(GPT2Config(vocab_size=300, n_positions=256, n_embd=64, n_layer=2, n_head=2)).eval()
tok, dev = ToyTok(), torch.device("cpu")
d = Path(tempfile.mkdtemp())
for pr, _ in sf.screen(m, tok, dev, facts[:4], T):
    pr["screening"]["included"] = pr["fact_id"] != "dracula"    # force a mix for the test
    json.dump(pr, open(d / f"{pr['fact_id']}.json", "w"))
loaded = st.load_probe_files(d)
assert [p["fact_id"] for p, _ in loaded] == ["frankenstein", "moby_dick", "pride_prejudice"], [p["fact_id"] for p, _ in loaded]
params = ["transformer.h.1.mlp.c_proj.weight"]
base = m.get_parameter(params[0]).detach().clone()
def edit_fn(e):
    with torch.no_grad(): m.get_parameter(params[0]).add_(0.3)
    return {}, m, None
rows = []
for p, _ in loaded:
    pre, post, chk = st.run_one_fact(m, tok, dev, p, edit_fn, params)
    assert torch.equal(m.get_parameter(params[0]), base), "weights not restored between facts"
    rows += list(st.fact_rows(p, pre, post, 0))
assert all("route_valid" in r for r in rows) and any(r["answer_label"].startswith("MARGIN") for r in rows)
st.write_csv(d / "x.csv", rows)
print("STUDY TESTS PASSED | rows", len(rows), "| restored between facts OK")
