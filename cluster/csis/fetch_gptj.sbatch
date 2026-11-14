#!/bin/bash
#SBATCH --job-name=ea_gptj
#SBATCH --partition=cpu-short
#SBATCH --cpus-per-task=8
#SBATCH --mem=72G
#SBATCH --time=03:00:00
#SBATCH --output=/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/logs/fetch_gptj_%j.out
# Plan 2.4: everything GPT-J 6B needs, on a CPU node (compute nodes have internet). Idempotent.
#   1. weights: EleutherAI/gpt-j-6b, branch main pinned to a revision (fp32 pytorch_model.bin, 24.2 GB, kept as
#      published: no safetensors exists on any branch, and converting would change the file); tokenizer files
#   2. covariance statistics for layers 3-8 (MEMIT/AlphaEdit; ROME's layer 5 included) from the ROME/MEMIT
#      authors' server, into EasyEdit's path data/stats/<model dir name>/wikipedia_stats/, verified with
#      EasyEdit's own loader
#   3. hparams: EasyEdit's hparams/{ROME,MEMIT,AlphaEdit}/gpt-j-6B.yaml with only model_name, device and
#      (AlphaEdit) P_loc changed; diffs printed
#   4. load check on CPU: parameter count, dtype, BOS behaviour, one greedy completion
# Disk: ~24 GB weights + ~6.4 GB statistics. The AlphaEdit projection (6 x 16384 x 16384 fp32, ~6.4 GB) is a
# separate step. Submit:  sbatch $EA_REPO/cluster/csis/fetch_gptj.sbatch
set -eo pipefail   # no -u: conda activate scripts reference unset variables
source /nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/repo/cluster/csis/paths.sh
echo "Job ${SLURM_JOB_ID:-local} on $(hostname) at $(date)"
df -h "$EA_ROOT" | tail -1; quota -s 2>/dev/null | tail -2 || true
REPO_ID=EleutherAI/gpt-j-6b
REV=47e169305d2e8376be1d31e765533382721b2cc1     # main, 2026-10-31
MDIR=$EA_MODELS/gpt-j-6B                          # basename = EasyEdit's stats directory name
SDIR=$EA_EASYEDIT/data/stats/gpt-j-6B/wikipedia_stats
URL=https://rome.baulab.info/data/stats/EleutherAI_gpt-j-6B/wikipedia_stats

echo "== 1/4 weights"
python - <<PY
from huggingface_hub import snapshot_download
from pathlib import Path
out = Path("$MDIR")
src = out / "SOURCE.txt"
if not src.exists():
    snapshot_download("$REPO_ID", revision="$REV", local_dir=str(out),
                      allow_patterns=["config.json", "pytorch_model.bin", "tokenizer.json", "tokenizer_config.json",
                                      "vocab.json", "merges.txt", "added_tokens.json", "special_tokens_map.json"])
    src.write_text("repo $REPO_ID\nrevision $REV\nbranch main (fp32)\n")
print(src.read_text(), end="")
PY
rm -rf "$MDIR/.cache"
ls -la "$MDIR"
md5sum "$MDIR/pytorch_model.bin" | tee "$MDIR/MD5.txt"

echo "== 2/4 covariance statistics, layers 3-8"
mkdir -p "$SDIR"
for L in 3 4 5 6 7 8; do
  F=transformer.h.$L.mlp.fc_out_float32_mom2_100000.npz
  if [ -s "$SDIR/$F" ]; then echo "exists: $F"; continue; fi
  wget -q -O "$SDIR/$F.part" "$URL/$F" && mv "$SDIR/$F.part" "$SDIR/$F"
done
md5sum "$SDIR"/*.npz | tee "$EA_ROOT/stats_md5_gpt-j-6B.txt"
cd "$EA_EASYEDIT"
python - <<PY
import glob
from easyeditor.util.runningstats import load_cached_state
for f in sorted(glob.glob("$SDIR/*.npz")):
    d = load_cached_state(f, {"sample_size": 100000}, quiet=True)
    assert d is not None, f"EasyEdit would NOT accept {f}"
    print("OK", f.rsplit("/", 1)[-1], {k: getattr(d[k], "shape", d[k]) for k in d})
print("GPT-J STATS READY")
PY

echo "== 3/4 hparams"
for M in ROME MEMIT AlphaEdit; do
  sed -e "s|^model_name:.*|model_name: \"$MDIR\"|" -e "s|^device:.*|device: 0|" \
      -e "s|^P_loc:.*|P_loc: \"./data/stats/gpt-j-6B/alphaedit_null_space_project.pt\"|" \
      "$EA_EASYEDIT/hparams/$M/gpt-j-6B.yaml" > "$EA_HPARAMS/${M}_gpt-j-6B.yaml"
  echo "-- $M: changes from EasyEdit's hparams/$M/gpt-j-6B.yaml"
  diff "$EA_EASYEDIT/hparams/$M/gpt-j-6B.yaml" "$EA_HPARAMS/${M}_gpt-j-6B.yaml" || true
done
md5sum "$EA_HPARAMS"/*gpt-j-6B.yaml

echo "== 4/4 load check (CPU)"
CUDA_VISIBLE_DEVICES="" python - <<PY
import sys, time, torch
sys.path.insert(0, "$EA_REPO/experiments/retrieval_poc")
import probe_scoring_v4 as ps
from transformers import AutoModelForCausalLM, AutoTokenizer
t = time.time()
tok = AutoTokenizer.from_pretrained("$MDIR")
model = AutoModelForCausalLM.from_pretrained("$MDIR", dtype=torch.float32).eval()
n = sum(p.numel() for p in model.parameters())
print(f"loaded in {time.time() - t:.0f}s | {type(model).__name__} | params {n/1e9:.3f} B | dtype {next(model.parameters()).dtype}")
print("tokenizer", type(tok).__name__, "| vocab", len(tok), "| BOS prepended by v4:", bool(ps.bos_prefix(tok)))
for name in ["transformer.h.5.mlp.fc_out.weight", "transformer.h.8.mlp.fc_out.weight"]:
    print(name, tuple(model.get_parameter(name).shape))
dev = torch.device("cpu")
print("greedy:", repr(ps.greedy_continuation(model, tok, "The novel Frankenstein was written by", dev, 6)))
s = ps.score_answer(model, tok, "The novel Frankenstein was written by", "Mary Shelley", dev)
print("Mary Shelley: rank", s["first_token_rank"], "P", round(s["sequence_probability"], 4), "tokens", s["answer_tokens"])
PY
du -sh "$MDIR" "$SDIR"
echo "GPT-J FETCH COMPLETE at $(date)"
