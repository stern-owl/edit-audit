# Experiments: what we run, why, and what is new over the draft

_Living document. Last updated 2026-10-31 ~13:20 IST. **All results in detail: `RESULTS.md`. Next experiments (E6, E8–E15): `NEXT_EXPERIMENTS.md`.** Live job status is in `STATUS.md`; the step-by-step record with
every number and every problem is in `entries/`. This file is the map: one section per experiment, written so that the
paper's experimental section can later be drafted from it._

---

## 1. The draft in one paragraph (baseline we build on)

The PVLDB Vision draft "Auditing Knowledge Edits in Language Models as Database Updates" treats a knowledge edit
(s, r, o → o*) as a database UPDATE and audits it per **access path** (a prompt template + direction + expected answer)
with three questions: **Q1 write visibility** (do forward paths return o*?), **Q2 stale reads** (does any path still return
o?), **Q3 side effects** (what else changed?). The audit layer has four stages: an access-path catalogue (fixed templates per
relation), **pre-registered screening** (keep only paths the unedited model answers), **verified edit runs** (check A:
repeated reads identical; B: the edit changed the weights; C: restoring the weights reproduces the original reads), and a
**path-level report** (no averaging across facts). Experiments: GPT-2 XL; ROME, MEMIT, AlphaEdit (EasyEdit defaults);
18 candidate facts → 12 admitted (6 novels, 5 companies, 1 invention); 10 paths per fact; 3 seeds; independent single
edits; 117 edit runs. Main findings: every edit succeeds on the edited question, yet the old subject is still rank 1 on
20/24 (ROME) and 23/24 (MEMIT, AlphaEdit) reverse-from-old paths; the new object climbs to rank ~2 on another company's
founder question while that question's correct answer stays first (Amazon→Zuckerberg: 36 → 2 on Microsoft).

## 2. What is new, at a glance

| Dimension | Draft | Phase 2 (this work) | Experiment |
|---|---|---|---|
| Reproducibility | one run on H100 MIG | full independent re-run on A100, row-by-row comparison with shipped outputs | E0 |
| Harness | GPT-2-specific (`GPT2Tokenizer`, no BOS) | model-agnostic scorer v4 + audit driver, proven equivalent to the draft's code on GPT-2 XL before use | E1 |
| Method comparison | ROME without covariance statistics vs MEMIT/AlphaEdit with them (confound acknowledged in the draft) | adds ROME **with** statistics | E2 |
| Side effects | rank of one candidate, log-prob change | + full-vocabulary KL / JS / TV / top-10 overlap; + divergences over the route's answer set; ΔP and Δrank of o* | E3 |
| Facts | 12 admitted, 3 relations, hand-picked | 316 candidates, 7 relations, deterministic construction, CounterFact P36 + hand-written + the draft's 18 | E4 |
| Consistency semantics | informal ("a novel has one author") | **declared per-relation cardinality and a consistency contract** that says which reads are violations and which are legitimate | E4 |
| Neighbours | 1 per fact, "first eligible" | 2 per fact, hash-chosen (no fact becomes everyone's neighbour) | E4 |
| Models | GPT-2 XL | + GPT-J 6B; + one modern 7–8B model (decision pending) | E5, E6 |
| Edit schedule | independent only (restore after every fact) | + **sequential** (edits accumulate; every fact re-audited after each edit) + **batch** | E7, E8 |
| Causal checks | position-0 cause and template cause left open | ablations that isolate each | E9 |
| Value over existing evaluation | one paragraph (RQ4) | the same edited models scored by EasyEdit / CounterFact metrics vs the audit; failure taxonomy | E10 |
| Infrastructure | colleague's cluster scripts | isolated CSIS A100 environment, pinned code snapshots per job, verified env (identical pip freeze, identical statistics md5s) | §3 |

What stays the same on purpose: the three audit questions, the four-stage layer, screening rules (frozen, identical
thresholds), checks A/B/C, per-fact reporting, the draft's templates for its three relations, EasyEdit commit `431d9bd`
and the draft's hparams. Every original file of the shipped artefact is byte-identical (`CHECKSUMS.md5` verified on the
laptop and in every cluster snapshot); all new code is in new files.

## 3. Shared infrastructure and rules (apply to every experiment)

