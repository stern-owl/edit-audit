#!/bin/bash
#SBATCH --job-name=fact_study
#SBATCH --partition=h100-mig
#SBATCH --gres=gpu:nvidia_h100_nvl_3g.47gb:1
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --array=0-2%1
#SBATCH --output=experiments/retrieval_poc/logs/fact_study_%A_seed%a.out
#SBATCH --error=experiments/retrieval_poc/logs/fact_study_%A_seed%a.err
# One array task per seed (0,1,2); %1 = one task at a time, so only one GPU slice is ever used.
# GPU: one MIG slice (above). Inside it, PyTorch is capped at GPU_MEM_GB GiB (below).
# Submit from the EasyEdit root:
#   cd /localstorage/home/f20220930/EasyEdit && sbatch --export=ALL,PROBES_DIR=<dir> experiments/retrieval_poc/run_fact_study.sh
set -euo pipefail

source /localstorage/home/f20220930/miniforge3/etc/profile.d/conda.sh
conda activate EasyEdit
cd /localstorage/home/f20220930/EasyEdit
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
export MPLCONFIGDIR="$PWD/.mplconfig"; mkdir -p "$MPLCONFIGDIR"
export GPU_MEM_GB="${GPU_MEM_GB:-20}"   # pilot ROME runs peaked at 8.1-9.6 GiB
export PYTORCH_ALLOC_CONF="expandable_segments:True"
: "${PROBES_DIR:?set PROBES_DIR, e.g. experiments/retrieval_poc/results/screen_3461/probes}"
SEED="${SLURM_ARRAY_TASK_ID:-0}"

echo "Job ${SLURM_ARRAY_JOB_ID:-local}_${SEED} on $(hostname) at $(date) | SEED=$SEED GPU_MEM_GB=$GPU_MEM_GB"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi -L || true
md5sum experiments/retrieval_poc/run_fact_study.py experiments/retrieval_poc/rome_paired_pilot.py \
  experiments/retrieval_poc/probe_scoring.py hparams/ROME/gpt2-xl.yaml
md5sum "$PROBES_DIR"/*.json

python experiments/retrieval_poc/run_fact_study.py --probes-dir "$PROBES_DIR" --seed "$SEED"
