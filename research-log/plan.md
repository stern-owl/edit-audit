# Work plan

Status: `todo` · `in progress` · `done` · `blocked (reason)` · `dropped (reason)`.
Entry links point to `entries/`. Venue (Vision vs research track) is deliberately deferred;
the plan is ordered so that phases 1–2 are useful under either choice.

## Phase 0: setup

| # | Item | Status | Entry |
|---|---|---|---|
| 0.1 | Read draft, repo and ChatGPT suggestions; write baseline review | done | [01](entries/2026-10-31_01_baseline-review.md) |
| 0.2 | Confirm which cluster account to use | done (D2) | [02](entries/2026-10-31_02_cluster-setup.md) |
| 0.3 | Set up own EasyEdit env on the cluster (EasyEdit commit `431d9bd`, Python 3.10, torch/transformers as in `edit-audit/environment/versions.txt`) | done (jobs 16972, 16975) | [02](entries/2026-10-31_02_cluster-setup.md) |
| 0.4 | Re-run GPT-2 XL baseline on the new GPUs (A100, not H100 MIG) and compare against shipped `deltas.csv` | **done**: reproduces exactly (0 rank/text differences; Tables 2–3 identical) | [02](entries/2026-10-31_02_cluster-setup.md) |

## Phase 1: cheap wins on GPT-2 XL

| # | Item | Status | Entry |
|---|---|---|---|
| 1.1 | ROME with covariance statistics (`mom2_adjustment: true`, layer 17 stats already fetched by `fetch_stats.sh`) to remove the ROME-vs-MEMIT/AlphaEdit confound | **done** (stale 22/24) | [04](entries/2026-10-31_04_phase1-gpt2xl.md) |
| 1.2 | Distributional side-effect metrics on every neighbour/control read: full-vocabulary next-token KL and JS (pre vs post), ΔP and Δrank of the new object; candidate-set version reported separately | **done** (E3, RESULTS §6) | [03](entries/2026-10-31_03_audit-driver-and-scorer-v4.md) |
| 1.3 | Ablation: subject at position 0 vs not, with wording held fixed (isolates the RQ4 cause the paper leaves open) | todo | |
| 1.4 | Ablation: neighbour drift under several neighbour templates (tests "shared company template" explanation in RQ3) | todo | |

## Phase 2: generalisation

| # | Item | Status | Entry |
|---|---|---|---|
| 2.1 | Port harness to any HF causal LM: `AutoTokenizer`/`AutoModelForCausalLM`, correct BOS handling, answer-tokenisation convention per tokenizer, no hard-coded paths; offline tests on a tiny Llama-style model | **done** (E1 identical) | [03](entries/2026-10-31_03_audit-driver-and-scorer-v4.md) |
| 2.2 | Fact set from CounterFact (+ own relations): per-relation reverse templates, pre-registered screening; target 100–300 admitted facts over 5–8 relations | **done** (78 GPT-2 XL / 128 GPT-J admitted; facts await human check) | [06](entries/2026-10-31_06_fact-set-v3-and-screening.md) |
| 2.3 | Relation cardinality declared per relation (1:1, N:1, N:M) and used to label reverse reads as violation vs legitimate | **done** (RESULTS §4.4) | [06](entries/2026-10-31_06_fact-set-v3-and-screening.md) |
| 2.4 | Second model: GPT-J 6B (published stats, all three methods have hparams) | **done** (128 facts, 3 methods; RESULTS §5) | [05](entries/2026-10-31_05_gptj-fetch.md) |
| 2.5 | Modern model: Llama-3-8B or Qwen2.5-7B (covariance stats must be computed; check memory/precision) | todo | |

## Phase 3: multi-edit consistency

| # | Item | Status | Entry |
|---|---|---|---|
| 3.1 | Sequential driver: apply edits without restoring, re-audit all earlier edits after each new one, single restore + check C at the end; keep AlphaEdit's `cache_c` (not reset) | **done** (E7v2) | [03](entries/2026-10-31_03_audit-driver-and-scorer-v4.md) |
| 3.2 | Batch editing (MEMIT, AlphaEdit) on the same fact sets | code written, not run | [03](entries/2026-10-31_03_audit-driver-and-scorer-v4.md) |
| 3.3 | Persistence: does an edit that passes Q1–Q3 still pass after k later edits? | **done** (E7v2, RESULTS §7) | [07](entries/2026-10-31_07_v3-audits-and-sequential.md) |

## Phase 4: audit vs conventional evaluation

| # | Item | Status | Entry |
|---|---|---|---|
| 4.1 | Run EasyEdit/CounterFact standard metrics on the same edited models; failure-detection table | todo | |
| 4.2 | Failure taxonomy per method (incomplete write, stale association, inverse inconsistency, locality interference, update corruption, rollback failure) | todo | |
| 4.3 | Related-work update: SEED (Findings EMNLP 2026), Pohl et al. 2025 | todo | |

## Phase 5: next experiments (designs in `NEXT_EXPERIMENTS.md`, written 2026-10-31)

| # | Item | Status | Entry |
|---|---|---|---|
| 5.1 | E10 audit vs standard metrics on the same edits (no GPU) | **done** (P9.6, P9.7) | 09 |
| 5.2 | E13 automatic Wikidata check of the 187 hand-written facts | todo | |
| 5.3 | E8s seeds 1–2 for E4 (GPT-2 XL) and E5 (GPT-J) | todo | |
| 5.4 | E8 batch editing as one transaction (same 60 + 18 as E7v2) | todo (code ready) | |
| 5.5 | E9a position-0 ablation with identical wording; E9b neighbour drift across templates | todo | |
| 5.6 | E6 modern 7–8B model (= plan 2.5) | blocked (decision D4) | |
| 5.7 | E11 inverse-index repair (new) | todo (target rule needs agreement) | |
| 5.8 | E12 durability under int8/4-bit quantization (new) | todo | |
| 5.9 | E14 natural-language paths | todo | |
| 5.10 | E15 more orders and longer sequences | todo | |

## Phase 6: novelty-driven experiments (`NOVELTY_AND_NEW_EXPERIMENTS.md`, 2026-11-05)

| # | Item | Status | Entry |
|---|---|---|---|
| 6.1 | N3 audit planning: cost-based path selection, transfer across models/methods (no GPU) | **done** (P9.1-P9.3) | 09 |
| 6.2 | N2 admission control: constraint check, violation predictors (no GPU); cascading repair (GPU) | offline part **done** (P9.4, P9.5); cascading repair GPT-2 XL **done** (18047, 18243) | 09, 11 |
| 6.3 | N1 commutativity and conflict-serializability of edit pairs | GPT-2 XL **done** (P10.1-P10.5); GPT-J open | 10 |
| 6.4 | N5 compensating edits vs physical undo | GPT-2 XL **done** (18047, 18243) | 11 |
| 6.5 | N4 atomicity of batched edits (replaces 5.4) | todo | |
| 6.6 | N6 durability under quantization, incl. edit/quantize order (replaces 5.8) | todo | |
| – | 5.7 (E11 inverse-index repair) and 5.10 (E15) | dropped (prior work: BIRD; crowded sequential literature) | |

## Deprioritised (from `next-steps.txt`), revisit after phase 3

- Human-annotated natural-language questions (Exp 4): replace with CounterFact paraphrases plus a small LLM-generated, manually checked set.
- Synthetic false-positive cases (Exp 7): use naturally failing edits (e.g. position-0 company edits) as negatives instead.
- Instruction-tuned models: edit prompts are completions; only if a reviewer-facing reason appears.