**Compute.** BITS CSIS cluster, account `yashsinha` (shared; caps 64 CPU, 2 GPU, 200 GB RAM, 5 running jobs), all files
under `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/` (= `EA_ROOT`). NVIDIA A100 80 GB, AMD EPYC 7502 CPUs.
Python 3.10.22, torch 2.9.1+cu128, transformers 5.5.4 (pip freeze identical to the original run), EasyEdit `431d9bd`.
Details: `environment.md`.

**Provenance.**
- Every job runs from a **pinned code snapshot** (`repo_snapshots/<timestamp>`) in a private working directory, prints the
  md5 of every script, hparams file and probe file it uses, and writes to `runs/<plan-item>_<desc>_<jobid>/`.
- Model weights pinned to a Hugging Face revision (`models/<name>/SOURCE.txt`); statistics and projection matrices md5-logged.
- Predictions are written into the log **before** the job that tests them is submitted. Negative results are reported.

**Verification of every edit run.** Checks A, B, C as in the draft; nothing from a run with a failed check is used.
The new driver adds: B is checked per edit call against the weights just before that call (needed once edits
accumulate), and the driver refuses to read if the editor returns a different model object.

**Statistics.** Results per fact and per path; aggregates are counts of paths. Uncertainty is reported across facts
(bootstrap over facts), never treating seeds as independent facts.

---

## 4. Experiments

Each experiment lists: the question, what is new compared with the draft, the design, the prediction made before
running (where applicable), the code and jobs, and the status.

### E0. Reproduction of the draft on new hardware (plan 0.4)
- **Question.** Do the draft's numbers survive a full re-run on different GPUs (A100 instead of H100 MIG), a different CPU
  (AMD EPYC), a freshly built environment and a GPT-2 XL download whose revision we pinned (the original did not record it)?
- **New over the draft.** The draft's reproducibility claim ("same hardware: identical numbers; other GPUs: small
  floating-point differences, ranks normally unchanged") had never been tested on other hardware.
- **Design.** ROME: the draft's own `reproduce.sh`, unchanged (screen v1 → edit 3 seeds → screen v2 → edit companies 3 seeds →
  `check_paper_numbers.py`). MEMIT and AlphaEdit: the draft's `run_method_study.py` on the shipped 12-fact probes, seeds 0–2.
  Then `compare_to_shipped.py` matches every output row with the shipped file: screening reports, Table 2
  (`aggregate.csv`), Table 3 (`per_fact.csv`), and all 18 `deltas.csv` files.
- **Prediction (before the run).** Identical ranks, validity flags, Table 2 and Table 3; log-probabilities may differ in
  the last digits.
- **Result: DONE, prediction confirmed.** The draft's own `check_paper_numbers.py` prints **identical** output for the shipped
  and the re-run results (Table 2, findings F1–F5). Row by row: Table 2 and Table 3 sources identical; 2,646 delta rows and
  both screening reports with **0 rank, 0 text (incl. greedy continuations) and 0 row differences**; log-probability drift
  ≤ 2×10⁻⁵ before and ≤ 2.6×10⁻⁴ after editing. Environment: pip freeze identical, statistics md5 identical; AlphaEdit
  projection bit-different (same per-layer ranks) with no visible effect.
- **Found along the way:** the shipped `check_paper_numbers.py` needs Python ≥ 3.12 (nested same-quote f-string, line 69),
  although the artefact documents Python 3.10. To fix when the artefact is next published.
- **Paper use.** A reproducibility statement: the audit's verdicts are hardware-independent at rank level.
- **Code / jobs.** `cluster/csis/baseline_rerun.sbatch`, `baseline_finish.sbatch`, `compare_to_shipped.py`; jobs 16978
  (MEMIT/AlphaEdit), 16987 (ROME), 16992 (finish). Results copied to `results/E0_baseline_a100_16987/`. Entry 02.

### E1. Equivalence of the new harness with the draft's code (plan 2.1 validation)
- **Question.** Does the model-agnostic driver (`run_audit.py` + scorer v4) reproduce the draft's measurements exactly
  where it should?
- **New over the draft.** The draft's scorer cannot read Llama-3 correctly (it drops the BOS token) and its scripts load
  only GPT-2. Before any cross-model claim, the replacement must be shown not to change GPT-2 XL results.
- **Design.** GPT-2 XL, shipped 12-fact probes, ROME/MEMIT/AlphaEdit with the draft's hparams, seeds 0–2, `--mode independent`.
  Compare every shared column with (a) the A100 re-run of the draft's code (E0) and (b) the shipped H100 results.
- **Prediction.** (a) identical numbers (same GPU, same token ids under the fast and slow GPT-2 tokenizers, same forward
  pass); (b) identical ranks. If either fails, nothing from the new driver is used until the cause is found.
