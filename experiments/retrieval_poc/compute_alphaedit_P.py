#!/usr/bin/env python3
"""Compute AlphaEdit's null-space projection matrix P once, exactly as EasyEdit does internally
(get_project for every edited layer), and save it to hparams.P_loc. Needs the covariance statistics
from fetch_stats.sh; no forward passes are run when they exist. CPU is enough (~1 SVD per layer)."""
import argparse, hashlib, sys
from pathlib import Path
import torch

ap = argparse.ArgumentParser()
ap.add_argument("--hparams", required=True)
a = ap.parse_args()

from easyeditor import AlphaEditHyperParams
from easyeditor.models.alphaedit.AlphaEdit_main import get_project
from transformers import GPT2LMHeadModel, GPT2Tokenizer

hp = AlphaEditHyperParams.from_hparams(a.hparams)
if Path(hp.P_loc).exists():
    sys.exit(f"{hp.P_loc} already exists; delete it first if you really want to recompute.")
hp.device = "cpu"
model = GPT2LMHeadModel.from_pretrained(hp.model_name).eval()
tok = GPT2Tokenizer.from_pretrained(hp.model_name)
W = model.get_parameter(f"{hp.rewrite_module_tmp.format(hp.layers[-1])}.weight")
P = torch.zeros((len(hp.layers), W.shape[0], W.shape[0]))
for i, layer in enumerate(hp.layers):
    P[i] = get_project(model, tok, layer, hp)
    print(f"layer {layer}: projection rank {int(torch.round(torch.trace(P[i])).item())} of {W.shape[0]}", flush=True)
torch.save(P, hp.P_loc)
print("saved", hp.P_loc, hashlib.md5(Path(hp.P_loc).read_bytes()).hexdigest())
