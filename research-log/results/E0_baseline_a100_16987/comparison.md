# Re-run vs shipped

- screen_v1: **SAME RANKS AND TEXT, numeric drift only**
- screen_v2: **SAME RANKS AND TEXT, numeric drift only**
- aggregate_table2: **IDENTICAL**
- per_fact_table3: **IDENTICAL**
- ROME_v1_seed0: **SAME RANKS AND TEXT, numeric drift only**
- ROME_v2_seed0: **SAME RANKS AND TEXT, numeric drift only**
- MEMIT_seed0: **SAME RANKS AND TEXT, numeric drift only**
- AlphaEdit_seed0: **SAME RANKS AND TEXT, numeric drift only**
- ROME_v1_seed1: **SAME RANKS AND TEXT, numeric drift only**
- ROME_v2_seed1: **SAME RANKS AND TEXT, numeric drift only**
- MEMIT_seed1: **SAME RANKS AND TEXT, numeric drift only**
- AlphaEdit_seed1: **SAME RANKS AND TEXT, numeric drift only**
- ROME_v1_seed2: **SAME RANKS AND TEXT, numeric drift only**
- ROME_v2_seed2: **SAME RANKS AND TEXT, numeric drift only**
- MEMIT_seed2: **SAME RANKS AND TEXT, numeric drift only**
- AlphaEdit_seed2: **SAME RANKS AND TEXT, numeric drift only**

## screen_v1
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/screen_3461/screen_report.csv` (180 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/0.4_baseline_a100_16987/rome/screen_v1/screen_report.csv` (180 rows)
- matched on ['fact_id', 'route']: 180 rows; only shipped 0; only re-run 0
- max |diff| `deciding_answer`: 0
- max |diff| `sequence_probability`: 2.4e-06
- rank differences: 0
- text differences: 0

## screen_v2
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/screen_3466/screen_report.csv` (180 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/0.4_baseline_a100_16987/rome/screen_v2/screen_report.csv` (180 rows)
- matched on ['fact_id', 'route']: 180 rows; only shipped 0; only re-run 0
- max |diff| `deciding_answer`: 0
- max |diff| `sequence_probability`: 2.4e-06
- rank differences: 0
- text differences: 0