- **Already shown offline** (job 16981, tiny random models): v4 = v3 field for field on GPT-2-style tokenizers; with a
  BOS-adding tokenizer on a tiny Llama, v4 prepends BOS and equals a brute-force log-probability.
- **Result: DONE, confirmed.** vs the A100 re-run of the draft's code: all 9 runs IDENTICAL (max |Δ| = 0); vs shipped:
  same ranks and text. The new driver is validated for all later experiments.
- **Code / jobs.** `probe_scoring_v4.py`, `run_audit.py`, `cluster/csis/phase1_gpt2xl.sbatch`; job 16994. Entries 03, 04.

### E2. ROME with covariance statistics (plan 1.1)
- **Question.** Are the draft's findings an artefact of running ROME without the covariance statistics that MEMIT and
  AlphaEdit use?
- **New over the draft.** The draft states this confound in its limitations but does not test it.
- **Design.** The draft's ROME hparams with only `mom2_adjustment: false → true` (layer-17 statistics, md5 identical to
  the original), same facts, probes, seeds and driver as E1.
- **Predictions (before the run).** P1: the edited question still succeeds on 12/12. P2: subject still rank 1 in every seed
  on ≥ 20/24 reverse-from-old paths (the stale-read finding survives). P3 (no direction committed): count of company
  neighbours where the new object enters the top 5 (draft 4/12), reported as observed.
- **Result: DONE.** P1 (12/12) and P2 (stale reverse reads 22/24) confirmed: the draft's finding is not a
  statistics artefact. New: with statistics ROME's forward profile equals AlphaEdit's (paraphrase 23/32, forward old
  still rank 1 9/32), so the draft's ROME-vs-others difference in visibility comes from the statistics.
- **Code / jobs.** Same job as E1 (16994). Entry 04.

### E3. Distributional side effects (plan 1.2)
- **Question.** How much does an edit change the model's answer distribution on facts it should not touch, beyond the
  rank of one candidate?
- **New over the draft.** The draft's Q3 reports whether the correct neighbour answer stays first and how far o* rises.
  E3 adds, for every read (all routes, not only neighbours):
  - **Full-vocabulary next-token divergence** between the unedited and edited model at the end of the prompt:
    KL(pre‖post), KL(post‖pre), Jensen–Shannon (bits, ∈ [0, 1]), total variation, argmax change, top-10 overlap.
  - **Answer-set divergence:** the same quantities over the route's candidate answers after renormalising each answer's
    full-answer probability within the set (the "clearly defined answer set" version, kept separate from the
    full-vocabulary one so a rank change is never mistaken for a distribution change).
  - **ΔP(o* | q) and Δrank(o*, q)** on unrelated prompts (already in the deltas: the `edit_leak` answer of control routes).
  Zero-probability tokens are handled with 0·log 0 = 0 (found and fixed while testing: masked vocabulary slots
  would otherwise give NaN).
- **Design.** Comes out of every `run_audit.py` run (`dist.csv`); first data from E1/E2 on GPT-2 XL, then every model.
- **Analysis planned.** Distribution of JS/KL on neighbours by method; relation between "correct answer still rank 1"
  (a standard specificity pass) and the size of the distribution shift; whether a pass co-occurs with large shifts.
- **First results (E4, GPT-2 XL, 78 facts):** neighbours keep their correct answer on 92–98% of reads (a standard
  specificity check passes), yet 84% (ROME), 32% (MEMIT), 37% (AlphaEdit) of those passing reads shift by JS > 0.01 bit;
  median neighbour JS 0.073 (ROME) vs 0.005 (MEMIT, AlphaEdit). GPT-J ROME: median neighbour JS 0.18.
- **Code / jobs.** `probe_scoring_v4.next_token_shift`, `candidate_shift`; `analyze_audit.py`; jobs 16994, 16995, 16997.
  Entries 03, 04, 07.

### E4. Larger fact set with declared relation semantics (plans 2.2, 2.3)
- **Question.** Do the findings hold over hundreds of facts and more relations, and can the audit tell real violations
  from legitimate behaviour once relation cardinality is declared?
