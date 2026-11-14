#!/usr/bin/env python3
"""Compute AlphaEdit's null-space projection matrix P once for ANY causal LM and save it to hparams.P_loc.

compute_alphaedit_P.py (v1) stays unchanged for provenance; it is GPT-2 specific (GPT2LMHeadModel). v2 loads the
model with AutoModelForCausalLM and calls EasyEdit's own get_project for every edited layer, so the numerics are
exactly EasyEdit's (CPU SVD of each layer's covariance, singular values below nullspace_threshold kept). The matrix
size is taken from get_project's output instead of guessing it from the weight layout (Conv1D vs Linear).
EasyEdit's own fallback writes "null_space_project.pt" into the working directory instead of P_loc; v2 writes P_loc.
Needs the covariance statistics; no forward passes are run when they exist.
"""
import argparse
import hashlib
import sys
import time
from pathlib import Path

import torch

ap = argparse.ArgumentParser()
ap.add_argument("--hparams", required=True)
a = ap.parse_args()

from easyeditor import AlphaEditHyperParams
from easyeditor.models.alphaedit.AlphaEdit_main import get_project
from transformers import AutoModelForCausalLM, AutoTokenizer

hp = AlphaEditHyperParams.from_hparams(a.hparams)
if Path(hp.P_loc).exists():
    sys.exit(f"{hp.P_loc} already exists; delete it first if you really want to recompute.")
hp.device = "cpu"
print("torch threads", torch.get_num_threads(), "| layers", hp.layers, "| threshold", hp.nullspace_threshold, flush=True)
model = AutoModelForCausalLM.from_pretrained(hp.model_name, dtype=torch.float32).eval()
tok = AutoTokenizer.from_pretrained(hp.model_name)
blocks = []
for layer in hp.layers:
    t = time.time()
    blocks.append(get_project(model, tok, layer, hp))
    d = blocks[-1].shape[0]
    print(f"layer {layer}: projection rank {int(torch.round(torch.trace(blocks[-1])).item())} of {d} "
          f"({time.time() - t:.0f}s)", flush=True)
P = torch.stack(blocks)
Path(hp.P_loc).parent.mkdir(parents=True, exist_ok=True)
torch.save(P, hp.P_loc)
h = hashlib.md5()
with open(hp.P_loc, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 24), b""):
        h.update(chunk)
print("saved", hp.P_loc, tuple(P.shape), h.hexdigest())
