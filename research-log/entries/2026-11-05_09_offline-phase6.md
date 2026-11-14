# 2026-11-05 · 09 · Phase 6, offline experiments: N3 audit planning, N2 admission control, E10 standard metrics

**Plan items:** 6.1 (N3), 6.2 (N2, offline part), 5.1 (E10). Designs: `NOVELTY_AND_NEW_EXPERIMENTS.md` §4.

## Data (no new GPU runs)
The eight independent audits already logged, analysed edit by edit:
| model | ROME (no stats) | ROME + stats | MEMIT | AlphaEdit |
|---|---|---|---|---|
| GPT-2 XL, 78 facts | E4 (16995) | E2X (18037) | E4 (16995) | E4 (16995) |
| GPT-J, 128 facts | E5 (16997) | E2J (18036) | E5 (16997) | E5 (17010) |
"Local configurations" = ROME + stats, MEMIT, AlphaEdit (main results); ROME without statistics is the ablation.

## Definitions fixed before the analysis
Per edit, violation types (valid paths only; reverse paths only for successful edits, as in analysis v1.2):
- **V0 edit failed:** new object not rank 1 on the edited question.
- **V1 incomplete write:** some paraphrase/context path without the new object at rank 1.
- **V2 stale read:** some reverse-from-old path still returns the subject at rank 1.
- **V3 inverse inconsistency:** some reverse-from-new path violates the relation contract.
- **V4 neighbour damage:** some same-relation neighbour loses its correct answer at rank 1.
- **V5 neighbour drift:** some neighbour passes the rank-1 check but its distribution moves by JS > 0.01 bit (soft; reported separately).
- **V6 neighbour leak:** the new object enters a neighbour's top 5.
- **Inconsistent edit** = any of V0–V4, V6. An access path (route type) *detects* a violation type if reading it on that edit shows it.
- **Audit plan** = a set of route types read for every edit; **cost** = number of questions asked (one per route type).
- **Standard plan** (CounterFact-style evaluation): edited question + 3 paraphrase/context paths + 2 same-relation neighbours.

## Predictions (written before running)
**N3 audit planning**
- P9.1 The standard plan misses ≥ 60% of the inconsistent edits for the local configurations (stale and inverse failures
  appear only on reverse paths).
- P9.2 A plan of 2 questions (one reverse-from-old + one same-relation neighbour) detects ≥ 90% of inconsistent edits for the
  local configurations.
- P9.3 A greedy plan chosen on one model transfers to the other model with ≤ 10 points loss of detection rate at the same budget.

**N2 admission control**
- P9.4 Pre-edit strength of the reverse association (subject log-probability on the reverse-from-old path, unedited model)
  predicts which successful edits leave a stale read: AUROC ≥ 0.65 for the local configurations.
- P9.5 For the one-to-one relations (capital, currency), ≥ 90% of successful edits whose new object has its own fact in the set
  leave the model in a state that violates the declared inverse functional dependency (the new object is still the
  top answer for its original subject while it is now also the answer for the edited subject).

**E10 standard metrics on the same edits**
- P9.6 Of the edits that pass all three CounterFact-style scores (efficacy, paraphrase, neighbourhood), ≥ 80% are flagged as
  inconsistent by the audit (local configurations).
- P9.7 Neighbourhood KL (CounterFact+) does not predict stale reads: AUROC of an edit's mean neighbour KL for V2 in [0.4, 0.6].

## Code
- `experiments/retrieval_poc/phase6_offline.py` v1.1 (standard library only; md5 `dfcdd0ef61e0c1fe8d1ce6a44eaf2ef7`).
  `load_edits()` builds one record per edit from `deltas.csv` / `dist.csv` (own-step reads, valid paths only): the
  violation types each route reveals (`det`), pre-edit features, CounterFact-style ES / PS / NS, neighbourhood KL, a
  BAKE-like reverse efficacy, the FD-state check. Same conventions as analysis v1.2 (reverse paths for successful edits
  only; same-relation neighbours whose correct answer is o* dropped; own-fact control kept apart). Plans: `rate()`,
  `greedy()` (greedy set cover, ties broken by route order); AUROC by mid-ranks (Mann-Whitney), 500-resample bootstrap
  over edits, seed 0.
- v1.0 -> v1.1 (before any result was used): added the "excluding V3" planning table and the `V2|pre1` predictor target
  (see below), UTF-8 console output on Windows. The v1.0 numbers for the shared sections were identical.
