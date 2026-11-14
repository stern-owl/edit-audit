#!/bin/bash
#SBATCH --job-name=ea_analyze
#SBATCH --partition=cpu-short
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/logs/analyze_%j.out
# analyze_audit.py over finished run_audit outputs (CPU, standard library only).
#   OUT   output directory     RUNS  space-separated NAME=<audit output dir> pairs
# Submit:  sbatch --export=ALL,OUT=...,RUNS="ROME=... MEMIT=..." $EA_REPO/cluster/csis/analyze.sbatch
set -eo pipefail   # no -u: conda activate scripts reference unset variables
source /nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/repo/cluster/csis/paths.sh
: "${OUT:?}" "${RUNS:?}"
echo "Job ${SLURM_JOB_ID:-local} on $(hostname) at $(date) | out $OUT"
cat "$EA_REPO/SYNCED_FROM.txt"
SP=$EA_REPO/experiments/retrieval_poc
md5sum $SP/analyze_audit.py $SP/relation_templates_v3.json
ARGS=()
for r in $RUNS; do ARGS+=(--run "$r"); done
python $SP/analyze_audit.py --templates $SP/relation_templates_v3.json --out "$OUT" "${ARGS[@]}" > "$OUT.stdout.txt"
echo "ANALYSIS COMPLETE at $(date): $OUT/report.md"
