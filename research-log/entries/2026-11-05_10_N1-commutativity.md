# 2026-11-05 · 10 · N1: commutativity of edit pairs (GPT-2 XL)

**Plan item:** 6.3. Design: `NOVELTY_AND_NEW_EXPERIMENTS.md` §4 N1. Database analogue: two writes commute if applying them
in either order gives the same state; a scheduler may reorder or batch commuting writes and must serialise conflicting ones.

## Code (written and tested before the run)
- `experiments/retrieval_poc/run_audit.py` **v1.3**: new `--mode pairs` (`audit_pairs()`), `--pairs`, `--sentinels-file`.
  Per pair (A, B) and order (AB, BA): from the unedited weights (AlphaEdit: cache reset before each order, then
  accumulating over the two edits), edit the first fact, then the second without restoring (check B for each call);
  read A, B and the sentinels (all routes); restore; re-read A and B (check C). Outputs as before plus
  `commute.csv` (per pair, read fact and route: KL both ways, JS, TV, argmax change, top-10 overlap between the AB and BA
  next-token distributions) and `pairs.csv` (per pair: checks; Frobenius norms of the first-edit updates dA (AB order) and
  dB (BA order) and their cosine; norms of the final updates dAB and dBA; **order gap** ||dAB − dBA||; **additivity gaps**
  ||dAB − (dA + dB)||, ||dBA − (dA + dB)||; cosine of the two subjects' **keys** (input of each rewrite module at the
  subject's last token of the edit prompt, unedited model), mean over rewrite layers and last layer).
  Modes independent / sequential / batch are unchanged (same code path; `audit()` now refuses mode pairs).
- `make_pairs.py` v1.0 (standard library): one class per unordered pair of admitted facts, first match wins:
  same_new (o*_A = o*_B), shared_object (o*_A = o_B or o_A = o*_B), chained (an object of one is the other's subject),
  neighbour (one is the other's same-relation control), other_shared, same_relation, disjoint. Sentinels first (by hash,
  round-robin over relations, never in a same_new / shared_object / chained pair), then pairs by md5(seed:a|b).
  On the GPT-2 XL admitted set (78 facts): available 2,285 disjoint, 618 same_relation, 64 neighbour, 30 shared_object,
  6 same_new, 0 chained, 0 other_shared. **Chosen: all 6 same_new, all 30 shared_object, 30 neighbour, 30 same_relation,
  30 disjoint = 126 pairs**; sentinels `chr_superman, com_twitter, cap_austria_hungary, cur_malaysia, inv_polio_vaccine,
  nov_uncle_tom_s_cabin`.
- Tests: `tests/test_pairs.py` (tiny random GPT-2, CPU): an additive per-fact editor commutes exactly (order gap,
  additivity gap and every AB/BA JS = 0); a weight-dependent editor does not; row bookkeeping; reset before each order;
  subject keys equal a manual forward pass; a sentinel inside a pair is refused; a no-op editor is caught by check B;
  make_pairs class rules and determinism. `cluster/csis/tests.sbatch` now also runs `test_pairs` and `test_phase6_offline`.
- `cluster/csis/audit_v3.sbatch`: with `MODE=pairs` it runs `make_pairs.py` on `PROBES` inside the job and passes the files.

## Run plan
GPT-2 XL, v3 admitted probes (job 16990), seed 0, `--reread-gen-tokens 0` (sentinels without greedy text).
Methods: the local configurations ROME+stats, MEMIT, AlphaEdit (ROME without statistics not run: ablation only, D5).
Two jobs (account cap 2 GPUs): MEMIT + AlphaEdit; ROME+stats.

## Definitions fixed before the run
- Paths: valid routes of A and B; sentinel routes reported separately. Verdict of a (path, answer) read = its first token at
  rank 1. **Order-dependent verdict**: the verdict differs between the AB and BA states.
- **Read gap** of a pair = median JS(AB ‖ BA) over the valid paths of A and B. Relative weight gap = ||dAB − dBA|| / mean(||dAB||, ||dBA||);
  relative additivity gap = ||dAB − (dA + dB)|| / ||dAB||.
- **First-edit retention**: in order XY, X's edited question still has o*_X at rank 1 after Y's edit (given X held after
  its own edit in the independent run E4/E2X).

## Predictions (written before the run)
- P10.1 Disjoint and same-relation pairs nearly commute under MEMIT and AlphaEdit: median read gap ≤ 0.01 bit and
  ≤ 5% of path verdicts order-dependent.
- P10.2 Pairs that share an entity (shared_object, same_new) commute less: their median read gap is ≥ 3× that of disjoint
  pairs, for every method.
- P10.3 Key overlap predicts order dependence: across all pairs, key cosine (mean over layers) has Spearman ρ ≥ 0.3 with the
  relative weight gap, for every method.
- P10.4 ROME+stats and MEMIT are close to additive on disjoint pairs (median relative additivity gap ≤ 0.1); AlphaEdit
  is not (its second update is projected away from the first edit's keys): its median is ≥ 2× MEMIT's.
- P10.5 First-edit retention is ≥ 95% for disjoint pairs and at least 10 points lower for shared_object pairs (the second
  edit writes the first edit's new object as its own old object), for every method.

## Results (jobs 18040 ROME+stats, 1:34 h; 18039 MEMIT then AlphaEdit, 2:43 h; all checks passed)
Outputs: `data/raw_runs/N1_gpt2-xl_pairs_18039/`, `.../N1_gpt2-xl_pairs_18040/` (38 files md5-verified against the cluster).
Analysis: `analyze_pairs.py` v1.0 → `research-log/results/N1_gpt2-xl/report.md`, `pairs_summary.csv`. Checks: smallest
check B 0.0079, largest check C 0 (every restore exact). First-edit retention and second-edit success count only edits that
succeed in the independent runs of the same configuration (E2X for ROME+stats, E4 for MEMIT and AlphaEdit).

| method | class (pairs) | median read gap (bits) | order-dependent verdicts | rel. weight gap | rel. additivity gap | key cosine | first-edit retention | second-edit success |
|---|---|---|---|---|---|---|---|---|
| ROME+stats | disjoint (30) | 0.0000 | 2/1008 = 0.2% | 0.08 | 0.05 | 0.10 | 60/60 | 60/60 |
| | same relation (30) | 0.0005 | 63/1062 = 6% | 0.42 | 0.29 | 0.32 | 55/60 = 92% | 60/60 |
| | neighbour (30) | 0.0005 | 45/1091 = 4% | 0.38 | 0.27 | 0.31 | 57/60 = 95% | 60/60 |
| | **shared object (30)** | 0.0017 | **143/1079 = 13%** | 0.53 | 0.37 | 0.35 | **43/60 = 72%** | 60/60 |
| | same new object (6) | 0.0003 | 8/218 = 4% | 0.42 | 0.30 | 0.30 | 12/12 | 12/12 |
| MEMIT | disjoint | 0.0000 | 1/1008 = 0.1% | 0.05 | 0.03 | 0.07 | 48/48 | 48/48 |
| | same relation | 0.0000 | 6/1062 = 0.6% | 0.22 | 0.15 | 0.18 | 56/57 = 98% | 56/57 |
| | neighbour | 0.0001 | 7/1091 = 0.6% | 0.19 | 0.13 | 0.19 | 57/58 = 98% | 57/58 |
| | **shared object** | 0.0001 | **51/1079 = 5%** | 0.22 | 0.16 | 0.20 | **46/57 = 81%** | 55/57 = 96% |
| | same new object | 0.0001 | 2/218 = 1% | 0.25 | 0.17 | 0.17 | 11/11 | 11/11 |
| AlphaEdit | disjoint | 0.0000 | 1/1008 = 0.1% | 0.06 | 0.04 | 0.07 | 60/60 | 60/60 |
| | same relation | 0.0000 | 9/1062 = 0.8% | 0.20 | 0.14 | 0.18 | 60/60 | 60/60 |
| | neighbour | 0.0000 | 7/1091 = 0.6% | 0.21 | 0.15 | 0.19 | 60/60 | 60/60 |
| | **shared object** | 0.0001 | **19/1079 = 2%** | 0.28 | 0.19 | 0.20 | **60/60 = 100%** | 60/60 |
| | same new object | 0.0000 | 4/218 = 2% | 0.26 | 0.19 | 0.17 | 12/12 | 12/12 |

Sentinels: median AB/BA gap 0.0000 bits in every class and method (order does not reach untouched facts).

**Conflict predictor (all 126 pairs, Spearman ρ, 95% bootstrap):** key cosine vs relative weight gap **0.94 [0.90, 0.96]**
(ROME+stats), **0.87 [0.79, 0.91]** (MEMIT), **0.88 [0.80, 0.92]** (AlphaEdit); key cosine vs read gap 0.92 / 0.81 / 0.86;
relative weight gap vs read gap 0.94-0.96. The overlap of the two subjects' keys at the rewrite layers, computed on the
unedited model before any edit, ranks pairs by how much their order matters.

**The conflict is a lost update.** Lost first edits concentrate in shared-object pairs (o*_A = o_B or o_A = o*_B). In
12 of the 17 lost first edits in shared-object pairs under ROME+stats and 10 of 14 under MEMIT (counted over all edits),
the second edit wrote the first edit's *old* object as its new object, and the first edit reverted to its old object
(e.g. Dracula: Bram Stoker → Mary Shelley, then Frankenstein: Mary Shelley → Bram Stoker; Dracula answers Bram Stoker
again, greedy text "Bram Stoker in 1897"). The second write wins and silently undoes the first: the edit-level analogue of
a lost update under concurrent writes to related items. Largest read gaps: ROME+stats p028 (cap_belgium / cap_poland,
JS 0.52 bits, 15 of 32 verdicts order-dependent, first edit lost in both orders), p023 (google / microsoft), p026
(apple / microsoft), p025 (amazon / facebook).

**AlphaEdit never loses a first edit** (0 in 126 pairs, both orders): its record of earlier edit keys (cache) protects the
first write against the second. Order dependence is not removed (19 order-dependent verdicts in shared-object pairs,
relative weight gap 0.28) but it no longer destroys an edit: the scheduler semantics is "first writer wins".

### Predictions
| ID | Prediction | Outcome |
|---|---|---|
| P10.1 | disjoint and same-relation pairs nearly commute under MEMIT and AlphaEdit (median read gap ≤ 0.01 bit, ≤ 5% order-dependent verdicts) | **confirmed** (medians 0.0000; 0.1-0.8% order-dependent) |
| P10.2 | shared-entity pairs' median read gap ≥ 3× disjoint, every method | **confirmed** (17-412×; but the disjoint median is ~0, so the ratio is unstable; order-dependent verdicts 2-13% vs 0.1-0.2% are the better statistic) |
| P10.3 | key cosine Spearman ρ ≥ 0.3 with the relative weight gap, every method | **confirmed** (0.87-0.94) |
| P10.4 | ROME+stats and MEMIT near-additive on disjoint pairs (median ≤ 0.1); AlphaEdit ≥ 2× MEMIT | first part **confirmed** (0.05, 0.03); second **refuted** (AlphaEdit 0.04, 1.3× MEMIT) |
| P10.5 | first-edit retention ≥ 95% disjoint and ≥ 10 points lower for shared-object pairs, every method | **confirmed for ROME+stats (100 → 72%) and MEMIT (100 → 81%); refuted for AlphaEdit** (100% in every class) |

### What this gives the paper
1. Edits on unrelated facts commute (weight-level additivity gap 3-5%, no order-dependent verdicts to speak of): a
   scheduler may reorder or batch them.
2. Edits that share an entity do not commute, and the failure has a database name: a **lost update** (the later write
   reverts the earlier one). Under ROME+stats 28% of first edits in shared-object pairs are lost, under MEMIT 19%.
3. **Conflicts are predictable before editing** from key overlap on the unedited model (ρ 0.87-0.94): the basis for a
   conflict graph and a conflict-aware scheduler (serialize or batch only non-conflicting edits; N4).
4. AlphaEdit implements "first writer wins": no lost updates, at the price of order dependence in the rest of the state.
5. Limitations: GPT-2 XL only, one seed, 126 pairs (6 same-new pairs), keys without the editors' context averaging.
