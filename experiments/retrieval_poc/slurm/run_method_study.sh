#!/bin/bash
#SBATCH --job-name=method_study
#SBATCH --partition=h100-mig
#SBATCH --gres=gpu:nvidia_h100_nvl_3g.47gb:1
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --array=0-2%1
#SBATCH --output=experiments/retrieval_poc/logs/method_study_%A_seed%a.out
#SBATCH --error=experiments/retrieval_poc/logs/method_study_%A_seed%a.err
# One array task per seed; %1 = one at a time, so only one GPU slice is used.
# GPU: one MIG slice; inside it PyTorch is capped at GPU_MEM_GB GiB (below).
# Host RAM 48G: MEMIT/AlphaEdit keep 5 covariance matrices (and AlphaEdit 2 more 5x6400x6400 tensors) in CPU memory.
# Submit from the EasyEdit root, e.g.:
#   sbatch --export=ALL,METHOD=MEMIT experiments/retrieval_poc/run_method_study.sh
set -euo pipefail

source /localstorage/home/f20220930/miniforge3/etc/profile.d/conda.sh
conda activate EasyEdit
cd /localstorage/home/f20220930/EasyEdit
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
export MPLCONFIGDIR="$PWD/.mplconfig"; mkdir -p "$MPLCONFIGDIR"
export GPU_MEM_GB="${GPU_MEM_GB:-24}"   # ROME peaked at 9.2 GiB; MEMIT/AlphaEdit edit 5 layers
export PYTORCH_ALLOC_CONF="expandable_segments:True"
: "${METHOD:?set METHOD to ROME, MEMIT or AlphaEdit}"
SP=experiments/retrieval_poc
HP="${HPARAMS:-$SP/hparams/${METHOD}_gpt2-xl}"
PROBES="${PROBES:-$SP/results/main_probes}"
SEED="${SLURM_ARRAY_TASK_ID:-0}"

echo "Job ${SLURM_ARRAY_JOB_ID:-local}_${SEED} on $(hostname) at $(date) | METHOD=$METHOD SEED=$SEED GPU_MEM_GB=$GPU_MEM_GB"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi -L || true
md5sum $SP/run_method_study.py $SP/run_fact_study.py $SP/rome_paired_pilot.py $SP/probe_scoring.py "$HP.yaml"
md5sum "$PROBES"/*.json

python $SP/run_method_study.py --method "$METHOD" --hparams "$HP" --probes-dir "$PROBES" --seed "$SEED"
