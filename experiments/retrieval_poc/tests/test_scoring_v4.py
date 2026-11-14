"""Offline checks of probe_scoring_v4 (CPU, no downloads).
  1. On GPT-2-style inputs (no BOS) v4 gives exactly the v3 scores, so GPT-2 XL results stay comparable.
  2. With a tokenizer that adds BOS (Llama-3 style), v4 prepends it and still equals a brute-force computation.
  3. Divergences: zero for identical distributions, analytic values for two-point distributions, JS in [0, 1].
  4. Candidate-set shift is invariant to adding a constant to every answer's log-probability.
"""
import math
import sys
from pathlib import Path

import torch
from tokenizers import Tokenizer, decoders, models, pre_tokenizers, processors, trainers
from transformers import GPT2Config, GPT2LMHeadModel, LlamaConfig, LlamaForCausalLM, PreTrainedTokenizerFast

SP = Path(sys.argv[1]); sys.path.insert(0, str(SP)); sys.path.insert(0, str(Path(__file__).parent))
import probe_scoring as v3
import probe_scoring_v4 as v4
from toytok import ToyTok

dev = torch.device("cpu")
PROMPT, ANSWER = "The novel Frankenstein was written by", "Mary Shelley"
NEW_KEYS = {"boundary_merge", "has_bos"}


def bpe_tokenizer(with_bos):
    corpus = ["The novel Frankenstein was written by Mary Shelley.", "Bram Stoker wrote the novel Dracula.",
              "The company Amazon was founded by Jeff Bezos.", "Who wrote the novel? It was written by"] * 20
    tk = Tokenizer(models.BPE())
    tk.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tk.decoder = decoders.ByteLevel()
    tk.train_from_iterator(corpus, trainers.BpeTrainer(vocab_size=320, special_tokens=["<bos>", "<eos>"],
                                                       initial_alphabet=pre_tokenizers.ByteLevel.alphabet()))
    if with_bos:
        tk.post_processor = processors.TemplateProcessing(single="<bos> $A", special_tokens=[("<bos>", tk.token_to_id("<bos>"))])
    return PreTrainedTokenizerFast(tokenizer_object=tk, bos_token="<bos>", eos_token="<eos>")


def brute(model, prompt_ids, answer_ids):
    total = 0.0
    for i, t in enumerate(answer_ids):
        with torch.no_grad():
            total += torch.log_softmax(model(torch.tensor([prompt_ids + answer_ids[:i]])).logits[0, -1], -1)[t].item()
    return total


def same_as_v3(model, tok):
    a = v3.score_answer(model, tok, PROMPT, ANSWER, dev)
    b = v4.score_answer(model, tok, PROMPT, ANSWER, dev)
    assert not b["has_bos"] and not b["boundary_merge"], b
    assert {k: v for k, v in b.items() if k not in NEW_KEYS} == a, "v4 differs from v3 on a no-BOS tokenizer"


torch.manual_seed(0)
# 1a. character-level toy tokenizer used by the v3 tests
same_as_v3(GPT2LMHeadModel(GPT2Config(vocab_size=200, n_positions=256, n_embd=64, n_layer=2, n_head=2)).eval(), ToyTok())
# 1b. byte-level BPE without BOS (GPT-2 convention)
tok = bpe_tokenizer(with_bos=False)
assert v4.bos_prefix(tok) == [], "a tokenizer that does not add BOS must not get one"
gpt = GPT2LMHeadModel(GPT2Config(vocab_size=len(tok), n_positions=256, n_embd=64, n_layer=2, n_head=2)).eval()
same_as_v3(gpt, tok)

# 2. byte-level BPE that adds BOS, on a tiny Llama
tok_b = bpe_tokenizer(with_bos=True)
bos = tok_b.convert_tokens_to_ids("<bos>")
assert v4.bos_prefix(tok_b) == [bos] and v4.encode_prompt(tok_b, PROMPT)[0] == bos
llama = LlamaForCausalLM(LlamaConfig(vocab_size=len(tok_b), hidden_size=64, intermediate_size=128, num_hidden_layers=2,
                                     num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=256)).eval()
