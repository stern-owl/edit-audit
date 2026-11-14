#!/bin/bash
#SBATCH --job-name=ea_audit
#SBATCH --partition=gpu-1day
#SBATCH --gres=gpu:a100-80gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=1-00:00:00
#SBATCH --output=/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/logs/audit_v3_%j.out
# run_audit.py on the facts a screening job admitted, for several methods, one process per (method, seed).
# Environment variables:
#   MODEL_NAME  directory under $EA_MODELS (gpt2-xl, gpt-j-6B); hparams are $EA_HPARAMS/<METHOD>_<MODEL_NAME>.yaml
#   PROBES      probes/ directory of a screening run (only facts with screening.included=true are used)
#   MODE        independent | sequential | batch | pairs (pairs: make_pairs.py runs here on PROBES with its defaults
#               and the pairs/sentinels are passed to run_audit.py; PAIRS_SEED optional, default 0)
#               | programs (make_programs.py runs here on PROBES with the v3 templates and candidates; N5 + N2)
#   METHODS     e.g. "ROME MEMIT AlphaEdit"          SEEDS  e.g. "0"
#   EXTRA       further run_audit.py arguments, e.g. "--order shuffle:1 --checkpoints 1,5,10 --reread-gen-tokens 0"
#   LABEL       short name for the run directory
#   HP_VARIANT  optional: use $EA_HPARAMS/<METHOD><HP_VARIANT>_<MODEL_NAME>.yaml; HP_VARIANT=mom2 with METHODS=ROME runs
#               ROME with covariance statistics (file created from the base file, only mom2_adjustment changed)
# Submit:  sbatch --export=ALL,MODEL_NAME=gpt2-xl,PROBES=...,MODE=independent,METHODS="ROME MEMIT AlphaEdit",SEEDS=0,LABEL=E4 \
#            $EA_REPO/cluster/csis/audit_v3.sbatch        (GPT-J: add --mem=64G)
set -eo pipefail   # no -u: conda activate scripts reference unset variables
source /nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/repo/cluster/csis/paths.sh
: "${MODEL_NAME:?}" "${PROBES:?}" "${MODE:?}" "${METHODS:?}" "${SEEDS:?}" "${LABEL:?}"
RUN=$EA_ROOT/runs/${LABEL}_${MODEL_NAME}_${MODE}_${SLURM_JOB_ID:-local}
mkdir -p "$RUN"
echo "Job ${SLURM_JOB_ID:-local} on $(hostname) at $(date) | $MODEL_NAME | $MODE | methods $METHODS | seeds $SEEDS | extra: ${EXTRA:-}"
echo "outputs in $RUN | probes $PROBES"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
cat "$EA_REPO/SYNCED_FROM.txt"
ea_workdir "$RUN/work"
SP=experiments/retrieval_poc
md5sum $SP/run_audit.py $SP/probe_scoring_v4.py $SP/run_method_study.py $SP/rome_paired_pilot.py
python - "$PROBES" <<'PY'
import json, sys, collections
from pathlib import Path
inc = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(sys.argv[1]).glob("*.json"))]
inc = [p for p in inc if p["screening"]["included"]]
print("included facts:", len(inc), dict(collections.Counter(p["relation"] for p in inc)))
PY
if [ "$MODE" = pairs ]; then
  python $SP/make_pairs.py --probes-dir "$PROBES" --out "$RUN/pairs" --seed "${PAIRS_SEED:-0}"
  md5sum $SP/make_pairs.py "$RUN/pairs/pairs.csv" "$RUN/pairs/sentinels.txt"
  EXTRA="--pairs $RUN/pairs/pairs.csv --sentinels-file $RUN/pairs/sentinels.txt ${EXTRA:-}"
fi
if [ "$MODE" = programs ]; then
  TPL=$SP/relation_templates_v3.json; CAND=$SP/facts_v3/candidate_facts_v3.csv
  python $SP/make_programs.py --probes-dir "$PROBES" --templates $TPL --candidates $CAND --out "$RUN/programs"
  md5sum $SP/make_programs.py $TPL $CAND "$RUN/programs/programs.jsonl" "$RUN/programs/derived_facts.csv" "$RUN/programs/sentinels.txt"
  EXTRA="--programs $RUN/programs/programs.jsonl --derived-facts $RUN/programs/derived_facts.csv --candidates $CAND --templates $TPL --sentinels-file $RUN/programs/sentinels.txt ${EXTRA:-}"
fi
for M in $METHODS; do
  HP="$EA_HPARAMS/${M}${HP_VARIANT:-}_${MODEL_NAME}"
  if [ "${HP_VARIANT:-}" = mom2 ] && [ ! -f "$HP.yaml" ]; then
    # the base file with only mom2_adjustment switched on (as for GPT-2 XL in plan 1.1)
    sed 's/^mom2_adjustment: false$/mom2_adjustment: true/' "$EA_HPARAMS/${M}_${MODEL_NAME}.yaml" > "$HP.yaml"
  fi
  [ -n "${HP_VARIANT:-}" ] && { diff "$EA_HPARAMS/${M}_${MODEL_NAME}.yaml" "$HP.yaml" || true; }
  md5sum "$HP.yaml"
  for s in $SEEDS; do
    echo "== $M${HP_VARIANT:-} seed $s"
    python $SP/run_audit.py --method $M --hparams "$HP" --model "$EA_MODELS/$MODEL_NAME" \
      --probes-dir "$PROBES" --mode "$MODE" --seed $s --output-dir "$RUN/$M${HP_VARIANT:-}" --tag "$LABEL" ${EXTRA:-}
  done
done
echo "AUDIT V3 JOB COMPLETE at $(date). Outputs: $RUN"
