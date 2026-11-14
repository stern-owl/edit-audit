# Related-work check for the phase-6 claims (2026-11-11)

Purpose: before spending more compute, check whether the strongest phase-6 results (N1 lost updates and key-overlap
predictor, N5 compensation is not undo, E10 standard metrics miss failures, N4 conflict-aware batching) are already
published. Searches of 2026-11-11 (web search; abstracts, repository pages and, where accessible, full text). Items marked
*unverified* were seen only as abstract or snippet and must be read in full before writing.

## Summary of verdicts
| Our result | Closest prior work | Verdict | How to claim it |
|---|---|---|---|
| **N1** lost updates between *compatible* edits; order dependence; key-overlap predictor; AlphaEdit "first writer wins" | Pitfalls (ICLR 2024) ConflictEdit; Duan et al. NAACL 2025 (same-subject perturbation); MEMIT-Merge (ACL Findings 2025); LEMoE order sensitivity | **Still novel as far as found** | Differ explicitly: our pairs are logically compatible and need not overwrite each other; different subjects sharing an *object*; both orders compared; predictor from keys before editing; editor semantics. Cite all four. |
| **N5** compensation is not an undo | Pitfalls Round-Edit (2023); **Caddeo, Sanguinetti, Atzori, Applied Sciences 2026** (edit-then-revert, ROME/MEMIT, GPT-2 XL/GPT-J, CounterFact); retractbench (Nov 2026, Qwen2.5) | **Largely known; downgrade** | Present as confirmation plus extensions: weight footprint of the undo exceeds the edit (1.08-1.63×), systematic over-compensation of the old answer (95-99%), AlphaEdit included, compensation after intervening edits, path-level audit, and the database reading (logical compensation vs physical undo log). Do not present "the revert is not a perfect inverse" as new. |
| **E10** standard metrics pass edits the audit rejects | RippleEdits (TACL 2024); MQuAKE (EMNLP 2023); CounterFact+ / BAKE | **General point known** | Our difference: the same edited models scored both ways, path-level verdicts including reverse paths, and the share is quantified (440/441). Present as motivation, not as a discovery. |
| **N4** (planned) conflict-aware batching | MEMIT-Merge (same-subject batch conflicts); CollabEdit (ICLR 2025, overlap between edit requests, *unverified* how); conflict-aware batch grouping in an attack paper (CareAttack, arXiv 2606.18310, *unverified*) | **Partly occupied** | Must target conflicts these do not cover (shared objects, cross-relation, order), use the key-overlap predictor, and compare with MEMIT-Merge on same-subject batches. Read CollabEdit in full first. |

## Paper by paper

