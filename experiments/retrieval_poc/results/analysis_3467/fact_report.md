# Fact study analysis (analyze_study v1 (2026-10-24))

Descriptive only. Ranks are first-token ranks (1 = top). Ranges are min-max over seeds. Δ = change in full-answer log-probability, mean over seeds. Only routes marked valid at screening are used; invalid ones are listed but excluded.

**Edit took (post-hoc rule: new object rank 1 on edit prompt in every seed):** amazon, apple, facebook, google, microsoft
**Edit did not take:** none

## amazon (company_founder)

**Q1 acquisition – new object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | new_object (Mark Zuckerberg) | 28 → 1 | +7.70 [+7.69, +7.71] |
| forward_edit_prompt | new_object (Mark Zuckerberg) | 34 → 1 | +8.73 [+8.73, +8.73] |
| paraphrase_question | new_object (Mark Zuckerberg) | 118 → 2-3 | +10.09 [+9.73, +10.34] |
| paraphrase_statement | new_object (Mark Zuckerberg) | 153 → 14-15 | +4.72 [+4.50, +4.90] |  _(invalid route, excluded)_

**Q2 persistence – old object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | old_object (Jeff Bezos) | 1 → 13-23 | -6.79 [-7.11, -6.25] |
| forward_edit_prompt | old_object (Jeff Bezos) | 1 → 17-39 | -9.02 [-9.40, -8.35] |
| paraphrase_question | old_object (Jeff Bezos) | 1 → 1 | -0.70 [-0.88, -0.52] |
| paraphrase_statement | old_object (Jeff Bezos) | 3 → 3 | -0.88 [-0.95, -0.82] |  _(invalid route, excluded)_

**Q2 persistence – reverse from OLD object (subject should stay if old fact persists)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_old_best_known | subject (Amazon) | 1 → 1 | -0.16 [-0.19, -0.12] |
| reverse_old_most_famous | subject (Amazon) | 1 → 1 | -0.28 [-0.35, -0.20] |

**Q3 access – reverse from NEW object (subject rises only if edit propagates backwards)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_new_best_known | alt:Facebook (Facebook) | 1 → 1 | +0.23 [+0.23, +0.23] |
| reverse_new_best_known | subject (Amazon) | 132 → 219-238 | -1.43 [-1.49, -1.33] |
| reverse_new_most_famous | alt:Facebook (Facebook) | 1 → 1 | -0.16 [-0.23, -0.07] |
| reverse_new_most_famous | subject (Amazon) | 62 → 91-107 | -0.47 [-0.56, -0.38] |

**Locality controls**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| control_new_object_own_fact | correct (Mark Zuckerberg) | 1 → 1 | +0.06 [+0.06, +0.06] |
| control_new_object_own_fact | edit_leak (Jeff Bezos) | 217 → 454-564 | -4.35 [-4.55, -4.08] |
| control_same_relation | correct (Bill Gates) | 1 → 1 | +0.18 [+0.12, +0.28] |
| control_same_relation | edit_leak (Mark Zuckerberg) | 36 → 2 | +6.18 [+5.96, +6.31] |

## apple (company_founder)

**Q1 acquisition – new object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | new_object (Bill Gates) | 21 → 1 | +6.60 [+6.59, +6.61] |
| forward_edit_prompt | new_object (Bill Gates) | 25 → 1 | +6.46 [+6.46, +6.46] |
| paraphrase_question | new_object (Bill Gates) | 13 → 2 | +4.15 [+3.95, +4.26] |
| paraphrase_statement | new_object (Bill Gates) | 13 → 3 | +3.19 [+3.10, +3.32] |

**Q2 persistence – old object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | old_object (Steve Jobs) | 1 → 2 | -2.37 [-2.54, -2.18] |
| forward_edit_prompt | old_object (Steve Jobs) | 1 → 2 | -5.77 [-5.97, -5.47] |
| paraphrase_question | old_object (Steve Jobs) | 1 → 1 | -0.12 [-0.16, -0.06] |
| paraphrase_statement | old_object (Steve Jobs) | 1 → 1 | -0.30 [-0.33, -0.26] |

**Q2 persistence – reverse from OLD object (subject should stay if old fact persists)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_old_best_known | subject (Apple) | 1 → 1 | +0.03 [+0.03, +0.04] |
| reverse_old_most_famous | subject (Apple) | 1 → 1 | -0.09 [-0.12, -0.07] |

