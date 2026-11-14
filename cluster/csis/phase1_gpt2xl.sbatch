#!/bin/bash
#SBATCH --job-name=ea_phase1
#SBATCH --partition=gpu-short
#SBATCH --gres=gpu:a100-80gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/logs/phase1_gpt2xl_%j.out
# GPT-2 XL, the draft's 12-fact probe set, seeds 0-2, run_audit.py --mode independent:
#   (a) plan 2.1 equivalence: ROME, MEMIT, AlphaEdit with the draft's hparams. The deltas must reproduce
#       - the A100 re-run of the draft's own scripts (BASELINE_RUN, plan 0.4): identical numbers expected
#         (same GPU, same token ids under GPT2TokenizerFast and GPT2Tokenizer, same forward pass);
#       - the shipped H100 results: identical ranks expected, log-probabilities up to GPU rounding.
#   (b) plan 1.2: dist.csv (full-vocabulary and candidate-set divergences) for all three methods.
#   (c) plan 1.1: ROME with covariance statistics (mom2_adjustment: true, layer-17 stats already present).
#       Prediction recorded before the run (research-log entry 04): stale reverse reads persist (subject still
#       rank 1 in every seed on >= 20/24 reverse-from-old paths) and the edited question still succeeds on 12/12.
# Submit:  sbatch --export=ALL,BASELINE_RUN=<runs/0.4_... dir> $EA_REPO/cluster/csis/phase1_gpt2xl.sbatch
set -eo pipefail   # no -u: conda activate scripts reference unset variables
source /nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/repo/cluster/csis/paths.sh
: "${BASELINE_RUN:?set BASELINE_RUN to the output dir of baseline_rerun.sbatch}"
RUN=$EA_ROOT/runs/1_phase1_gpt2xl_${SLURM_JOB_ID:-local}
mkdir -p "$RUN"
echo "Job ${SLURM_JOB_ID:-local} on $(hostname) at $(date) | outputs in $RUN | baseline $BASELINE_RUN"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
cat "$EA_REPO/SYNCED_FROM.txt"
ea_workdir "$RUN/work"
SP=experiments/retrieval_poc
MODEL=$EA_MODELS/gpt2-xl
md5sum $SP/run_audit.py $SP/probe_scoring_v4.py $SP/probe_scoring.py $SP/rome_paired_pilot.py $SP/run_method_study.py

