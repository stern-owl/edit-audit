# 2026-10-31 · 02 · CSIS cluster setup and baseline re-run preparation

**Plan items:** 0.2 (done), 0.3 (in progress), 0.4 (prepared)

## Goal
Get a working, isolated EasyEdit environment on the CSIS A100 cluster that reproduces the colleague's software
stack exactly, and prepare the job that checks the shipped GPT-2 XL results replicate on the new hardware.

## Account and rules
User confirmed account `yashsinha` and working path `/nfs_home/users/yashsinha/F20220612_Aadit` (decisions D2).
Project root: `EA_ROOT=/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit`. Layout and rules: `environment.md`.

## Cluster inspection (login node, read-only)
- 5 nodes × 2 A100 80 GB, 128 CPUs, ~234 GiB RAM; partitions and limits in `environment.md`.
- Account quota 807/999 GB used, shared across students: ~190 GB headroom.
- Existing `F20220612_Aadit/` content (128 GB) is other work; nothing reusable (the `venv/` is Python 3.13 without torch;
  `hf_cache/` has only Qwen models).
- Compute-node internet: `srun -p debug` on `csis.cn1` got HTTP 200 from huggingface.co, rome.baulab.info, pypi.org, github.com.

## Problem found and fixed: line endings
- Symptom: after the first sync, bash and Python scripts in `repo/` on the cluster contained `\r`.
- Cause: system git config on the laptop has `core.autocrlf=true`; all 134 tracked files were checked out with CRLF.
  The commits themselves are LF, except 34 result CSVs whose CRLF is genuine (Python `csv` default line terminator).
- Fix: `git config core.autocrlf false` (repo-local), delete and re-checkout all tracked files (no tracked file had
  local changes), add `.gitattributes` with `* -text`, re-sync.
- Verification: all entries of `CHECKSUMS.md5` match, both on the laptop (Python md5 check) and on the cluster
  (`md5sum -c --quiet CHECKSUMS.md5`). The shipped artefact is byte-identical to the colleague's commit `d774397`.
- The first setup job (16972) was submitted before the fix but was still installing pip packages when the
  corrected files were synced, before it reached any repo script.

## New files (git branch `csis-phase2`, uncommitted)
| File | Purpose |
|---|---|
| `.gitattributes` | `* -text`: no line-ending conversion on any OS |
| `cluster/csis/paths.sh` | Single definition of all paths and caches under `EA_ROOT`; activates the env |
| `cluster/csis/sync.sh` | Laptop → cluster copy of the working tree via `tar | ssh`; writes `repo/SYNCED_FROM.txt` |
| `cluster/csis/setup_env.sbatch` | One-time, idempotent setup on `cpu-short` (8 CPUs, 48 GB, 3 h) |
| `cluster/csis/baseline_rerun.sbatch` | Plan 0.4: full GPT-2 XL re-run on one A100 + row-by-row comparison |
| `cluster/csis/compare_to_shipped.py` | Row-matched comparison of any two result CSVs (stdlib only) |

### `setup_env.sbatch` steps
1. Conda env by prefix `EA_ROOT/env`, `python=3.10` from conda-forge only (`--override-channels`; avoids the
   defaults-channel ToS prompt and does not touch the shared base env). Then `pip install -r` the colleague's
   `environment/pip-freeze.txt` minus the `packaging @ file://` line (a conda build path), plus `packaging`.
   Writes `EA_ROOT/pip-freeze_csis.txt` and diffs it against the original.
2. EasyEdit cloned and checked out at `431d9bd73db4608a4781010b687891737604c8e2` (asserted);
   `EasyEdit/experiments` symlinked to `repo/experiments`, as the README's "copy experiments/ into EasyEdit" step.
3. GPT-2 XL from `openai-community/gpt2-xl` at the revision current at download time, pinned and written to
   `models/gpt2-xl/SOURCE.txt`; only safetensors + tokenizer/config files. Note: the original run did not record its
   revision (`gpt2-xl_source.txt` is listed as "to add" in `environment/README.md` but missing).
