# 2026-11-11 · 13 · The replication jobs of entry 12 all failed: a flag-check bug and a full quota

**Why.** All six jobs queued in entry 12 (18781-18786) ended `FAILED`. This entry records the two causes, the code fix
and what is needed before the jobs can be resubmitted. None of the six runs produced usable results.

## What failed (sacct, checked 2026-11-11 ~23:00 IST)

| Job | What | Ran | Cause |
|---|---|---|---|
| 18781 | N1 GPT-J, MEMIT + AlphaEdit | 19:26-19:27 (1 min) | flag-check bug (below) |
| 18782 | N1 GPT-J, ROME+stats | 18 s | flag-check bug |
| 18783 | N1 seed 1 GPT-2 XL, MEMIT + AlphaEdit | 18 s | flag-check bug |
| 18784 | N1 seed 1 GPT-2 XL, ROME+stats | 16 s | flag-check bug |
| 18785 | N5/N2 seed 1 GPT-2 XL, MEMIT + AlphaEdit | 19:28-20:18 (50 min) | log stops mid-line (in a MEMIT edit, layer 16); account quota full |
| 18786 | N5/N2 seed 1 GPT-2 XL, ROME+stats | 4 s, empty log | account quota full |

### 1. Flag-check bug in `run_audit.py` v1.3 (jobs 18781-18784)
All four pairs jobs stopped right after loading the pairs with
`ValueError: --pairs / --programs / --sentinels-file only apply to pairs / programs mode`.
The guard was written as `if mode == "programs": ... elif args.pairs or args.sentinels_file or args.programs: raise`,
so it also fired in pairs mode. It came in with programs mode (entry 11), after the GPT-2 XL pairs runs 18039/18040
(entry 10) had finished, which is why those succeeded. No test called `main()`, so the tests did not catch it.

**Fix (`run_audit.py` v1.3.1, 2026-11-11):** the guard is replaced by `check_mode_args(args)`, called right after
argument parsing, before the model loads, so a wrong flag now fails in seconds. Rules: pairs mode needs `--pairs` and
accepts `--sentinels-file`; programs mode needs `--programs` and accepts `--sentinels-file`, `--derived-facts`; every
other mode refuses all four. Stricter than v1.3 in one respect: `--derived-facts` outside programs mode is refused (it
used to be ignored). `audit_v3.sbatch` passes only the flags of the chosen mode, so no submission changes.
The edit/read logic is unchanged: only argument checking moved. `AUDIT_VERSION` = `run_audit v1.3.1 (2026-11-11)`.

**Test:** new block 7 in `tests/test_pairs.py`: valid flag sets for all five modes are accepted; 17 invalid sets are
refused (missing `--pairs`/`--programs`, cross-mode flags, any of the four flags in independent/sequential/batch).
Run on the laptop with the function extracted from the source (no `transformers` locally): passes. The full
`tests.sbatch` suite must run on the cluster before resubmission.

### 2. Account quota full (jobs 18785, 18786)
`quota -s` at ~23:00: **1000 G used, 999 G soft, 1000 G hard** (6-day grace), so writes fail. Our project is
**51 G, the same as on 2026-11-05**, so other users of the shared `yashsinha` account filled it. 18785's log ends mid-line
at 20:18 (13 MB of partial output in `runs/N25s1_gpt2-xl_programs_18785`); 18786 wrote nothing. Disk `/nfs_home` itself
has 14 T free: the limit is the per-account quota.

Space needed: the earlier N1/N5 runs wrote 21-41 MB each; all six reruns need < 1 GB plus logs. Nothing in our project can
be deleted without loss: GPT-2 XL weights (6.4 G), GPT-J weights (24.2 G, fp32 `.bin`), GPT-J AlphaEdit projection
(6.4 G), GPT-2 XL projection (0.8 G), covariance statistics, the env. Converting GPT-J to fp16 would save ~12 G but
changes the weights against E5 (not done).

## Next
1. Free space (user's decision: other users of the account, or something in `F20220612_Aadit` the user owns).
2. `sync.sh` (needs free space), run `tests.sbatch`, then resubmit the six jobs unchanged, chained with `--dependency`
   on the tests job. The partial run 18785 is not used; the rerun replaces it.
3. Predictions P13.1-P13.5 in entry 12 stay as written; they were registered before any run, and no run produced output.