- **New over the draft.**
  - **Scale and breadth:** 316 candidates over 7 relations (draft: 18 over 3).
  - **Existing dataset:** CounterFact P36 (capitals) used exactly as published.
  - **Finding about the method:** most CounterFact relations cannot be audited in the reverse direction (their objects
    have thousands of subjects), which is why only P36 is usable; recorded in entry 06.
  - **Consistency contract** (frozen in `relation_templates_v3.json` before scoring): edits are UPDATEs; a reverse read
    from the old object that still returns s is a stale read for **every** relation (so co-founders etc. do not excuse
    Q2); reverse-from-new must reach rank 1 only for 1:1 relations (capital, currency) and must at least rise otherwise;
    for 1:1 relations the edit request itself violates the constraint (o* would have two subjects) and is flagged.
  - **Neighbours:** two per fact, hash-chosen.
- **Relations.** novel_author (54), company_founder (33), invention_inventor (26) [draft templates]; country_capital (111,
  CounterFact P36, 33 duplicate-capital groups); painting_painter (32); character_creator (29); country_currency (31).
- **Construction** (`build_candidates_v3.py`, deterministic): draft facts verbatim; hand-written facts get their new object
  by a seeded cyclic shift within the relation (each new object is another fact's true object; no swaps; the
  new-object control always exists); CounterFact facts keep their published counterfactual. Facts whose subject contains
  the object's name are dropped (28). Duplicate capitals are resolved at screening by a pre-edit rule.
- **Screening** (`screen_facts_v4.py`): the draft's rules unchanged; per model; outputs frozen probe files that every later
  experiment on that model reads.
- **Open item.** The 187 hand-written facts must be checked by a person before results on them are reported.
- **Screening results so far.** GPT-2 XL: **78/316 included** (novels 30, companies 18, capitals 13, currencies 9,
  characters 6, inventions 2, paintings 0). **GPT-J: 128/316 included** (novels 44, companies 27, characters 20, capitals 17,
  inventions 14, paintings 5, currencies 1; 16 of the draft's 18 facts). Currency on GPT-J fails on the forward template
  (likely " Japanese yen"), not on knowledge. Paintings fail on GPT-2 XL
  because the model continues "was painted by" with " the artist …", so the painter's first token ranks low (a template
  artefact of the first-token rule, not missing knowledge); borderline facts can be excluded because their *neighbour*
  is unknown. A pre-edit revision (neighbours only from known facts; article-tolerant painting/invention templates) is
  proposed in entry 06 and awaits a decision.
- **Decision (D5, user):** v3 stays frozen, no re-screening; one seed for large runs.
- **Audit at scale (job 16995, queued after E1):** GPT-2 XL, 78 facts, ROME/MEMIT/AlphaEdit, independent, seed 0.
  Predictions P4.1–P4.5 in entry 07 (incl. contract checks for 1:1 vs non-functional relations).
- **Audit result (GPT-2 XL, 78 facts, seed 0; 95% CI over facts):** edited question succeeds 100% (ROME, AlphaEdit) and
  82% (MEMIT; fails mostly on capitals and currencies). **Stale reverse reads: ROME 57% [48, 66], MEMIT 76% [69, 84],
  AlphaEdit 74% [66, 81]** of valid reverse-from-old paths. Relation contract: the subject reaches rank 1 on 0% of
  reverse-from-new paths and rises on only 4–13%; violations 91–97% overall and 100% on the 1:1 relations.
  Predictions P4.3–P4.5 confirmed; P4.1 fails for MEMIT, P4.2 fails for ROME (57% < 70%).
- **Jobs.** Tests 16989; screening 16990/16991; audit 16995; analysis 17011. Entries 06, 07.

### E5. Cross-model audit: GPT-J 6B (plan 2.4)
- **Question.** Are the stale reverse reads and the neighbour drift properties of knowledge editing, or of GPT-2 XL?
- **New over the draft.** Second architecture/scale (6B, rotary attention, different MLP layout).
- **Design.** GPT-J pinned at revision `47e16930…` (fp32), EasyEdit's own GPT-J hparams (ROME layer 5; MEMIT/AlphaEdit
  layers 3–8 with published statistics), only machine-specific fields changed. Facts: the v3 facts admitted by GPT-J's own
  screening (E4), plus the draft's 12 where admitted. ROME, MEMIT, AlphaEdit; independent mode; seeds 0–2; all E3 metrics.
- **Prediction (to be written before submission):** the draft's main pattern (forward success ⇏ reverse consistency).
- **Prediction (written before submission, entry 07):** edited question succeeds for ≥ 90% of facts; subject still rank 1
  on ≥ 70% of valid reverse-from-old paths for every method.
