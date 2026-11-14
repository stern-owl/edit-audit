# Environment

## Local machine (Windows 11 laptop)
- Folder: `C:\Desktop\edit-audit\` (draft PDF, `next-steps.txt`, `edit-audit/` repo, this log).
- Python 3.11.9; **no** torch/transformers installed (checked 2026-10-31). No local GPU.
- Use: editing code, offline tests (after installing CPU torch + transformers), analysis of CSVs.

## Original runs (colleague, for provenance)
- Cluster with Slurm partition `h100-mig`, one MIG slice `nvidia_h100_nvl_3g.47gb`, `--mem=24G/48G`.
- Home `/localstorage/home/f20220930/` (Yash Aggarwal), conda env `EasyEdit`.
- Python 3.10.21, torch 2.9.1+cu128, transformers 5.5.4, EasyEdit commit `431d9bd73db4608a4781010b687891737604c8e2`
  (from `edit-audit/environment/versions.txt`; full list in `pip-freeze.txt`).
- Peak GPU memory: screening ~6 GiB, ROME editing 9.2 GiB, MEMIT/AlphaEdit 7.6 GiB (GPT-2 XL).

## CSIS cluster (used for all phase 2 work; see decisions D2)
- `ssh bits-cluster` → 172.24.16.132, port 22, user `yashsinha`, key auth (`~/.ssh/id_ed25519`). Login node `csis.mn1`.
- **Hardware:** 5 nodes (`csis.cn1`–`cn4`, `csis.mn1`), each **2× NVIDIA A100 80 GB**, 128 CPUs, ~234 GiB RAM. Slurm GRES name `gpu:a100-80gb`.
- **Partitions:** `debug` 30 min, `cpu-short` 12 h (default), `cpu-long` 1 day, `gpu-short` 8 h, `gpu-long` 12 h,
  `gpu-1day`, `gpu-3day`, `bigmem` 12 h, `test-gpu` 7 days. All partitions span all nodes.
- **Internet:** compute nodes reach huggingface.co, pypi.org, github.com and rome.baulab.info (tested 2026-10-31 with `srun -p debug`).
- **Software:** shared miniconda at `/nfs_home/software/miniconda` (used only to create our own env by prefix; base env not modified); Lmod modules include `cuda/12.8`; no `nvcc` on the login node.
- **Disk:** `/nfs_home` 24 TB (15 TB free). **Quota for account `yashsinha`: 807 GB used of 999 GB soft / 1000 GB hard (2026-10-31)**, shared by all students on this account, so ~190 GB headroom in total. Keep model downloads to what is needed; purge pip/conda caches.
- `F20220612_Aadit/` was already 128 GB before this project (65 GB `hf_cache` with Qwen2.5-1.5B-Instruct and Qwen3.8-27B, 51 GB `ollama_models`, etc.).

### Project layout on the cluster (`EA_ROOT=/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit`)
Defined once in `cluster/csis/paths.sh`, which every job sources.

| Path | Content |
|---|---|
| `repo/` | Snapshot of the local repo pushed by `cluster/csis/sync.sh`; `repo/SYNCED_FROM.txt` records the commit and number of uncommitted files |
| `env/` | Own conda env (Python 3.10, conda-forge only) with the colleague's exact pip versions |
| `EasyEdit/` | EasyEdit at commit `431d9bd73db4608a4781010b687891737604c8e2`; `EasyEdit/experiments` → `repo/experiments` (symlink) |
| `EasyEdit/data/stats/` | Covariance statistics and AlphaEdit projection matrices (EasyEdit reads them from here) |
| `models/<name>/` | Model weights; `SOURCE.txt` records repo id and pinned revision |
| `hparams/` | Hyperparameter files as run (`model_name` pointing into `models/`) |
| `runs/<plan-item>_<desc>_<jobid>/` | All outputs of one job |
| `logs/` | Slurm stdout/stderr, `<job>_<jobid>.out` |
| `cache/` | `HF_HOME`, pip, conda pkgs, matplotlib, nltk, tmp. Never in `$HOME` |

### Workflow
1. Edit code on the laptop (git branch `phase2`).
2. `bash cluster/csis/sync.sh` copies the working tree to `repo/` (nothing on the cluster is deleted).
3. `ssh bits-cluster 'sbatch /nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/repo/cluster/csis/<job>.sbatch'`.
4. Copy small outputs back to the laptop for analysis; log everything in `entries/`.

### Account limits (`sacctmgr show assoc user=yashsinha`, 2026-10-31)
Account `faculty`, user `yashsinha`: **GrpTRES cpu=64, gres/gpu=2, mem=200G; MaxJobs=5** (running at once). These are
shared with every other student using this account (e.g. job `WATCHDOG` is not ours). Jobs beyond the cap wait with
reason `AssocGrpMemLimit`. Request only what is needed: measured MaxRSS was ~2 GB for GPT-2 XL editing and 8.7 GB for
the GPT-J projection job (which had requested 96 GB). Defaults now: baseline/phase-1 32 GB, screening 24 GB (GPT-J 64 GB,
because its 24 GB `.bin` checkpoint is read fully into RAM). Pending jobs can be shrunk with
`scontrol update JobId=<id> MinMemoryNode=<MB>` (MB, not "24G").

### Slurm virtual-memory limit (fixed 2026-10-31)
Jobs get a soft `ulimit -v` of half their `--mem` (hard limit unlimited). That breaks mmap of model weights and CUDA
initialisation. `paths.sh` raises the soft limit to the hard one; RAM is still capped by `--mem`. Any new job script
must source `paths.sh` (they all do).

### Line endings (fixed 2026-10-31)
The laptop's system git config has `core.autocrlf=true`, which had rewritten all 134 tracked files with CRLF
(breaking bash scripts on Linux and every md5 in `CHECKSUMS.md5`). Fix: `git config core.autocrlf false` in this
repo, re-checkout, and a `.gitattributes` with `* -text`. After the fix all files match `CHECKSUMS.md5`, locally
and on the cluster. 34 result CSVs legitimately contain CRLF in the commit (Python's csv writer), so a blanket
CRLF→LF conversion would have been wrong.

### Laptop copies of cluster outputs (verified 2026-10-31 16:01)
- `C:\Desktop\edit-audit\data\cluster_mirror\` = full copy of `EA_ROOT/runs`, `logs`, `hparams`, `pip-freeze_csis.txt`,
  `stats_md5_gpt-j-6B.txt` (job work directories excluded; they only hold symlinks). **1,055 / 1,055 files md5-identical to
  the cluster.** Six symlinks in `runs/0.4_baseline_a100_16987/` (to MEMIT/AlphaEdit folders of run 16978) cannot be
  created on Windows; their targets are in the mirror as real folders.
- `C:\Desktop\edit-audit\data
aw_runs\` = the subset used for `RESULTS.md` (81 files, all identical to the mirror).
- **Re-verified 2026-11-14:** all 1,161 files under `EA_ROOT/runs` (job `work/` dirs excluded) and `EA_ROOT/logs` are
  md5-identical on the laptop, in `cluster_mirror\` or `raw_runs\` (runs after 2026-10-31 that were used for results
  live in `raw_runs\` only). The failed runs 18046, 18781-18785 and 19 later Slurm logs were copied into `cluster_mirror\`
  that day.
- Not mirrored on purpose (large, reproducible from pinned sources): model weights, covariance statistics, AlphaEdit
  projections, the conda env, caches.
- Code: laptop working tree and cluster snapshot `repo_snapshots/20261031-160121` are identical (163 / 163 files by md5).
