"""Model-agnostic probe scoring (v4) plus distributional side-effect metrics.

probe_scoring.py (v3.1) stays unchanged for provenance: every shipped GPT-2 XL run logs its md5. v4 keeps its
score fields and conventions and changes only what other tokenizers need:

  * Beginning-of-sequence token. v3 encodes prompts with add_special_tokens=False, which is right for GPT-2
    (no BOS) but drops the BOS that Llama-3 and similar models are trained with. v4 prepends BOS exactly when the
    tokenizer itself would (`tokenizer(text)` starts with bos_token_id), so each model is read the way it is used.
  * Answer tokenisation. v3 tokenises prompt and " " + answer separately and concatenates them. v4 tokenises
    prompt + " " + answer jointly and takes the part after the prompt's tokens. For byte-level BPE (GPT-2, Llama-3,
    Qwen) the two are identical, because pre-tokenisation splits at the space; for SentencePiece tokenizers the
    joint form is the one that matches running text. If the prompt's tokens are not a prefix of the joint
    tokenisation (a merge across the boundary), v4 falls back to the v3 convention and sets boundary_merge=True.

Distributional metrics compare the full next-token distribution at the end of a prompt before and after an edit.
They complement the candidate ranks: a neighbour can keep its correct answer at rank 1 while the distribution moves.
  next_token_shift(pre, post)    KL(pre||post), KL(post||pre), JS (base 2, in [0,1]), total variation,
                                 argmax change and top-10 overlap, over the whole vocabulary.
  candidate_shift(pre, post)     the same divergences over a fixed answer set, after renormalising each answer's
                                 full-answer probability within the set (so multi-token answers are comparable).
"""
import math

import torch

from probe_scoring import cap_gpu_memory, gpu_peak_gb, split_alternatives  # noqa: F401  (re-exported)

SCRIPT_VERSION = "probe_scoring v4.0 (2026-10-31)"
LN2 = math.log(2.0)


def _ids(tokenizer, text):
    return list(tokenizer(text, add_special_tokens=False)["input_ids"])


def bos_prefix(tokenizer):
    """[bos_token_id] if the tokenizer adds BOS by itself, else []."""
    bos = getattr(tokenizer, "bos_token_id", None)
    if bos is None:
        return []
    probe = list(tokenizer("a", add_special_tokens=True)["input_ids"])
    return [bos] if probe and probe[0] == bos else []


def encode_prompt(tokenizer, prompt):
    ids = bos_prefix(tokenizer) + _ids(tokenizer, prompt)
    if not ids:
        raise ValueError(f"Empty token sequence for {prompt!r}")
    return ids


def encode_pair(tokenizer, prompt, answer):
    """(prompt_ids, answer_ids, boundary_merge) under the v4 convention described above."""
    bos = bos_prefix(tokenizer)
    p = _ids(tokenizer, prompt)
    joint = _ids(tokenizer, prompt + " " + answer)
    if joint[:len(p)] == p and len(joint) > len(p):
        a, merged = joint[len(p):], False
    else:
        a, merged = _ids(tokenizer, " " + answer), True
    if not p or not a:
        raise ValueError(f"Empty token sequence for {prompt!r} / {answer!r}")
    return bos + p, a, merged


def _logits(model, ids, device):
    with torch.inference_mode():
        return model(torch.tensor([ids], device=device)).logits[0].float()


def score_answer(model, tokenizer, prompt, answer, device):
    """Same fields as probe_scoring.score_answer, plus boundary_merge and has_bos."""
    prompt_ids, answer_ids, merged = encode_pair(tokenizer, prompt, answer)
    start, n = len(prompt_ids), len(answer_ids)
    logits = _logits(model, prompt_ids + answer_ids, device)
    pred_logits = logits[start - 1 : start - 1 + n]
    log_probs = torch.log_softmax(pred_logits, dim=-1)
    targets = torch.tensor(answer_ids, device=log_probs.device)
    token_lps = log_probs.gather(1, targets.unsqueeze(1)).squeeze(1)
    first_logits = pred_logits[0]
    first_rank = int((first_logits > first_logits[targets[0]]).sum().item()) + 1
    sum_lp = float(token_lps.sum().item())
    return {
        "answer": answer,
        "answer_tokens": [tokenizer.decode([t]) for t in answer_ids],
        "num_tokens": n,
        "token_logprobs": [float(x) for x in token_lps.tolist()],
        "sum_logprob": sum_lp,
        "sequence_probability": math.exp(sum_lp),
        "mean_token_logprob": sum_lp / n,
        "mean_token_probability": math.exp(sum_lp / n),
        "first_token_probability": math.exp(float(token_lps[0].item())),
        "first_token_rank": first_rank,
        "boundary_merge": merged,
        "has_bos": bool(bos_prefix(tokenizer)),
    }


