#!/bin/bash
# Download the precomputed GPT-2 XL covariance statistics (Wikipedia, 100k samples) that MEMIT and
# AlphaEdit need, from the ROME/MEMIT authors' server, into the path EasyEdit reads them from.
# Login node, no GPU. ~5 files x ~160 MB. Run from the EasyEdit root.
set -euo pipefail
D=data/stats/gpt2-xl/wikipedia_stats
URL=https://rome.baulab.info/data/stats/gpt2-xl/wikipedia_stats
mkdir -p "$D"
for L in 13 14 15 16 17; do
  F=transformer.h.$L.mlp.c_proj_float32_mom2_100000.npz
  if [ -s "$D/$F" ]; then echo "exists: $F"; continue; fi
  wget -q --show-progress -O "$D/$F.part" "$URL/$F" && mv "$D/$F.part" "$D/$F"
done
md5sum "$D"/*.npz | tee experiments/retrieval_poc/stats_md5.txt
# Verify with EasyEdit's own loader: each file must load as a cached statistic with sample_size=100000.
python - <<'PY'
import glob, numpy as np
from easyeditor.util.runningstats import load_cached_state
for f in sorted(glob.glob("data/stats/gpt2-xl/wikipedia_stats/*.npz")):
    d = load_cached_state(f, {"sample_size": 100000}, quiet=True)
    assert d is not None, f"EasyEdit would NOT accept {f}"
    keys = {k: getattr(d[k], "shape", d[k]) for k in d}
    print("OK", f.rsplit("/", 1)[-1], keys)
print("STATS READY")
PY
