# Next experiments

> **Superseded in part (2026-11-05):** after the novelty check in `NOVELTY_AND_NEW_EXPERIMENTS.md`, E11 and E15 are dropped,
> E8 is replaced by N4 (atomicity) and E12 by N6 (quantization with the order question); E6, E10, E8s, E13 stay; new N1–N5.

_Written 2026-10-31 ~16:10 IST, after the phase 2 results (`RESULTS.md`). Nothing below has been run. Each experiment
gets its predictions written into a dated entry **before** its job is submitted (rule from `README.md`). Experiment IDs
continue the numbering of `EXPERIMENTS.md` (E0–E10); E11–E15 are new._

## Why these experiments: the reviewer risks they answer

| Risk a reviewer will raise | Answered by |
|---|---|
| "GPT-2 XL and GPT-J are 2019–2021 models; does this hold on a current model?" | E6 |
| "You claim the audit catches what standard evaluation misses; show it on the same edits" | E10 |
| "Scale-up results use one seed" | E8s (seeds) |
| "187 hand-written facts are unverified" | E13 (Wikidata check) |
| "Stale reverse reads are the known reversal curse; what does the database view add?" | E11 (inverse-index repair), E8 (batch as one transaction), E12 (durability) |
| "The draft's two open causes (position 0, shared template) are still open" | E9 |
| "Fixed templates only" | E14 |
| "One order, 60 edits" | E15 |

## Priority and order

| Tier | ID | Experiment | GPU cost (estimate) | Needs a decision? | Code status |
|---|---|---|---|---|---|
| 1 | E6 | Modern 7–8B model | stats 4–8 h + projection ~3 CPU-h + audit ~4 h | **yes: Llama-3-8B or Qwen2.5-7B** | driver/scorer ready; stats + projection jobs ready; hparams to write |
| 1 | E10 | Audit vs standard metrics, same edits | none (from logged reads) | no | to write: `standard_metrics.py` |
| 1 | E8s | Seeds 1 and 2 for E4 and E5 | ~2 h (GPT-2 XL) + ~7 h (GPT-J) | no | ready (`audit_v3.sbatch`, `SEEDS="1 2"`) |
| 1 | E13 | Automatic fact check against Wikidata | none | no | to write: `check_facts_wikidata.py` |
| 2 | E8 | Batch editing as one transaction | ~1 h | no | ready (`--mode batch`) |
| 2 | E11 | Inverse-index repair (new) | ~2 h | target rule (proposed below) | small additions to the driver |
| 2 | E9 | Causal ablations: position 0, neighbour templates | < 1 h | no | templates + small screening run |
| 2 | E12 | Durability under quantization (new) | 1–2 h | no | to write: re-read after int8/4-bit |
| 3 | E14 | Natural-language paths | ~1 h | source of questions | to write |
| 3 | E15 | More orders, longer sequences | ~2 h (GPT-2 XL), ~6 h (GPT-J) | no | ready |

