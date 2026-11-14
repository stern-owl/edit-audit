# Novelty check and the redesigned experiment set

_Written 2026-11-05. Based on literature searches run the same day (sources at the end). **The prior-work summaries come
from search results and abstracts; each paper must be read in full before the related-work section is written.**_

## 1. Verdict in one paragraph
Several things the paper currently presents as findings are already known: edits fail in the reverse direction (Ma et al.,
BAKE/BIRD, 2023; Xu et al., 2026), full-distribution neighbour divergence catches side effects that rank metrics miss
(CounterFact+ / Neighborhood KL, Hoelscher-Obermaier et al., 2023), sequential editing collapses ROME and MEMIT while
AlphaEdit holds up (many 2024–2026 papers), edits decay under fine-tuning (two 2025 papers), and edits can be reversed from
the weights (ICLR 2026). What we found **no** prior work on is the database half of the paper: integrity constraints and
admission control for edit requests, commutativity and serializability of edit sequences, atomicity of batched edits,
compensating edits as transactional undo, and cost-based planning of which access paths to audit. The paper should
therefore lead with those, and use the existing results (stale reverse reads, hidden drift, sequential collapse) as the
motivating evidence and the validation of the audit, not as the contribution.

## 2. Novelty of what we have and what was planned
| Item | Closest prior work | Overlap | What is still ours | Verdict |
|---|---|---|---|---|
| Stale reverse reads (Q2) | BAKE/BIRD (Ma et al. 2023): edited models fail in reverse; Xu et al. 2026 (TMLR) | high: the phenomenon | per-path audit with verified runs; "survival of pre-edit rank-1 reverse reads" (95–98%); relation-contract labels (1:1 vs non-functional) | **not a contribution alone**; keep as evidence |
| Reverse-from-new never reaches rank 1 (Q3) | BAKE's reversibility metric covers the direction | medium | the 1:1 contract view: the edit itself violates a functional dependency | partly ours |
| Hidden drift, full-distribution divergence (E3) | CounterFact+ Neighborhood KL (2023) | **high** | "passes rank-1 specificity yet shifts" split; per-path; Q2+Q3 joint reading | **metric not novel**; cite NKL, keep as tool |
| ROME paradox (fewest stale reads by overwriting) | Pitfalls (Li et al. 2024) on distortion; CounterFact+ on specificity | medium | the explicit Q2-vs-Q3 trade-off as an argument for per-question reporting | ours, modest |
| Sequential collapse (E7) | Gupta et al. 2024; REVIVE (ACL 2026); NeurIPS 2026 batch-equivalent sequential editing; r-ROME | **high** | sentinel + checkpoint audit design; stale reads under accumulation; "edits kept, other knowledge erodes" for AlphaEdit | methodology ours, findings largely known |
| Batch vs sequential (E8) | "Is bigger batch always better" (2024); NeurIPS 2026 | high | (none unless reframed as atomicity, N4 below) | **reframe or drop** |
| Inverse-index repair (E11) | **BIRD** (bidirectional editing objective) | **very high** | almost nothing | **drop** (cite BIRD; optionally audit BIRD as an extra editor) |
| Durability under fine-tuning (E12 variant) | two 2025 papers on edit decay under fine-tuning | high | – | drop the fine-tuning variant |
| Durability under quantization (E12) | CACHE-UK (2026): editing *already quantized* models, 4-bit hurts paraphrase generalisation | medium | quantizing an *edited* model and auditing stale reads/drift; edit-then-quantize vs quantize-then-edit | **partly novel**, tier 2 |
| Undo by reversing edits | Tracing and Reversing Edits (ICLR 2026): reverse from weights | medium | compensating edit (o* → o) vs physical restore, audited on all paths | **partly novel** (N5) |
| Predicting edit outcome before editing | Knowledge Spectrum (2025): popularity/familiarity predict efficacy and side effects; "perplexingness" | medium | predicting *consistency violations* (stale reads, contract violations, leaks) and acting on it as admission control | **partly novel** (N2) |
| Comparison with standard metrics (E10) | Pohl et al. 2025; CounterFact+ | medium | failure-type table on identical edits incl. contract violations | needed for positioning, not novelty |
| Modern model (E6), seeds (E8s), Wikidata check (E13) | – | – | – | **needed for credibility**, not novelty |
| Integrity constraints on edits | logical-rule KE benchmarks (2026) propagate entailed facts; no work on FD / key constraints for edit admission | low | constraint declaration, violation detection, admission, cascading repair | **novel** |
| Commutativity / serializability of edits | same-subject perturbation (2025); knowledge-conflict pairs (Pitfalls 2024); none tests A;B = B;A | low | the commutativity test, conflict prediction, serializable schedules | **novel** |
| Audit planning (which paths to read under a budget) | ComprehendEdit samples similar/dissimilar items (multimodal); nothing for path selection | low | cost-based audit plans, transfer across models/methods | **novel** |

