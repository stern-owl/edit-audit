# 2026-11-05 · 11 · N5 compensating edits and N2 cascading repair (GPT-2 XL)

**Plan items:** 6.4 (N5), 6.2 (N2, GPU part). Designs: `NOVELTY_AND_NEW_EXPERIMENTS.md` §4. Database analogues: a
compensating transaction undoes a committed write logically (a new write), not physically (an undo log); ON UPDATE CASCADE
applies the follow-up writes that keep a declared constraint satisfied.

## Code (written and tested before the run)
- `run_audit.py` v1.3, new `--mode programs` (`audit_programs()`, `program_edit()`), with `--programs`,
  `--derived-facts`, `--candidates`, `--templates`, `--sentinels-file`. A program starts from the unedited weights
  (AlphaEdit: cache reset first, then accumulating over its steps), applies its steps (one edit call per step; a step with
  several edits is one `batch_edit` call), checks B after every step, reads its facts and the sentinels after the steps in
  `read_at` (all routes, compared with the unedited reads in deltas/dist), restores, re-reads the edited facts (check C).
  A program with `compare_to` is compared read by read with that program's final reads (`commute.csv`). Check rows per
  step carry the step and cumulative update norms (the cumulative norm after a compensation is the weight residue).
  ROME has no batch edit: its run skips the `cascade_batch` programs (logged in the manifest).
  Derived facts (the swap repairs) get probes from `screen_facts_v4.build_probes` (v3 templates, neighbours from the v3
  candidates) and route validity from the same screening rules, judged on the unedited model inside the run.