Suggested sequence: **E10, E13, E9, E8, E8s (GPT-2 XL) now in parallel** (no decision needed, ~4–5 GPU-h under the
account's 2-GPU cap) → **E6** as soon as the model is chosen (statistics job first; it is the long pole) → **E11, E12** →
E8s (GPT-J), E14, E15 as time allows.

---

## E6. Cross-model audit on a modern 7–8B model (plan 2.5)
- **Question.** Do stale reverse reads (Q2), invisible reverse-from-new reads (Q3) and neighbour drift persist on a current
  architecture (RoPE, SwiGLU MLP, grouped-query attention, larger vocabulary)?
- **Model options.** Llama-3-8B: standard in editing papers (AlphaEdit's own evaluation), gated (Meta approval + Hugging Face
  token on the cluster). Qwen2.5-7B: open; no published covariance statistics. Both need statistics computed by us unless a
  trustworthy published set is found.
- **Design.** fp32 weights pinned to a revision; EasyEdit's hparams for the model with only machine-specific fields changed
  (as for GPT-J); covariance statistics for the MEMIT/AlphaEdit layers (EasyEdit `layer_stats`, Wikipedia, 100k samples,
  computed once on GPU, md5-logged); AlphaEdit projection with `compute_alphaedit_P_v2.py`; screening v3 (frozen rules, no
  re-design); audit of ROME, MEMIT, AlphaEdit, independent mode, seed 0, then sequential (E7 design: held-out sentinels,
  checkpoints) if time allows.
- **Checks specific to this model.** Scorer v4 prepends BOS for Llama-3 (unit-tested on a tiny Llama); confirm on the real
  tokenizer that answer tokens and BOS are as expected before screening; verify the AlphaEdit cache size from the
  `down_proj` input dimension (`alphaedit_reset` handles `nn.Linear`).
- **Resources.** Weights ~32 GB fp32 + statistics ~5 × (input dim² × 4 bytes) ≈ 4 GB for 5 layers of dimension 14336 +
  projection of the same size; check the shared quota first (~140 GB free after GPT-J). One A100 80 GB suffices for fp32 8B.
- **Outputs.** As E5: `analysis_E6_<model>/`, per-fact tables, overlap with GPT-2 XL/GPT-J facts.

## E10. The audit vs standard evaluation, on the same edited models (plans 4.1, 4.2)
- **Question.** Which failures does each evaluation flag for the *same* edits? This is the paper's practical claim.
- **Standard metrics computed from the reads already logged** (no new GPU runs):
  - CounterFact-style: efficacy = P(o*) > P(o) on the edited question; paraphrase score = same on paraphrase paths;
    neighbourhood score = P(correct) > P(o*) on neighbour paths; magnitudes as in Meng et al. (2022).
  - EasyEdit-style: teacher-forced token accuracy of o* on the edited question and paraphrases, locality as unchanged top-1
    on neighbours (recomputed from logged token log-probabilities where possible; otherwise one cheap re-run that saves
    EasyEdit's own returned metrics).
- **Failure taxonomy per edit** (draft's agenda, `next-steps.txt` Exp 8): incomplete write (a forward path misses o*),
  stale association (reverse-from-old returns s), inverse inconsistency (contract violation on reverse-from-new),
  locality drift (control JS > 0.01 bit while rank-1 holds), update corruption (control loses its correct answer),
  rollback failure (check C; expected never).
- **Table to produce.** Rows = failure types; columns = "flagged by CounterFact scores", "flagged by EasyEdit metrics",
  "flagged by the audit"; counts per method and model; plus the share of edits rated fully successful by the standard
  metrics that the audit flags.
- **Ground truth and false positives.** The relation contract labels each reverse read; a manual check of 50 sampled
  flagged reads (by a person) estimates the audit's false-positive rate; cases where a reverse read returns a legitimate
  other subject count as non-failures by construction.
- **Code.** New `experiments/retrieval_poc/standard_metrics.py` + offline test; reads `deltas.csv`/`dist.csv`.

## E8s. Seeds 1 and 2 for the main runs
- **Question.** Are the scale-up verdicts stable across editor seeds (ROME and the context-template sampling of all three)?
- **Design.** Identical to E4 and E5 with `SEEDS="1 2"`; report per-path verdict agreement across seeds (share of paths with
  the same rank-1 verdict in all three seeds), and recompute the headline rates as "in every seed" / "in some seed" as in
  the draft. Intervals stay over facts.
- **Cost.** GPT-2 XL ~2 GPU-h; GPT-J ~7 GPU-h (run GPT-J MEMIT/AlphaEdit first if time is short).

## E13. Automatic fact verification against Wikidata
- **Question.** Are the 187 hand-written (subject, relation, object) facts true according to Wikidata?
- **Design.** For each fact, resolve subject and object to Wikidata items (label search, then disambiguation by type) and query
  the corresponding property: novel P50 (author), company P112 (founded by), invention P61 (discoverer or inventor),
  painting P170 (creator), character P170 (creator), currency P38 (currency of the country). Output per fact: verified /
  object differs / not found / ambiguous. Only the non-verified rows need a person's check.
- **Runs on the laptop** (network access to the Wikidata query service; no GPU). Results become a frozen file next to
  `own_facts.csv`; facts that fail are reported, not silently dropped (results with and without them).

## E8. Batch editing as one transaction (plan 3.2)
- **Question.** Is one batched write of n facts different from n sequential writes? Database view: one transaction vs n
  transactions; does batching avoid the interference seen in E7?
- **Design.** GPT-2 XL, the same 60 edited facts and 18 sentinels as E7v2 (`--order shuffle:1 --holdout 18`), MEMIT and
  AlphaEdit (ROME has no batch mode), `--mode batch` with batch size 60 (one call) and 10 (six calls); full reads after
  each call. Compare with E7v2 at k = 60: edits holding, stale reads, sentinel retention, untouched-control JS.
- **Cost.** ~1 GPU-h. Code ready (`run_audit.py --mode batch`, tested offline).

## E11. Inverse-index repair (new)
- **Question.** In a database, an update must also update every index on the column. If the editor is also asked to write
  the inverse path, does the audit pass, and what does the second write cost in side effects?
- **Design (proposal; needs agreement on the target rule).** For each fact, after the forward edit (s, r, o → o*), issue a
  second edit on the reverse-from-old prompt naming o, with a target that is consistent with the update:
  - inverse-non-functional relations: o's other best-known subject (e.g. "Mary Shelley is best known for writing the
    novel" → *The Last Man*), taken from the fact's `old_alt` when available, otherwise from the unedited model's own
    second-ranked subject on that prompt (pre-edit read, so no post-hoc choice);
  - one-to-one relations: no consistent target exists (o has no other subject), which is itself the finding; report as
    "repair impossible without deleting the tuple".
  Then audit all paths (Q1–Q3) and compare with the forward-only edit of E4: stale reads, reverse-from-new, neighbour
  drift, update norm. Variants: repair in the same batch (MEMIT/AlphaEdit) vs a second sequential write.
- **Why it matters.** Turns "editors fail the reverse path" into a database-style result about maintaining derived access
  paths (view/index maintenance), and measures its cost.
- **Cost.** ~2 GPU-h on GPT-2 XL. Code: a `--repair` option in the driver that builds the second request from the probe file.

## E9. Causal ablations left open by the draft (plans 1.3, 1.4)
- **E9a, subject at position 0.** The draft's company edits failed when the edit prompt began with the subject; rewording
  changed both position and wording. Same words, different position: "Apple was founded by" vs `<|endoftext|>` + "Apple
  was founded by" (position 1, no new words) vs the draft's "The company Apple was founded by". ROME on GPT-2 XL for the
  three subject-first company facts (Apple, Facebook, Microsoft) plus Amazon and Google, 3 seeds. Prediction to write:
  the BOS-prefixed prompt succeeds like the reworded one (position is the cause).
- **E9b, why neighbours drift.** Read each same-relation neighbour through three templates (edit-prompt template,
  statement paraphrase, question paraphrase) and compare the rise of o* across them. If drift appears only under the
  shared edit-prompt template, the draft's template explanation holds.
- **Cost.** < 1 GPU-h together.

## E12. Durability under quantization (new)
- **Question.** Edited models are deployed quantized. Do edits, stale reads and side effects survive 8-bit and 4-bit
  quantization? (Draft's agenda item "durability and erasure".)
- **Design.** GPT-2 XL and GPT-J, MEMIT and AlphaEdit, the E4/E5 facts: edit in fp32, then quantize the edited model
  (bitsandbytes int8 and nf4) and re-read every path; compare with the fp32 post-edit reads and with the quantized
  *unedited* model (so quantization error is separated from edit effects). Report: edits still visible, stale reads, control
  correctness, JS between fp32-edited and quantized-edited reads.
- **Checks.** Check C (restore) stays in fp32; quantization is applied to a copy after the fp32 reads.
- **Cost.** 1–2 GPU-h. Needs `bitsandbytes` in the env (check against the pinned versions first).

## E14. Natural-language paths
- **Question.** Are stale reads an artefact of fixed templates?
- **Design.** For the facts in common across models: CounterFact's own paraphrase prompts where they exist (P36), plus 5
  reverse questions per fact generated by an LLM *and checked by a person* (never generated and judged by the same model);
  audit them as extra paths, scored like the templated ones.
- **Cost.** ~1 GPU-h; the human check is the main cost.

## E15. More orders and longer sequences
- **Question.** Do the E7v2 patterns (ROME collapse, MEMIT decay, AlphaEdit erosion of unedited knowledge) depend on the
  edit order, and where does AlphaEdit's erosion end?
- **Design.** E7v2 with `--order shuffle:2` and `shuffle:3`; on GPT-J, 110 edits + 18 sentinels with checkpoints every 10.
- **Cost.** ~2 GPU-h (GPT-2 XL), ~6 GPU-h (GPT-J).

---

## Decisions needed from the user
1. **E6 model:** Llama-3-8B (needs Meta approval on Hugging Face and a token for the cluster) or Qwen2.5-7B.
2. **E11 target rule:** the proposal above (old object's other best-known subject; one-to-one relations reported as
   "repair impossible").
3. **E13 follow-up:** a person checks the facts the Wikidata query does not verify.
