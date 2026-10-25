import json, sys, tempfile
from pathlib import Path
import torch
from transformers import GPT2Config, GPT2LMHeadModel

SP = Path(sys.argv[1]); sys.path.insert(0, str(SP)); sys.path.insert(0, str(Path(__file__).parent))
import rome_paired_pilot as rp
from toytok import ToyTok

torch.manual_seed(0)
model = GPT2LMHeadModel(GPT2Config(vocab_size=200, n_positions=256, n_embd=64, n_layer=2, n_head=2)).eval()
tok, dev = ToyTok(), torch.device("cpu")
probes = json.load(open(SP / "frankenstein_frozen_probes.json"))
params = ["transformer.h.1.mlp.c_proj.weight"]

def live_edit():
    orig = {n: model.get_parameter(n).detach().clone() for n in params}
    with torch.no_grad():
        model.get_parameter(params[0]).add_(torch.randn_like(model.get_parameter(params[0])) * 0.5)
    return {"rewrite_acc": [1.0]}, model, orig

def restoring_edit():  # mimics edit(..., sequential_edit=False): restores before returning
    m, mdl, orig = live_edit()
    with torch.no_grad():
        for n, w in orig.items(): mdl.get_parameter(n).copy_(w)
    return m, mdl, orig

phases, checks, metrics = rp.run_pilot(model, tok, dev, probes, live_edit, params)
assert checks["check_B_weight_change_max_abs"] > 0 and checks["check_C_restore_max_diff"] <= 1e-4
assert rp.max_score_diff(phases["pre"], phases["post"]) > 1e-3, "post should differ from pre"
deltas = list(rp.delta_rows(phases["pre"], phases["post"], probes))
margins = [d for d in deltas if d["answer_label"].startswith("MARGIN")]
assert len(margins) == 4 and len(list(rp.long_rows(phases))) == 4 * 20
with tempfile.TemporaryDirectory() as d:
    rp.write_csv(f"{d}/x.csv", deltas); json.dumps(phases)
try:
    rp.run_pilot(model, tok, dev, probes, restoring_edit, params); raise SystemExit("Check B missed a restored edit")
except RuntimeError as e:
    print("Check B correctly caught:", str(e)[:70])
print("PILOT TESTS PASSED | delta rows", len(deltas), "| checks", {k: round(v, 6) for k, v in checks.items() if not isinstance(v, dict)})
