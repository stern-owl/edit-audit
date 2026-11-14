# Re-run vs shipped

- ROME_s0: **SAME RANKS AND TEXT, numeric drift only**
- MEMIT_s0: **SAME RANKS AND TEXT, numeric drift only**
- AlphaEdit_s0: **SAME RANKS AND TEXT, numeric drift only**
- ROME_s1: **SAME RANKS AND TEXT, numeric drift only**
- MEMIT_s1: **SAME RANKS AND TEXT, numeric drift only**
- AlphaEdit_s1: **SAME RANKS AND TEXT, numeric drift only**
- ROME_s2: **SAME RANKS AND TEXT, numeric drift only**
- MEMIT_s2: **SAME RANKS AND TEXT, numeric drift only**
- AlphaEdit_s2: **SAME RANKS AND TEXT, numeric drift only**

## ROME_s0
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/1_phase1_gpt2xl_16994/rome12_shipped_seed0.csv` (224 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/1_phase1_gpt2xl_16994/ROME_gpt2-xl/audit_p1_gpt2-xl_ROME_independent_seed0/deltas.csv` (224 rows)
- matched on ['fact_id', 'seed', 'route', 'answer_label']: 224 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 2e-05
- max |diff| `post_sum_logprob`: 0.000204
- max |diff| `delta_sum_logprob`: 0.000208
- rank differences: 0
- text differences: 0

## MEMIT_s0
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/study_3574_MEMIT_seed0/deltas.csv` (224 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/1_phase1_gpt2xl_16994/MEMIT_gpt2-xl/audit_p1_gpt2-xl_MEMIT_independent_seed0/deltas.csv` (224 rows)
- matched on ['fact_id', 'seed', 'route', 'answer_label']: 224 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 2e-05
- max |diff| `post_sum_logprob`: 2.46e-05
- max |diff| `delta_sum_logprob`: 2.59e-05
- rank differences: 0
- text differences: 0

## AlphaEdit_s0
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/study_3583_AlphaEdit_seed0/deltas.csv` (224 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/1_phase1_gpt2xl_16994/AlphaEdit_gpt2-xl/audit_p1_gpt2-xl_AlphaEdit_independent_seed0/deltas.csv` (224 rows)
- matched on ['fact_id', 'seed', 'route', 'answer_label']: 224 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 2e-05
- max |diff| `post_sum_logprob`: 0.00012
- max |diff| `delta_sum_logprob`: 0.000121
- rank differences: 0
- text differences: 0

## ROME_s1
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/1_phase1_gpt2xl_16994/rome12_shipped_seed1.csv` (224 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/1_phase1_gpt2xl_16994/ROME_gpt2-xl/audit_p1_gpt2-xl_ROME_independent_seed1/deltas.csv` (224 rows)
- matched on ['fact_id', 'seed', 'route', 'answer_label']: 224 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 2e-05
- max |diff| `post_sum_logprob`: 5.44e-05
- max |diff| `delta_sum_logprob`: 5.45e-05
- rank differences: 0
- text differences: 0

## MEMIT_s1
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/study_3574_MEMIT_seed1/deltas.csv` (224 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/1_phase1_gpt2xl_16994/MEMIT_gpt2-xl/audit_p1_gpt2-xl_MEMIT_independent_seed1/deltas.csv` (224 rows)
- matched on ['fact_id', 'seed', 'route', 'answer_label']: 224 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 2e-05
- max |diff| `post_sum_logprob`: 3.24e-05
- max |diff| `delta_sum_logprob`: 3.77e-05
- rank differences: 0
- text differences: 0

## AlphaEdit_s1
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/study_3583_AlphaEdit_seed1/deltas.csv` (224 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/1_phase1_gpt2xl_16994/AlphaEdit_gpt2-xl/audit_p1_gpt2-xl_AlphaEdit_independent_seed1/deltas.csv` (224 rows)
- matched on ['fact_id', 'seed', 'route', 'answer_label']: 224 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 2e-05
- max |diff| `post_sum_logprob`: 2.29e-05
- max |diff| `delta_sum_logprob`: 3.34e-05
- rank differences: 0
- text differences: 0

## ROME_s2
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/1_phase1_gpt2xl_16994/rome12_shipped_seed2.csv` (224 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/1_phase1_gpt2xl_16994/ROME_gpt2-xl/audit_p1_gpt2-xl_ROME_independent_seed2/deltas.csv` (224 rows)
- matched on ['fact_id', 'seed', 'route', 'answer_label']: 224 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 2e-05
- max |diff| `post_sum_logprob`: 6.48e-05
- max |diff| `delta_sum_logprob`: 6.5e-05
- rank differences: 0
- text differences: 0

## MEMIT_s2
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/study_3574_MEMIT_seed2/deltas.csv` (224 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/1_phase1_gpt2xl_16994/MEMIT_gpt2-xl/audit_p1_gpt2-xl_MEMIT_independent_seed2/deltas.csv` (224 rows)
- matched on ['fact_id', 'seed', 'route', 'answer_label']: 224 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 2e-05
- max |diff| `post_sum_logprob`: 0.000258
- max |diff| `delta_sum_logprob`: 0.00026
- rank differences: 0
- text differences: 0

## AlphaEdit_s2
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/study_3583_AlphaEdit_seed2/deltas.csv` (224 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/1_phase1_gpt2xl_16994/AlphaEdit_gpt2-xl/audit_p1_gpt2-xl_AlphaEdit_independent_seed2/deltas.csv` (224 rows)
- matched on ['fact_id', 'seed', 'route', 'answer_label']: 224 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 2e-05
- max |diff| `post_sum_logprob`: 0.000228
- max |diff| `delta_sum_logprob`: 0.000226
- rank differences: 0
- text differences: 0
