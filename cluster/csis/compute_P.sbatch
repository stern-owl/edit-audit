#!/bin/bash
#SBATCH --job-name=ea_P
#SBATCH --partition=cpu-long
#SBATCH --cpus-per-task=32
#SBATCH --mem=96G
#SBATCH --time=1-00:00:00
#SBATCH --output=/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/logs/compute_P_%j.out
# AlphaEdit null-space projection for one model (CPU, EasyEdit's own get_project; no GPU used).
# GPT-J: 6 layers x SVD of a 16384 x 16384 covariance; the result is ~6.4 GB.
# Submit:  sbatch --export=ALL,HP=AlphaEdit_gpt-j-6B $EA_REPO/cluster/csis/compute_P.sbatch
set -eo pipefail   # no -u: conda activate scripts reference unset variables
source /nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/repo/cluster/csis/paths.sh
: "${HP:?set HP to an hparams name in \$EA_HPARAMS, e.g. AlphaEdit_gpt-j-6B}"
export CUDA_VISIBLE_DEVICES=""
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-32} MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-32}
echo "Job ${SLURM_JOB_ID:-local} on $(hostname) at $(date) | $HP"
cat "$EA_REPO/SYNCED_FROM.txt"
RUN=$EA_ROOT/runs/compute_P_${HP}_${SLURM_JOB_ID:-local}; ea_workdir "$RUN/work"
md5sum experiments/retrieval_poc/compute_alphaedit_P_v2.py "$EA_HPARAMS/$HP.yaml"
python experiments/retrieval_poc/compute_alphaedit_P_v2.py --hparams "$EA_HPARAMS/$HP"
du -sh data/stats/*/alphaedit_null_space_project.pt
echo "COMPUTE P COMPLETE at $(date)"
