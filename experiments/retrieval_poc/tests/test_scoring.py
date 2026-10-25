"""Offline check of probe_scoring: full-answer log-prob equals a brute-force computation, and scoring is deterministic."""
import sys
from pathlib import Path
import torch
from transformers import GPT2Config, GPT2LMHeadModel

SP = Path(sys.argv[1]); sys.path.insert(0, str(SP)); sys.path.insert(0, str(Path(__file__).parent))
import probe_scoring as ps
from toytok import ToyTok

torch.manual_seed(0)
model = GPT2LMHeadModel(GPT2Config(vocab_size=200, n_positions=256, n_embd=64, n_layer=2, n_head=2)).eval()
tok, dev = ToyTok(), torch.device("cpu")
prompt, answer = "The novel Frankenstein was written by", "Mary Shelley"
s = ps.score_answer(model, tok, prompt, answer, dev)

p_ids, a_ids = tok(prompt)["input_ids"], tok(" " + answer)["input_ids"]
brute = 0.0
for i, t in enumerate(a_ids):
    with torch.no_grad():
        lg = model(torch.tensor([p_ids + a_ids[:i]])).logits[0, -1]
    brute += torch.log_softmax(lg, -1)[t].item()
assert abs(brute - s["sum_logprob"]) < 1e-4, (brute, s["sum_logprob"])
assert s["num_tokens"] == len(a_ids) and "".join(s["answer_tokens"]) == " " + answer
assert ps.score_answer(model, tok, prompt, answer, dev) == s, "scoring is not deterministic"
print("SCORING TESTS PASSED | brute", round(brute, 4))
