# 2026-10-31 · 07 · First new experiments: v3 audit (GPT-2 XL, GPT-J) and sequential editing

**Plan items:** 2.2/E4 (audit on the v3 facts), 2.4/E5 (GPT-J), 3.1/3.3/E7 (sequential editing and persistence)

## Decision taken (user, 2026-10-31 ~02:10)
"I don't want to waste much time on reruns, and want to test new things." Therefore:
- **The v3 fact set and its screening stay frozen as they are** (no template or neighbour revision, no re-screening).
  The weaknesses found in entry 06 (painting template, unknown neighbours) are reported as limitations of v3.
- **One seed** (seed 0) for the new large runs. Justification: in the draft and in E0, seeds agreed closely
  (identical rank-1 verdicts across seeds for almost all paths). Seed variance is not re-measured at the new scale.
- Decision D5 in `decisions.md`.

All runs below depend on Phase 1 (job 16994) passing: if the driver does not reproduce the draft's code (E1), these
results are not used.

## Run 1: E4 independent audit on GPT-2 XL, v3 facts
- Facts: the 78 admitted by screening 16990 (`runs/2.2_screen_v3_gpt2-xl_16990/screen/probes`).
- ROME, MEMIT, AlphaEdit with the draft's hparams; `--mode independent`; seed 0; all E3 metrics.
- **Predictions (before the run):**
  - P4.1 The edited question succeeds (new object rank 1) for ≥ 90% of facts under every method.
  - P4.2 The draft's main finding generalises: for every method, the subject is still rank 1 on **≥ 70%** of valid
    reverse-from-old paths (draft: 20/24 = 83% ROME, 23/24 = 96% MEMIT/AlphaEdit).
  - P4.3 For inverse-non-functional relations, the subject becomes **less** likely on the majority of valid
    reverse-from-new paths (draft: 23/24), i.e. the contract's minimum requirement is violated in most cases.
  - P4.4 For the 1:1 relations (capital, currency), the subject reaches rank 1 on reverse-from-new paths in **< 20%** of
    cases, i.e. the inverse-functional requirement is violated in most cases.
  - P4.5 Neighbours keep their correct answer at rank 1 in ≥ 90% of cases (specificity "passes") while full-vocabulary JS
    on those same reads is nonzero; no threshold committed.

## Run 2: E7 sequential editing on GPT-2 XL, v3 facts
- Same 78 facts, edited one after another without restoring, order `shuffle:1` (relations interleaved), seed 0.
- After every edit the just-edited fact is read; all 78 facts are re-read at steps 1, 2, 5, 10, 20, 30, 40, 50, 60, 70
  and 78 (`--reread-gen-tokens 0` for re-reads of facts not edited at that step, to keep cost down).
- AlphaEdit: `cache_c` cleared once at the start, then accumulates (its intended sequential use).
- One restore and check C at the end.
- **Predictions (before the run):**
  - P7.1 Persistence: the fraction of already-edited facts whose new object is still rank 1 on the edit prompt at the
    final step is **lower** than right after their own edit, for all three methods; the drop is largest for ROME and
    smallest for AlphaEdit.
  - P7.2 Unedited facts degrade: the fraction of not-yet-edited facts whose old object is still rank 1 on their edit
    prompt falls as k grows, more for ROME/MEMIT than for AlphaEdit.
  - P7.3 Stale reverse reads do not disappear with more edits: at the final step, among edited facts, the subject is still
    rank 1 on ≥ 50% of valid reverse-from-old paths for every method.
  - P7.4 Cumulative weight-update norm grows roughly linearly in k for ROME and MEMIT, sub-linearly for AlphaEdit.

## Run 3: E5 independent audit on GPT-J 6B, v3 facts
- Facts admitted by GPT-J screening (job 16991). EasyEdit's GPT-J hparams (ROME layer 5 without statistics; MEMIT and
  AlphaEdit layers 3–8 with published statistics; AlphaEdit projection from job 16986). Seed 0; independent mode.
- Waits for 16991 (screening) and 16986 (projection).
- **Predictions (before the run):** P5.1 = P4.1 and P5.2 = P4.2 hold on GPT-J too (forward success does not imply reverse
  consistency on a second architecture/scale).

## Jobs (submitted 02:12, script `cluster/csis/audit_v3.sbatch`, code snapshot `repo_snapshots/20261031-021251`)
| Job | Run | Depends on | Partition / mem |
|---|---|---|---|
| 16995 | Run 1: E4, GPT-2 XL, independent, ROME MEMIT AlphaEdit, seed 0 | afterok 16994 (Phase 1) | gpu-1day, 32 GB |
| 16996 | Run 2: E7, GPT-2 XL, sequential, AlphaEdit MEMIT ROME, seed 0, `--order shuffle:1 --checkpoints 1,2,5,10,20,30,40,50,60,70 --reread-gen-tokens 0` | afterok 16994 | gpu-1day, 32 GB |
| 16997 | Run 3: E5, GPT-J, independent, ROME MEMIT AlphaEdit, seed 0 | afterok 16994, 16991, 16986 | gpu-1day, 64 GB |
Outputs: `runs/<LABEL>_<model>_<mode>_<jobid>/<method>/audit_<LABEL>_<model>_<method>_<mode>_seed0/`.