**Li et al., "Unveiling the Pitfalls of Knowledge Editing for Large Language Models", ICLR 2024** ([arXiv 2310.02129](https://arxiv.org/abs/2310.02129)).
ConflictEdit: *Reverse Edit* (e1 = (s1, r1, o1 → o2), e2 = (o2, r2, s1 → s2) with r2 the reverse relation) and *Composite
Edit* (two edits linked by a logical rule through a tied fact). Edits applied in one fixed order (e1 then e2); metrics
(Conflict Score, Conflict Magnitude, Tied Fact Damage) test whether the *second* edit correctly overrides the first.
Round-Edit: edit o1 → o* then back o* → o1; measures distortion (JS over the true label set, share of other true labels
that drop). FT, MEND, ROME, MEMIT on GPT-2 XL and GPT-J. No order comparison, no predictor from model internals.
*Relation to us:* their conflicting pairs are designed to overwrite each other; ours (shared object) are compatible and
should both hold. Round-Edit is the first version of our N5.

**Caddeo, Sanguinetti, Atzori, "On Reversibility as Language Model Behavioral Property in Parametric Knowledge Editing",
Applied Sciences 16, 2026** ([doi 10.3390/app16136567](https://doi.org/10.3390/app16136567); full text blocked (HTTP 403),
details from a repository that cites it). Edit-then-revert with ROME and MEMIT on CounterFact, GPT-2 XL and GPT-J;
log-probabilities of new and original targets; concludes reversibility should be read behaviourally, not as a parametric
inverse. *Relation to us:* same setting and core message as N5. **Must be read in full** (request through the library or
the authors) to see whether they measure weight distance, over-compensation or neighbour effects.

**retractbench** ([github.com/capnknives/retractbench](https://github.com/capnknives/retractbench), active, results dated
3 Nov 2026). Write, revoke, probe on Qwen2.5-1.5B/7B; GRACE-style codebook, ROME, SVD-truncation reversal; exact-match and
probability scores, control for side effects of the undo itself; finds approximate undo never exact, only restore/subtract
exact. *Relation to us:* parallel work on undo with a modern model; our physical-restore check C is their "restore".

**Duan et al., "Related Knowledge Perturbation Matters: Rethinking Multiple Pieces of Knowledge Editing in Same-Subject",
NAACL 2025 (short)** ([arXiv 2502.06868](https://arxiv.org/abs/2502.06868)). Several relations of the *same subject*
edited one after another; ROME and MEMIT show later edits interfering with earlier ones (benchmark S2RKE).
*Relation to us:* interference between successive edits, but same subject; our lost updates are between different subjects
sharing an object, both orders, with a predictor.

**Dong, Shen, Xia, "MEMIT-Merge", ACL Findings 2025** ([arXiv 2502.07322](https://arxiv.org/abs/2502.07322)). Same-subject
edits in one MEMIT batch conflict because identical keys must map to different values; merging values per key keeps success
above 90%. *Relation to us:* key-level explanation of conflicts (supports our key-overlap predictor) for identical keys;
ours predicts conflicts from graded key similarity across different subjects.

**Zheng et al., "CollabEdit: Towards Non-destructive Collaborative Knowledge Editing", ICLR 2025**
([arXiv 2410.09508](https://arxiv.org/abs/2410.09508)). Collaborative editing across parties; names knowledge overlap,
conflict and forgetting; one snippet says a residual-based measure detects overlap between edit requests. *Unverified*;
read before N4.

**LEMoE (arXiv 2406.20030).** Lifelong editing with a mixture-of-experts adaptor; the same edit set in shuffled orders
changes performance by 20-90 points. *Relation to us:* order sensitivity shown for an adaptor method, not for
locate-then-edit weight edits and not pair-level.

**Cohen et al., "Evaluating the Ripple Effects of Knowledge Editing in Language Models", TACL 2024**
([arXiv 2307.12976](https://arxiv.org/abs/2307.12976)). RippleEdits, 5K edits; editors fail to propagate implied updates
(logical generalisation, composition, aliasing); in-context editing best. **Zhong et al., "MQuAKE", EMNLP 2023**
([ACL Anthology](https://aclanthology.org/2023.emnlp-main.971)). Multi-hop questions after edits; ROME on GPT-J answers
7.4% vs 40.5% before. *Relation to us:* establish that single-fact metrics miss knock-on failures; our E10 adds the same-edit
comparison and reverse-path (stale read) verdicts.

## Consequences for the plan
1. **Lead with N1** (lost updates between compatible edits + key-overlap predictor + editor semantics); it is the most
   novel result found. The GPT-J and seed-1 runs (entry 12) are the right next step.
2. **Reframe N5** as confirming and extending Round-Edit / Caddeo et al.; keep the database framing (logical compensation
   vs physical undo log) and the new measurements. Obtain the Caddeo et al. full text.
3. **E10** is motivation; cite RippleEdits, MQuAKE, CounterFact+, BAKE.
4. **N4** must be designed against MEMIT-Merge and CollabEdit (read both in full first).
5. Still to check: knowledge-editing surveys of 2025-2026 for "transaction", "serializability", "commutativity" framings;
   the Spectral collapse paper (arXiv 2601.11042) and BetaEdit (arXiv 2605.09285) for sequential-editing claims.
