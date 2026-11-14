#!/bin/bash
#SBATCH --job-name=ea_bfinish
#SBATCH --partition=cpu-short
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/logs/baseline_finish_%j.out
# Finishes plan 0.4 for a baseline run whose ROME part completed but whose reproduce.sh stopped at its last step:
# the shipped check_paper_numbers.py nests same-quote f-strings (line 69), which is valid only in Python >= 3.12,
# while the documented environment is Python 3.10 (SyntaxError in job 16987). The script is standard-library only, so
# it is run here, unchanged, with the cluster's shared Python 3.13 (used read-only).
# Then: link the finished MEMIT/AlphaEdit runs, compare_methods, and the row-by-row comparison with the shipped results.
# Submit:  sbatch --export=ALL,RUN=<runs/0.4_... dir>,REUSE_METHODS_FROM=<dir> $EA_REPO/cluster/csis/baseline_finish.sbatch
set -eo pipefail   # no -u: conda activate scripts reference unset variables
source /nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/repo/cluster/csis/paths.sh
: "${RUN:?}" "${REUSE_METHODS_FROM:?}"
PY312=/nfs_home/software/miniconda/bin/python3.13
echo "Job ${SLURM_JOB_ID:-local} on $(hostname) at $(date) | finishing $RUN"
cat "$EA_REPO/SYNCED_FROM.txt"
ea_workdir "$RUN/work_finish"
SP=experiments/retrieval_poc
R=$SP/results
$PY312 -V

echo "== check_paper_numbers.py (unchanged) on the SHIPPED results: must print the paper's numbers"
$PY312 $SP/check_paper_numbers.py --results $R | tee "$RUN/check_paper_numbers_shipped.txt"
echo "== check_paper_numbers.py on the A100 re-run"
$PY312 $SP/check_paper_numbers.py --results "$RUN/rome" --study-v1 v1 --study-v2 v2 | tee "$RUN/check_paper_numbers_rerun.txt"
echo "== diff of the two printouts (no output = identical)"
diff "$RUN/check_paper_numbers_shipped.txt" "$RUN/check_paper_numbers_rerun.txt" && echo "IDENTICAL PRINTOUTS" || true

echo "== MEMIT and AlphaEdit from $REUSE_METHODS_FROM"
V1=$R/screen_3461/probes V2=$R/screen_3466/probes_company bash $SP/make_main_probes.sh "$RUN"
for d in "$REUSE_METHODS_FROM"/study_a100_{MEMIT,AlphaEdit}_seed{0,1,2}; do
  test -s "$d/deltas.csv" || { echo "missing $d/deltas.csv"; exit 1; }
  ln -sfn "$d" "$RUN/$(basename "$d")"; echo "reusing $d"
done
diff <(cd "$REUSE_METHODS_FROM/main_probes" && md5sum *.json) <(cd "$RUN/main_probes" && md5sum *.json) && echo "same probe files"
python $SP/compare_methods.py \
  --method ROME      "$RUN"/rome/study_v1_seed{0,1,2}/deltas.csv "$RUN"/rome/study_v2_seed{0,1,2}/deltas.csv \
  --method MEMIT     "$RUN"/study_a100_MEMIT_seed{0,1,2}/deltas.csv \
  --method AlphaEdit "$RUN"/study_a100_AlphaEdit_seed{0,1,2}/deltas.csv \
  --out "$RUN/compare_methods"

echo "== row-by-row comparison with the shipped results"
PAIRS=(--pair screen_v1 $R/screen_3461/screen_report.csv "$RUN/rome/screen_v1/screen_report.csv"
       --pair screen_v2 $R/screen_3466/screen_report.csv "$RUN/rome/screen_v2/screen_report.csv"
       --pair aggregate_table2 $R/compare_methods/aggregate.csv "$RUN/compare_methods/aggregate.csv"
       --pair per_fact_table3 $R/compare_methods/per_fact.csv "$RUN/compare_methods/per_fact.csv")
for s in 0 1 2; do
  PAIRS+=(--pair ROME_v1_seed$s $R/study_3462_seed$s/deltas.csv "$RUN/rome/study_v1_seed$s/deltas.csv"
          --pair ROME_v2_seed$s $R/study_3467_seed$s/deltas.csv "$RUN/rome/study_v2_seed$s/deltas.csv"
          --pair MEMIT_seed$s $R/study_3574_MEMIT_seed$s/deltas.csv "$RUN/study_a100_MEMIT_seed$s/deltas.csv"
          --pair AlphaEdit_seed$s $R/study_3583_AlphaEdit_seed$s/deltas.csv "$RUN/study_a100_AlphaEdit_seed$s/deltas.csv")
done
python "$EA_REPO/cluster/csis/compare_to_shipped.py" "${PAIRS[@]}" --out "$RUN/comparison.md" > /dev/null; head -30 "$RUN/comparison.md"   # no pipe: under pipefail a closed pipe kills the job (16992)
echo "BASELINE RERUN COMPLETE at $(date). Full comparison: $RUN/comparison.md"
