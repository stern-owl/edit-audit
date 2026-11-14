#!/bin/bash
#SBATCH --job-name=ea_screen
#SBATCH --partition=gpu-short
#SBATCH --gres=gpu:a100-80gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=04:00:00
#SBATCH --output=/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/logs/screen_v3_%j.out
# Plan 2.2: pre-registered screening of the v3 candidate facts (facts_v3/candidate_facts_v3.csv, templates v3) on one
# model. No edit is applied. Output: runs/2.2_screen_v3_<model>_<jobid>/screen/
# Submit:  sbatch --export=ALL,MODEL_NAME=gpt2-xl $EA_REPO/cluster/csis/screen_v3.sbatch
# GPT-J (24 GB .bin, loaded fully into RAM): add --mem=64G. Measured: GPT-2 XL baseline MaxRSS ~2 GB.
set -eo pipefail   # no -u: conda activate scripts reference unset variables
source /nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/repo/cluster/csis/paths.sh
: "${MODEL_NAME:?set MODEL_NAME to a directory name under \$EA_MODELS}"
RUN=$EA_ROOT/runs/2.2_screen_v3_${MODEL_NAME}_${SLURM_JOB_ID:-local}
mkdir -p "$RUN"
echo "Job ${SLURM_JOB_ID:-local} on $(hostname) at $(date) | $MODEL_NAME | outputs in $RUN"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
cat "$EA_REPO/SYNCED_FROM.txt"
ea_workdir "$RUN/work"
SP=experiments/retrieval_poc
md5sum $SP/screen_facts_v4.py $SP/screen_facts.py $SP/probe_scoring_v4.py $SP/relation_templates_v3.json \
       $SP/facts_v3/candidate_facts_v3.csv $SP/facts_v3/own_facts.csv
python $SP/screen_facts_v4.py --facts $SP/facts_v3/candidate_facts_v3.csv --templates $SP/relation_templates_v3.json \
  --model "$EA_MODELS/$MODEL_NAME" --output-dir "$RUN" --tag screen
echo "SCREEN V3 JOB COMPLETE at $(date)"