- Test: `tests/test_phase6_offline.py` (hand-made rows: V0-V6 logic, failed-edit exclusion, o*-equal neighbour dropped,
  invalid paths ignored, FD check, ES/PS/NS/NKL/BAKE values, standard plan misses a stale-only edit, greedy plan; rank
  AUROC = brute-force pairwise AUROC on 200 random tie-heavy cases). Passes locally (md5 `71b2c72cafa3bd775544081dda490ed5`).
- Run (laptop, 35 s): `python phase6_offline.py --templates relation_templates_v3.json --out research-log/results/phase6_offline --run MODEL/CONFIG=<audit dir>` (x8).
  Outputs: `results/phase6_offline/report.md` (md5 `52a7299122e09ecd5d96fe961c761163`), `edits.jsonl` (one record per
  edit and run, md5 `bf663734131225d1e23edd5daf797925`). Pooled rows: `GPT-2 XL/local` (234 edits), `GPT-J/local` (384),
  `all/local` (618) = ROME+stats + MEMIT + AlphaEdit.

## Results (full tables: `results/phase6_offline/report.md`)

### N3 audit planning
Inconsistent edits are almost all edits: 617 of 618 (local configurations); the one exception (GPT-2 XL ROME+stats,
`chr_snoopy`) only drifts (V5). V3 (reverse-from-new contract) alone is present in 566 of 618.

| pool (local configurations) | inconsistent | standard plan (6 questions) | reverse-old + neighbour (2) | greedy 1 | greedy 2 | greedy 3 |
|---|---|---|---|---|---|---|
| GPT-2 XL | 233 | 56% | 67% | 84% | 91% | 97% |
| GPT-J | 384 | **25%** | 68% | 86% | 97% | 99% |
| both | 617 | **37%** | 68% | 84% | 94% | 97% |
| both, excluding V3 | 564 | 40% | 74% | 82% | 93% | 97% |

- The standard plan sees V0, V1, V4, V5, V6 by construction and **none** of V2 / V3: 0 of 524 stale edits and 0 of 566
  inverse-inconsistent edits (local configurations). On GPT-2 XL it still catches 56% because many edits are also
  incomplete writes (V1: 118 of 234 edits fail on some paraphrase/context path); on GPT-J, where writes are more
  complete (V1: 62 of 384), it catches 25%.
- Greedy plans always start with reverse paths: budget 2 = one reverse-from-new + one reverse-from-old path (94% of
  inconsistent edits, pooled); without V3, two reverse-from-old paths (93%). A same-relation neighbour is never among
  the first two choices for a local configuration (neighbour damage is rare: V4 42 / 618, V6 54 / 618); it is for
  GPT-J ROME without statistics (V4 75 / 128).
- Transfer across models (plans chosen on one model's pooled local configurations): budget 1: 84 -> 82% / 86 -> 84%;
  budget 2: GPT-J's plan on GPT-2 XL 91% (= GPT-2 XL's own 91%), **GPT-2 XL's plan on GPT-J 85% vs 97% (-12 points)**,
  because GPT-2 XL picks a paraphrase path second (its V1 failures); budget 3: within 4 points both ways (97/98%, 93/99%).
- Adaptive audit (pooled greedy order, stop at the first violation): **1.26 questions per edit** on average (all local)
  instead of 11; 1.18-1.47 per run. Caveat: the order is chosen on the same edits (in-sample); the transfer table is the
  out-of-sample check, and almost every edit is inconsistent, which makes early stopping cheap.

### N2 admission control
- **FD state:** of the successful one-to-one edits (capital, currency) whose new object has its own fact in the set, the
  new object still answers its original subject after the edit in **66 / 66 (100%)** (local configurations; also 24 / 24
  for ROME without statistics). The edited model therefore maps two subjects to one value under a declared inverse FD in
  every checked case; an admission check on the request (does o* already have a subject under a 1:1 relation?) would
  have flagged every one of these edits before it was applied.
- **Pre-edit predictors (AUROC, pooled local, 95% CI):**

  | target | positives / n | P(o*) before (`pre_logp_new`) | rank of o* before | P(o) before | reverse-old strength | reverse-new closeness |
  |---|---|---|---|---|---|---|
  | V2 stale | 524 / 604 | 0.68 [0.62, 0.74] | 0.57 | 0.55 | **0.91 [0.89, 0.94]** | 0.66 |
  | V2 stale, reverse read rank 1 before | 524 / 539 | 0.70 [0.60, 0.81] | 0.41 | 0.51 | **0.81 [0.72, 0.89]** | 0.54 |
  | V4 neighbour damage | 42 / 618 | 0.43 | 0.46 | 0.50 | 0.44 | 0.55 |
  | V6 neighbour leak | 54 / 618 | 0.71 [0.63, 0.79] | **0.78 [0.70, 0.84]** | 0.55 | 0.72 | 0.75 |

  - Most of the stale-read prediction is the **pre-edit state itself**: every stale edit (524 / 524) had a reverse read
    at rank 1 before the edit, and 97% of such edits (524 / 539) stay stale. The rule "the reverse index already points
    to the subject" has recall 100% and precision 97% for V2 under local configurations. Among those 539 edits,
    reverse strength still ranks the 15 that become fresh lower (AUROC 0.81, wide interval: only 15 negatives).
  - Neighbour leaks are more likely when the new object is already plausible for the prompt (rank AUROC 0.78), i.e. the
    edit has to move less; neighbour damage is not predictable from these features (AUROCs 0.43-0.55).
  - GPT-J MEMIT and AlphaEdit give identical rows for V2 and V6: the same 115 edits are stale and the same 8 leak
    (checked fact by fact; V1 and V4 differ), and the features are pre-edit, so identical AUROCs follow.

