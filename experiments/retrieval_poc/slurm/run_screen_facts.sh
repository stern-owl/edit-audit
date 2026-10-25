#!/bin/bash
#SBATCH --job-name=screen_facts
#SBATCH --partition=h100-mig
#SBATCH --gres=gpu:nvidia_h100_nvl_3g.47gb:1
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --output=experiments/retrieval_poc/logs/screen_facts_%j.out
#SBATCH --error=experiments/retrieval_poc/logs/screen_facts_%j.err
# GPU: one MIG slice (above). Inside it, PyTorch is capped at GPU_MEM_GB GiB (below).
# Submit from the EasyEdit root:
#   cd /localstorage/home/f20220930/EasyEdit && sbatch experiments/retrieval_poc/run_screen_facts.sh
set -euo pipefail

source /localstorage/home/f20220930/miniforge3/etc/profile.d/conda.sh
conda activate EasyEdit
cd /localstorage/home/f20220930/EasyEdit
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
export MPLCONFIGDIR="$PWD/.mplconfig"; mkdir -p "$MPLCONFIGDIR"
export GPU_MEM_GB="${GPU_MEM_GB:-12}"   # scoring only; peaked at 5.85 GiB in job 3449
export PYTORCH_ALLOC_CONF="expandable_segments:True"
FACTS="${FACTS:-experiments/retrieval_poc/candidate_facts_v2.csv}"
TEMPLATES="${TEMPLATES:-experiments/retrieval_poc/relation_templates.json}"

echo "Job ${SLURM_JOB_ID:-local} on $(hostname) at $(date) | GPU_MEM_GB=$GPU_MEM_GB"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi -L || true
md5sum "$FACTS" "$TEMPLATES" experiments/retrieval_poc/screen_facts.py experiments/retrieval_poc/probe_scoring.py

python experiments/retrieval_poc/screen_facts.py --facts "$FACTS" --templates "$TEMPLATES" \
  --tag "screen_${SLURM_JOB_ID:-local}"
