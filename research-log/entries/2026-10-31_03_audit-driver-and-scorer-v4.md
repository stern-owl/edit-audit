# 2026-10-31 · 03 · Model-agnostic scorer (v4), distributional metrics, and the audit driver

**Plan items:** 2.1 (code), 1.2 (code), 3.1 (code), 3.2 (code). None of these has been run on a real model yet.

## Goal
One driver that runs the draft's audit on any Hugging Face causal LM, records distributional side effects, and
supports independent, sequential and batch edit schedules, without changing any file of the shipped artefact.

## Provenance rule followed
The colleague added `run_method_study.py` next to `run_fact_study.py` instead of editing it, because every shipped log
records script md5s. Same here: `probe_scoring.py`, `run_method_study.py`, `tests/run_tests.sh` etc. are unchanged
(all still match `CHECKSUMS.md5`). New files only:

| File | Role |
|---|---|
| `experiments/retrieval_poc/probe_scoring_v4.py` | Scorer v4.0: same score fields as v3.1, plus BOS handling, joint answer tokenisation, full next-token distributions, divergences |
| `experiments/retrieval_poc/run_audit.py` | Driver v1.0: `--mode independent|sequential|batch`, any EasyEdit method, any model |
| `experiments/retrieval_poc/tests/test_scoring_v4.py` | Offline tests of v4 |
| `experiments/retrieval_poc/tests/test_audit.py` | Offline tests of the driver core |
| `cluster/csis/tests.sbatch` | CPU job: shipped test suite + the two new tests |

## Scorer v4 (`probe_scoring_v4.py`)
- **BOS:** prepended exactly when the tokenizer itself adds it (`tokenizer("a")` starts with `bos_token_id`). GPT-2 and Qwen2.5: no BOS (unchanged from v3). Llama-3: BOS. v3 never added BOS, which would silently misread Llama-3.
- **Answer tokens:** tokenise `prompt + " " + answer` jointly and take the part after the prompt's tokens. Identical to v3 for byte-level BPE (GPT-2, Llama-3, Qwen) because pre-tokenisation splits at the space. If the prompt is not a token prefix of the joint form, fall back to v3's separate tokenisation and flag `boundary_merge=True`.
- **Distributions:** `probe_prompt(..., keep_distribution=True)` keeps the full next-token log-distribution (computed in float64, stored float32 on CPU, never written to disk).
- **Metrics:**
  - `next_token_shift(pre, post)`: KL(pre‖post), KL(post‖pre), Jensen–Shannon in bits (∈ [0, 1]), total variation, argmax change, top-10 overlap, over the whole vocabulary.
  - `candidate_shift(pre, post)`: the same divergences over the route's answer set after renormalising each answer's full-answer probability within the set. This is the "clearly defined answer set" version that `next-steps.txt` asks for, kept separate from the full-vocabulary version.
  - ΔP and Δrank of the new object on unrelated prompts are already in the deltas (`edit_leak` answer on control routes).
- `greedy_continuation(max_new_tokens=0)` returns `""` (used to skip generation on re-reads).

## Driver (`run_audit.py`)
- Core function `audit(...)` takes the model, tokenizer, facts, a list of edit steps, an `edit_fn` and an `emit` sink; no EasyEdit import, so it is tested offline with a fake editor (same pattern as `rome_paired_pilot.run_pilot`).
- **Modes:**
  - `independent`: edit fact → read it → restore → check C on that fact. The draft's protocol.
  - `sequential`: edits accumulate. After each edit the just-edited fact is read; at checkpoints (`--checkpoints`, default every step; the last step always) **every** fact is read, edited or not. One restore + check C over all facts at the end.
  - `batch`: `editor.batch_edit` in chunks of `--batch-size` (default all facts), every fact read after each chunk, one restore at the end.
