#!/usr/bin/env python3
"""Paired ROME study over screened facts, one seed per process.

For each included fact: score (pre) -> rescore (check A) -> edit -> check B -> score (post)
-> restore original weights -> rescore (check C). Every fact is edited from the unedited model.
Any failed check stops the run (results after a failed check would be uninterpretable).

Outputs in --output-dir/study_<tag>/:
  deltas.csv     one row per (fact, route, answer): pre, post, change, ranks, route validity
  checks.csv     one row per fact: checks A/B/C, ROME delta norm
  full.jsonl     all scores (pre and post) per fact
  manifest.json  seed, versions, md5 of every probe file used
"""
import argparse
import csv
import hashlib
import json
import os
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_scoring import SCRIPT_VERSION, cap_gpu_memory, gpu_peak_gb  # noqa: E402
from rome_paired_pilot import max_score_diff, max_weight_diff, restore, score_all, set_seed, snapshot  # noqa: E402

STUDY_VERSION = "run_fact_study v1 (2026-10-24)"
KEYS = ["sum_logprob", "first_token_rank", "sequence_probability"]


def load_probe_files(probes_dir, include_all=False):
    files = sorted(Path(probes_dir).glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No probe files in {probes_dir}")
    out = []
    for f in files:
        b = f.read_bytes()
        p = json.loads(b)
        if include_all or p["screening"]["included"]:
            out.append((p, hashlib.md5(b).hexdigest()))
    return out


def fact_rows(probes, pre, post, seed):
    for r in probes["routes"]:
        a_pre, a_post = pre[r["route"]]["answers"], post[r["route"]]["answers"]
        for label in a_pre:
            yield {"fact_id": probes["fact_id"], "relation": probes["relation"], "seed": seed,
                   "route": r["route"], "kind": r["kind"], "route_valid": r["valid"], "answer_label": label,
                   "answer": a_pre[label]["answer"],
                   "pre_sum_logprob": a_pre[label]["sum_logprob"], "post_sum_logprob": a_post[label]["sum_logprob"],
                   "delta_sum_logprob": a_post[label]["sum_logprob"] - a_pre[label]["sum_logprob"],
                   "pre_first_token_rank": a_pre[label]["first_token_rank"],
                   "post_first_token_rank": a_post[label]["first_token_rank"],
                   "pre_greedy": pre[r["route"]]["greedy_continuation"],
                   "post_greedy": post[r["route"]]["greedy_continuation"]}
        if {"old_object", "new_object"} <= set(a_pre):
            m_pre = a_pre["new_object"]["sum_logprob"] - a_pre["old_object"]["sum_logprob"]
            m_post = a_post["new_object"]["sum_logprob"] - a_post["old_object"]["sum_logprob"]
            yield {"fact_id": probes["fact_id"], "relation": probes["relation"], "seed": seed,
                   "route": r["route"], "kind": r["kind"], "route_valid": r["valid"],
                   "answer_label": "MARGIN new_minus_old", "answer": "",
                   "pre_sum_logprob": m_pre, "post_sum_logprob": m_post, "delta_sum_logprob": m_post - m_pre,
                   "pre_first_token_rank": "", "post_first_token_rank": "", "pre_greedy": "", "post_greedy": ""}


def run_one_fact(model, tokenizer, device, probes, edit_fn, rewrite_params, tol=1e-4):
    pre = score_all(model, tokenizer, probes, device)
    chk = {"fact_id": probes["fact_id"], "check_A_repeat_max_diff": max_score_diff(pre, score_all(model, tokenizer, probes, device))}
    if chk["check_A_repeat_max_diff"] > tol:
        raise RuntimeError(f"{probes['fact_id']}: check A failed {chk}")
    original = snapshot(model, rewrite_params)
    result = edit_fn(probes["edit"])
    edited = result[1] if isinstance(result, (tuple, list)) and len(result) > 1 and isinstance(result[1], torch.nn.Module) else model
    chk["check_B_weight_change_max_abs"] = max_weight_diff(edited, original)
    if chk["check_B_weight_change_max_abs"] == 0.0:
        raise RuntimeError(f"{probes['fact_id']}: check B failed (edit not live)")
    chk["rome_delta_frobenius_norm"] = sum(float((edited.get_parameter(n).detach() - w).norm().item()) for n, w in original.items())
    post = score_all(edited, tokenizer, probes, device)
    restore(edited, original)
    chk["check_C_restore_max_diff"] = max_score_diff(pre, score_all(edited, tokenizer, probes, device))
    if chk["check_C_restore_max_diff"] > tol:
        raise RuntimeError(f"{probes['fact_id']}: check C failed {chk}")
    return pre, post, chk


def write_csv(path, rows):
    rows = list(rows)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probes-dir", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--output-dir", default="experiments/retrieval_poc/results")
    ap.add_argument("--tag", default=os.environ.get("SLURM_ARRAY_JOB_ID", os.environ.get("SLURM_JOB_ID", "local")))
    ap.add_argument("--model", default="/localstorage/home/f20220930/EasyEdit/huggingface_cache/gpt2-xl")
    ap.add_argument("--hparams", default="./hparams/ROME/gpt2-xl")
    ap.add_argument("--gpu-mem-gb", type=float, default=float(os.environ.get("GPU_MEM_GB", "20")))
    args = ap.parse_args()

    facts = load_probe_files(args.probes_dir)
    print(STUDY_VERSION, "|", SCRIPT_VERSION, "| seed", args.seed, "|", len(facts), "included facts:",
          [p["fact_id"] for p, _ in facts], flush=True)
    print("GPU memory:", cap_gpu_memory(args.gpu_mem_gb), flush=True)

    from easyeditor import BaseEditor, ROMEHyperParams
    from transformers import GPT2Tokenizer
    hparams = ROMEHyperParams.from_hparams(args.hparams)
    tokenizer = GPT2Tokenizer.from_pretrained(args.model)
    editor = BaseEditor.from_hparams(hparams)
    model = editor.model
    model.eval()
    device = next(model.parameters()).device
    if device.type != "cuda":
        raise RuntimeError("Model not on CUDA")
    rewrite_params = [hparams.rewrite_module_tmp.format(layer) + ".weight" for layer in hparams.layers]

    def edit_fn(e):
        set_seed(args.seed)
        return editor.edit(prompts=[e["prompt"]], ground_truth=[e["target_old"]], target_new=[e["target_new"]],
                           subject=[e["subject"]], sequential_edit=True, verbose=False)

    out = Path(args.output_dir) / f"study_{args.tag}_seed{args.seed}"
    out.mkdir(parents=True, exist_ok=True)
    rows, checks = [], []
    with open(out / "full.jsonl", "w", encoding="utf-8") as full:
        for i, (probes, _) in enumerate(facts, 1):
            pre, post, chk = run_one_fact(model, tokenizer, device, probes, edit_fn, rewrite_params)
            rows.extend(fact_rows(probes, pre, post, args.seed))
            checks.append(chk)
            full.write(json.dumps({"fact_id": probes["fact_id"], "seed": args.seed, "pre": pre, "post": post,
                                   "checks": chk}, ensure_ascii=False) + "\n")
            full.flush()
            e = post["forward_edit_prompt"]["answers"]["new_object"]
            print(f"[{i}/{len(facts)}] {probes['fact_id']}: checks A/B/C passed | edit-prompt new-answer rank "
                  f"{e['first_token_rank']} P={e['sequence_probability']:.3f}", flush=True)
    write_csv(out / "deltas.csv", rows)
    write_csv(out / "checks.csv", checks)
    with open(out / "manifest.json", "w") as f:
        json.dump({"study_version": STUDY_VERSION, "scorer": SCRIPT_VERSION, "seed": args.seed,
                   "probes_dir": args.probes_dir, "probe_md5": {p["fact_id"]: m for p, m in facts},
                   "mom2_adjustment": hparams.mom2_adjustment, "layers": hparams.layers,
                   "gpu_peak_gb": gpu_peak_gb()}, f, indent=1)
    print("Saved under", out, flush=True)
    print(f"Peak GPU memory allocated: {gpu_peak_gb()} GiB (cap {args.gpu_mem_gb} GiB)", flush=True)
    print(f"STUDY COMPLETE: {len(facts)} facts, seed {args.seed}, all checks passed. Descriptive only.", flush=True)


if __name__ == "__main__":
    main()