4. `fetch_stats.sh` (layers 13–17 Wikipedia stats), md5s diffed against `environment/stats_md5.txt`;
   hparams written to `EA_ROOT/hparams/` from `environment/*_gpt2-xl.yaml` with only `model_name` changed (diff printed).
5. AlphaEdit projection matrix via `compute_alphaedit_P.py` on CPU; md5 printed next to the original from `logs/alphaedit_P_3576.out`.
6. Offline tests (`tests/run_tests.sh`).

### `baseline_rerun.sbatch` design (plan 0.4)
- One A100 on `gpu-short`, 64 GB RAM, 8 h limit, `GPU_MEM_GB=40` (the cap does not affect numerics).
- ROME: `reproduce.sh` unchanged (screen v1 → edit 3 seeds → screen v2 → edit companies 3 seeds → `check_paper_numbers.py`).
  Its fixed output dir `results_rerun` is symlinked to `runs/0.4_baseline_a100_<jobid>/rome`.
- MEMIT and AlphaEdit: `run_method_study.py` on the **shipped** 12-fact probe set built by `make_main_probes.sh` from
  `results/screen_3461` and `results/screen_3466` (same probe files as jobs 3574/3583), seeds 0–2.
- `compare_methods.py` on the re-run, then `compare_to_shipped.py` for: both screening reports, Table 2
  (`aggregate.csv`), Table 3 (`per_fact.csv`), and every `deltas.csv` (ROME v1, ROME v2, MEMIT, AlphaEdit × 3 seeds).
- **Prediction (written before the run):** ranks, validity flags and Table 2/3 entries identical to the shipped files;
  log-probabilities may differ in the last digits (A100 vs H100 kernels). Any rank or validity change is a finding
  and goes into the paper's reproducibility notes.

### `compare_to_shipped.py` self-tests (laptop, shipped files)
- Each of `aggregate.csv`, `per_fact.csv`, `screen_3461/screen_report.csv`, `study_3462_seed0/deltas.csv` against itself → IDENTICAL.
- MEMIT seed 0 vs seed 1 → DIFFERS (rows keyed by seed do not match), as intended.
- First version keyed only on `fact_id/seed/route/answer_label`, which collapses `aggregate.csv` (keys `scope, method`)
  to one row; fixed by adding `scope, fact, method` to the key candidates and asserting key uniqueness.

## Runs
| Job | What | Partition / node | Elapsed | Status |
|---|---|---|---|---|
| 16972 | `setup_env.sbatch` | cpu-short / csis.cn1 | 24:56 | FAILED at step 5 (virtual-memory limit, below) |
| 16975 | `setup_env.sbatch` (resubmitted after fix; steps 1–4 skipped where done) | cpu-short / csis.cn1 | 3:52 | **COMPLETED** |
| 16977 | `tests.sbatch` (shipped suite + phase-2 tests) | cpu-short | | submitted |
| 16978 | `baseline_rerun.sbatch` (plan 0.4) | gpu-short, 1× A100 80 GB | | submitted |