- `make_programs.py` v1.0 (standard library). On the GPT-2 XL admitted set (78 facts, the same 6 sentinels as N1):
  - N5 `compensate` (72 facts): [A], [A~inv] (A~inv = same prompt and subject, o* → o); reads after both steps.
  - N5 `compensate_late` (20 facts by hash): [A], [X1..X5], [A~inv], with 5 unrelated edits (no shared entity), compared
    with `reference` [X1..X5] (the state a perfect undo of A reaches).
  - N2 (9 one-to-one edits whose new object o* already has a subject s' the model knows, i.e. a valid own-fact control):
    the swap repair S = (s': o* → o); programs `cascade` [A], [S] (reads after A alone and after both), `cascade_rev`
    [S], [A], `cascade_batch` [A + S]. Cases: cap_belgium, cap_chile, cap_hawaii, cap_poland, cur_china, cur_israel,
    cur_japan, cur_nigeria, cur_russia. 429 edit calls in total (ROME: 420).
- Test: `tests/test_programs.py` (tiny GPT-2, CPU): an additive editor with an exact inverse compensates to the unedited
  weights and reads, late compensation reaches the reference; a weight-dependent editor leaves a residue; bookkeeping,
  batch step as one call, derived validity, edited sentinel refused, check B; make_programs case selection and swap targets.

## Run plan
Jobs: tests 18042 failed in `test_programs` (a sub-case where a derived fact is never read: the driver judged its
validity without a read; fixed by skipping unread derived facts, no effect on the real programs, which read every
derived fact); queued 18043/18044 cancelled. Tests 18045 all passed; N5+N2 jobs **18046** (MEMIT, AlphaEdit) and
**18047** (ROME+stats), waiting for a GPU.
GPT-2 XL, seed 0, `--reread-gen-tokens 0`; ROME+stats, MEMIT, AlphaEdit; two jobs queued behind the N1 jobs (GPU cap 2).

## Definitions fixed before the run
- Paths: valid routes. Verdict = first token at rank 1. **Unedited verdict restored** = same verdict as the unedited model.
- N5: **compensated** = o back at rank 1 on the edited question after A~inv. **Relative weight residue** =
  cumulative norm after A~inv / cumulative norm after A. **Over-compensation** = P(o) on the edited question after A~inv
  above its unedited value. Neighbour residue ratio = median neighbour JS (vs unedited) after A~inv / after A.
- N2 target state after A and S: s → o* and s' → o (both edited questions at rank 1); reverse-from-o* returns s
  (A's reverse_new subject at rank 1) and not s'; reverse-from-o returns s' (S's reverse_new subject at rank 1) and not s
  (A's reverse_old subject not at rank 1). **Forward-consistent** = both edits hold; **fully consistent** = forward-consistent
  and every valid reverse path of A and S agrees with the target state.

## Predictions (written before the run)
**N5**
- P11.1 Compensation restores the forward answer (o at rank 1 on the edited question) for ≥ 95% of facts under ROME+stats and MEMIT.
- P11.2 Compensation is not a physical undo: median relative weight residue ≥ 0.3 for every method, and over-compensation
  (P(o) above its unedited value) in ≥ 70% of compensated facts.
- P11.3 Side effects persist: median neighbour residue ratio ≥ 0.3 for every method.
- P11.4 AlphaEdit compensates worse than MEMIT (≥ 10 points fewer compensated facts): its cache protects the keys of earlier
  edits, including A's own key, against the compensating update.
- P11.5 Late compensation is further from the reference than immediate compensation is from the unedited model: median JS
  over A's paths larger for `compensate_late` (vs reference) than for `compensate` (vs unedited), for every method.

**N2** (9 cases; descriptive)
- P12.1 After A alone the inverse FD is violated in every case (s' still answers o*), as in entry 09; after the cascade
  (A then S) s' no longer answers o* in ≥ 80% of cases for MEMIT and AlphaEdit.
- P12.2 The fully consistent state is reached in ≤ 20% of cases for every method and order (reverse paths stay stale).
- P12.3 The batch reaches the forward-consistent state at least as often as either sequential order (MEMIT, AlphaEdit).

## Results (jobs 18047 ROME+stats, 1:16 h; 18243 MEMIT then AlphaEdit, 2:23 h; all checks passed)
Outputs: `data/raw_runs/N25_gpt2-xl_programs_18047/`, `.../N25_gpt2-xl_programs_18243/` (md5-verified against the cluster).
Analysis: `analyze_programs.py` v1.0 → `results/N5_N2_gpt2-xl/report.md`. Smallest check B 0.0043, largest check C 0.
Job 18046 (first MEMIT/AlphaEdit attempt) failed before any edit: EasyEdit's `edit()` asserts `batch_size == 1` and the
driver had set the run-wide maximum (2); `run_audit.py` now sets `hparams.batch_size` per edit call (batch steps only).

### N5 compensating edits (72 facts; reads after the edit and after the compensating edit o* → o)
| | ROME+stats | MEMIT | AlphaEdit |
|---|---|---|---|
| edit succeeds | 72/72 | 60/72 = 83% | 72/72 |
| compensated (o back at rank 1), of successful edits | **72/72** | **60/60** | **72/72** |
| over-compensated: P(o) above its unedited value | **70/72 = 97%** | **57/60 = 95%** | **71/72 = 99%** |
| median Δ log P(o) vs unedited | +0.67 | +0.61 | +0.65 |
| verdicts back to the unedited verdict (all valid reads of A) | 98% | 99% | 99% |
| median JS of A's paths vs unedited: after edit → after undo | 0.017 → 0.011 | 0.011 → 0.005 | 0.017 → 0.007 |
| median neighbour JS vs unedited: after edit → after undo | 0.018 → **0.025** | 0.003 → **0.005** | 0.004 → **0.006** |
| median neighbour residue ratio (after undo / after edit) | 1.13 | 0.95 | 1.12 |
| median weight residue ‖W_undo − W0‖ / ‖W_edit − W0‖ | **1.31** | **1.08** | **1.63** |
| late compensation (5 edits in between): compensated | 20/20 | 19/20 | 20/20 |
| late vs reference, median JS of A's paths (immediate undo vs unedited, same facts) | 0.017 (0.008) | 0.005 (0.005) | 0.007 (0.008) |

- **A compensating edit restores the answer but is not an undo.** The forward answer comes back in every case and 98-99%
  of the audit's verdicts return to their unedited values, but the old object is now *more* probable than before
  (95-99% of facts, +0.6 nats), the weights end **further** from the unedited weights than after the edit itself
  (residue 1.08-1.63 × the edit's own update), and same-relation neighbours are as disturbed as after the edit (ratio
  0.95-1.13) or more. Only a physical restore (check C: exact) returns the unedited model.
- The compensation does not get harder when other edits intervene (late vs immediate: equal for MEMIT and AlphaEdit; only
  ROME+stats doubles), and the 5 intervening edits are left essentially untouched (median JS 0.0000-0.0003).
- AlphaEdit compensates as well as the others (100%): its cache of earlier keys does not block a write to the same key.

### N2 cascading repair (9 one-to-one edits; S = the swap s': o* → o)
| state | ROME+stats: both edits hold | MEMIT | AlphaEdit |
|---|---|---|---|
| A alone (FD violated: s' still answers o*) | 0/9 (9/9 violated) | 0/9 (9/9) | 0/9 (9/9) |
| A then S | 2/9 | 1/9 | **9/9** |
| S then A | 4/9 | 1/9 | **9/9** |
| A + S as one batch | n/a (no batch for ROME) | 1/9 | **9/9** |
| **fully consistent** (both hold and all reverse paths agree) | **0/9 in every state** | 0/9 | 0/9 |

- **ROME+stats: the repair is itself a lost update.** S writes o (A's old object) and moves o* away from s', which is the
  shared-object pattern of N1: with S second, A is reverted in 7 of 9 cases; with S first, A reverts S in 5 of 9.
- **MEMIT** mostly fails to apply either edit for these capital/currency facts (A alone holds in 4/9; after the cascade
  both hold in 1/9 in every order and in the batch).
- **AlphaEdit reaches the forward-consistent state in all 9 cases in every order and as a batch**: s → o*, s' → o, and s'
  no longer answers o* (FD restored on the forward paths).
- **No method in any state reaches the consistent state on the reverse paths**: from o* the model never answers s (0/18
  valid reads), from o it never answers s' (0/18); 72% of the o* reads still exclude s' only because they never named it
  first. The reverse index is untouched by both writes, so a cascade restores the declared FD on the forward paths only.

### Predictions
| ID | Prediction | Outcome |
|---|---|---|
| P11.1 | compensation restores the forward answer ≥ 95% (ROME+stats, MEMIT) | **confirmed** (100%, 100%) |
| P11.2 | weight residue ≥ 0.3 and over-compensation ≥ 70%, every method | **confirmed** (residue 1.08-1.63; over-compensation 95-99%) |
| P11.3 | neighbour residue ratio ≥ 0.3, every method | **confirmed** (0.95-1.13) |
| P11.4 | AlphaEdit compensates ≥ 10 points worse than MEMIT | **refuted** (both 100%) |
| P11.5 | late compensation further from the reference than immediate undo from the unedited model, every method | **refuted except ROME+stats** (MEMIT equal, AlphaEdit lower) |
| P12.1 | FD violated after A alone in every case; after the cascade s' no longer answers o* in ≥ 80% (MEMIT, AlphaEdit) | first part **confirmed** (9/9 all methods); second **AlphaEdit yes (9/9), MEMIT no** (3-4/9) |
| P12.2 | fully consistent in ≤ 20% of cases, every method and order | **confirmed** (0/9 everywhere) |
| P12.3 | batch forward-consistent at least as often as either sequential order (MEMIT, AlphaEdit) | **confirmed** (ties: 1 = 1 = 1; 9 = 9 = 9) |

### What this gives the paper
1. **Compensation ≠ undo**: a logical inverse write restores the answer but leaves a larger weight footprint, an
   over-confident old answer and unchanged neighbour drift; editing systems need a physical undo log (weight snapshot /
   delta) for rollback, as databases do.
2. **Cascades restore constraints only where they are written**: the swap repair restores the inverse FD on the forward
   paths for AlphaEdit (9/9) but never on the reverse paths; for ROME+stats the repair collides with the original edit
   (lost update, as in N1).
3. Limitations: GPT-2 XL, one seed, 9 cascade cases (one-to-one relations only), MEMIT's low success on these facts.