## Analysis tool: `experiments/retrieval_poc/analyze_audit.py` v1.0 (new)
The draft's `analyze_study.py` / `compare_methods.py` handle independent single edits only. The new script reads any
`run_audit.py` output and writes `report.md` + `summary.csv`:
- **Independent:** per method × relation (and grouped by inverse cardinality): edit_ok, para_new1, fwd_old1, rev_old_stale,
  rev_new_rank1, rev_new_rises, **rev_new_violation** (the relation contract: inverse-functional → subject must be rank 1;
  otherwise its log-probability must rise), ctl_correct1, leak_top5, **ctl_pass_js>0.01** (share of control reads that pass
  the standard specificity check yet move by JS > 0.01 bits), median control JS.
- **Sequential/batch:** per step with a full re-read: edit_ok and rev_old_stale on edited facts, retention (old object
  still rank 1) on unedited facts, controls, median JS; and **persistence** (edits that took at their own step and still
  hold at the last step).
- Every rate has a 95% bootstrap interval over **facts** (2000 resamples, seed 0).
- Offline test `tests/test_analyze_audit.py` (hand-made contract cases; end to end on tiny-model independent and
  sequential outputs): passed in job 16998, together with all other tests.

## Results (analysis jobs 17011–17013; reports copied to `research-log/results/analysis_*/`)
All runs: every edit passed checks A, B, C (independent: per fact; sequential: per step + final restore).

### Run 1, E4: GPT-2 XL, 78 facts, independent (job 16995, 1:02:50) — `analysis_E4_gpt2-xl/report.md`
Rates over valid paths, [95% bootstrap CI over facts].

| | ROME | MEMIT | AlphaEdit |
|---|---|---|---|
| edited question new@1 (facts) | 78/78 = 100% | **64/78 = 82%** [73, 90] | 78/78 = 100% |
| paraphrase/context new@1 | 75% [68, 82] | 55% [45, 65] | 78% [72, 84] |
| forward old still rank 1 | 15% [10, 19] | 33% [25, 41] | 14% [10, 18] |
| **reverse-from-old stale (subject rank 1)** | **57%** [48, 66] | **76%** [69, 84] | **74%** [66, 81] |
| reverse-from-new subject rank 1 | 0% | 0% | 0% |
| reverse-from-new subject rises | 4% | 11% | 12% |
| **contract violation on reverse-from-new** | **97%** [95, 99] | **93%** [88, 97] | **91%** [85, 96] |
| controls keep correct answer | 92% [88, 96] | 98% [95, 99] | 96% [93, 98] |
| new value enters a control's top 5 | 15% [10, 21] | 4% [1, 7] | 7% [4, 11] |
| **controls that pass specificity yet move JS > 0.01 bit** | **84%** [77, 90] | 32% [25, 41] | 37% [28, 46] |
| median control JS (bits) | 0.073 | 0.0050 | 0.0056 |

By relation (stale reverse reads, ROME / MEMIT / AlphaEdit): novels 51/80/80%, companies 53/78/72%, capitals 72/84/76%,
currencies 78/78/78%, characters 10/20/20% (6 facts), inventions 100% (2 facts). MEMIT's edited-question failures are
concentrated in capitals (7/13 succeed) and currencies (3/9).

Predictions: **P4.1** (≥ 90% edit success, every method) holds for ROME and AlphaEdit, **fails for MEMIT** (82%).
**P4.2** (≥ 70% stale) holds for MEMIT and AlphaEdit, **fails for ROME** (57%; draft 83% on 12 facts).
**P4.3 confirmed** (subject rises on only 4–13% of non-functional reverse-from-new paths). **P4.4 confirmed** (0% rank 1
on 1:1 relations; 100% contract violations there for every method). **P4.5 confirmed**: specificity passes on 92–98% of
control reads while a third (MEMIT, AlphaEdit) to 84% (ROME) of those passing reads move by more than 0.01 bit.