**Q3 access – reverse from NEW object (subject rises only if edit propagates backwards)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_new_best_known | alt:Microsoft (Microsoft) | 1 → 1 | -0.00 [-0.01, +0.00] |
| reverse_new_best_known | subject (Apple) | 56 → 168-186 | -1.91 [-1.96, -1.83] |
| reverse_new_most_famous | alt:Microsoft (Microsoft) | 1 → 1 | +0.08 [+0.07, +0.09] |
| reverse_new_most_famous | subject (Apple) | 18 → 74-77 | -2.03 [-2.09, -1.96] |

**Locality controls**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| control_new_object_own_fact | correct (Bill Gates) | 1 → 1 | +0.66 [+0.66, +0.66] |
| control_new_object_own_fact | edit_leak (Steve Jobs) | 7 → 21-22 | -5.68 [-5.93, -5.37] |
| control_same_relation | correct (Jeff Bezos) | 1 → 1 | +0.30 [+0.26, +0.35] |
| control_same_relation | edit_leak (Bill Gates) | 52 → 3 | +4.32 [+3.94, +4.58] |

## facebook (company_founder)

**Q1 acquisition – new object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | new_object (Jeff Bezos) | 362 → 1 | +11.50 [+11.44, +11.54] |
| forward_edit_prompt | new_object (Jeff Bezos) | 217 → 1 | +12.07 [+12.07, +12.08] |
| paraphrase_question | new_object (Jeff Bezos) | 279 → 2-3 | +8.74 [+8.38, +9.01] |
| paraphrase_statement | new_object (Jeff Bezos) | 180 → 3-5 | +5.66 [+5.42, +5.88] |

**Q2 persistence – old object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | old_object (Mark Zuckerberg) | 1 → 3-4 | -3.58 [-3.93, -3.04] |
| forward_edit_prompt | old_object (Mark Zuckerberg) | 1 → 8-12 | -8.14 [-8.44, -7.62] |
| paraphrase_question | old_object (Mark Zuckerberg) | 1 → 1 | -1.17 [-1.30, -1.04] |
| paraphrase_statement | old_object (Mark Zuckerberg) | 1 → 3-5 | -1.34 [-1.40, -1.29] |

**Q2 persistence – reverse from OLD object (subject should stay if old fact persists)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_old_best_known | subject (Facebook) | 1 → 2 | -0.65 [-0.69, -0.62] |
| reverse_old_most_famous | subject (Facebook) | 1 → 1 | -0.25 [-0.29, -0.22] |

**Q3 access – reverse from NEW object (subject rises only if edit propagates backwards)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_new_best_known | alt:Amazon (Amazon) | 1 → 1 | -0.02 [-0.03, -0.01] |
| reverse_new_best_known | subject (Facebook) | 142 → 325-331 | -1.42 [-1.45, -1.39] |
| reverse_new_most_famous | alt:Amazon (Amazon) | 1 → 1 | -0.06 [-0.07, -0.06] |
| reverse_new_most_famous | subject (Facebook) | 59 → 134-142 | -1.03 [-1.08, -0.99] |

**Locality controls**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| control_new_object_own_fact | correct (Jeff Bezos) | 1 → 1 | +0.44 [+0.44, +0.44] |
| control_new_object_own_fact | edit_leak (Mark Zuckerberg) | 34 → 79-80 | -4.05 [-4.07, -4.03] |
| control_same_relation | correct (Bill Gates) | 1 → 1 | +0.18 [+0.10, +0.29] |
| control_same_relation | edit_leak (Jeff Bezos) | 162 → 4-6 | +6.46 [+5.91, +6.80] |

## google (company_founder)

**Q1 acquisition – new object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | new_object (Bill Gates) | 18 → 1 | +6.17 [+6.17, +6.17] |
| forward_edit_prompt | new_object (Bill Gates) | 15 → 1 | +6.10 [+6.10, +6.10] |
| paraphrase_question | new_object (Bill Gates) | 7 → 1 | +4.13 [+4.09, +4.17] |
| paraphrase_statement | new_object (Bill Gates) | 14 → 3 | +4.20 [+4.14, +4.25] |  _(invalid route, excluded)_

