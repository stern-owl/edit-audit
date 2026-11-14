# Status and how to resume

_Last updated 2026-11-14._

## Jobs (as of 08:15 IST)
| Job | What | State |
|---|---|---|
| 16987/16992 | E0 baseline on A100 | done: reproduces exactly |
| 16994 | E1 equivalence, E2 ROME+stats | done: E1 identical; E2 confirms stale reads 22/24 |
| 16990 / 16991 | E4 screening GPT-2 XL / GPT-J | done: 78 / 128 admitted |
| 16995 | E4 audit GPT-2 XL, 78 facts | done (entry 07) |
| 16996 | E7 sequential GPT-2 XL | done, partly valid (entry 07) |
| 16997 | E5 audit GPT-J: ROME, MEMIT done; AlphaEdit crashed (EasyEdit bug) | done/partial |
| 17010 | E5 GPT-J AlphaEdit with fix | **done** |
| 17014 → 17015 | tests → E7v2 sequential with held-out sentinels and checkpoints | **done** |

All submitted jobs are finished. Results in `RESULTS.md`; raw outputs copied to `C:\Desktop\edit-audit\data\raw_runs\`.

| 18035 / 18036 / 18037 | tests / GPT-J ROME+stats / GPT-2 XL ROME+stats | **done** (entry 08) |

## Disk (2026-11-05)
The shared `yashsinha` quota (1000 GB) was full; ~1 GB was freed by deleting our conda package cache. Check `quota`
before every submission; our project uses ~52 GB.
Later on 2026-11-05 the account was again at 1000 GB (17 MB over the 999 GB soft quota, 6-day grace). With the
user's approval (they run calibread) the calibread Ollama model Qwen2.5-14B-Instruct q3_K_M (7.34 GB; tags
`calibread-qwen25-14b-instruct-q3`, `qwen2.5:14b-instruct-q3_K_M`) was removed from `F20220612_Aadit/ollama_models`;
only blobs not shared with the 72B model were deleted. Usage after: 993 GB. Re-fetch: `ollama pull qwen2.5:14b-instruct-q3_K_M`.

## Phase 6 progress
- Done offline (entry 09): E10 standard metrics vs audit, N3 audit planning, N2 admission control (FD check, predictors).
- Done on GPT-2 XL: N1 commutativity (entry 10; jobs 18039, 18040), N5 compensation and N2 cascade (entry 11; jobs
  18047, 18243; 18046 failed on EasyEdit's batch_size assertion, fixed).
- 2026-11-11: related-work check (`RELATED_WORK_CHECK.md`): N1 still novel as far as found; N5 largely known (Pitfalls
  Round-Edit, Caddeo et al. 2026), reframe as confirmation + extension; E10 is motivation (RippleEdits, MQuAKE).
- Queued 2026-11-11 (entry 12): N1 on GPT-J (18781, 18782), seed 1 of N1 (18783, 18784) and N5/N2 (18785, 18786).
- **All six FAILED (entry 13):** 18781-18784 on a flag-check bug in `run_audit.py` v1.3 (fixed locally in v1.3.1, with a
  test; not yet synced); 18785-18786 because the account quota is full again (1000/1000 G; our project 51 G, unchanged).
  **Blocked on freeing space.** Then: `sync.sh`, `tests.sbatch`, resubmit the six jobs unchanged with `--dependency`.
- 2026-11-14: quota back to 889/999 G (~110 G free; freed by others). Laptop copies verified md5-identical to the cluster
  (1,161 files, see `environment.md`). Resubmission not yet done.
- Open: N1 on GPT-J (~5 GPU-h); N4 atomicity with conflict-aware batching (now possible: key overlap predicts conflicts);
  N6 quantization; D4 modern model. Designs: `NOVELTY_AND_NEW_EXPERIMENTS.md`.

## Open decisions for the user
- **D4 (plan 2.5):** modern model: Llama-3-8B (gated: needs Meta approval on Hugging Face + an HF token on the cluster) or Qwen2.5-7B (open, but covariance statistics must be computed: GPU-hours + ~20 GB Wikipedia).
- ~~Whether to commit~~ **Done 2026-11-14:** branch `phase2` pushed to the (public) fork AaditS04/edit-audit, PR #1
  (https://github.com/AaditS04/edit-audit/pull/1): code, `research-log/` and `data/raw_runs/`. Commits 632ad40, 093e0d3.
- D1 venue: deferred.

## Next work after the results are in
- GPT-J: model-agnostic AlphaEdit projection script (16384² × 6 layers, ~6.4 GB), then pre-registered screening of the 12 facts on GPT-J.
- Plan 2.2: CounterFact-based fact set (relations, reverse templates, cardinality, frozen screening rules).
- Plan 3.1: first sequential-editing run on GPT-2 XL with `run_audit.py --mode sequential`.

## Things learned the hard way (see entry 02)
- Never re-extract files under a running job: `sync.sh` now makes snapshots and flips the `repo` symlink.
- Slurm's soft `ulimit -v` is half of `--mem`; `paths.sh` raises it (hard limit is unlimited).
- The laptop's SSH link to the cluster drops packets; chain jobs with `--dependency` instead of waiting on the laptop.