## 3. Re-positioned contribution for the paper
1. **A transactional specification for knowledge edits**: declared relation constraints (functional dependencies, keys),
   per-path read semantics (visibility, stale reads, side effects), and verified write/undo (checks A/B/C).
2. **Database mechanisms applied to edits, each with new experiments** (N1–N5 below): admission control, serializability,
   atomicity, compensation, audit planning.
3. **Evidence that the specification is needed** (existing results, cited against prior work): stale reverse reads survive
   95–98% of the time; specificity passes while distributions move; the ROME paradox; sequential erosion.

## 4. The new experiments (designs; predictions to be written before each run)

### N1. Edit commutativity and conflict-serializability (novel, tier 1)
- **Question.** Do two edits commute? In a database, two writes to different items commute and a scheduler may reorder them;
  writes to the same item do not. Is there an analogue for edits, and can conflicts be predicted?
- **Design.** Pairs of admitted facts (A, B), GPT-2 XL then GPT-J, MEMIT and AlphaEdit (ROME as a reference). For each pair:
  apply A then B, read everything; restore; apply B then A, read everything; restore (checks A/B/C each time). Pair classes,
  fixed before running:
  - disjoint: different relation, no shared entity;
  - same relation, no shared entity;
  - **shared object**: o*_A = o_B or o_A = o*_B (e.g. Amazon → Zuckerberg and Facebook → Bezos);
  - **chained**: o*_A is B's subject or B's old object;
  - same-relation neighbours of each other (B is A's control).
- **Metrics.** Commutativity gap per pair: JS between the AB and BA reads on every path (both facts, their neighbours,
  sentinels); share of paths whose audit verdict (rank-1 outcome) differs between orders; gap in edit success of the first
  vs second edit.
- **Conflict predictor.** Cosine similarity of the two edits' MLP keys at the edited layers (the subject representations the
  editors write to) and of their value updates; entity overlap. Test whether high key overlap predicts non-commutation (AUROC).
- **Payoff.** A "conflict graph" over edit requests; schedules that batch only commuting edits; a direct DB-theory result.
- **Cost.** ~100 pairs × 2 orders × (2 edits + reads) ≈ 1.5–2 GPU-h on GPT-2 XL; GPT-J ~5 h. Driver: a new `--mode pairs`.

### N2. Integrity constraints and admission control for edit requests (novel framing, tier 1)
- **Question.** Can declared constraints flag, before any weights change, edits that will produce inconsistent states, and
  can a cascading edit repair them?
- **Design.**
  - Constraints per relation (already declared in `relation_templates_v3.json`): forward functional dependency
    (subject → object) and, for 1:1 relations, the inverse dependency (object → subject).
  - **Admission check:** an edit (s, r, o → o*) violates the inverse FD when o* already has a subject s' (e.g. "capital of
    France := Rome" while Rome is Italy's capital). Flag every v3 edit as violating / not violating.
  - **Outcomes:** compare audit results of flagged vs unflagged edits (contract violations, the new object's own fact,
    neighbour leaks).
  - **Cascading repair (DB "ON UPDATE CASCADE"):** for flagged edits also apply the edit that restores the constraint
    (s' gets a new object, or s' is moved), as one batch and as two sequential writes; audit whether the database-consistent
    state is reached on all paths and at what side-effect cost.
  - **Predicting violations from pre-edit reads:** pre-edit P(o* | s, r) ("perplexingness"), reverse-path strength, subject
    position/tokenisation, key norm; predict stale reads and leaks (AUROC), compare with Knowledge-Spectrum-style predictors.
- **Cost.** Admission check and predictors: no GPU (logged reads). Cascade runs ~1–2 GPU-h.

### N3. Audit planning: which access paths to read under a budget (novel, tier 1, no GPU)
- **Question.** The full catalogue is expensive (here ~11 paths per fact, more with paraphrases and models). Which subset of
  paths catches most violations? Does a plan learned on one model/method transfer?
- **Design.** From the logged reads of all runs: each path type has a cost (forward passes, incl. greedy generation) and a set
  of violations it detects per edit. Greedy weighted set cover and an exact ILP for small budgets; report detection rate vs
  budget curves; train the plan on GPT-2 XL MEMIT, test on GPT-J and on AlphaEdit/ROME; also an adaptive plan that reads
  cheap paths first and stops early (like a query plan with early termination).
- **Cost.** None (CPU, existing data). Implements the draft's "audit planning" agenda item directly.

### N4. Atomicity of batched edits (reframed E8, tier 2)
- **Question.** Is a batched edit all-or-nothing? A database transaction commits all writes or none; does a MEMIT/AlphaEdit
  batch partially commit, and are the members that fail predictable from conflicts (N1)?
- **Design.** Batches of size 5, 10, 30, 60 drawn (a) at random, (b) to maximise and (c) to minimise predicted conflict (N1's
  key overlap). Metrics: share of batches with partial commit; per-member success vs its conflict score; stale reads and
  sentinel drift vs batch composition.
