# 2026-11-05 · 08 · Teammate review: ROME with statistics on GPT-J; three analysis corrections

## Comments received (teammate, relayed by the user)
1. Run ROME with covariance statistics on GPT-J, since it ran without statistics earlier.
2. In `analyze_audit.py`: (a) count stale reverse reads only for edits that succeeded; (b) report the JS share over
   passing control reads, not all control reads; (c) drop neighbours whose correct answer already equals the new object.

## Check of each comment against the data (raw outputs in `data/raw_runs/`)
| Comment | Finding | Effect on reported numbers |
|---|---|---|
| 1 | Valid. On GPT-2 XL, statistics turned ROME into an AlphaEdit-like editor (E2). GPT-J ROME's low stale rate (30%) with heavy neighbour damage may be the same no-statistics effect. Layer-5 statistics for GPT-J are already on the cluster. | potentially changes the claim "a single score rewards the worst editor" |
| 2a | Valid. Only GPT-2 XL MEMIT has failed edits (14/78). | stale 113/148 = 76% → 90/120 = 75%; all other runs unchanged (no failed edits) |
| 2b | Valid, and it exposes a **wording error in RESULTS.md and the results page**: "of the reads that pass specificity, X% shift" was computed over **all** control reads. | the stated 32–84% must be recomputed over passing reads |
| 2c | Valid. The controls whose correct answer is the new object are exactly the "new object's own fact" controls (50 of 164 on GPT-2 XL, 102 of 309 on GPT-J). No same-relation neighbour has correct = o* (screening's eligibility rule excludes them). Mixing the two inflated "neighbour keeps its answer" and counted the old object rising on o*'s own fact as a "leak". | neighbour metrics recomputed on same-relation neighbours only; own-fact check reported separately |

## Code changes
- `analyze_audit.py` v1.2:
  - reverse-path metrics (`rev_old_stale`, new `rev_old_survival`, `rev_new_*`) only for successful edits (sequential: edits
    still holding at that step); unconditional versions kept as `*_all`;
  - neighbour metrics `nb_correct1`, `nb_leak_top5`, `nb_pass_shift` (= among neighbour reads passing the rank-1 check, share
    with JS > 0.01 bit), `nb JS median` on same-relation neighbours only; o*-equal neighbours dropped (none exist; rule kept);
    `own_correct1` reported separately; sequential `nbU_*` likewise.
- `report_details.py` v1.1: quantiles split into "neighbour" and "new object's own fact"; per-fact stale shown as n/a for
  failed edits; per-fact controls, leaks and JS on neighbours only.
- `tests/test_analyze_audit.py`: hand-made cases for each rule (failed edit excluded, survival only over pre-edit rank-1
  paths, own-fact control not a neighbour, own-fact leak row not a neighbour leak, o*-equal neighbour dropped, pass-shift
  denominator = passing reads).
- `cluster/csis/audit_v3.sbatch`: `HP_VARIANT` (e.g. `mom2`) selects `<METHOD><variant>_<model>.yaml`, created from the base
  file with only `mom2_adjustment` switched on.

## Comment 1 run: ROME + statistics on GPT-J (and, for parity, on GPT-2 XL's 78 facts)
- GPT-J: EasyEdit's GPT-J ROME hparams (layer 5) with `mom2_adjustment: true`; statistics
  `transformer.h.5.mlp.fc_out_float32_mom2_100000.npz` (md5 `989e850f4bfcb67f7aaf8bc951923cb3`); the 128 admitted facts;
  independent mode, seed 0.
- GPT-2 XL: `ROMEmom2_gpt2-xl.yaml` from plan 1.1, the 78 admitted facts (E2 covered only the draft's 12).
- **Predictions (written before submission):**
  - P8.1 GPT-J ROME+stats edits succeed on ≥ 90% of facts.
  - P8.2 GPT-J ROME+stats stale reverse reads rise to the MEMIT/AlphaEdit level (≥ 70%; ROME without statistics: 30%).
  - P8.3 GPT-J ROME+stats neighbour damage falls: same-relation neighbours keep their correct answer on ≥ 90% of reads
    (ROME without statistics: well below), and o* becomes a neighbour's top answer on ≤ 5% (without statistics: 24%).
  - If P8.2 and P8.3 hold, ROME's low stale rate on GPT-J is an effect of running it without statistics, and the
    "single score rewards the worst editor" example must be stated as such (it remains a valid example of why Q2 and Q3
    must be read together, but it is a configuration effect, not a property of ROME).

## Jobs
| Job | What | Outcome |
|---|---|---|
| 18032 | tests | FAILED after 1 s, empty log: **the account's disk quota is full** (see below) |
| 18033 | GPT-J ROME+stats | cancelled before it started (would have run the old snapshot: the sync had failed) |
| 18034 | GPT-2 XL ROME+stats (78 facts) | cancelled before it started (same reason) |

### Blocker: shared disk quota exhausted (2026-11-05 ~02:30)
- `quota -s` for `yashsinha` on `/nfs_home`: **1000 GB used, soft 999 GB (6-day grace), hard 1000 GB** (was 807 GB on
  2026-10-31). The sync's remote `tar` could not write the new snapshot, and jobs cannot write their logs.
- Our project uses 52 GB (`models` 29 GB, `EasyEdit` 14 GB incl. statistics and projections, `env` 7.8 GB, `cache` 1.1 GB,
  runs/logs/snapshots ~0.1 GB); the rest of `F20220612_Aadit/` is unchanged (127 GB). The ~140 GB increase since 31 October
  is elsewhere on the shared account, outside our folder; nothing outside our folder was inspected further or touched.
- The only part of ours that is safe to delete is the 1.1 GB conda package cache; not done without the user's go-ahead.
- Comment 1 (ROME+stats on GPT-J) waits for space. The live cluster code is still snapshot `20261031-160121` (old).

### Unblocked (2026-11-05 ~03:05, user chose option 2)
- Deleted our own conda package cache `EA_ROOT/cache/conda_pkgs` (1.1 GB, 53 entries of base-env packages; the env keeps its
  hard-linked files and still imports torch/transformers). Free space under the hard limit afterwards: 1,040,112 KB (~1 GB).
- Synced code snapshot `repo_snapshots/20261105-030703`; verified on the cluster (contains `HP_VARIANT`, analyze_audit v1.2).
- **18035 tests: ALL PASSED** (shipped suite + phase 2, incl. the new reviewer-rule cases).
- **18036** GPT-J ROME+stats (128 facts) and **18037** GPT-2 XL ROME+stats (78 facts), `afterok:18035`, submitted.
- Risk: the quota is shared; other users can fill the freed space again.

## Results: comment 2 applied locally on the mirrored data (no cluster needed)
- Torch-free part of `tests/test_analyze_audit.py` (all hand-made reviewer-rule cases) **passed locally**; the full test
  suite needs the cluster.
- Re-analysis with v1.2 of E4, E5, E7v2 → `research-log/results/v1.2/` (analysis reports, summaries, details).

| Metric | v1.1 (reported before) | v1.2 (corrected) |
|---|---|---|
| stale reverse reads, GPT-2 XL MEMIT | 113/148 = 76% | **90/120 = 75%** (successful edits); all other runs unchanged |
| survival of pre-edit rank-1 reverse reads | 72 / 98 / 95%; 37 / 97 / 97% | unchanged in substance (MEMIT GPT-2 XL 90/92) |
| reverse-from-new reads reaching rank 1 | 0 of 1,215 | **0 of 1,187** (successful edits) |
| contract violations, GPT-2 XL MEMIT | 142/153 = 93% | 115/125 = 92%; 1:1 relations 20/20 |
| neighbours keep correct answer (GPT-2 XL R/M/A) | 92 / 98 / 96% | **89 / 96 / 94%** |
| neighbours keep correct answer (GPT-J R/M/A) | 68 / 98 / 98% | **52 / 97 / 98%** |
| o* in a neighbour's top 5 (GPT-2 XL R/M/A) | 15 / 4 / 7% | **21 / 4 / 10%** |
| o* in a neighbour's top 5 (GPT-J R/M/A) | 32 / 4 / 4% | **47 / 4 / 4%** |
| passing reads with JS > 0.01 bit (GPT-2 XL R/M/A) | 84 / 32 / 37% (over all controls) | **88 / 25 / 33%** (over passing neighbours) |
| passing reads with JS > 0.01 bit (GPT-J R/M/A) | 65 / 38 / 32% | **94 / 26 / 20%** |
| median neighbour JS (GPT-2 XL; GPT-J) | 0.073 / 0.0050 / 0.0056; 0.18 / 0.0057 / 0.0039 | **0.066 / 0.0026 / 0.0028; 0.23 / 0.0034 / 0.0020** |
| E7v2 after 60 edits: stale (edits holding) R/M/A | 0 / 75 / 73% | 0/10, **56/73 = 77%**, 82/113 = 73% |
| E7v2 after 60 edits: untouched neighbours correct | 5 / 78 / 85% | **2 / 73 / 83%**; median JS 0.82 / 0.14 / 0.11 |
| cross-model common facts, GPT-2 XL MEMIT stale | 93/120 = 78% | 79/104 = 76% |
| prediction P4.5 (controls ≥ 90% correct) | confirmed | MEMIT, AlphaEdit yes; **ROME 89% (narrow miss)** |

Interpretation: the own-fact controls had inflated the "passes but shifts" share for MEMIT/AlphaEdit (o* is strengthened
on its own fact by design) and masked ROME's neighbour damage (own-fact controls always keep o*). The corrected statement is
weaker for MEMIT/AlphaEdit (a quarter to a third of passing neighbours shift) and stronger against ROME.

## Documents updated
- `RESULTS.md`: corrections box at the top + 27 passages (headline, §4.3, §4.4, §5.1–5.3, §6, §7.1, §8, §9, §10).
- Results page republished (version 2, same link): tiles, findings, Table 5 (new rows: survival, own-fact check, pass-share
  over passing reads), heatmap metrics, Table 6, Figures 4–5 (neighbours only), Table 7, Table 8, sequential panels and
  Table 9, explorer (stale "n/a" for failed edits), scorecard P4.2/P4.5/P7.3.

## Result: ROME + statistics on GPT-2 XL, 78 facts (job 18037, 22:39, all checks passed; analysed with v1.2)
`results/v1.2/analysis_E2X_gpt2-xl_ROMEstats/`. Seed 0, same facts and probes as E4.

| | ROME (no stats) | **ROME + stats** | MEMIT | AlphaEdit |
|---|---|---|---|---|
| edited question new@1 | 100% | **100%** | 82% | 100% |
| paraphrase/context new@1 | 75% | 69% | 55% | 78% |
| forward old still rank 1 | 15% | 20% | 33% | 14% |
| stale reverse reads (successful edits) | 57% [48, 66] | **73%** [65, 81] | 75% | 74% |
| survival of pre-edit rank-1 reverse reads | 72% | **94%** [89, 98] | 98% | 95% |
| contract violations, reverse-from-new | 97% | 88% | 92% | 91% |
| neighbours keep correct answer | 89% | **96%** | 96% | 94% |
| new value in a neighbour's top 5 | 21% | **5%** | 4% | 10% |
| passing neighbours with JS > 0.01 bit | 88% | 60% | 25% | 33% |
| median neighbour JS (bits) | 0.066 | 0.0125 | 0.0026 | 0.0028 |

- With statistics, ROME's stale-read rate rises to the MEMIT/AlphaEdit level (57% → 73%) and its neighbour damage falls to
  their level (leaks 21% → 5%), confirming E2 (12 facts) at 78 facts. Its distribution shift stays larger than MEMIT's and
  AlphaEdit's (median 0.0125 vs ~0.003 bits).
- Implication (pending GPT-J, job 18036, 50/128 facts done at 03:43): ROME's low stale rate is a property of running it
  **without** statistics, i.e. of broad overwriting, not of ROME's rank-one update as such.

## Result: ROME + statistics on GPT-J, 128 facts (job 18036, 1:03:20, all checks passed; analysed with v1.2)
`results/v1.2/analysis_E2J_gpt-j_ROMEstats/`. Checks: worst A 0, smallest B 0.027, worst C 0; per-edit update norm
4.94 / 6.17 / 9.73 (min / median / max).

| | ROME (no stats) | **ROME + stats** | MEMIT | AlphaEdit |
|---|---|---|---|---|
| edited question new@1 | 100% | **100%** | 100% | 100% |
| paraphrase/context new@1 | 99% | 96% | 91% | 93% |
| stale reverse reads | 30% [23, 37] | **72%** [65, 78] | 78% | 78% |
| survival of pre-edit rank-1 reverse reads | 37% | **88%** [83, 92] | 97% | 97% |
| contract violations, reverse-from-new | 87% | 86% | 88% | 85% |
| neighbours keep correct answer | 52% [44, 59] | **92%** [88, 96] | 97% | 98% |
| new value in a neighbour's top 5 | 47% | **9%** | 4% | 4% |
| new value becomes a neighbour's top answer | 50/207 = 24% | **7/207 = 3%** | 1/207 | 1/207 |
| passing neighbours with JS > 0.01 bit | 94% | 35% | 26% | 20% |
| median neighbour JS (bits) | 0.23 | 0.0053 | 0.0034 | 0.0020 |

Same comparison on GPT-2 XL (job 18037): new value becomes a neighbour's top answer 7/114 = 6% → 1/114 = 1%.

**Predictions:** P8.1 (edit success ≥ 90%) confirmed (100%). P8.2 (stale ≥ 70%) confirmed (72%). P8.3 (neighbours ≥ 90%
correct, o* top answer ≤ 5%) confirmed (92%, 3%).

**Conclusion.** The teammate's concern is confirmed on both models: ROME's low stale-read rate and its neighbour damage are
effects of running it **without** covariance statistics (EasyEdit's default; the original ROME uses them). With statistics,
ROME behaves like MEMIT and AlphaEdit: stale reverse reads 72–73%, survival 88–94%, small side effects (slightly larger than
MEMIT/AlphaEdit: median neighbour JS 0.0053 vs 0.002–0.003 on GPT-J; 0.0125 vs ~0.003 on GPT-2 XL). The "single score
rewards the worst editor" example is therefore a **configuration** effect; it remains a valid demonstration that Q2 and Q3
must be read together (a configuration that breaks more reverse reads does so by overwriting), but it must not be stated
as a property of ROME. Main-text ROME numbers should be ROME with statistics; ROME without statistics becomes an ablation.