- **Result (ROME, MEMIT; 128 facts):** edited question 100% for both. **Stale reverse reads: MEMIT 78% [73, 85] (pattern
  holds on GPT-J); ROME 30% [23, 37]**, but ROME pays with collateral damage: neighbours keep their correct answer on only
  68% of reads, the new value enters the top 5 of 32% of neighbours, median neighbour JS 0.18. A low stale-read rate can
  thus come from broad overwriting, which is why Q2 and Q3 must be read together.
- **AlphaEdit on GPT-J (job 17010, after fixing an EasyEdit bug):** edited question 100%; stale reverse reads 78% [73, 85];
  survival of pre-edit rank-1 reverse reads 97%; neighbours correct 98%; median neighbour JS 0.0039. Same pattern as MEMIT.
  P5.1 and P5.2 confirmed for MEMIT and AlphaEdit, P5.2 fails for ROME (30%, by overwriting).
- **Jobs.** 16982 (fetch), 16986 (projection), 16991 (screening), 16997 (audit ROME/MEMIT), 17010 (AlphaEdit), 17013
  (analysis). Entries 05, 06, 07.

### E6. Cross-model audit: a modern 7–8B model (plan 2.5)
- **Design.** As E5. Candidates: **Llama-3-8B** (gated: needs Meta approval + HF token; AlphaEdit evaluates on it) or
  **Qwen2.5-7B** (open; covariance statistics must be computed: GPU-hours + ~20 GB Wikipedia). The scorer already handles
  Llama-3's BOS (E1 offline test).
- **Status.** Waiting for the user's decision (D4).

### E7. Sequential editing and persistence (plans 3.1, 3.3)
- **Question.** When edits accumulate without restoring, do earlier edits stay visible, do stale reads grow or shrink, and
  what happens to facts that were never edited? Does an edit that passes Q1–Q3 right after it is made still pass k edits
  later? (Database view: consistency of committed writes under later writes.)
- **New over the draft.** The draft edits one fact at a time and restores before the next; sequential editing is listed as
  future work. SEED (Findings EMNLP 2026) studies several edits of the same entity; our angle is the per-path audit of
  every earlier edit and every untouched fact after each write.