V1=$SP/results/screen_3461/probes V2=$SP/results/screen_3466/probes_company bash $SP/make_main_probes.sh "$RUN"
md5sum "$RUN"/main_probes/*.json

# ROME with covariance statistics: the draft's ROME file with only mom2_adjustment changed.
sed 's/^mom2_adjustment: false$/mom2_adjustment: true/' "$EA_HPARAMS/ROME_gpt2-xl.yaml" > "$EA_HPARAMS/ROMEmom2_gpt2-xl.yaml"
diff "$EA_HPARAMS/ROME_gpt2-xl.yaml" "$EA_HPARAMS/ROMEmom2_gpt2-xl.yaml" || true
md5sum "$EA_HPARAMS"/*.yaml

for CFG in ROME:ROME_gpt2-xl MEMIT:MEMIT_gpt2-xl AlphaEdit:AlphaEdit_gpt2-xl ROME:ROMEmom2_gpt2-xl; do
  M=${CFG%%:*}; HP=${CFG#*:}
  for s in 0 1 2; do
    echo "== $HP seed $s"
    python $SP/run_audit.py --method $M --hparams "$EA_HPARAMS/$HP" --model "$MODEL" --probes-dir "$RUN/main_probes" \
      --mode independent --seed $s --output-dir "$RUN/$HP" --tag p1
  done
done

echo "== equivalence: run_audit (v4) vs the draft's scripts"
# Shipped ROME deltas are split over study 3462 (novels + invention; its v1 company rows are the failed edits)
# and 3467 (v2 companies). Merge them into the 12-fact set the other methods use.
python - "$SP/results" "$BASELINE_RUN" "$RUN" <<'PY'
import csv, sys
from pathlib import Path
shipped, base, run = map(Path, sys.argv[1:])
COMP = {"amazon", "apple", "facebook", "google", "microsoft"}
for s in range(3):
    for name, v1, v2 in (("shipped", shipped / f"study_3462_seed{s}", shipped / f"study_3467_seed{s}"),
                         ("a100", base / "rome" / f"study_v1_seed{s}", base / "rome" / f"study_v2_seed{s}")):
        rows = [r for r in csv.DictReader(open(v1 / "deltas.csv", newline="", encoding="utf-8")) if r["fact_id"] not in COMP]
        rows += list(csv.DictReader(open(v2 / "deltas.csv", newline="", encoding="utf-8")))
        with open(run / f"rome12_{name}_seed{s}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
        print(name, "seed", s, "ROME 12-fact rows:", len(rows), "facts:", len({r["fact_id"] for r in rows}))
PY
R=$SP/results
P_A100=(); P_SHIP=()
for s in 0 1 2; do
  A=audit_p1_gpt2-xl
  P_A100+=(--pair ROME_s$s "$RUN/rome12_a100_seed$s.csv" "$RUN/ROME_gpt2-xl/${A}_ROME_independent_seed$s/deltas.csv"
           --pair MEMIT_s$s "$BASELINE_RUN/study_a100_MEMIT_seed$s/deltas.csv" "$RUN/MEMIT_gpt2-xl/${A}_MEMIT_independent_seed$s/deltas.csv"
           --pair AlphaEdit_s$s "$BASELINE_RUN/study_a100_AlphaEdit_seed$s/deltas.csv" "$RUN/AlphaEdit_gpt2-xl/${A}_AlphaEdit_independent_seed$s/deltas.csv")
  P_SHIP+=(--pair ROME_s$s "$RUN/rome12_shipped_seed$s.csv" "$RUN/ROME_gpt2-xl/${A}_ROME_independent_seed$s/deltas.csv"
           --pair MEMIT_s$s $R/study_3574_MEMIT_seed$s/deltas.csv "$RUN/MEMIT_gpt2-xl/${A}_MEMIT_independent_seed$s/deltas.csv"
           --pair AlphaEdit_s$s $R/study_3583_AlphaEdit_seed$s/deltas.csv "$RUN/AlphaEdit_gpt2-xl/${A}_AlphaEdit_independent_seed$s/deltas.csv")
done
python "$EA_REPO/cluster/csis/compare_to_shipped.py" --drop-margin "${P_A100[@]}" --out "$RUN/equivalence_vs_a100_rerun.md" > /dev/null; head -30 "$RUN/equivalence_vs_a100_rerun.md"   # no pipe: under pipefail a closed pipe kills the job (16992)
python "$EA_REPO/cluster/csis/compare_to_shipped.py" --drop-margin "${P_SHIP[@]}" --out "$RUN/equivalence_vs_shipped.md" > /dev/null; head -30 "$RUN/equivalence_vs_shipped.md"   # no pipe: under pipefail a closed pipe kills the job (16992)

echo "== Table 2 counts for ROME with covariance statistics (plan 1.1), next to the draft's three configurations"
python $SP/compare_methods.py \
  --method ROME          "$RUN"/ROME_gpt2-xl/audit_p1_gpt2-xl_ROME_independent_seed{0,1,2}/deltas.csv \
  --method MEMIT         "$RUN"/MEMIT_gpt2-xl/audit_p1_gpt2-xl_MEMIT_independent_seed{0,1,2}/deltas.csv \
  --method AlphaEdit     "$RUN"/AlphaEdit_gpt2-xl/audit_p1_gpt2-xl_AlphaEdit_independent_seed{0,1,2}/deltas.csv \
  --method ROME+stats    "$RUN"/ROMEmom2_gpt2-xl/audit_p1_gpt2-xl_ROME_independent_seed{0,1,2}/deltas.csv \
  --out "$RUN/compare_methods" || echo "compare_methods failed on run_audit deltas (see above); analyse offline"
echo "PHASE 1 GPT-2 XL COMPLETE at $(date). Outputs: $RUN"