s = v4.score_answer(llama, tok_b, PROMPT, ANSWER, dev)
p_ids, a_ids, merged = v4.encode_pair(tok_b, PROMPT, ANSWER)
assert p_ids[0] == bos and not merged and s["has_bos"]
assert abs(brute(llama, p_ids, a_ids) - s["sum_logprob"]) < 1e-4
assert "".join(s["answer_tokens"]) == " " + ANSWER, s["answer_tokens"]
assert v4.score_answer(llama, tok_b, PROMPT, ANSWER, dev) == s, "scoring is not deterministic"
pp = v4.probe_prompt(llama, tok_b, PROMPT, [("old", ANSWER), ("new", "Bram Stoker")], dev, keep_distribution=True)
lp = pp.pop("_next_token_logprobs")
assert lp.shape == (len(tok_b),) and lp.dtype == torch.float32 and abs(float(lp.double().exp().sum()) - 1) < 1e-5

# 3. divergences
z = v4.next_token_shift(lp, lp.clone())
assert all(abs(z[k]) < 1e-12 for k in ("kl_pre_post", "kl_post_pre", "js_bits", "tv")) and not z["argmax_changed"]
assert z["top10_overlap"] == 1.0
p, q = torch.tensor([0.5, 0.5], dtype=torch.float64).log(), torch.tensor([0.9, 0.1], dtype=torch.float64).log()
d = v4._divergences(p, q)
kl = 0.5 * math.log(0.5 / 0.9) + 0.5 * math.log(0.5 / 0.1)
m = [0.7, 0.3]
js = 0.5 * (0.5 * math.log(0.5 / m[0]) + 0.5 * math.log(0.5 / m[1])) + 0.5 * (0.9 * math.log(0.9 / m[0]) + 0.1 * math.log(0.1 / m[1]))
assert abs(d["kl_pre_post"] - kl) < 1e-12 and abs(d["js_bits"] - js / math.log(2)) < 1e-12 and abs(d["tv"] - 0.4) < 1e-12
inf = float("inf")   # exactly-zero probabilities (-inf log-probs), e.g. vocabulary slots masked with -inf logits
disjoint = v4._divergences(torch.tensor([0.0, -inf], dtype=torch.float64), torch.tensor([-inf, 0.0], dtype=torch.float64))
assert abs(disjoint["js_bits"] - 1.0) < 1e-12 and disjoint["kl_pre_post"] == inf and disjoint["tv"] == 1.0, disjoint
masked = v4._divergences(torch.tensor([-0.5, -1.0, -inf]).double(), torch.tensor([-0.7, -0.8, -inf]).double())
assert all(math.isfinite(masked[k]) for k in masked) and masked["js_bits"] > 0, masked   # a shared zero is ignored
other = v4.next_token_shift(lp, torch.log_softmax(torch.randn_like(lp), -1))
assert 0 < other["js_bits"] <= 1 and other["kl_pre_post"] > 0

# 4. candidate-set shift
pre = {"Jane Austen": -0.3, "Bram Stoker": -6.0, "Mary Shelley": -4.0}
assert v4.candidate_shift(pre, {k: v - 2.5 for k, v in pre.items()})["js_bits"] < 1e-12
moved = v4.candidate_shift(pre, {"Jane Austen": -0.3, "Bram Stoker": -1.0, "Mary Shelley": -4.0})
assert moved["kl_pre_post"] > 0 and moved["js_bits"] > 0
print("SCORING V4 TESTS PASSED | v3-equal on no-BOS tokenizers | BOS brute", round(s["sum_logprob"], 4),
      "| JS random", round(other["js_bits"], 4), "| candidate JS", round(moved["js_bits"], 4))
