# 2026-10-31 · 01 · Baseline review of draft, repo and suggestions

**Plan items:** 0.1 (done), 0.2 (raised)

## Goal
Understand the state of the project inherited from the colleague before extending it.

## Inputs read
- `Auditing_Knowledge_Edits_in_Language_Models_as_Database_Updates__Vision_.pdf` (6 pages, PVLDB Vol. 20 vision draft;
  authors Yash Aggarwal, Aadit Shah, Yash Sinha).
- `next-steps.txt` (ChatGPT's suggestions, 8 experiments + roadmap).
- `edit-audit/` repo: README, all scripts under `experiments/retrieval_poc/`, hparams in `environment/`,
  `results/compare_methods/aggregate.csv`. Git log: `6e99030` (supplementary material), `d774397` (MEMIT/AlphaEdit, Tables 2–3).

## State of the draft
- **Framing:** an edit is a database UPDATE; audit asks Q1 write visibility, Q2 stale reads, Q3 side effects, per fact and per access path, no averaging.
- **Layer:** access-path catalogue (fixed templates per relation) → pre-registered screening (keep only paths the unedited model answers) → verified edit run (checks A/B/C) → path-level report.
- **Setup:** GPT-2 XL; ROME (layer 17, no covariance stats), MEMIT and AlphaEdit (layers 13–17, Wikipedia stats), EasyEdit defaults; 18 candidate facts → 12 admitted (6 novels, 5 companies, 1 invention); 10 paths per fact; 3 seeds; 117 edit runs, all passed A/B/C.
- **Findings (Table 2, `aggregate.csv`):**
  - Edited question: new object rank 1 for 12/12 facts under every method.
  - Q1 paraphrase/context new object rank 1 in every seed: novels+invention 19/19 (ROME), 17/19 (MEMIT, AlphaEdit); companies 8/13, 3/13, 6/13.
  - Q2 reverse-from-old, subject still rank 1 every seed: 20/24 ROME, 23/24 MEMIT, 23/24 AlphaEdit.
  - Q3 reverse-from-new, subject less likely: 23/24 all methods. Neighbours keep correct answer: 22/22. New object enters top 5 on same-relation neighbour: 4/12 (all companies), e.g. Amazon→Zuckerberg moves Zuckerberg 36 → 2 on Microsoft.
  - RQ4: company edits with subject at prompt position 0 failed under ROME (new object rank 510–7387, neighbours damaged); rewording fixed them; cause not isolated (position and wording changed together).

## Code observations relevant to the plan
- `GPT2Tokenizer` hard-coded in `screen_facts.py`, `run_fact_study.py`, `run_method_study.py`, `rome_paired_pilot.py`, `compute_alphaedit_P.py` (`GPT2LMHeadModel`).
- Default paths point at `/localstorage/home/f20220930/...` in four scripts.
- `probe_scoring.score_answer` tokenises prompt and `" " + answer` separately with `add_special_tokens=False`: correct for GPT-2; for Llama-3 the BOS token is missing, so scores would be wrong without error.
- `run_one_fact` always restores weights after each fact; sequential editing needs a new driver. `run_method_study.py` deliberately resets AlphaEdit's `cache_c_new` before each edit; a sequential run must not.
- Side effects are measured only as the rank/log-prob of named candidates; logits for the full vocabulary are already computed in `score_answer`, so full-distribution KL/JS is a small addition.
- `fetch_stats.sh` downloads GPT-2 XL stats for layers 13–17, which includes ROME's layer 17, so ROME-with-stats needs no new download.

## Assessment of `next-steps.txt`
- **Agree:** the gaps (one model, 12 facts, single edits); top three priorities (sequential, cross-model, distributional).
- **Verified citations** (web search 2026-10-31):
  - Simon & Ewetz, "Beyond Single Edits: Rethinking Knowledge Editing Evaluation with Multi-Edit Entities and Undirected Probing", Findings of EMNLP 2026, https://aclanthology.org/2026.findings-emnlp.43/ (repo: https://github.com/dominic-simon/SEED-KE-Benchmark). Details of their results not yet read.
  - Pohl, Ploner, Akbik, "Towards a Principled Evaluation of Knowledge Editors", L2M2 @ ACL 2025, https://aclanthology.org/2025.l2m2-1.4: metric, methodology and batch size can reorder editors.
- **Missing from the suggestions:**
  1. Venue/scope decision (D1).
  2. ROME-without-stats vs MEMIT/AlphaEdit-with-stats confound (plan 1.1).
  3. Two causes the paper leaves untested: position 0 (1.3) and shared company template (1.4).
  4. CounterFact as the concrete route to 100+ facts; screening admitted 12/18, so expect ~1,000 candidates for 100–300 admitted.
- **Deprioritised:** human-annotated natural questions, synthetic false-positive cases, instruction-tuned models (see `plan.md`).

## Cluster check
See `decisions.md` D2 and `environment.md`. Passwordless SSH to `bits-cluster` works as user `yashsinha` (CSIS, A100, Slurm). No jobs submitted pending confirmation that this account may be used.

## Next
- User to resolve D2.
- Meanwhile, local work that needs no GPU: plan 2.1 (port harness) and 1.2 (distributional metrics) with offline tests; requires CPU `torch` + `transformers` installed locally.
