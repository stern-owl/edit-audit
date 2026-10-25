#!/usr/bin/env python3
"""One-fact paired ROME pilot: score -> rescore (no-edit control) -> edit -> score -> restore -> score.

All four scoring passes use the same frozen probes and the same scoring code (probe_scoring.py),
in one process, so the in-memory edit never has to persist across jobs.

Built-in checks (the job stops with an error if one fails):
  A. Repeat check:  scoring the unedited model twice gives identical numbers.
  B. Live-edit check: the ROME rewrite weights actually differ after editor.edit() returns.
     (Some EasyEdit versions restore weights inside edit() when sequential_edit=False.)
  C. Restore check: putting the saved original weights back reproduces the pre-edit scores.

Outputs in --output-dir, tagged with the Slurm job id:
  pilot_<tag>.json          everything: metadata, all four passes, EasyEdit's own metrics
  pilot_<tag>_long.csv      one row per (phase, route, answer)
  pilot_<tag>_deltas.csv    one row per (route, answer): pre, post, change; plus new-minus-old margins
Scores are descriptive behavioural measurements; they do not show where knowledge is stored.
"""
import argparse
import csv
import hashlib
import json
import os
import random
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_scoring import SCRIPT_VERSION, cap_gpu_memory, gpu_peak_gb, probe_prompt  # noqa: E402

PILOT_VERSION = "rome_paired_pilot v1 (2026-10-23)"
SCORE_KEYS = ["sum_logprob", "sequence_probability", "first_token_probability", "first_token_rank", "num_tokens"]


def set_seed(seed):
    # ROME samples random context prefixes while computing the edit, so the edit itself depends on the seed.
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def score_all(model, tokenizer, probes, device):
    return {r["route"]: probe_prompt(model, tokenizer, r["prompt"], list(r["answers"].items()), device)
            for r in probes["routes"]}


def max_score_diff(a, b):
    worst = 0.0
    for route in a:
        for label in a[route]["answers"]:
            worst = max(worst, abs(a[route]["answers"][label]["sum_logprob"] - b[route]["answers"][label]["sum_logprob"]))
    return worst


def snapshot(model, names):
    return {n: model.get_parameter(n).detach().clone() for n in names}


def max_weight_diff(model, snap):
    return max(float((model.get_parameter(n).detach() - w).abs().max().item()) for n, w in snap.items())


def restore(model, snap):
    with torch.no_grad():
        for n, w in snap.items():
            model.get_parameter(n).copy_(w)


def long_rows(phases):
    for phase, scores in phases.items():
        for route, r in scores.items():
            for label, s in r["answers"].items():
                yield {"phase": phase, "route": route, "prompt": r["prompt"], "answer_label": label,
                       "answer": s["answer"], **{k: s[k] for k in SCORE_KEYS},
                       "greedy_continuation": r["greedy_continuation"]}


def delta_rows(pre, post, probes):
    roles = {r["route"]: r["role"] for r in probes["routes"]}
    for route in pre:
        a_pre, a_post = pre[route]["answers"], post[route]["answers"]
        for label in a_pre:
            yield {"route": route, "role": roles[route], "answer_label": label, "answer": a_pre[label]["answer"],
                   "pre_sum_logprob": a_pre[label]["sum_logprob"], "post_sum_logprob": a_post[label]["sum_logprob"],
                   "delta_sum_logprob": a_post[label]["sum_logprob"] - a_pre[label]["sum_logprob"],
                   "pre_first_token_rank": a_pre[label]["first_token_rank"],
                   "post_first_token_rank": a_post[label]["first_token_rank"],
                   "pre_greedy": pre[route]["greedy_continuation"], "post_greedy": post[route]["greedy_continuation"]}
        if {"old_object", "new_object"} <= set(a_pre):
            m_pre = a_pre["new_object"]["sum_logprob"] - a_pre["old_object"]["sum_logprob"]
            m_post = a_post["new_object"]["sum_logprob"] - a_post["old_object"]["sum_logprob"]
            yield {"route": route, "role": roles[route], "answer_label": "MARGIN new_minus_old",
                   "answer": "", "pre_sum_logprob": m_pre, "post_sum_logprob": m_post,
                   "delta_sum_logprob": m_post - m_pre, "pre_first_token_rank": "", "post_first_token_rank": "",
                   "pre_greedy": "", "post_greedy": ""}