def next_token_logprobs(model, tokenizer, prompt, device):
    """Full next-token log-distribution at the end of `prompt`: computed in float64, kept as float32 on CPU
    (in memory only; ~0.5 MB per read for a 128k vocabulary). Divergences upcast to float64 again."""
    return torch.log_softmax(_logits(model, encode_prompt(tokenizer, prompt), device)[-1].double(), dim=-1).float().cpu()


def top_k(tokenizer, logprobs, k=5):
    v, i = torch.topk(logprobs, k)
    return [{"token": tokenizer.decode([int(t)]), "probability": float(math.exp(x))} for x, t in zip(v.tolist(), i.tolist())]


def greedy_continuation(model, tokenizer, prompt, device, max_new_tokens=10):
    if max_new_tokens <= 0:
        return ""
    ids = torch.tensor([encode_prompt(tokenizer, prompt)], device=device)
    pad = tokenizer.pad_token_id if getattr(tokenizer, "pad_token_id", None) is not None else tokenizer.eos_token_id
    with torch.inference_mode():
        out = model.generate(ids, attention_mask=torch.ones_like(ids), max_new_tokens=max_new_tokens,
                             do_sample=False, num_beams=1, pad_token_id=pad)
    return tokenizer.decode(out[0, ids.shape[1]:])


def probe_prompt(model, tokenizer, prompt, answers, device, gen_tokens=10, keep_distribution=False):
    """Same output as probe_scoring.probe_prompt; with keep_distribution the full next-token log-distribution
    is returned under "_next_token_logprobs" (a tensor: strip it before writing JSON)."""
    lp = next_token_logprobs(model, tokenizer, prompt, device)
    out = {
        "prompt": prompt,
        "greedy_continuation": greedy_continuation(model, tokenizer, prompt, device, gen_tokens),
        "top5_next_tokens": top_k(tokenizer, lp, 5),
        "answers": {label: score_answer(model, tokenizer, prompt, ans, device) for label, ans in answers},
    }
    if keep_distribution:
        out["_next_token_logprobs"] = lp
    return out


def _plogratio(p, la, lb):
    """sum of p * (la - lb) with the convention 0 * log 0 = 0 (entries with p == 0 contribute nothing, even when
    la is -inf, e.g. vocabulary slots a model masks with -inf logits). Gives +inf if p > 0 where lb is -inf."""
    return float(torch.where(p > 0, p * (la - lb), torch.zeros_like(p)).sum())


def _divergences(lp, lq):
    """KL(p||q), KL(q||p), JS (bits), TV for log-distributions lp, lq over the same support (float64)."""
    p, q = lp.exp(), lq.exp()
    kl_pq = _plogratio(p, lp, lq)
    kl_qp = _plogratio(q, lq, lp)
    lm = torch.logaddexp(lp, lq) - math.log(2.0)
    js = 0.5 * _plogratio(p, lp, lm) + 0.5 * _plogratio(q, lq, lm)
    return {"kl_pre_post": max(kl_pq, 0.0), "kl_post_pre": max(kl_qp, 0.0), "js_bits": max(js, 0.0) / LN2,
            "tv": 0.5 * float((p - q).abs().sum())}


def next_token_shift(pre_lp, post_lp, k=10):
    d = _divergences(pre_lp.double(), post_lp.double())
    top_pre, top_post = set(torch.topk(pre_lp, k).indices.tolist()), set(torch.topk(post_lp, k).indices.tolist())
    d.update({"argmax_changed": int(pre_lp.argmax()) != int(post_lp.argmax()), f"top{k}_overlap": len(top_pre & top_post) / k})
    return d


def candidate_shift(pre_sum_logprobs, post_sum_logprobs):
    """Divergences between the answer-set distributions before and after, each renormalised within the set.
    Inputs: dicts answer -> full-answer log-probability, with identical keys."""
    keys = sorted(pre_sum_logprobs)
    if keys != sorted(post_sum_logprobs) or len(keys) < 2:
        raise ValueError("candidate_shift needs the same >= 2 answers before and after")
    a = torch.tensor([pre_sum_logprobs[k] for k in keys], dtype=torch.float64)
    b = torch.tensor([post_sum_logprobs[k] for k in keys], dtype=torch.float64)
    return _divergences(a - torch.logsumexp(a, 0), b - torch.logsumexp(b, 0))