**Q2 persistence – old object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | old_object (Larry Page) | 1 → 2 | -3.63 [-3.75, -3.44] |
| forward_edit_prompt | old_object (Larry Page) | 1 → 6-7 | -7.18 [-7.33, -6.92] |
| paraphrase_question | old_object (Larry Page) | 1 → 2 | -0.94 [-1.04, -0.84] |
| paraphrase_statement | old_object (Larry Page) | 3 → 1 | +0.24 [+0.21, +0.27] |  _(invalid route, excluded)_

**Q2 persistence – reverse from OLD object (subject should stay if old fact persists)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_old_best_known | subject (Google) | 1 → 1 | +0.03 [+0.02, +0.04] |
| reverse_old_most_famous | subject (Google) | 1 → 1 | -0.21 [-0.23, -0.18] |

**Q3 access – reverse from NEW object (subject rises only if edit propagates backwards)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_new_best_known | alt:Microsoft (Microsoft) | 1 → 1 | +0.02 [+0.02, +0.03] |
| reverse_new_best_known | subject (Google) | 34 → 89-95 | -1.64 [-1.65, -1.62] |
| reverse_new_most_famous | alt:Microsoft (Microsoft) | 1 → 1 | -0.07 [-0.09, -0.04] |
| reverse_new_most_famous | subject (Google) | 38 → 134-146 | -1.72 [-1.74, -1.69] |

**Locality controls**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| control_new_object_own_fact | correct (Bill Gates) | 1 → 1 | +0.63 [+0.62, +0.63] |
| control_new_object_own_fact | edit_leak (Larry Page) | 32 → 113-132 | -4.96 [-5.35, -4.63] |
| control_same_relation | correct (Steve Jobs) | 1 → 1 | +0.01 [-0.02, +0.04] |
| control_same_relation | edit_leak (Bill Gates) | 25 → 2 | +3.79 [+3.77, +3.82] |

## microsoft (company_founder)

**Q1 acquisition – new object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | new_object (Steve Jobs) | 7 → 1 | +7.44 [+7.43, +7.44] |
| forward_edit_prompt | new_object (Steve Jobs) | 7 → 1 | +7.04 [+7.04, +7.05] |
| paraphrase_question | new_object (Steve Jobs) | 14 → 1 | +6.51 [+6.49, +6.54] |
| paraphrase_statement | new_object (Steve Jobs) | 3 → 1 | +2.90 [+2.89, +2.92] |

**Q2 persistence – old object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | old_object (Bill Gates) | 1 → 2-3 | -4.35 [-4.51, -4.24] |
| forward_edit_prompt | old_object (Bill Gates) | 1 → 4-6 | -6.41 [-6.58, -6.32] |
| paraphrase_question | old_object (Bill Gates) | 1 → 2 | -0.55 [-0.61, -0.50] |
| paraphrase_statement | old_object (Bill Gates) | 1 → 2 | -1.14 [-1.18, -1.12] |

**Q2 persistence – reverse from OLD object (subject should stay if old fact persists)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_old_best_known | subject (Microsoft) | 1 → 1 | -0.11 [-0.11, -0.10] |
| reverse_old_most_famous | subject (Microsoft) | 1 → 1 | -0.45 [-0.51, -0.36] |

**Q3 access – reverse from NEW object (subject rises only if edit propagates backwards)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_new_best_known | alt:Apple (Apple) | 1 → 1 | +0.00 [-0.00, +0.01] |
| reverse_new_best_known | subject (Microsoft) | 26 → 52-53 | -1.12 [-1.14, -1.10] |
| reverse_new_most_famous | alt:Apple (Apple) | 1 → 1 | -0.09 [-0.16, -0.00] |
| reverse_new_most_famous | subject (Microsoft) | 55 → 124-132 | -0.95 [-0.97, -0.94] |

**Locality controls**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| control_new_object_own_fact | correct (Steve Jobs) | 1 → 1 | +0.41 [+0.40, +0.41] |
| control_new_object_own_fact | edit_leak (Bill Gates) | 25 → 50-61 | -3.18 [-3.30, -3.07] |
| control_same_relation | correct (Jeff Bezos) | 1 → 1 | -0.58 [-0.62, -0.54] |
| control_same_relation | edit_leak (Steve Jobs) | 8 → 2 | +3.59 [+3.55, +3.65] |