- **Cost.** ~2 GPU-h. Depends on N1's predictor.

### N5. Compensating edits vs physical undo (partly novel, tier 2)
- **Question.** If an edit must be withdrawn, is a compensating edit (o* → o) a true undo, or does it leave residue, as a
  compensating transaction may in a database without an undo log?
- **Design.** For each fact: edit (o → o*), then compensate (o* → o); compare the final model with the unedited one on every
  path (verdicts, JS) and with physical restore (exact by check C). Also after k unrelated later edits (compensation that is
  not the last write). MEMIT, AlphaEdit, ROME; GPT-2 XL.
- **Prior work to cite and differ from:** reversal from weights without knowing the edit (ICLR 2026).
- **Cost.** ~1–2 GPU-h.

### N6. Durability under quantization (partly novel, tier 2)
- **Design.** As E12 in `NEXT_EXPERIMENTS.md`, plus the order question: edit-then-quantize vs quantize-then-edit (a physical
  vs logical operation that may not commute), audited on all paths. Cite CACHE-UK and the fine-tuning decay papers.

## 5. What stays from `NEXT_EXPERIMENTS.md`, what changes
| Previous item | Decision |
|---|---|
| E6 modern model | **keep, tier 1** (credibility; still needs the model decision) |
| E10 vs standard metrics | **keep, tier 1** (positioning against CounterFact+, BAKE, EasyEdit); add NKL and BAKE's reversibility as compared metrics |
| E8s seeds | **keep** |
| E13 Wikidata check | **keep** |
| E9 ablations | keep, tier 3 (closes the draft's open causes; low novelty) |
| E8 batch | **replaced by N4** (atomicity) |
| E11 inverse-index repair | **dropped** (BIRD); optionally audit BIRD as an additional editor in E10 |
| E12 durability | **replaced by N6** (quantization only, with the order question) |
| E14 natural-language paths | tier 3 |
| E15 longer sequences | **dropped** (crowded area) |

## 6. Suggested order and cost
| Order | Experiments | GPU | Notes |
|---|---|---|---|
| 1 | **N3** audit planning, **N2** admission check + predictors, **E10** | none | all from logged reads; can start immediately |
| 2 | **N1** commutativity on GPT-2 XL | ~2 h | needs `--mode pairs` in the driver + offline test |
| 3 | **N2** cascading repair, **N5** compensation | ~3 h | small driver additions |
| 4 | **E6** modern model; N1 on GPT-J / modern model | ~15 h | after the model decision and disk space |
| 5 | **N4** atomicity, **N6** quantization, E8s seeds | ~5 h | |

Disk: N1–N5 write only small outputs (tens of MB). E6 needs ~40 GB of weights and statistics; the shared quota is full, so it
must wait for space.

## 7. Prior work to read in full before writing (from the searches of 2026-11-05)
- Ma et al., "Untying the Reversal Curse via Bidirectional Language Model Editing" (BAKE, BIRD), arXiv 2310.10322.
- Xu et al., "Evaluating the Reversal Curse in Model Editing", TMLR 2026 (already cited in the draft; check overlap with BAKE).
- Hoelscher-Obermaier et al., "Detecting Edit Failures in Large Language Models: An Improved Specificity Benchmark"
  (CounterFact+, Neighborhood KL), ACL Findings 2023, arXiv 2305.17553.
- Li et al., "Unveiling the Pitfalls of Knowledge Editing for Large Language Models", ICLR 2024 (knowledge conflict, distortion).
- Simon & Ewetz, "Beyond Single Edits" (SEED), Findings of EMNLP 2026.
- Pohl et al., "Towards a Principled Evaluation of Knowledge Editors", L2M2 @ ACL 2025.
- "Related Knowledge Perturbation Matters: Rethinking Multiple Pieces of Knowledge Editing in Same-Subject", arXiv 2502.06868.
- "Is Bigger Edit Batch Size Always Better? An Empirical Study on Model Editing with Llama-3", arXiv 2405.00664.
- "Rethinking Sequential Locate-Then-Edit: Optimality and Stability", NeurIPS 2026.
- REVIVE / sequential editing collapse, ACL 2026; "On the Superimposed Noise Accumulation Problem…", arXiv 2505.07899;
  r-ROME (implementation artefacts in ROME).
- "Can Fine-Tuning Erase Your Edits?", arXiv 2511.05852; "On the Retention of Edited Knowledge in Fine-tuned Language Models",
  arXiv 2507.14198.
- "Tracing and Reversing Edits in LLMs", ICLR 2026 (arXiv 2505.20819).
- "Diagnosing Model Editing via Knowledge Spectrum", arXiv 2509.17482; "How Well Can Knowledge Edit Methods Edit Perplexing
  Knowledge?".
- "Benchmarking Knowledge Editing using Logical Rules", arXiv 2606.10554.
- CACHE-UK (editing quantized LLMs), arXiv 2607.28292.
