# Research log: edit-audit, phase 2

This folder records every step taken to extend the PVLDB draft
"Auditing Knowledge Edits in Language Models as Database Updates [Vision]"
(PDF in the parent folder; code in `../edit-audit/`, the colleague's supplementary-material repo).

**Copy in the repo (2026-11-14):** this folder and `data/raw_runs/` are also committed on branch `phase2` of
https://github.com/AaditS04/edit-audit (folders `research-log/` and `data/raw_runs/`). The master copy is the one on
the laptop (`C:\Desktop\edit-audit
esearch-log\`); the repo copy is refreshed from it before each push.

Originally it sat outside the `edit-audit/` git repo on purpose: that repo is the shipped artifact for the
current draft and stays byte-identical to its `CHECKSUMS.md5` until we decide to publish a new version.

## Files

| File | What it holds |
|---|---|
| `RESULTS.md` | **All results in detail** (every number, table, prediction outcome, bug, limitation), compiled from the raw outputs for drafting the paper. |
| `site/edit-audit-results.html` | Shareable results web page built from `RESULTS.md` (published: https://claude.ai/artifact/CKWPueg9DGZ3HJXF8b9NTA, private until shared). Open items deliberately left out at the user's request. |
| `NOVELTY_AND_NEW_EXPERIMENTS.md` | Novelty check against prior work (2026-11-05) and the redesigned experiment set N1–N6; supersedes parts of `NEXT_EXPERIMENTS.md`. |
| `NEXT_EXPERIMENTS.md` | The next experiments (E6, E8–E15): reviewer risk each answers, design, cost, dependencies, decisions needed. |
| `RELATED_WORK_CHECK.md` | Prior work closest to the phase-6 results and how each claim must be framed (2026-11-11). |
| `EXPERIMENTS.md` | Every experiment (E0–E10): question, what is new over the draft, design, predictions, code, jobs, status. |
| `STATUS.md` | What is running right now and how to resume. Read this first. |
| `plan.md` | The phased work plan with a status for every item. Updated whenever an item starts or finishes. |
| `decisions.md` | Open and settled decisions, each with date, options, outcome and reason. |
| `environment.md` | Where things run: machines, accounts, clusters, paths, library versions. |
| `entries/YYYY-MM-DD_NN_<slug>.md` | One entry per piece of work, in order. Never edited after the fact except to add a dated correction note at the bottom. |

## What every entry records

1. **Goal**: what question the work answers and which plan item it belongs to.
2. **What was done**: code changed (file, function, why), commands run, on which machine.
3. **Runs**: Slurm job IDs, seeds, model, method, hparams file and md5, probe set and md5, GPU type, peak memory, wall time.
4. **Results**: the numbers, with the path of the raw output file they come from. Negative and null results are recorded the same way as positive ones.
5. **Checks**: tests run and their outcome; checks A/B/C status for edit runs.
6. **Deviations and problems**: anything that did not go as planned, including failed jobs.
7. **Next**: what this entry unblocks or changes in the plan.

## Rules carried over from the original study

- Screening rules and templates are frozen (versioned file + md5) before any post-edit data exist.
  A predicted outcome is written down before the run that tests it.
- An edit run is only reported if checks A (repeat reads identical), B (edit is live) and
  C (restore is exact) pass.
- Results are reported per fact and per path; aggregates never replace the per-fact table.
- Confidence intervals are computed across facts, not across seeds.