- **Design.** `run_audit.py --mode sequential`: edits in a recorded order (sorted, and shuffled with several order seeds);
  after each edit the just-edited fact is read; at checkpoints every fact in the set is read (edited and not yet edited);
  one restore and check C at the end. AlphaEdit's record of earlier edits is cleared once at the start and then left to
  accumulate (its intended lifelong mode; verified in EasyEdit's source). Outputs record, per read, whether and when the
  fact was edited, so persistence curves Q1/Q2/Q3(k) can be drawn per fact. First on GPT-2 XL with the 12 draft facts,
  then with the v3 facts, then on GPT-J.
- **First run (job 16996, queued after E1):** GPT-2 XL, the 78 v3 facts admitted by screening, order `shuffle:1`, seed 0,
  all facts re-read at steps 1, 2, 5, 10, 20, 30, 40, 50, 60, 70, 78; AlphaEdit, MEMIT, ROME.
- **Predictions (entry 07):** P7.1 earlier edits lose visibility by the end (most for ROME, least for AlphaEdit);
  P7.2 unedited facts degrade with k; P7.3 stale reverse reads persist (≥ 50% at the end); P7.4 cumulative update norm
  roughly linear for ROME/MEMIT, sub-linear for AlphaEdit.
- **First run (16996) partly valid.** After 78 sequential edits: edits still holding ROME 14/78, MEMIT 51/71, **AlphaEdit
  78/78**; stale reverse reads on edited facts MEMIT 72%, AlphaEdit 72%, ROME 0%, but ROME's 0% is model collapse
  (median JS 0.88, no neighbour answer at rank 1), not consistency. Two errors of mine made the side-effect part
  invalid: commas in `--checkpoints` were eaten by `sbatch --export` (full re-reads only at steps 1 and 78), and with
  no held-out facts every neighbour was itself edited by the end.
- **E7v2 (job 17015):** 60 edited + 18 held-out sentinel facts, full re-reads at 1, 2, 5, 10, 20, 30, 40, 50, 60; controls
  scored only while their fact is unedited (`run_audit.py` v1.2, `analyze_audit.py` v1.1).
- **E7v2 result (job 17015):** after 60 edits, edits still holding ROME 5/60, MEMIT 38/53, **AlphaEdit 60/60**;
  never-edited sentinels keep their answer ROME 0%, MEMIT 72%, AlphaEdit 83%; untouched-neighbour median JS 0.82 / 0.13 /
  0.12; stale reverse reads on edited facts stay ~70–75% for MEMIT/AlphaEdit at every checkpoint. P7.1–P7.3 confirmed
  (ROME's 0% stale = collapse), P7.4 not supported. Full curve table in `RESULTS.md` §7.
- **Status.** 16996 done (partly valid), 17015 done. Entry 07, `RESULTS.md` §7.

### E8. Batch editing (plan 3.2)
- **Question.** Does editing many facts in one call (MEMIT, AlphaEdit) change visibility, stale reads and side effects
  compared with the same facts edited independently or sequentially?
- **Design.** `run_audit.py --mode batch --batch-size B` (EasyEdit `batch_edit`), B ∈ {all, and a few smaller sizes},
  same facts and reads as E7, so independent vs sequential vs batch is a like-for-like comparison.
- **Status.** Code done; runs after E7.

### E9. Causal ablations left open by the draft (plans 1.3, 1.4)
- **E9a, subject at position 0 (RQ4).** The draft's company edits failed when the prompt began with the subject, and
  succeeded after rewording, which changed both position and wording. Planned design: same words, different position:
  "Apple was founded by" vs the identical string preceded by GPT-2's `<|endoftext|>` token (position 1, no new words) vs
  the draft's reworded prompt. ROME on GPT-2 XL, then the other methods/models.
- **E9b, why neighbours drift (RQ3).** The draft suspects the shared company template. Planned design: read each
  neighbour through several templates (statement, question, contextual) and compare the rise of o* across templates.
- **Status.** Designed, not yet implemented.

### E10. Does the audit find what standard evaluation misses? (plans 4.1, 4.2)
- **Question.** The paper's main claim is practical: an engineer using the audit finds failures that standard pipelines
  miss. This must be shown, not argued.
- **Design.** On exactly the same edited models (same runs as E1/E5/E7): compute EasyEdit's metrics (rewrite /
  rephrase accuracy, locality) and CounterFact-style scores (efficacy: P(o*) > P(o); paraphrase; neighbourhood); build a
  failure-detection table per edit: incomplete write, stale association, inverse inconsistency, locality drift, update
  corruption, rollback failure: which evaluation flags which. Use the relation contract (E4) as ground truth for what is a
  violation; report false positives/negatives, and verify a subset of labels by hand.
- **Status.** **Done offline** (entry 09, `results/phase6_offline/`, `phase6_offline.py` v1.1): CounterFact-style ES/PS/NS,
  neighbourhood KL and a BAKE-like reverse efficacy on the eight independent runs; 440 of the 441 edits that pass all three
  standard scores are flagged by the audit. Not yet done: EasyEdit's own metric code on the same edits, rollback failure
  (needs N5), hand verification of a label subset.

---

## 5. How the `next-steps.txt` suggestions map to these experiments

| Suggestion | Where | Notes |
|---|---|---|
| 1. Other architectures | E5, E6 | GPT-J now; modern model pending decision |
| 2. Sequential and batch editing | E7, E8 | code ready |
| 3. Distributional side effects (KL, JS, ΔP, Δrank) | E3 | all four plus TV, top-10 overlap, answer-set version |
| 4. Natural, non-templated questions | not yet | deprioritised: human annotation is expensive; CounterFact paraphrases + a checked LLM-generated set later |
| 5. Relation-specific constraints | E4 | contract frozen before scoring |
| 6. Comparison with existing evaluation | E10 | |
| 7. False positives / negatives of the audit | E10 | uses the contract labels and naturally failing edits (E0's position-0 failures) instead of synthetic cases |
| 8. Failure taxonomy | E10 | |
| Larger fact set (100–300) | E4 | 316 candidates; admitted count after screening |
| Related work (SEED 2026, Pohl et al. 2025) | paper | both verified to exist (entry 01) |
| Added by us, not in the suggestions | E0, E1, E2, E9 | reproduction, harness equivalence, ROME confound, causal ablations |

## 6. Known limitations and open questions (current)
- Hand-written facts unverified by a person (E4).
- Templates are still fixed per relation (no natural-language variation yet).
- Only locate-then-edit methods (ROME, MEMIT, AlphaEdit); no meta-learning or memory-based editors.
- AlphaEdit projection on our CPU differs from the original at the bit level (ranks identical); effect on results measured in E0.
- Venue not decided; the experiment set is ordered so E0–E5 serve a Vision paper and E6–E10 a research-track paper.
