#!/bin/bash
# Build the 12-fact probe set used by the MEMIT/AlphaEdit runs (and equivalent to the ROME main set):
# novels + invention from screening 3461 (templates v1), companies from screening 3466 (templates v2).
# Run from the EasyEdit root (or the repo root for the shipped results). Pass a different results dir as $1 for a re-run.
set -euo pipefail
R="${1:-experiments/retrieval_poc/results}"
V1="${V1:-$R/screen_3461/probes}"; V2="${V2:-$R/screen_3466/probes_company}"
mkdir -p "$R/main_probes"
cp --no-preserve=mode "$V1"/{frankenstein,dracula,pride_prejudice,moby_dick,nineteen84,war_peace,www}.json "$R/main_probes/"
cp --no-preserve=mode "$V2"/{amazon,apple,facebook,google,microsoft}.json "$R/main_probes/"
test "$(ls "$R/main_probes" | wc -l)" -eq 12 && echo "main_probes: 12 facts"
