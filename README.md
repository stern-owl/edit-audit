# Edit audit: supplementary material

Code, frozen inputs and raw outputs for the PVLDB Vol. 20 vision paper
**"Did the Write Land Everywhere? Auditing Knowledge Edits in Language Models as Database Updates"**.

The paper edits single facts in GPT-2 XL with three methods, ROME, MEMIT and AlphaEdit (via EasyEdit). It then checks every way of asking for the fact: forward questions, paraphrases, reverse questions, and unrelated "neighbour" facts. This repository lets you:

| Level | What it shows | Needs | Time |
|---|---|---|---|
| **L0** | Every number in the paper's Tables 2–3 and findings F1–F5 comes from the shipped raw outputs | Python 3, CPU | seconds |
| **L1** | The scoring, screening, edit-and-restore logic behaves as described (tests on a tiny random model) | Python 3, PyTorch, Transformers, CPU | < 1 min |
| **L2** | Full re-run of all screening and editing experiments | 1 GPU with 16 GB or more, EasyEdit, GPT-2 XL | ~1 h |

## L0: check the paper's numbers (no GPU)

```bash
python experiments/retrieval_poc/check_paper_numbers.py
```
It prints the ROME headline numbers and finding F5 (ranks 510–7387 for the failed first-position edits).

Tables 2 and 3 (all three methods) come from:
```bash
P=experiments/retrieval_poc; R=$P/results
python $P/compare_methods.py \
  --method ROME      $R/study_3462_seed{0,1,2}/deltas.csv $R/study_3467_seed{0,1,2}/deltas.csv \
  --method MEMIT     $R/study_3574_MEMIT_seed{0,1,2}/deltas.csv \
  --method AlphaEdit $R/study_3583_AlphaEdit_seed{0,1,2}/deltas.csv \
  --out /tmp/compare_methods
```
It prints the aggregate counts of Table 2 (e.g. reverse-from-old still rank 1: 20/24, 23/24, 23/24) and, per fact, the neighbour ranks of Table 3. The shipped output is in `results/compare_methods/`. Everything is computed directly from `results/study_*/deltas.csv`.

## L1: offline tests (no GPU, no downloads)

```bash
pip install torch transformers
bash experiments/retrieval_poc/tests/run_tests.sh
```
The tests check four things:
- Full-answer scoring matches a brute-force computation and is deterministic.
- The harness catches an editor that silently undoes its own edit (check B).
- Weights are restored exactly between facts (check C).
- Screening and the per-fact output rows are well formed.

## L2: full re-run (GPU)