### Run 3 (part), E5: GPT-J 6B, 128 facts, independent: ROME and MEMIT (job 16997) — `analysis_E5_gpt-j_ROME_MEMIT/report.md`
| | ROME | MEMIT |
|---|---|---|
| edited question new@1 | 128/128 = 100% | 128/128 = 100% |
| paraphrase/context new@1 | 99% | 91% |
| **reverse-from-old stale** | **30%** [23, 37] | **78%** [73, 85] |
| contract violation on reverse-from-new | 87% [82, 91] | 88% [83, 93] |
| **controls keep correct answer** | **68%** [63, 73] | 98% [96, 99] |
| new value enters a control's top 5 | **32%** [27, 37] | 4% [2, 6] |
| median control JS (bits) | **0.18** | 0.0057 |
- **P5.1 confirmed** (100% for both). **P5.2:** MEMIT confirms (78%); **ROME does not (30%)**, but its low stale rate comes
  with heavy collateral damage: a third of neighbour reads lose their correct answer and the new value enters the top 5
  of 32% of neighbours. ROME on GPT-J (layer 5, no statistics) "fixes" the inverse read largely by overwriting broadly,
  which is exactly what a single stale-read number would reward. This is the clearest case so far for reporting Q2 and
  Q3 together (paper point: per-question audit vs a single score).
- AlphaEdit on GPT-J crashed at its first edit: EasyEdit `431d9bd` does not initialise `cache_c` for GPT-J
  (`AlphaEdit_main.py` handles only llama/qwen/gpt2-xl there, although its projection code handles GPT-J).
  **Fix:** `run_audit.py` v1.1 `alphaedit_reset` creates the zero matrix itself (input dimension from the module type;
  identical to EasyEdit's own initialisation on GPT-2 XL; unit-tested for Linear and Conv1D). Re-run of AlphaEdit only:
  job **17010** (running).

### Run 2, E7: GPT-2 XL sequential (job 16996, 1:27:56) — partly valid, see problems
`analysis_E7_gpt2-xl/report.md`.
- **Valid:** persistence of each edit (read right after its own edit vs after all 78 edits) and stale reads on edited facts:
  | | took at own step | still hold after 78 edits | stale reverse reads after 78 edits |
  |---|---|---|---|
  | ROME | 78/78 | **14** (64 lost) | 0/148 (model collapsed: median JS 0.88 on all reads, no control answer at rank 1) |
  | MEMIT | 71/78 | **51** (20 lost) | 106/148 = 72% |
  | AlphaEdit | 78/78 | **78** (0 lost) | 107/148 = 72% |
  **P7.1** confirmed for ROME and MEMIT (largest loss ROME), AlphaEdit loses nothing. **P7.3** confirmed for MEMIT and
  AlphaEdit; ROME's 0% is collapse, not consistency: a stale-read metric alone would rate the destroyed model best.
- **Problem A (my submission error):** `sbatch --export=...,EXTRA="... --checkpoints 1,2,5,..."` splits on commas, so the run
  got `--checkpoints 1`: full re-reads only at steps 1 and 78; no curves.
- **Problem B (my design error):** without held-out facts, every neighbour and every new-object-own-fact control is itself
  an edited fact by step 78, so "control keeps its correct answer" at the end conflates damage with that control's own
  edit working. P7.2 cannot be tested from this run.
- **Fix (run_audit v1.2, analyze_audit v1.1):** `--holdout N` (last N facts of the order are only read, never edited);
  delta rows carry `control_fact`, and the analysis scores controls only while their fact is still unedited; checkpoints
  accept `:` separators. Test extended (held-out group, exclusion of edited controls). **E7v2 = job 17015**: 60 edited +
  18 held out, full re-reads at 1, 2, 5, 10, 20, 30, 40, 50, 60.

### Results that completed later (jobs 17010, 17015; analysed locally on the copied raw outputs, see `RESULTS.md`)
- **17010, GPT-J AlphaEdit** (1:11:01, all checks passed, `run_audit` v1.1 with `alphaedit_reset`): stale reverse reads
  193/246 = 78% [73, 85], identical counts to MEMIT in every relation although the runs differ (1,074/2,568 rows differ
  in post-edit rank; median update norm 5.40 vs 4.75): both leave 192 of the 198 pre-edit rank-1 reverse reads unchanged.
- **17015, E7v2** (1:27:16, all checks passed, final restore exact): full curve table in `RESULTS.md` §7.1. After 60 edits:
  ROME 5/60 edits hold, sentinels 0/18; MEMIT 38/53, sentinels 13/18; AlphaEdit 60/60, sentinels 15/18.
- New summary statistic introduced for the results document: **survival of pre-edit rank-1 reverse reads** (of the
  reverse-from-old paths returning the subject at rank 1 before the edit, the share still doing so after it): GPT-2 XL
  ROME 72%, MEMIT 98%, AlphaEdit 95%; GPT-J ROME 37%, MEMIT 97%, AlphaEdit 97%.
- Detailed tables (per fact, quantiles, leaks, overlap, sequential, checks): `experiments/retrieval_poc/report_details.py`
  v1.0 → `research-log/results/details/`.