## Results of job 16975 (setup complete)
- **Python** 3.10.22 (original 3.10.21; conda-forge's current 3.10 patch). **torch** 2.9.1+cu128, CUDA 12.8, **transformers** 5.5.4.
- **pip freeze vs original:** no differences (the diff printed no lines; `packaging` excluded from the comparison). Full list in `EA_ROOT/pip-freeze_csis.txt`.
- **AlphaEdit projection** `EasyEdit/data/stats/gpt2-xl/alphaedit_null_space_project.pt`:
  - per-layer projection ranks **identical** to the original job 3576: layer 13 → 5081, 14 → 4921, 15 → 4776, 16 → 4659, 17 → 4476 (of 6400);
  - file md5 **differs**: `de475f2bb445d51290412d3cbd70b787` (csis) vs `9331c2d4c5833b0098efdd69ef4b60ce` (original).
  - Likely cause: floating-point differences in the eigendecomposition on a different CPU (csis: AMD EPYC 7502; original node CPU unknown). The kept null space has the same dimension; whether the last-digit differences propagate to any reported number is tested by the AlphaEdit part of job 16978.
- **Offline tests (shipped suite):** all four passed: `SCORING TESTS PASSED | brute -69.091`, `PILOT TESTS PASSED`, `SCREEN TESTS PASSED`, `STUDY TESTS PASSED`.
- **Disk after setup:** env 7.9 GB, EasyEdit (incl. stats + P) 1.8 GB, models 6.0 GB, cache 5.1 GB before `pip cache purge` (removed 4.4 GB). Total ≈ 16 GB of the account's ~190 GB headroom.
- **Shared account note:** `squeue -u yashsinha` also shows job 16875 `WATCHDOG` (cpu-long), which belongs to another user of the account; not touched.

## Results of job 16972 (steps 1–4 succeeded)
- **Timing:** pip install ~20 min (≈4.5 GB of wheels, mostly torch 900 MB and the NVIDIA CUDA libraries, at only ~3 MB/s from PyPI); GPT-2 XL 6.4 GB from Hugging Face ~1 min; stats 5 × 160 MB at ~120 MB/s.
- **GPT-2 XL:** `openai-community/gpt2-xl` revision `15ea56dee5df4983c59b2538573817e1667135e2`; `model.safetensors` md5 `3507eb1b373d0620a44ab09cb0df857b` (6,431,829,964 bytes). The original run's revision was never recorded, so 0.4 also tests whether this matters.
- **EasyEdit:** HEAD asserted equal to `431d9bd73db4608a4781010b687891737604c8e2`; `import easyeditor` OK.
- **Covariance statistics:** md5 of all five files **identical** to `environment/stats_md5.txt`.
- **hparams** (`EA_ROOT/hparams/`): the only diff from `environment/*_gpt2-xl.yaml` is the `model_name` line.
  md5: ROME `0f28c8c9985ed8597f2d46a2bfed5f89`, MEMIT `ddcb470af6e01eefdc9711248fd74c06`, AlphaEdit `d7ec585ca02d807f8fe27766bfacaa8c`.
- pip freeze diff vs original: in `logs/setup_env_16972.out` (to be summarised from job 16975's output).

## Problem 2: Slurm virtual-memory limit (fixed)
- **Symptom:** step 5 (`compute_alphaedit_P.py`) died in `safe_open(model.safetensors)` with `MemoryError: Cannot allocate memory (os error 12)`; sacct MaxRSS only 1.4 GB of 48 GB.
- **Diagnosis:** `srun -p debug --mem=16G`: `ulimit -v` = 8,388,608 kB (soft), i.e. half of `--mem`; hard limit unlimited; `ulimit -m` = 16 GB.
  mmap of the 6.4 GB weights plus torch's CUDA libraries exceeds the soft address-space limit
  (`libcusparseLt.so.0: failed to map segment`). CUDA jobs reserve even more address space, so every GPU job would have failed too.
- **Fix:** `cluster/csis/paths.sh` raises the soft limit to the hard one: `ulimit -S -v "$(ulimit -H -v)"`. This is a per-process user setting within the limit the admins allow; actual RAM stays capped by `--mem`.
- **Verification:** same `srun` test with the fix: `ulimit -v` = unlimited, `safe_open OK 628 tensors`.

## Problem 3: job 16978's ROME part cut short by a code sync (my error; fixed)
- **Symptom:** in `logs/baseline_rerun_16978.out`, `reproduce.sh` printed `== 1/4` and `== 2/4`, finished v1 seed 2
  (`STUDY COMPLETE ... seed 2`, outputs written 01:08:43), and then the outer job went straight to
  `== MEMIT and AlphaEdit`. No `== 3/4` (v2 screening), `== 4/4` (v2 company edits), no analysis, no error, exit 0.
- **Cause:** `sync.sh` re-extracted the repo over `repo/` at 01:04:35, 01:08:02 and 01:19:28 while the job ran. Bash
  reads a running script from its file in chunks; seed 2 was running during the 01:08:02 sync, and when it returned
  bash read the next chunk of a file that had been rewritten in place, saw end-of-file and exited 0. The outer
  sbatch script is safe (Slurm spools a private copy), and Python reads whole files at start, so the MEMIT/AlphaEdit
  runs were not affected.
- **What survives:** ROME screening v1 and v1 edits seeds 0–2 (complete, all checks passed); MEMIT and AlphaEdit
  seeds 0–2. **Missing:** ROME screening v2, v2 company edits, `check_paper_numbers.py`, and the comparison
  (it will fail on the missing ROME v2 files).
- **Fix:** `sync.sh` now writes each sync to a new `EA_ROOT/repo_snapshots/<timestamp>/` and atomically repoints the
  symlink `EA_ROOT/repo` (`ln -sfn` + `mv -T`). Running jobs keep the files they opened; only later jobs see new code.
  One-time migration of the plain `repo/` directory into a snapshot is done after job 16978 ends.
- **Recovery:** `baseline_rerun.sbatch` gained `REUSE_METHODS_FROM=<dir>`: re-run ROME (`reproduce.sh`) in a new run
  directory, link the finished MEMIT/AlphaEdit outputs of 16978 (probe md5s checked equal), then run the full comparison.

### Recovery carried out (01:27)
- Job 16978 ended FAILED after 27:29 as expected: MEMIT and AlphaEdit seeds 0–2 all `STUDY COMPLETE ... all checks passed`,
  then `FileNotFoundError: .../rome/study_v2_seed0/deltas.csv` in the comparison step.
- Migration: `repo/` moved to `repo_snapshots/20261031-initial/`, `repo` is now a symlink; first new-style sync created
  `repo_snapshots/20261031-012724/`. `md5sum -c CHECKSUMS.md5` inside it: all shipped files OK.
- Submitted **16983** = `baseline_rerun.sbatch` with `REUSE_METHODS_FROM=runs/0.4_baseline_a100_16978` (ROME re-run + full comparison),
  and **16984** = `phase1_gpt2xl.sbatch` with `--dependency=afterok:16983` and `BASELINE_RUN=runs/0.4_baseline_a100_16983`.
  The chain now runs on the cluster and no longer depends on the laptop's connection.

### Problem 3b: the snapshot design was incomplete (my error; fixed)
- **Symptom:** recovery job 16983 FAILED after 12:01. ROME v1 (3 seeds), screening v2 and all five v2 company edits of
  seed 0 passed checks A/B/C, then `run_fact_study.py` could not write
  `experiments/retrieval_poc/results_rerun/study_v2_seed0/deltas.csv` (FileNotFoundError).
- **Cause:** the job ran from `EasyEdit/`, whose `experiments` link went through the `repo` symlink. My 01:37:49 sync
  (to submit the GPT-J projection job) repointed `repo` to a new snapshot, which does not contain the job's
  `results_rerun` link, so the job's next relative path resolved into the wrong snapshot.
- **Fix:** `paths.sh` resolves `EA_REPO=$(readlink -f $EA_ROOT/repo)` once at job start (pinned), and every job now runs in
  a private working directory `ea_workdir $RUN/work` with links `data → EasyEdit/data`, `hparams → EasyEdit/hparams`,
  `experiments → <pinned snapshot>/experiments` (EasyEdit's only relative paths are `./data/stats` and `logs/run.log`).
  `EasyEdit/experiments` stays a live link for interactive use only.
- **Test:** login-node check: workdir built from snapshot `20261031-014159`; after a further sync `repo` pointed to
  `20261031-014213` while the workdir still pointed to `014159`.
- **Resubmitted:** 16987 (recovery, `REUSE_METHODS_FROM=runs/0.4_baseline_a100_16978`) → 16988 Phase 1 (`afterok:16987`).
  16984 (the Phase 1 job chained to 16983) was cancelled, since its dependency could never be met.
- Job 16986 (GPT-J projection, started 01:37) is unaffected: Python had loaded its script, and it reads EasyEdit's real `data/`.

### Problem 3c: the shipped `check_paper_numbers.py` does not run on the documented Python (found; worked around)
- Job 16987: `reproduce.sh` ran all ROME steps (screen v1, 3 seeds, screen v2, 3 seeds of v2 companies, both analyses) and
  then stopped at its final call: `check_paper_numbers.py` line 69 → `SyntaxError: f-string: unmatched '['`.
- Cause: line 69 nests f-strings with the same quote character (`f'{r[chr(100)+'elta_mean']:+.2f}'` inside an f-string),
  valid only from Python 3.12 (PEP 701). The artefact's environment is Python 3.10, and the README's L0 says "Python 3".
  The colleague must have run L0 with a newer Python. **This is a bug in the shipped artefact**; to be fixed when the
  artefact is next published (the fix changes `CHECKSUMS.md5`, so not done now).
- Workaround: `cluster/csis/baseline_finish.sbatch` runs the unchanged script with the cluster's shared Python 3.13
  (standard library only, used read-only), then the parts of the baseline job that had not run.
- Job 16992 then ended with exit 120 from a `BrokenPipeError`: my `compare_to_shipped.py ... | head -30` under
  `pipefail`. The report had already been written. Fixed in all scripts (write to file, then `head` the file).
  Because 16992 "failed", its dependent Phase 1 job 16993 was cancelled and resubmitted without dependency as **16994**.

## Results of plan 0.4 (E0): the draft reproduces exactly on A100
Run directory `runs/0.4_baseline_a100_16987/` (ROME from 16987, MEMIT/AlphaEdit linked from 16978, same probe md5s).
Copies in `research-log/results/E0_baseline_a100_16987/`.
- **`check_paper_numbers.py`, shipped vs re-run: IDENTICAL PRINTOUTS** (Table 2 per fact; F1 new answer rank 1 in 36/36 runs,
  P 0.956–0.998; F1 paraphrase/context 19/19 novels+invention, 8/13 companies; F2 reverse-from-old still rank 1 in every
  seed 20/24; F3 reverse-from-new decreases 23/24; F4 neighbour correct 22/22, company new-value worst rank 6;
  F5 subject-first company edits new-answer rank 510–7387, Microsoft/Bill Gates after Apple edit rank 996–6398).
- **Row-by-row (`comparison.md`):** Table 2 `aggregate.csv` IDENTICAL; Table 3 `per_fact.csv` IDENTICAL (also verified
  byte-for-byte locally); screening v1 (180 rows) and v2, all 18 `deltas.csv` (2,646 rows: ROME v1 228×3, ROME v2 110×3,
  MEMIT 272×3, AlphaEdit 272×3): **0 rank differences, 0 text differences (incl. every greedy continuation), 0 missing rows**.
- **Numeric drift:** max |Δ| pre-edit log-prob 2×10⁻⁵; post-edit 2.6×10⁻⁴ (MEMIT seed 2); screening sequence probability 2.4×10⁻⁶.
- The bit-different AlphaEdit projection matrix (identical ranks) has no visible effect.
- **Prediction (identical ranks/validity, last-digit log-prob drift): confirmed.**

## Problem 4: flaky SSH from the laptop to the cluster (mitigated)
- Around 01:20 several `ssh bits-cluster` calls timed out (ping: 50% packet loss). My job-wait helper treated a failed
  `squeue` call as "job left the queue", so three waits reported "finished" early (16978, 16982) and the automatic
  Phase 1 submission correctly refused (no completion marker in the log). Nothing wrong was submitted.
- **Fix:** the helper (outside the repo, laptop-only) only stops when the cluster positively answers that the job is
  gone; ssh failures are retried. Same for a retrying wrapper used for remote commands.

## Next
- When setup passes: submit `baseline_rerun.sbatch` (plan 0.4).
- In parallel, start plan 2.1 (model-agnostic harness) and 1.2 (distributional metrics) as code + offline tests.
