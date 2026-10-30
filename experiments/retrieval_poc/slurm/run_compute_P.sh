#!/bin/bash
#SBATCH --job-name=alphaedit_P
#SBATCH --partition=h100-mig
#SBATCH --gres=gpu:nvidia_h100_nvl_3g.47gb:1
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --output=experiments/retrieval_poc/logs/alphaedit_P_%j.out
#SBATCH --error=experiments/retrieval_poc/logs/alphaedit_P_%j.err
# CPU-only computation (SVD of five 6400x6400 matrices); the GPU slice is only requested because this
# partition is the one we know works. No GPU memory is used (the model is loaded on CPU). Host RAM 32G.
set -euo pipefail
source /localstorage/home/f20220930/miniforge3/etc/profile.d/conda.sh
conda activate EasyEdit
cd /localstorage/home/f20220930/EasyEdit
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
export CUDA_VISIBLE_DEVICES=""
md5sum experiments/retrieval_poc/compute_alphaedit_P.py experiments/retrieval_poc/hparams/AlphaEdit_gpt2-xl.yaml data/stats/gpt2-xl/wikipedia_stats/*.npz
python experiments/retrieval_poc/compute_alphaedit_P.py --hparams experiments/retrieval_poc/hparams/AlphaEdit_gpt2-xl
