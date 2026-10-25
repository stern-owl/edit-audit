#!/bin/bash
# Full re-run of the paper's experiments WITHOUT Slurm, on one GPU.
#
# Run from the EasyEdit root (after copying this repo's experiments/ folder into it):
#   MODEL=/path/to/gpt2-xl bash experiments/retrieval_poc/reproduce.sh
#
# Memory: each step caps PyTorch at GPU_MEM_GB of GPU memory (default 20 GiB).
# The original runs peaked at about 6 GiB (screening) and 9.2 GiB (editing), so a
# 16 GB GPU is enough; set GPU_MEM_GB lower or higher to match your card.
# Host RAM: about 24-32 GB. Time: about 45-60 minutes on one H100 MIG 3g.47gb slice.
set -euo pipefail

: "${MODEL:?set MODEL to the local GPT-2 XL directory; it must equal model_name in hparams/ROME/gpt2-xl.yaml}"
HPARAMS="${HPARAMS:-./hparams/ROME/gpt2-xl}"
export GPU_MEM_GB="${GPU_MEM_GB:-20}"
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
export PYTORCH_ALLOC_CONF="expandable_segments:True"
SP=experiments/retrieval_poc
RES=$SP/results_rerun
mkdir -p "$RES"

echo "== checksums of inputs (compare with CHECKSUMS.md5 in the repo)"
md5sum $SP/*.py $SP/*.json $SP/*.csv "$HPARAMS.yaml"

echo "== 1/4 screen all 18 facts with templates v1 (no edits)"
python $SP/screen_facts.py --facts $SP/candidate_facts_v2.csv --templates $SP/relation_templates.json \
  --model "$MODEL" --hparams "$HPARAMS" --gpu-mem-gb "$GPU_MEM_GB" --output-dir "$RES" --tag screen_v1

echo "== 2/4 edit the facts included under v1, seeds 0-2 (one process per seed)"
for s in 0 1 2; do
  python $SP/run_fact_study.py --probes-dir "$RES/screen_v1/probes" --seed $s \
    --model "$MODEL" --hparams "$HPARAMS" --gpu-mem-gb "$GPU_MEM_GB" --output-dir "$RES" --tag v1
done

echo "== 3/4 re-screen with templates v2 (company edit prompt no longer starts with the subject)"
python $SP/screen_facts.py --facts $SP/candidate_facts_v2.csv --templates $SP/relation_templates_v2.json \
  --model "$MODEL" --hparams "$HPARAMS" --gpu-mem-gb "$GPU_MEM_GB" --output-dir "$RES" --tag screen_v2
mkdir -p "$RES/screen_v2/probes_company"
cp "$RES"/screen_v2/probes/{microsoft,apple,amazon,facebook,google}.json "$RES/screen_v2/probes_company/"

echo "== 4/4 edit the five company facts with v2 probes, seeds 0-2"
for s in 0 1 2; do
  python $SP/run_fact_study.py --probes-dir "$RES/screen_v2/probes_company" --seed $s \
    --model "$MODEL" --hparams "$HPARAMS" --gpu-mem-gb "$GPU_MEM_GB" --output-dir "$RES" --tag v2
done

echo "== analysis"
python $SP/analyze_study.py $RES/study_v1_seed{0,1,2}/deltas.csv --out $RES/analysis_v1
python $SP/analyze_study.py $RES/study_v2_seed{0,1,2}/deltas.csv --out $RES/analysis_v2
python $SP/check_paper_numbers.py --results "$RES" --study-v1 v1 --study-v2 v2
echo "Done. Compare the numbers above with the paper and with results/ (the original outputs)."