1. **EasyEdit.** Clone [EasyEdit](https://github.com/zjunlp/EasyEdit) at commit `431d9bd` and install its requirements in a Python 3.10 environment. Then copy this repo's `experiments/` folder into the EasyEdit root.
2. **Model.** Download GPT-2 XL (`openai-community/gpt2-xl` on Hugging Face) to a local directory.
3. **Hyperparameters.** Use EasyEdit's `hparams/ROME/gpt2-xl.yaml` unchanged, except set `model_name:` to your local GPT-2 XL directory. The original file had md5 `5411d8d45cd21b4295c653bf28cbc5f1`, with `layers: [17]` and `mom2_adjustment: false`, so no Wikipedia covariance statistics are needed. The file as run is included in `environment/`.
4. **Run.** From the EasyEdit root:
   ```bash
   MODEL=/path/to/gpt2-xl GPU_MEM_GB=20 bash experiments/retrieval_poc/reproduce.sh
   ```
   `GPU_MEM_GB` caps PyTorch's share of the GPU. The original runs peaked at about 6 GiB (screening) and 9.2 GiB (editing). Outputs go to `experiments/retrieval_poc/results_rerun/`, and the script ends by printing the same numbers as L0. This covers ROME.
5. **MEMIT and AlphaEdit.**
   - Covariance statistics: `bash experiments/retrieval_poc/fetch_stats.sh` downloads the published GPT-2 XL Wikipedia statistics (5 files, ~800 MB) and checks that EasyEdit accepts them. md5s are in `environment/` and in every log.
   - Hyperparameters: EasyEdit's `hparams/MEMIT/gpt2-xl.yaml` and `hparams/AlphaEdit/gpt2-xl.yaml` with only `model_name` (and, for AlphaEdit, `P_loc`) changed. The files as run are in `environment/`.
   - AlphaEdit projection, computed once on CPU: `python experiments/retrieval_poc/compute_alphaedit_P.py --hparams <AlphaEdit yaml>`.
   - Probes: `bash experiments/retrieval_poc/make_main_probes.sh` builds the 12-fact set.
   - Runs, one process per seed:
     ```bash
     python experiments/retrieval_poc/run_method_study.py --method MEMIT --hparams <MEMIT yaml without .yaml> --probes-dir <results>/main_probes --seed $s
     ```
     Do the same with `--method AlphaEdit`.
   - The Slurm versions are `slurm/run_method_study.sh` (48G RAM, 24 GiB GPU cap; MEMIT/AlphaEdit peaked at 7.6 GiB) and `slurm/run_compute_P.sh`.

The `slurm/` scripts are the exact job scripts used on our cluster (one MIG slice, `--mem=24G`/`32G`). They contain our absolute paths and are provided for provenance; `reproduce.sh` is the portable equivalent.

### What to expect from a re-run
- **Same hardware and software versions:** identical numbers. Every run reads each prompt twice and requires bit-identical scores (check A).
- **Other GPUs or library versions:** small floating-point differences in log-probabilities, with ranks normally unchanged. ROME samples random context prefixes, so each seed runs in its own process with a fixed seed.
- **Screening** is deterministic: it uses no edits and no sampling.

## How the experiment works

1. **Screening** (`screen_facts.py`) builds each fact's questions from fixed per-relation templates and scores them on the unedited model. It keeps a question only if the model answers it correctly before the edit, using the rules in `relation_templates*.json`. These rules were written before any edit was run.
2. **Editing** (`run_fact_study.py`, shared helpers in `rome_paired_pilot.py`) applies, per fact and seed: read all questions, save the weights, edit, read again, restore, read a third time. It refuses to save results unless three checks pass:
   - (A) repeated reads are identical;
   - (B) the edited weights actually changed;
   - (C) restoring reproduces the original reads exactly.
3. **Scoring** (`probe_scoring.py`) records each answer's full-answer log-probability, its first-token rank, and a greedy continuation.
4. **Analysis** (`analyze_study.py`) reports each fact and question separately, valid questions only, with no averaging across facts.

## Provenance: which run produced what

| Paper element | Run | Inputs | Outputs |
|---|---|---|---|
| Screening, templates v1 | job 3461 | `candidate_facts_v2.csv`, `relation_templates.json` | `results/screen_3461/`, `logs/screen_facts_3461.out` |
| Table 2 novels + invention; F5 (failed company edits) | job 3462, seeds 0–2 | `results/screen_3461/probes/` | `results/study_3462_seed*/`, `logs/fact_study_3462_seed*.out` |
| Screening, templates v2 | job 3466 | `relation_templates_v2.json` | `results/screen_3466/`, `logs/screen_facts_3466.out` |
| Table 2 companies (ROME) | job 3467, seeds 0–2 | `results/screen_3466/probes_company/` | `results/study_3467_seed*/`, `logs/fact_study_3467_seed*.out` |
| AlphaEdit projection matrix | job 3576 | covariance statistics | `logs/alphaedit_P_3576.out` (md5 of the matrix) |
| Tables 2–3, MEMIT | job 3574, seeds 0–2 | `main_probes` (12 facts, built by `make_main_probes.sh`) | `results/study_3574_MEMIT_seed*/`, `logs/method_study_3574_seed*.out` |
| Tables 2–3, AlphaEdit | job 3583, seeds 0–2 | same | `results/study_3583_AlphaEdit_seed*/`, `logs/method_study_3583_seed*.out` |

Job 3577 (a first AlphaEdit attempt) stopped at an import error before any edit was made. EasyEdit's `easyeditor.models` attribute is shadowed by `easyeditor.trainer.models`. `run_method_study.py` v1.1 fixes this; its logs are in `logs/failed_3577_alphaedit_import/`. The MEMIT logs record v1 of the script, which differs from v1.1 only in that AlphaEdit-only import line.

AlphaEdit keeps a record of earlier edits between calls (`cache_c`) to protect them. Because every fact is restored before the next one, `run_method_study.py` clears that record before each edit, so all facts are edited from the same starting point. This is logged as `alphaedit_cache_reset` in each run's manifest.

Each log prints the md5 of every script, the hyperparameter file and every probe file it used. `CHECKSUMS.md5` lists the md5 of every file in this repository, so you can confirm the shipped scripts are byte-identical to the ones in the logs (`md5sum -c CHECKSUMS.md5`).

`relation_templates_v2.json` was written after job 3462 and before any v2 scoring. It records the hypothesis and the prediction that job 3467 then tested.

## Limitations
One model (GPT-2 XL), three editing methods with EasyEdit's default settings (ROME without covariance statistics; MEMIT and AlphaEdit with them), 12 included facts over three relations (only one invention), three seeds, single-fact edits only. Reads use first-token ranks of the canonical tokenisation.

## License
Code: MIT (see `LICENSE`). The fact list and templates are original and released under the same license. GPT-2 XL and EasyEdit are under their own licenses and are not redistributed here.