## aggregate_table2
**Verdict: IDENTICAL**
- shipped: `experiments/retrieval_poc/results/compare_methods/aggregate.csv` (9 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/0.4_baseline_a100_16987/compare_methods/aggregate.csv` (9 rows)
- matched on ['scope', 'method']: 9 rows; only shipped 0; only re-run 0
- max |diff| `facts`: 0
- rank differences: 0
- text differences: 0

## per_fact_table3
**Verdict: IDENTICAL**
- shipped: `experiments/retrieval_poc/results/compare_methods/per_fact.csv` (36 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/0.4_baseline_a100_16987/compare_methods/per_fact.csv` (36 rows)
- matched on ['fact', 'method']: 36 rows; only shipped 0; only re-run 0
- max |diff| `edit P`: 0
- rank differences: 0
- text differences: 0

## ROME_v1_seed0
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/study_3462_seed0/deltas.csv` (228 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/0.4_baseline_a100_16987/rome/study_v1_seed0/deltas.csv` (228 rows)
- matched on ['fact_id', 'seed', 'route', 'answer_label']: 228 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 2e-05
- max |diff| `post_sum_logprob`: 6.68e-05
- max |diff| `delta_sum_logprob`: 6.77e-05
- rank differences: 0
- text differences: 0

## ROME_v2_seed0
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/study_3467_seed0/deltas.csv` (110 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/0.4_baseline_a100_16987/rome/study_v2_seed0/deltas.csv` (110 rows)
- matched on ['fact_id', 'seed', 'route', 'answer_label']: 110 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 7.99e-06
- max |diff| `post_sum_logprob`: 0.000204
- max |diff| `delta_sum_logprob`: 0.000208
- rank differences: 0
- text differences: 0

## MEMIT_seed0
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/study_3574_MEMIT_seed0/deltas.csv` (272 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/0.4_baseline_a100_16987/study_a100_MEMIT_seed0/deltas.csv` (272 rows)
- matched on ['fact_id', 'method', 'seed', 'route', 'answer_label']: 272 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 2e-05
- max |diff| `post_sum_logprob`: 3.28e-05
- max |diff| `delta_sum_logprob`: 3.37e-05
- rank differences: 0
- text differences: 0

## AlphaEdit_seed0
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/study_3583_AlphaEdit_seed0/deltas.csv` (272 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/0.4_baseline_a100_16987/study_a100_AlphaEdit_seed0/deltas.csv` (272 rows)
- matched on ['fact_id', 'method', 'seed', 'route', 'answer_label']: 272 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 2e-05
- max |diff| `post_sum_logprob`: 0.00012
- max |diff| `delta_sum_logprob`: 0.000121
- rank differences: 0
- text differences: 0

## ROME_v1_seed1
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/study_3462_seed1/deltas.csv` (228 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/0.4_baseline_a100_16987/rome/study_v1_seed1/deltas.csv` (228 rows)
- matched on ['fact_id', 'seed', 'route', 'answer_label']: 228 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 2e-05
- max |diff| `post_sum_logprob`: 5.58e-05
- max |diff| `delta_sum_logprob`: 5.97e-05
- rank differences: 0
- text differences: 0

## ROME_v2_seed1
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/study_3467_seed1/deltas.csv` (110 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/0.4_baseline_a100_16987/rome/study_v2_seed1/deltas.csv` (110 rows)
- matched on ['fact_id', 'seed', 'route', 'answer_label']: 110 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 7.99e-06
- max |diff| `post_sum_logprob`: 1.81e-05
- max |diff| `delta_sum_logprob`: 1.79e-05
- rank differences: 0
- text differences: 0

## MEMIT_seed1
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/study_3574_MEMIT_seed1/deltas.csv` (272 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/0.4_baseline_a100_16987/study_a100_MEMIT_seed1/deltas.csv` (272 rows)
- matched on ['fact_id', 'method', 'seed', 'route', 'answer_label']: 272 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 2e-05
- max |diff| `post_sum_logprob`: 3.26e-05
- max |diff| `delta_sum_logprob`: 3.79e-05
- rank differences: 0
- text differences: 0

## AlphaEdit_seed1
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/study_3583_AlphaEdit_seed1/deltas.csv` (272 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/0.4_baseline_a100_16987/study_a100_AlphaEdit_seed1/deltas.csv` (272 rows)
- matched on ['fact_id', 'method', 'seed', 'route', 'answer_label']: 272 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 2e-05
- max |diff| `post_sum_logprob`: 2.34e-05
- max |diff| `delta_sum_logprob`: 3.34e-05
- rank differences: 0
- text differences: 0

## ROME_v1_seed2
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/study_3462_seed2/deltas.csv` (228 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/0.4_baseline_a100_16987/rome/study_v1_seed2/deltas.csv` (228 rows)
- matched on ['fact_id', 'seed', 'route', 'answer_label']: 228 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 2e-05
- max |diff| `post_sum_logprob`: 6.57e-05
- max |diff| `delta_sum_logprob`: 6.96e-05
- rank differences: 0
- text differences: 0

## ROME_v2_seed2
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/study_3467_seed2/deltas.csv` (110 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/0.4_baseline_a100_16987/rome/study_v2_seed2/deltas.csv` (110 rows)
- matched on ['fact_id', 'seed', 'route', 'answer_label']: 110 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 7.99e-06
- max |diff| `post_sum_logprob`: 9.3e-06
- max |diff| `delta_sum_logprob`: 1.05e-05
- rank differences: 0
- text differences: 0

## MEMIT_seed2
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/study_3574_MEMIT_seed2/deltas.csv` (272 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/0.4_baseline_a100_16987/study_a100_MEMIT_seed2/deltas.csv` (272 rows)
- matched on ['fact_id', 'method', 'seed', 'route', 'answer_label']: 272 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 2e-05
- max |diff| `post_sum_logprob`: 0.000259
- max |diff| `delta_sum_logprob`: 0.00026
- rank differences: 0
- text differences: 0

## AlphaEdit_seed2
**Verdict: SAME RANKS AND TEXT, numeric drift only**
- shipped: `experiments/retrieval_poc/results/study_3583_AlphaEdit_seed2/deltas.csv` (272 rows)
- re-run: `/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit/runs/0.4_baseline_a100_16987/study_a100_AlphaEdit_seed2/deltas.csv` (272 rows)
- matched on ['fact_id', 'method', 'seed', 'route', 'answer_label']: 272 rows; only shipped 0; only re-run 0
- max |diff| `pre_sum_logprob`: 2e-05
- max |diff| `post_sum_logprob`: 0.000228
- max |diff| `delta_sum_logprob`: 0.000226
- rank differences: 0
- text differences: 0
