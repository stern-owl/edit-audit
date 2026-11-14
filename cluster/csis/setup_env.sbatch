#!/bin/bash
#SBATCH --job-name=ea_setup
#SBATCH --partition=cpu-short
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=03:00:00
#SBATCH --output=/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/logs/setup_env_%j.out
# One-time environment setup on a CPU node (compute nodes have internet). Idempotent: finished steps are skipped.
#   1. conda env (python 3.10, conda-forge only) with the colleague's exact pip versions
#   2. EasyEdit at commit 431d9bd, with experiments/ linked to this repo
#   3. GPT-2 XL weights at a pinned Hugging Face revision
#   4. GPT-2 XL covariance statistics (fetch_stats.sh) and hparams with our model path
#   5. AlphaEdit projection matrix (CPU, ~5 SVDs of 6400x6400)
#   6. offline tests
# Submit from the login node:  sbatch $EA_REPO/cluster/csis/setup_env.sbatch
set -eo pipefail   # no -u: conda activate scripts reference unset variables
source /nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/repo/cluster/csis/paths.sh
echo "Job ${SLURM_JOB_ID:-local} on $(hostname) at $(date)"
SP=$EA_REPO/experiments/retrieval_poc
EASYEDIT_COMMIT=431d9bd73db4608a4781010b687891737604c8e2
GPT2_REPO=openai-community/gpt2-xl

echo "== 1/6 conda env"
if [ ! -d "$EA_ENV/conda-meta" ]; then
  conda create -y -p "$EA_ENV" --override-channels -c conda-forge python=3.10 pip
fi
conda activate "$EA_ENV"
export PYTHONPATH="$EA_EASYEDIT:${PYTHONPATH:-}"
python -V
if ! python -c "import torch, transformers" 2>/dev/null; then
  # The 'packaging @ file://' line is a conda build artefact; install packaging from PyPI instead.
  grep -v '^packaging @' "$EA_REPO/environment/pip-freeze.txt" > "$TMPDIR/reqs.txt"
  pip install --no-input -r "$TMPDIR/reqs.txt" packaging
fi
pip freeze > "$EA_ROOT/pip-freeze_csis.txt"
echo "pip freeze differences vs the original run (< original, > csis):"
diff <(grep -v '^packaging' "$EA_REPO/environment/pip-freeze.txt" | sort) \
     <(grep -v '^packaging' "$EA_ROOT/pip-freeze_csis.txt" | sort) || true
python -c "import torch, transformers; print('torch', torch.__version__, 'cuda', torch.version.cuda, '| transformers', transformers.__version__)"

echo "== 2/6 EasyEdit"
if [ ! -d "$EA_EASYEDIT/.git" ]; then
  git clone https://github.com/zjunlp/EasyEdit "$EA_EASYEDIT"
fi
git -C "$EA_EASYEDIT" checkout -q "$EASYEDIT_COMMIT"
test "$(git -C "$EA_EASYEDIT" rev-parse HEAD)" = "$EASYEDIT_COMMIT"
echo "EasyEdit HEAD $(git -C "$EA_EASYEDIT" rev-parse HEAD)"
ln -sfn "$EA_ROOT/repo/experiments" "$EA_EASYEDIT/experiments"   # live link, for interactive use only
python -c "import easyeditor; print('easyeditor import OK')"

echo "== 3/6 GPT-2 XL"
python - <<PY
from huggingface_hub import HfApi, snapshot_download
from pathlib import Path
out = Path("$EA_MODELS/gpt2-xl")
src = out / "SOURCE.txt"
if not src.exists():
    sha = HfApi().model_info("$GPT2_REPO").sha
    snapshot_download("$GPT2_REPO", revision=sha, local_dir=str(out),
                      allow_patterns=["config.json", "generation_config.json", "model.safetensors",
                                      "tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt"])
    src.write_text(f"repo $GPT2_REPO\nrevision {sha}\n")
print(src.read_text(), end="")
PY
md5sum "$EA_MODELS/gpt2-xl/model.safetensors"

echo "== 4/6 covariance statistics and hparams"
cd "$EA_EASYEDIT"
bash experiments/retrieval_poc/fetch_stats.sh
echo "stats md5 vs original (no output = identical):"
diff <(sort "$EA_REPO/environment/stats_md5.txt") <(sort experiments/retrieval_poc/stats_md5.txt) && echo "identical" || echo "STATS DIFFER FROM ORIGINAL"
for M in ROME MEMIT AlphaEdit; do
  sed "s|^model_name:.*|model_name: \"$EA_MODELS/gpt2-xl\"|" "$EA_REPO/environment/${M}_gpt2-xl.yaml" > "$EA_HPARAMS/${M}_gpt2-xl.yaml"
  echo "-- $M: only model_name may differ from the file as originally run"
  diff "$EA_REPO/environment/${M}_gpt2-xl.yaml" "$EA_HPARAMS/${M}_gpt2-xl.yaml" || true
done
md5sum "$EA_HPARAMS"/*.yaml

echo "== 5/6 AlphaEdit projection matrix"
P=data/stats/gpt2-xl/alphaedit_null_space_project.pt
if [ ! -f "$P" ]; then
  CUDA_VISIBLE_DEVICES="" python experiments/retrieval_poc/compute_alphaedit_P.py --hparams "$EA_HPARAMS/AlphaEdit_gpt2-xl"
fi
md5sum "$P"
echo "original run's md5 (logs/alphaedit_P_3576.out):"
grep -o "saved .*" "$SP/logs/alphaedit_P_3576.out" || true

echo "== 6/6 offline tests"
cd "$EA_REPO"
bash experiments/retrieval_poc/tests/run_tests.sh

echo "== disk use"
du -sh "$EA_ENV" "$EA_EASYEDIT" "$EA_MODELS" "$EA_ROOT/cache" 2>/dev/null
pip cache purge || true
echo "SETUP COMPLETE at $(date)"
