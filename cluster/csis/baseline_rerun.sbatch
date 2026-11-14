#!/bin/bash
#SBATCH --job-name=ea_baseline
#SBATCH --partition=gpu-short
#SBATCH --gres=gpu:a100-80gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/logs/baseline_rerun_%j.out
# Plan item 0.4: re-run every GPT-2 XL experiment of the draft on an A100 80GB (the originals ran on an
# H100 MIG 3g.47gb slice) and compare each output row with the shipped results.
#   ROME:            reproduce.sh unchanged (screen v1, edit, screen v2, edit companies, check_paper_numbers)
#   MEMIT/AlphaEdit: run_method_study.py on the SHIPPED 12-fact probe set (same probe md5 as jobs 3574/3583)
# Prediction written before the run: ranks and validity flags identical to the shipped files; log-probabilities
# may differ in the last digits (different GPU kernels). Any rank or validity change is recorded as a finding.
# Submit:  sbatch $EA_REPO/cluster/csis/baseline_rerun.sbatch
set -eo pipefail   # no -u: conda activate scripts reference unset variables
source /nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/repo/cluster/csis/paths.sh
RUN=$EA_ROOT/runs/0.4_baseline_a100_${SLURM_JOB_ID:-local}
mkdir -p "$RUN"
echo "Job ${SLURM_JOB_ID:-local} on $(hostname) at $(date) | outputs in $RUN"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
cat "$EA_REPO/SYNCED_FROM.txt"
python -c "import torch, transformers; print('torch', torch.__version__, '| transformers', transformers.__version__, '| device', torch.cuda.get_device_name(0))"
ea_workdir "$RUN/work"
SP=experiments/retrieval_poc
MODEL=$EA_MODELS/gpt2-xl
export GPU_MEM_GB=40

echo "== ROME (reproduce.sh)"
# reproduce.sh writes to $SP/results_rerun; point that at this run's folder.
rm -f "$SP/results_rerun"; ln -s "$RUN/rome" "$SP/results_rerun"; mkdir -p "$RUN/rome"
MODEL=$MODEL HPARAMS=$EA_HPARAMS/ROME_gpt2-xl bash $SP/reproduce.sh
rm -f "$SP/results_rerun"

echo "== MEMIT and AlphaEdit on the shipped 12-fact probes"
V1=$SP/results/screen_3461/probes V2=$SP/results/screen_3466/probes_company bash $SP/make_main_probes.sh "$RUN"
md5sum "$RUN"/main_probes/*.json
if [ -n "${REUSE_METHODS_FROM:-}" ]; then
  # Job 16978's MEMIT/AlphaEdit runs completed normally; only its ROME part was cut short (entry 02). Link them.
  for d in "$REUSE_METHODS_FROM"/study_a100_{MEMIT,AlphaEdit}_seed{0,1,2}; do
    test -s "$d/deltas.csv" || { echo "missing $d/deltas.csv"; exit 1; }
    ln -sfn "$d" "$RUN/$(basename "$d")"; echo "reusing $d"
  done
  diff <(cd "$REUSE_METHODS_FROM/main_probes" && md5sum *.json) <(cd "$RUN/main_probes" && md5sum *.json) && echo "same probe files"
else
  for M in MEMIT AlphaEdit; do
    for s in 0 1 2; do
      python $SP/run_method_study.py --method $M --hparams "$EA_HPARAMS/${M}_gpt2-xl" --model "$MODEL" \
        --probes-dir "$RUN/main_probes" --seed $s --output-dir "$RUN" --tag a100 --gpu-mem-gb $GPU_MEM_GB
    done
  done
fi
python $SP/compare_methods.py \
  --method ROME      "$RUN"/rome/study_v1_seed{0,1,2}/deltas.csv "$RUN"/rome/study_v2_seed{0,1,2}/deltas.csv \
  --method MEMIT     "$RUN"/study_a100_MEMIT_seed{0,1,2}/deltas.csv \
  --method AlphaEdit "$RUN"/study_a100_AlphaEdit_seed{0,1,2}/deltas.csv \
  --out "$RUN/compare_methods"

echo "== row-by-row comparison with the shipped results"
R=$SP/results
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