- **Checks:** A over all facts before any edit; B per edit call against the weights just before that call; C per fact (independent) or once at the end. The driver also refuses to continue if the editor returns a different model object than the one being read.
- **Per-step norms:** `step_delta_frobenius_norm` (this call) and `cumulative_delta_frobenius_norm` (vs unedited).
- **AlphaEdit `cache_c`:** cleared before every edit in independent mode (as in the draft); cleared once at the start and then left to accumulate in sequential and batch modes. That accumulation is AlphaEdit's designed protection of earlier edits. Verified in EasyEdit `431d9bd`: `AlphaEdit_main.py` adds `layer_ks @ layer_ks.T` for every edit to the global `cache_c`; `cache_c_new=False` forces re-initialisation. `editor.edit(..., sequential_edit=True)` keeps the edited weights; `batch_edit` chunks by `hparams.batch_size`.
- **Order:** `--order sorted` (by fact_id) or `shuffle:<seed>`; the order and the steps are written to the manifest.
- **Outputs (streamed, so partial output survives a timeout):** `deltas.csv` (one row per step × read fact × route × answer; columns include `step`, `edited_facts`, `fact_edited`, `fact_edit_step`), `dist.csv` (one row per step × read fact × route), `checks.csv`, `baseline_reads.json`, `manifest.json` (versions, md5 of probes/hparams/stats/projection, model revision, tokenizer class, BOS flag, dtype, cache policy, GPU).
- **Cost note:** a read of one fact is ≈10 routes × (1 distribution pass + ~2–3 answer passes + 10 greedy steps). `--reread-gen-tokens 0` skips generation for re-reads of facts not edited at that step, and `--checkpoints` limits full re-reads; both are needed for 100+ facts.

## Offline tests written (to be run on the cluster: no torch on the laptop)
- `test_scoring_v4.py`: v4 equals v3 field-for-field on the toy character tokenizer and on an in-memory byte-level BPE without BOS. A BOS-adding BPE on a tiny Llama gets BOS prepended and still equals a brute-force log-probability. KL/JS/TV match analytic values for a two-point distribution; JS of disjoint distributions = 1 bit; candidate shift is invariant to adding a constant to every answer.
- `test_audit.py`: independent restores after each fact; sequential reads n×n (step, fact) pairs, untouched facts show nonzero JS, cumulative norm grows, final restore exact; checkpoints {2} read only the edited fact at steps 1 and 3; batch of 3+1; an editor that undoes its edit fails check B; an edit to a weight outside the snapshot fails check C (both modes).

## Test runs (`cluster/csis/tests.sbatch`, cpu-short, CPU only)
| Job | Result | What failed and what was changed |
|---|---|---|
| 16977 | FAILED | `test_scoring_v4.py` two-point KL/JS check, tolerance 1e-12. **Test bug:** the reference distributions were built in float32 (`torch.tensor([...]).log().double()`), so the expected values carried ~1e-8 float32 error. Fixed by building them in float64. Everything before this line had passed (v4 = v3 on both no-BOS tokenizers; BOS + tiny Llama equals brute force). |
| 16979 | FAILED | Disjoint-distribution check gave `nan`. **Real code issue:** `-1e300` became `-inf` in float32, and `0 × (−inf)` = `nan` inside KL/JS. Exactly-zero probabilities also occur in real models (vocabulary slots masked with `-inf` logits). **Fix in `probe_scoring_v4._divergences`:** new helper `_plogratio` applies 0·log 0 = 0 (terms with p = 0 contribute nothing); KL is +inf if p > 0 where q = 0; JS stays finite. Test now checks the `-inf` cases explicitly (disjoint → JS = 1 bit exactly, KL = inf, TV = 1; a shared masked slot leaves all divergences finite). |
| 16980 | FAILED | `test_audit.py`: "check C missed a failure in independent mode". **Test design flaw:** the "edit outside the snapshot" fake added the constant 0.5 to every entry of a layer-0 `c_proj` weight. That shifts all hidden dimensions equally, which every following LayerNorm removes exactly, so the outputs did not change and check C was right to pass. Fixed by adding random noise instead (comment in the test explains why). |
| 16981 | **COMPLETED** | **All tests pass:** shipped suite (4) + `test_scoring_v4` + `test_audit`. Check B caught the self-undoing editor (sequential); check C caught the unrestorable edit in independent (diff 1.97) and sequential (diff 2.57) mode. |

## Status
Code and offline tests pass (job 16981). Not yet run on a real model.

## Next
1. Run `tests.sbatch`.
2. Equivalence job: `run_audit.py --mode independent` on GPT-2 XL with the shipped 12-fact probes for ROME, MEMIT and AlphaEdit must reproduce the shipped `deltas.csv` ranks (validates v4 + the driver against the draft before any new claim relies on them).