### E10 standard metrics vs the audit (same edits)
| pool (local) | pass ES | pass PS | pass NS | pass all three | of those, audit flags | ... stale (V2) | ... inverse (V3) | ... damage/leak | ... drift (V5) | BAKE-like reverse efficacy | AUROC NKL -> V2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GPT-2 XL | 94% | 50% | 92% | 116 / 234 | 99% | 83% | 91% | 10% | 27% | 11% | 0.39 [0.30, 0.48] |
| GPT-J | 100% | 87% | 94% | 325 / 384 | 100% | 87% | 92% | 9% | 30% | 2% | 0.54 [0.47, 0.60] |
| both | 98% | 73% | 93% | 441 / 618 | **440 / 441** | **86%** | 91% | 9% | 29% | 6% | **0.47 [0.41, 0.53]** |

- 441 edits look clean on all three CounterFact-style scores; the audit flags 440. Without counting V3, 387 / 441 (88%)
  are still flagged, 380 of them as stale reads. 53 are flagged by V3 alone.
- BAKE-like reverse efficacy (edited subject preferred over o*'s own subject on reverse-from-new paths) is 2-12%,
  consistent with BAKE's reverse-efficacy findings (prior work; cite, do not claim).
- Neighbourhood KL does not predict stale reads: pooled AUROC 0.47; on GPT-2 XL it is weakly *below* 0.5 (MEMIT 0.37,
  AlphaEdit 0.33: edits that disturb neighbours more are slightly *less* often stale), on GPT-J 0.51-0.59.

### Predictions
| ID | Prediction | Outcome |
|---|---|---|
| P9.1 | standard plan misses >= 60% of inconsistent edits (local) | **confirmed pooled** (misses 63%) and on GPT-J (75%); **not on GPT-2 XL** (44%, because V1 is visible to it) |
| P9.2 | reverse-old + neighbour (2 questions) detects >= 90% | **refuted** (68%; 74% without V3); the best 2-question plan is two reverse paths (94%) |
| P9.3 | greedy plan transfers across models with <= 10 points loss | **mostly**: 5 of 6 budget/direction cells within 4 points; GPT-2 XL's budget-2 plan on GPT-J loses 12 |
| P9.4 | reverse-old strength predicts V2 with AUROC >= 0.65 | **confirmed** (0.91; 0.87-0.96 per configuration), mostly through the pre-edit rank-1 state; 0.81 within that state |
| P9.5 | >= 90% of checked 1:1 edits leave an FD-violating state | **confirmed** (66 / 66) |
| P9.6 | >= 80% of edits passing ES/PS/NS are flagged by the audit | **confirmed** (440 / 441; 88% without V3) |
| P9.7 | NKL AUROC for V2 in [0.4, 0.6] | **confirmed pooled** (0.47) and on GPT-J (0.54); GPT-2 XL slightly below (0.39) |

### What this gives the paper
1. **Evaluation gap, quantified on the same edits** (E10): 71% of edits pass all three standard scores, and 99.8% of
   those are inconsistent by the audit; 86% are stale reads, which standard evaluation cannot see by construction.
2. **Audit planning** (N3): the cheapest informative audit reads reverse paths first; two reverse questions find 94% of
   inconsistent edits, the six-question standard plan 37%. Plans transfer across models at budgets 1 and 3.
3. **Admission control** (N2): for 1:1 relations the violation is decidable before the edit from the request and the
   model's current state (100% of checked cases). For stale reads, the pre-edit reverse state alone predicts the outcome
   (recall 100%, precision 97%), so an engine can warn before writing.
4. **Limitations:** plans and the order are chosen in-sample except for the cross-model transfer; one seed; the FD check
   covers only 66 edits (o* must have its own fact in the set); "inconsistent" is dominated by V3, so every planning
   table is also given without V3.
