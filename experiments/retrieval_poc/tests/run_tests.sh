#!/bin/bash
# Offline tests on a tiny random GPT-2 (CPU, no downloads, < 1 minute). Run from the repository root.
set -euo pipefail
SP=experiments/retrieval_poc
for t in test_scoring test_pilot test_screen test_study; do
  echo "== $t"; python "$SP/tests/$t.py" "$SP"
done
echo "ALL OFFLINE TESTS PASSED"
