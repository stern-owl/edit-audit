"""Shared probe scoring for the LLM-editing audit (pre-edit validation and, later, paired ROME runs).

Every function here is deterministic (inference mode, greedy decoding), so the same prompt
scored twice on the same weights gives the same numbers. Use these functions unchanged
before and after an edit so pre/post comparisons use one scoring procedure.

Score fields per (prompt, answer):
  sum_logprob            log P(answer tokens | prompt), summed over answer tokens.
                         exp(sum_logprob) is the probability of the whole answer string
                         under this tokenization. Use THIS for old-vs-new comparisons.
  mean_token_logprob     sum_logprob / num_tokens (length-normalized).
  mean_token_probability exp(mean_token_logprob). Kept for continuity with earlier runs;
                         NOT a sequence probability, and biased toward multi-token answers
                         whose later tokens are near-certain (e.g. " Bram" -> " Stoker").
  first_token_*          probability and rank of the answer's first token only.
"""
import math

import torch

SCRIPT_VERSION = "probe_scoring v3.1 (2026-10-23)"


def cap_gpu_memory(limit_gb, device_index=0):
    """Hard-cap this process's PyTorch GPU memory at `limit_gb` GiB.

    Call BEFORE loading the model. Exceeding the cap raises a CUDA out-of-memory error
    instead of taking more of the GPU. Returns a dict to log. No-op without CUDA.
    """
    if not torch.cuda.is_available():
        return {"cuda": False}
    free_b, total_b = torch.cuda.mem_get_info(device_index)
    total_gb = total_b / 2**30
    if limit_gb and limit_gb > 0:
        frac = min(1.0, limit_gb / total_gb)
        torch.cuda.set_per_process_memory_fraction(frac, device_index)
    else:
        frac = 1.0
    return {"cuda": True, "visible_total_gb": round(total_gb, 2), "visible_free_gb": round(free_b / 2**30, 2),
            "cap_gb": limit_gb, "cap_fraction": round(frac, 4)}


def gpu_peak_gb(device_index=0):
    if not torch.cuda.is_available():
        return None
    return round(torch.cuda.max_memory_allocated(device_index) / 2**30, 2)


def encode(tokenizer, text):
    ids = tokenizer(text, add_special_tokens=False)["input_ids"]
    if len(ids) == 0:
        raise ValueError(f"Empty token sequence for {text!r}")
    return ids


def score_answer(model, tokenizer, prompt, answer, device):
    """Score `answer` as a continuation of `prompt`.

    Convention kept from earlier runs: prompt and ' ' + answer are tokenized separately
    and concatenated, so the answer's tokenization is identical across prompts.
    """
    prompt_ids = encode(tokenizer, prompt)
    answer_ids = encode(tokenizer, " " + answer)
    input_ids = torch.tensor([prompt_ids + answer_ids], device=device)
    start = len(prompt_ids)
    n = len(answer_ids)
    with torch.inference_mode():
        logits = model(input_ids).logits[0].float()
    # Logits at position t predict token t+1, so answer token i is predicted at start+i-1.
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
    }


def next_token_top_k(model, tokenizer, prompt, device, k=5):
    ids = torch.tensor([encode(tokenizer, prompt)], device=device)
    with torch.inference_mode():
        logits = model(ids).logits[0, -1].float()
    probs = torch.softmax(logits, dim=-1)
    top = torch.topk(probs, k)
    return [
        {"token": tokenizer.decode([int(i)]), "probability": float(p)}
        for p, i in zip(top.values.tolist(), top.indices.tolist())
    ]


def greedy_continuation(model, tokenizer, prompt, device, max_new_tokens=10):
    ids = torch.tensor([encode(tokenizer, prompt)], device=device)
    with torch.inference_mode():
        out = model.generate(
            ids,
            attention_mask=torch.ones_like(ids),
            max_new_tokens=max_new_tokens,
            do_sample=False,
            num_beams=1,
            pad_token_id=tokenizer.eos_token_id,
        )
    return tokenizer.decode(out[0, ids.shape[1]:])


def probe_prompt(model, tokenizer, prompt, answers, device, gen_tokens=10):
    """Score several candidate answers for one prompt, plus what the model actually says."""
    return {
        "prompt": prompt,
        "greedy_continuation": greedy_continuation(model, tokenizer, prompt, device, gen_tokens),
        "top5_next_tokens": next_token_top_k(model, tokenizer, prompt, device, 5),
        "answers": {label: score_answer(model, tokenizer, prompt, ans, device) for label, ans in answers},
    }


def split_alternatives(cell):
    return [a.strip() for a in (cell or "").split("|") if a.strip()]
