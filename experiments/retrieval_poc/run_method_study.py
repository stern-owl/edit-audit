#!/usr/bin/env python3
"""Paired single-fact edit study for ROME, MEMIT or AlphaEdit, one seed per process.

Same protocol as run_fact_study.py (which stays unchanged for provenance): for each included fact,
score -> rescore (check A) -> edit -> check B -> score -> restore -> rescore (check C).
Every fact is edited from the unedited model.

Differences from run_fact_study.py:
  * --method selects the editor; --hparams must point to that method's yaml.
  * --probes-dir accepts several directories (main set = v1 novels/invention + v2 companies).
  * AlphaEdit keeps a process-wide record of past edit keys (cache_c) and protects them in later
    edits. Because we restore the weights after every fact, that record is cleared before each
    edit so every fact is edited independently (logged as alphaedit_cache_reset=True).
  * Logs md5 of the hparams file, of every covariance-statistics file and of the AlphaEdit
    projection matrix, so a run can be tied to the exact statistics it used.

Outputs in --output-dir/study_<tag>_<method>_seed<N>/: deltas.csv, checks.csv, full.jsonl, manifest.json
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_scoring import SCRIPT_VERSION, cap_gpu_memory, gpu_peak_gb  # noqa: E402
from rome_paired_pilot import set_seed  # noqa: E402
from run_fact_study import fact_rows, load_probe_files, run_one_fact, write_csv  # noqa: E402

STUDY_VERSION = "run_method_study v1.1 (2026-10-28)"
METHODS = ("ROME", "MEMIT", "AlphaEdit")


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_many(dirs):
    facts, seen = [], set()
    for d in dirs:
        for p, m in load_probe_files(d):
            if p["fact_id"] in seen:
                raise ValueError(f"fact {p['fact_id']} appears in more than one --probes-dir")
            seen.add(p["fact_id"])
            facts.append((p, m))
    return sorted(facts, key=lambda x: x[0]["fact_id"])


def stats_files(hparams):
    """Covariance files the method will read (empty for ROME without mom2 adjustment)."""
    if not getattr(hparams, "mom2_adjustment", False):
        return {}
    model_dir = str(hparams.model_name).rstrip("/").rsplit("/")[-1]   # EasyEdit naming
    out = {}
    for layer in hparams.layers:
        name = hparams.rewrite_module_tmp.format(layer)
        f = (Path(hparams.stats_dir) / model_dir / f"{hparams.mom2_dataset}_stats"
             / f"{name}_{hparams.mom2_dtype}_mom2_{hparams.mom2_n_samples}.npz")
        out[str(f)] = md5(f) if f.exists() else "MISSING"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", required=True, choices=METHODS)
    ap.add_argument("--probes-dir", required=True, nargs="+")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--output-dir", default="experiments/retrieval_poc/results")
    ap.add_argument("--tag", default=os.environ.get("SLURM_ARRAY_JOB_ID", os.environ.get("SLURM_JOB_ID", "local")))
    ap.add_argument("--model", default="/localstorage/home/f20220930/EasyEdit/huggingface_cache/gpt2-xl")
    ap.add_argument("--hparams", required=True)
    ap.add_argument("--gpu-mem-gb", type=float, default=float(os.environ.get("GPU_MEM_GB", "24")))
    args = ap.parse_args()

    facts = load_many(args.probes_dir)
    print(STUDY_VERSION, "|", SCRIPT_VERSION, "| method", args.method, "| seed", args.seed, "|", len(facts),
          "included facts:", [p["fact_id"] for p, _ in facts], flush=True)
    print("GPU memory:", cap_gpu_memory(args.gpu_mem_gb), flush=True)

    import easyeditor
    from transformers import GPT2Tokenizer
    hp_cls = {"ROME": easyeditor.ROMEHyperParams, "MEMIT": easyeditor.MEMITHyperParams,
              "AlphaEdit": easyeditor.AlphaEditHyperParams}[args.method]
    hparams = hp_cls.from_hparams(args.hparams)
    if hparams.alg_name != args.method:
        raise ValueError(f"hparams alg_name={hparams.alg_name!r} but --method={args.method!r}")
    if Path(str(hparams.model_name)).expanduser().resolve() != Path(args.model).expanduser().resolve():
        raise ValueError(f"Model mismatch: hparams model_name={hparams.model_name!r}; --model={args.model!r}")
    hp_file = args.hparams if args.hparams.endswith(".yaml") else args.hparams + ".yaml"
    stats = stats_files(hparams)
    print("hparams", hp_file, md5(hp_file), "| layers", hparams.layers, "| mom2_adjustment",
          getattr(hparams, "mom2_adjustment", None), flush=True)
    for f, m in stats.items():
        print("stats", m, f, flush=True)
    if "MISSING" in stats.values():
        raise FileNotFoundError("Covariance statistics missing; run fetch_stats.sh first (refusing to compute them inside a study job).")
    p_md5 = None
    if args.method == "AlphaEdit":
        if not Path(hparams.P_loc).exists():
            raise FileNotFoundError(f"AlphaEdit projection {hparams.P_loc} missing; run compute_alphaedit_P.py first.")
        p_md5 = md5(hparams.P_loc)
        print("AlphaEdit projection", hparams.P_loc, p_md5, flush=True)
        import importlib  # easyeditor.models is shadowed by easyeditor.trainer.models as an attribute
        alpha_main = importlib.import_module("easyeditor.models.alphaedit.AlphaEdit_main")

    tokenizer = GPT2Tokenizer.from_pretrained(args.model)
    editor = easyeditor.BaseEditor.from_hparams(hparams)
    model = editor.model
    model.eval()
    device = next(model.parameters()).device
    if device.type != "cuda":
        raise RuntimeError("Model not on CUDA")
    rewrite_params = [hparams.rewrite_module_tmp.format(layer) + ".weight" for layer in hparams.layers]

    def edit_fn(e):
        set_seed(args.seed)
        if args.method == "AlphaEdit":
            alpha_main.cache_c_new = False      # forget keys of earlier (already restored) edits
        return editor.edit(prompts=[e["prompt"]], ground_truth=[e["target_old"]], target_new=[e["target_new"]],
                           subject=[e["subject"]], sequential_edit=True, verbose=False)

    out = Path(args.output_dir) / f"study_{args.tag}_{args.method}_seed{args.seed}"
    out.mkdir(parents=True, exist_ok=True)
    rows, checks = [], []
    with open(out / "full.jsonl", "w", encoding="utf-8") as full:
        for i, (probes, _) in enumerate(facts, 1):
            pre, post, chk = run_one_fact(model, tokenizer, device, probes, edit_fn, rewrite_params)
            chk["delta_frobenius_norm"] = chk.pop("rome_delta_frobenius_norm")   # summed over all edited layers
            chk["method"] = args.method
            rows.extend(fact_rows(probes, pre, post, args.seed))
            checks.append(chk)
            full.write(json.dumps({"fact_id": probes["fact_id"], "method": args.method, "seed": args.seed,
                                   "pre": pre, "post": post, "checks": chk}, ensure_ascii=False) + "\n")
            full.flush()
            e = post["forward_edit_prompt"]["answers"]["new_object"]
            print(f"[{i}/{len(facts)}] {probes['fact_id']}: checks A/B/C passed | edit-prompt new-answer rank "
                  f"{e['first_token_rank']} P={e['sequence_probability']:.3f} | update norm "
                  f"{chk['delta_frobenius_norm']:.2f}", flush=True)
    for r in rows:
        r["method"] = args.method
    write_csv(out / "deltas.csv", rows)
    write_csv(out / "checks.csv", checks)
    with open(out / "manifest.json", "w") as f:
        json.dump({"study_version": STUDY_VERSION, "scorer": SCRIPT_VERSION, "method": args.method,
                   "seed": args.seed, "probes_dirs": args.probes_dir,
                   "probe_md5": {p["fact_id"]: m for p, m in facts},
                   "hparams_file": hp_file, "hparams_md5": md5(hp_file), "layers": hparams.layers,
                   "mom2_adjustment": getattr(hparams, "mom2_adjustment", None), "stats_md5": stats,
                   "alphaedit_projection_md5": p_md5, "alphaedit_cache_reset": args.method == "AlphaEdit",
                   "gpu_peak_gb": gpu_peak_gb()}, f, indent=1)
    print("Saved under", out, flush=True)
    print(f"Peak GPU memory allocated: {gpu_peak_gb()} GiB (cap {args.gpu_mem_gb} GiB)", flush=True)
    print(f"STUDY COMPLETE: {args.method}, {len(facts)} facts, seed {args.seed}, all checks passed. Descriptive only.",
          flush=True)


if __name__ == "__main__":
    main()