def write_csv(path, rows):
    rows = list(rows)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def run_pilot(model, tokenizer, device, probes, edit_fn, rewrite_params, tol=1e-4):
    """Core sequence, separated from EasyEdit loading so it can be tested offline."""
    log = {}
    pre = score_all(model, tokenizer, probes, device)
    pre_repeat = score_all(model, tokenizer, probes, device)
    log["check_A_repeat_max_diff"] = max_score_diff(pre, pre_repeat)
    if log["check_A_repeat_max_diff"] > tol:
        raise RuntimeError(f"Check A failed: repeat scoring differs by {log['check_A_repeat_max_diff']}")
    print("Check A passed (repeat scoring identical):", log["check_A_repeat_max_diff"], flush=True)

    original = snapshot(model, rewrite_params)
    result = edit_fn()
    metrics = result[0] if isinstance(result, (tuple, list)) else None
    edited = result[1] if isinstance(result, (tuple, list)) and len(result) > 1 and isinstance(result[1], torch.nn.Module) else model
    log["check_B_weight_change_max_abs"] = max_weight_diff(edited, original)
    if log["check_B_weight_change_max_abs"] == 0.0:
        raise RuntimeError("Check B failed: rewrite weights unchanged after edit(); the edit is not live. "
                           "Do not interpret any post-edit scores from this run.")
    log["rome_delta_frobenius_norm"] = {n: float((edited.get_parameter(n).detach() - w).norm().item())
                                        for n, w in original.items()}
    print("Check B passed (edit is live):", log["check_B_weight_change_max_abs"], flush=True)

    post = score_all(edited, tokenizer, probes, device)

    restore(edited, original)
    restored = score_all(edited, tokenizer, probes, device)
    log["check_C_restore_max_diff"] = max_score_diff(pre, restored)
    if log["check_C_restore_max_diff"] > tol:
        raise RuntimeError(f"Check C failed: restored model differs from pre-edit by {log['check_C_restore_max_diff']}")
    print("Check C passed (restore reproduces pre-edit):", log["check_C_restore_max_diff"], flush=True)
    return {"pre": pre, "pre_repeat": pre_repeat, "post": post, "restored": restored}, log, metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probes", default="experiments/retrieval_poc/frankenstein_frozen_probes.json")
    ap.add_argument("--output-dir", default="experiments/retrieval_poc/results")
    ap.add_argument("--tag", default=os.environ.get("SLURM_JOB_ID", "local"))
    ap.add_argument("--model", default="/localstorage/home/f20220930/EasyEdit/huggingface_cache/gpt2-xl")
    ap.add_argument("--hparams", default="./hparams/ROME/gpt2-xl")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--gpu-mem-gb", type=float, default=float(os.environ.get("GPU_MEM_GB", "20")))
    args = ap.parse_args()

    probes_bytes = Path(args.probes).read_bytes()
    probes = json.loads(probes_bytes)
    print(PILOT_VERSION, "|", SCRIPT_VERSION, "| probes md5", hashlib.md5(probes_bytes).hexdigest(), flush=True)
    print("GPU memory:", cap_gpu_memory(args.gpu_mem_gb), flush=True)
    set_seed(args.seed)

    from easyeditor import BaseEditor, ROMEHyperParams
    from transformers import GPT2Tokenizer

    hparams = ROMEHyperParams.from_hparams(args.hparams)
    if Path(str(hparams.model_name)).expanduser().resolve() != Path(args.model).expanduser().resolve():
        raise ValueError(f"Model mismatch: hparams={hparams.model_name!r}; --model={args.model!r}")
    tokenizer = GPT2Tokenizer.from_pretrained(args.model)
    editor = BaseEditor.from_hparams(hparams)
    model = editor.model
    model.eval()
    device = next(model.parameters()).device
    if device.type != "cuda":
        raise RuntimeError("Model not on CUDA")
    rewrite_params = [hparams.rewrite_module_tmp.format(layer) + ".weight" for layer in hparams.layers]
    print("Device", device, "| rewrite params", rewrite_params, "| mom2_adjustment", hparams.mom2_adjustment, flush=True)

    e = probes["edit"]

    def edit_fn():
        set_seed(args.seed)
        return editor.edit(prompts=[e["prompt"]], ground_truth=[e["target_old"]], target_new=[e["target_new"]],
                           subject=[e["subject"]], sequential_edit=True, verbose=False)

    phases, checks, easyedit_metrics = run_pilot(model, tokenizer, device, probes, edit_fn, rewrite_params)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = out_dir / f"pilot_{args.tag}"
    meta = {"pilot_version": PILOT_VERSION, "scorer": SCRIPT_VERSION, "seed": args.seed,
            "probes_file": args.probes, "probes_md5": hashlib.md5(probes_bytes).hexdigest(),
            "hparams": {k: (v if isinstance(v, (int, float, str, bool, list, type(None))) else str(v))
                        for k, v in vars(hparams).items()},
            "edit": e, "checks": checks, "gpu_peak_gb": gpu_peak_gb()}
    with open(f"{stem}.json", "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "phases": phases, "easyedit_metrics": easyedit_metrics}, f, ensure_ascii=False,
                  indent=1, default=str)
    write_csv(f"{stem}_long.csv", long_rows(phases))
    write_csv(f"{stem}_deltas.csv", delta_rows(phases["pre"], phases["post"], probes))
    print("Saved:", f"{stem}.json", f"{stem}_long.csv", f"{stem}_deltas.csv", flush=True)
    print(f"Peak GPU memory allocated: {gpu_peak_gb()} GiB (cap {args.gpu_mem_gb} GiB)", flush=True)
    print("PILOT COMPLETE: checks A, B, C passed. Results are one fact, one seed: descriptive only.", flush=True)


if __name__ == "__main__":
    main()
