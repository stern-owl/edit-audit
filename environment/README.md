# Environment as run (fill from the cluster before publishing)

Files to add here (commands in the repo-preparation notes):
- `pip-freeze.txt`      exact Python package versions of the EasyEdit conda env
- `versions.txt`        Python, torch, transformers, CUDA, GPU, EasyEdit commit
- `ROME_gpt2-xl.yaml`   the hyperparameter file used (md5 5411d8d45cd21b4295c653bf28cbc5f1)
- `gpt2-xl_source.txt`  where the GPT-2 XL weights came from (repo id + revision)

For the MEMIT/AlphaEdit runs, also add:
- `MEMIT_gpt2-xl.yaml`, `AlphaEdit_gpt2-xl.yaml` (from experiments/retrieval_poc/hparams/; AlphaEdit md5 902d223bb2ed9b25cc7fe775435a063f)
- `stats_md5.txt` (written by fetch_stats.sh)
