#!/bin/bash
#SBATCH --job-name=ea_tests
#SBATCH --partition=cpu-short
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/logs/tests_%j.out
# Offline tests on CPU: the shipped suite (tests/run_tests.sh, unchanged) plus the tests of code added in phase 2.
# Submit:  sbatch $EA_REPO/cluster/csis/tests.sbatch
set -eo pipefail   # no -u: conda activate scripts reference unset variables
source /nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/repo/cluster/csis/paths.sh
export CUDA_VISIBLE_DEVICES=""
cd "$EA_REPO"
cat SYNCED_FROM.txt
SP=experiments/retrieval_poc
echo "== shipped suite"
bash $SP/tests/run_tests.sh
echo "== phase 2"
for t in test_scoring_v4 test_audit test_screen_v4 test_analyze_audit test_pairs test_programs test_phase6_offline; do
  echo "== $t"; python "$SP/tests/$t.py" "$SP"
done
echo "ALL TESTS PASSED (shipped + phase 2)"
