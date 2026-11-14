# Phase 6 offline analyses (phase6_offline v1.1 (2026-11-05))

## N3. Audit planning

Detection rate = share of inconsistent edits (any of V0 edit failed, V1 incomplete write, V2 stale read, V3 inverse inconsistency, V4 neighbour damage, V6 neighbour leak) that the plan reveals. Cost = questions asked per edit.

| run | edits | inconsistent | full catalogue (11) | standard plan (6) | 1 reverse-old + 1 neighbour (2) | greedy 1 | greedy 2 | greedy 3 | greedy plan (order) |
|---|---|---|---|---|---|---|---|---|---|
| GPT-2 XL/ROME | 78 | 77 | 77/77 = 100% | 56/77 = 73% | 55/77 = 71% | 75/77 = 97% | 77/77 = 100% | 77/77 = 100% | reverse_new_most_famous, reverse_old_most_famous, forward_edit_prompt |
| GPT-2 XL/ROME+stats | 78 | 77 | 77/77 = 100% | 46/77 = 60% | 55/77 = 71% | 68/77 = 88% | 74/77 = 96% | 76/77 = 99% | reverse_new_most_famous, reverse_old_most_famous, reverse_old_best_known |
| GPT-2 XL/MEMIT | 78 | 78 | 78/78 = 100% | 45/78 = 58% | 45/78 = 58% | 58/78 = 74% | 73/78 = 94% | 76/78 = 97% | reverse_new_most_famous, paraphrase_question, reverse_old_most_famous |
| GPT-2 XL/AlphaEdit | 78 | 78 | 78/78 = 100% | 40/78 = 51% | 56/78 = 72% | 70/78 = 90% | 75/78 = 96% | 77/78 = 99% | reverse_new_most_famous, reverse_old_most_famous, reverse_new_best_known |
| GPT-J/ROME | 128 | 128 | 128/128 = 100% | 93/128 = 73% | 89/128 = 70% | 114/128 = 89% | 122/128 = 95% | 127/128 = 99% | reverse_new_best_known, control_same_relation, reverse_new_most_famous |
| GPT-J/ROME+stats | 128 | 128 | 128/128 = 100% | 29/128 = 23% | 83/128 = 65% | 108/128 = 84% | 126/128 = 98% | 128/128 = 100% | reverse_new_most_famous, reverse_old_most_famous, reverse_old_best_known |
| GPT-J/MEMIT | 128 | 128 | 128/128 = 100% | 36/128 = 28% | 90/128 = 70% | 111/128 = 87% | 126/128 = 98% | 128/128 = 100% | reverse_new_most_famous, reverse_old_most_famous, reverse_new_best_known |
| GPT-J/AlphaEdit | 128 | 128 | 128/128 = 100% | 31/128 = 24% | 90/128 = 70% | 110/128 = 86% | 125/128 = 98% | 127/128 = 99% | reverse_new_best_known, reverse_old_most_famous, reverse_new_most_famous |
| GPT-2 XL/local | 234 | 233 | 233/233 = 100% | 131/233 = 56% | 156/233 = 67% | 196/233 = 84% | 212/233 = 91% | 225/233 = 97% | reverse_new_most_famous, paraphrase_question, reverse_old_most_famous |
| GPT-J/local | 384 | 384 | 384/384 = 100% | 96/384 = 25% | 263/384 = 68% | 329/384 = 86% | 372/384 = 97% | 382/384 = 99% | reverse_new_best_known, reverse_old_most_famous, reverse_new_most_famous |
| all/local | 618 | 617 | 617/617 = 100% | 227/617 = 37% | 419/617 = 68% | 521/617 = 84% | 583/617 = 94% | 599/617 = 97% | reverse_new_best_known, reverse_old_most_famous, paraphrase_question |

Same, **excluding V3** (inverse inconsistency; near-universal and already known from BAKE): inconsistent = any of V0, V1, V2, V4, V6.

| run | inconsistent | standard plan (6) | 1 reverse-old + 1 neighbour (2) | greedy 1 | greedy 2 | greedy 3 | greedy plan (order) |
|---|---|---|---|---|---|---|---|
| GPT-2 XL/ROME | 70 | 56/70 = 80% | 55/70 = 79% | 45/70 = 64% | 56/70 = 80% | 64/70 = 91% | reverse_old_best_known, paraphrase_statement, control_same_relation |
| GPT-2 XL/ROME+stats | 71 | 46/71 = 65% | 55/71 = 77% | 54/71 = 76% | 65/71 = 92% | 69/71 = 97% | reverse_old_most_famous, reverse_old_best_known, paraphrase_statement |
| GPT-2 XL/MEMIT | 73 | 45/73 = 62% | 45/73 = 62% | 46/73 = 63% | 64/73 = 88% | 72/73 = 99% | reverse_old_most_famous, paraphrase_question, reverse_old_best_known |
| GPT-2 XL/AlphaEdit | 70 | 40/70 = 57% | 56/70 = 80% | 56/70 = 80% | 65/70 = 93% | 70/70 = 100% | reverse_old_most_famous, reverse_old_best_known, paraphrase_statement |
| GPT-J/ROME | 112 | 93/112 = 83% | 89/112 = 79% | 65/112 = 58% | 93/112 = 83% | 108/112 = 96% | control_same_relation_2, control_same_relation, reverse_old_most_famous |
| GPT-J/ROME+stats | 113 | 29/113 = 26% | 83/113 = 73% | 98/113 = 87% | 110/113 = 97% | 113/113 = 100% | reverse_old_most_famous, reverse_old_best_known, control_same_relation_2 |
| GPT-J/MEMIT | 119 | 36/119 = 30% | 90/119 = 76% | 104/119 = 87% | 115/119 = 97% | 117/119 = 98% | reverse_old_most_famous, reverse_old_best_known, control_same_relation_2 |
| GPT-J/AlphaEdit | 118 | 31/118 = 26% | 90/118 = 76% | 104/118 = 88% | 115/118 = 97% | 116/118 = 98% | reverse_old_most_famous, reverse_old_best_known, paraphrase_statement |
| GPT-2 XL/local | 214 | 131/214 = 61% | 156/214 = 73% | 156/214 = 73% | 184/214 = 86% | 208/214 = 97% | reverse_old_most_famous, reverse_old_best_known, paraphrase_question |
| GPT-J/local | 350 | 96/350 = 27% | 263/350 = 75% | 306/350 = 87% | 340/350 = 97% | 346/350 = 99% | reverse_old_most_famous, reverse_old_best_known, control_same_relation_2 |
| all/local | 564 | 227/564 = 40% | 419/564 = 74% | 462/564 = 82% | 524/564 = 93% | 548/564 = 97% | reverse_old_most_famous, reverse_old_best_known, paraphrase_question |

Violation types per run (edits with the type) and how many of those the standard plan reveals:

| run | V0 edit failed | V1 incomplete write | V2 stale read | V3 inverse inconsistency | V4 neighbour damage | V5 neighbour drift | V6 neighbour leak |
|---|---|---|---|---|---|---|---|
| GPT-2 XL/ROME | 0 (0 by standard) | 36 (36 by standard) | 51 (0 by standard) | 77 (0 by standard) | 13 (13 by standard) | 62 (62 by standard) | 22 (22 by standard) |
| GPT-2 XL/ROME+stats | 0 (0 by standard) | 41 (41 by standard) | 65 (0 by standard) | 74 (0 by standard) | 5 (5 by standard) | 52 (52 by standard) | 6 (6 by standard) |
| GPT-2 XL/MEMIT | 14 (14 by standard) | 43 (43 by standard) | 54 (0 by standard) | 62 (0 by standard) | 4 (4 by standard) | 24 (24 by standard) | 5 (5 by standard) |
| GPT-2 XL/AlphaEdit | 0 (0 by standard) | 34 (34 by standard) | 65 (0 by standard) | 73 (0 by standard) | 7 (7 by standard) | 29 (29 by standard) | 11 (11 by standard) |
| GPT-J/ROME | 0 (0 by standard) | 2 (2 by standard) | 50 (0 by standard) | 121 (0 by standard) | 75 (75 by standard) | 77 (77 by standard) | 75 (75 by standard) |
| GPT-J/ROME+stats | 0 (0 by standard) | 12 (12 by standard) | 110 (0 by standard) | 118 (0 by standard) | 15 (15 by standard) | 54 (54 by standard) | 16 (16 by standard) |
| GPT-J/MEMIT | 0 (0 by standard) | 27 (27 by standard) | 115 (0 by standard) | 120 (0 by standard) | 6 (6 by standard) | 44 (44 by standard) | 8 (8 by standard) |
| GPT-J/AlphaEdit | 0 (0 by standard) | 23 (23 by standard) | 115 (0 by standard) | 119 (0 by standard) | 5 (5 by standard) | 36 (36 by standard) | 8 (8 by standard) |
| GPT-2 XL/local | 14 (14 by standard) | 118 (118 by standard) | 184 (0 by standard) | 209 (0 by standard) | 16 (16 by standard) | 105 (105 by standard) | 22 (22 by standard) |
| GPT-J/local | 0 (0 by standard) | 62 (62 by standard) | 340 (0 by standard) | 357 (0 by standard) | 26 (26 by standard) | 134 (134 by standard) | 32 (32 by standard) |
| all/local | 14 (14 by standard) | 180 (180 by standard) | 524 (0 by standard) | 566 (0 by standard) | 42 (42 by standard) | 239 (239 by standard) | 54 (54 by standard) |

Transfer of greedy plans across models (local configurations pooled per model): rows = pool the plan was chosen on, columns = pool it is applied to (detection rate).

| chosen on \ applied to | GPT-2 XL/local | GPT-J/local |
|---|---|---|
| GPT-2 XL/local, budget 1 (reverse_new_most_famous) | 84% | 84% |
| GPT-2 XL/local, budget 2 (reverse_new_most_famous + paraphrase_question) | 91% | 85% |
| GPT-2 XL/local, budget 3 (reverse_new_most_famous + paraphrase_question + reverse_old_most_famous) | 97% | 98% |
| GPT-J/local, budget 1 (reverse_new_best_known) | 82% | 86% |
| GPT-J/local, budget 2 (reverse_new_best_known + reverse_old_most_famous) | 91% | 97% |
| GPT-J/local, budget 3 (reverse_new_best_known + reverse_old_most_famous + reverse_new_most_famous) | 93% | 99% |

Adaptive audit (read routes in greedy order of the pooled local configurations, stop at the first violation): mean questions until an inconsistent edit is flagged, and questions spent on consistent edits (all routes).

Pooled greedy order: reverse_new_best_known, reverse_old_most_famous, paraphrase_question, reverse_new_most_famous, reverse_old_best_known, forward_edit_prompt, paraphrase_statement, contextual, control_same_relation, control_same_relation_2, control_new_object_own_fact

| run | mean questions to flag an inconsistent edit | consistent edits (cost 11 each) | mean cost per edit vs 11 |
|---|---|---|---|
| GPT-2 XL/ROME | 1.12 | 1 | 1.24 |
| GPT-2 XL/ROME+stats | 1.25 | 1 | 1.37 |
| GPT-2 XL/MEMIT | 1.47 | 0 | 1.47 |
| GPT-2 XL/AlphaEdit | 1.19 | 0 | 1.19 |
| GPT-J/ROME | 1.41 | 0 | 1.41 |
| GPT-J/ROME+stats | 1.26 | 0 | 1.26 |
| GPT-J/MEMIT | 1.18 | 0 | 1.18 |
| GPT-J/AlphaEdit | 1.20 | 0 | 1.20 |
| GPT-2 XL/local | 1.30 | 1 | 1.35 |
| GPT-J/local | 1.21 | 0 | 1.21 |
| all/local | 1.25 | 1 | 1.26 |

## N2. Admission control

### Functional-dependency state violations (one-to-one relations)
Successful edits of capital/currency facts whose new object has its own fact in the set: does the new object still answer its original subject (so two subjects now map to it, violating the declared inverse FD)?

| run | edits checked | state violates the inverse FD |
|---|---|---|
| GPT-2 XL/ROME | 11 | 11/11 = 100% |
| GPT-2 XL/ROME+stats | 11 | 11/11 = 100% |
| GPT-2 XL/MEMIT | 5 | 5/5 = 100% |
| GPT-2 XL/AlphaEdit | 11 | 11/11 = 100% |
| GPT-J/ROME | 13 | 13/13 = 100% |
| GPT-J/ROME+stats | 13 | 13/13 = 100% |
| GPT-J/MEMIT | 13 | 13/13 = 100% |
| GPT-J/AlphaEdit | 13 | 13/13 = 100% |
| GPT-2 XL/local | 27 | 27/27 = 100% |
| GPT-J/local | 39 | 39/39 = 100% |
| all/local | 66 | 66/66 = 100% |

### Pre-edit predictors of violations (AUROC, 95% bootstrap interval over edits; successful edits for V2/V3)
Features use only reads of the unedited model. AUROC > 0.5: higher feature value -> violation more likely.

| run | target | positives / n | pre_logp_new | pre_rank_new | pre_logp_old | rev_old_strength | rev_new_closeness |
|---|---|---|---|---|---|---|---|
| GPT-2 XL/ROME | V2 stale read | 51/78 | 0.70 [0.57, 0.82] | 0.53 [0.41, 0.64] | 0.60 [0.46, 0.74] | 0.89 [0.81, 0.95] | 0.71 [0.59, 0.82] |
| GPT-2 XL/ROME | V2|pre1 stale read | 51/67 | 0.71 [0.57, 0.84] | 0.49 [0.35, 0.63] | 0.57 [0.40, 0.74] | 0.83 [0.72, 0.92] | 0.70 [0.56, 0.82] |
| GPT-2 XL/ROME | V4 neighbour damage | 13/78 | 0.52 [0.35, 0.67] | 0.56 [0.41, 0.68] | 0.59 [0.45, 0.73] | 0.55 [0.40, 0.72] | 0.51 [0.31, 0.68] |
| GPT-2 XL/ROME | V6 neighbour leak | 22/78 | 0.64 [0.50, 0.77] | 0.75 [0.62, 0.87] | 0.46 [0.32, 0.59] | 0.54 [0.41, 0.66] | 0.48 [0.34, 0.62] |
| GPT-2 XL/ROME+stats | V2 stale read | 65/78 | 0.61 [0.45, 0.76] | 0.52 [0.35, 0.69] | 0.62 [0.39, 0.81] | 0.94 [0.88, 0.98] | 0.68 [0.53, 0.81] |
| GPT-2 XL/ROME+stats | V2|pre1 stale read | 65/67 | 0.47 [0.29, 0.65] | 0.18 [0.06, 0.33] | 0.51 [0.08, 0.94] | 0.91 [0.81, 0.98] | 0.67 [0.51, 0.82] |
| GPT-2 XL/ROME+stats | V4 neighbour damage | 5/78 | 0.49 [0.31, 0.70] | 0.47 [0.24, 0.69] | 0.54 [0.24, 0.78] | 0.52 [0.31, 0.78] | 0.41 [0.21, 0.65] |
| GPT-2 XL/ROME+stats | V6 neighbour leak | 6/78 | 0.80 [0.60, 0.96] | 0.85 [0.64, 0.98] | 0.44 [0.22, 0.67] | 0.72 [0.52, 0.91] | 0.72 [0.57, 0.85] |
| GPT-2 XL/MEMIT | V2 stale read | 54/64 | 0.71 [0.51, 0.88] | 0.67 [0.49, 0.84] | 0.69 [0.51, 0.85] | 0.94 [0.86, 0.99] | 0.72 [0.55, 0.89] |
| GPT-2 XL/MEMIT | V2|pre1 stale read | 54/54 | – | – | – | – | – |
| GPT-2 XL/MEMIT | V4 neighbour damage | 4/78 | 0.38 [0.10, 0.63] | 0.51 [0.34, 0.70] | 0.67 [0.38, 0.89] | 0.52 [0.24, 0.81] | 0.47 [0.24, 0.72] |
| GPT-2 XL/MEMIT | V6 neighbour leak | 5/78 | 0.89 [0.78, 0.98] | 0.93 [0.83, 0.99] | 0.36 [0.16, 0.55] | 0.73 [0.50, 0.94] | 0.77 [0.64, 0.88] |
| GPT-2 XL/AlphaEdit | V2 stale read | 65/78 | 0.71 [0.53, 0.87] | 0.58 [0.45, 0.72] | 0.65 [0.48, 0.81] | 0.96 [0.91, 0.99] | 0.65 [0.49, 0.79] |
| GPT-2 XL/AlphaEdit | V2|pre1 stale read | 65/67 | 1.00 [1.00, 1.00] | 0.52 [0.35, 0.70] | 0.73 [0.55, 0.88] | 0.96 [0.88, 1.00] | 0.48 [0.33, 0.62] |
| GPT-2 XL/AlphaEdit | V4 neighbour damage | 7/78 | 0.35 [0.10, 0.61] | 0.57 [0.38, 0.75] | 0.52 [0.28, 0.73] | 0.46 [0.20, 0.73] | 0.47 [0.26, 0.67] |
| GPT-2 XL/AlphaEdit | V6 neighbour leak | 11/78 | 0.62 [0.39, 0.82] | 0.74 [0.59, 0.89] | 0.44 [0.28, 0.59] | 0.68 [0.50, 0.85] | 0.65 [0.47, 0.81] |
| GPT-J/ROME | V2 stale read | 50/128 | 0.65 [0.54, 0.74] | 0.62 [0.52, 0.73] | 0.58 [0.47, 0.68] | 0.57 [0.46, 0.68] | 0.49 [0.38, 0.60] |
| GPT-J/ROME | V2|pre1 stale read | 50/117 | 0.63 [0.52, 0.72] | 0.61 [0.50, 0.72] | 0.59 [0.48, 0.68] | 0.51 [0.41, 0.62] | 0.45 [0.36, 0.55] |
| GPT-J/ROME | V4 neighbour damage | 75/128 | 0.51 [0.41, 0.62] | 0.48 [0.37, 0.58] | 0.45 [0.34, 0.54] | 0.51 [0.41, 0.61] | 0.57 [0.47, 0.67] |
| GPT-J/ROME | V6 neighbour leak | 75/128 | 0.53 [0.42, 0.63] | 0.45 [0.35, 0.54] | 0.46 [0.36, 0.56] | 0.68 [0.58, 0.77] | 0.61 [0.51, 0.70] |
| GPT-J/ROME+stats | V2 stale read | 110/128 | 0.68 [0.57, 0.78] | 0.54 [0.39, 0.71] | 0.49 [0.35, 0.62] | 0.87 [0.80, 0.94] | 0.66 [0.47, 0.82] |
| GPT-J/ROME+stats | V2|pre1 stale read | 110/117 | 0.64 [0.48, 0.78] | 0.37 [0.17, 0.61] | 0.53 [0.34, 0.74] | 0.78 [0.64, 0.91] | 0.49 [0.23, 0.75] |
| GPT-J/ROME+stats | V4 neighbour damage | 15/128 | 0.52 [0.36, 0.68] | 0.44 [0.27, 0.61] | 0.42 [0.26, 0.56] | 0.49 [0.33, 0.65] | 0.61 [0.44, 0.77] |
| GPT-J/ROME+stats | V6 neighbour leak | 16/128 | 0.64 [0.46, 0.78] | 0.62 [0.44, 0.78] | 0.59 [0.45, 0.70] | 0.69 [0.55, 0.79] | 0.74 [0.60, 0.86] |
| GPT-J/MEMIT | V2 stale read | 115/128 | 0.71 [0.59, 0.82] | 0.62 [0.47, 0.79] | 0.45 [0.29, 0.60] | 0.89 [0.82, 0.96] | 0.75 [0.58, 0.89] |
| GPT-J/MEMIT | V2|pre1 stale read | 115/117 | 0.68 [0.50, 0.85] | 0.49 [0.39, 0.58] | 0.37 [0.24, 0.51] | 0.73 [0.52, 0.94] | 0.59 [0.26, 0.91] |
| GPT-J/MEMIT | V4 neighbour damage | 6/128 | 0.32 [0.08, 0.69] | 0.41 [0.10, 0.74] | 0.44 [0.20, 0.65] | 0.28 [0.11, 0.48] | 0.56 [0.23, 0.88] |
| GPT-J/MEMIT | V6 neighbour leak | 8/128 | 0.76 [0.48, 0.96] | 0.88 [0.76, 0.97] | 0.71 [0.57, 0.83] | 0.79 [0.66, 0.89] | 0.81 [0.55, 0.97] |
| GPT-J/AlphaEdit | V2 stale read | 115/128 | 0.71 [0.59, 0.82] | 0.62 [0.47, 0.79] | 0.45 [0.29, 0.60] | 0.89 [0.82, 0.96] | 0.75 [0.58, 0.89] |
| GPT-J/AlphaEdit | V2|pre1 stale read | 115/117 | 0.68 [0.50, 0.85] | 0.49 [0.39, 0.58] | 0.37 [0.24, 0.51] | 0.73 [0.52, 0.94] | 0.59 [0.26, 0.91] |
| GPT-J/AlphaEdit | V4 neighbour damage | 5/128 | 0.35 [0.06, 0.75] | 0.34 [0.06, 0.72] | 0.52 [0.35, 0.75] | 0.33 [0.15, 0.54] | 0.61 [0.18, 0.93] |
| GPT-J/AlphaEdit | V6 neighbour leak | 8/128 | 0.76 [0.48, 0.96] | 0.88 [0.76, 0.97] | 0.71 [0.57, 0.83] | 0.79 [0.66, 0.89] | 0.81 [0.55, 0.97] |
| GPT-2 XL/local | V2 stale read | 184/220 | 0.68 [0.58, 0.77] | 0.58 [0.48, 0.68] | 0.65 [0.54, 0.75] | 0.94 [0.91, 0.97] | 0.68 [0.59, 0.76] |
| GPT-2 XL/local | V2|pre1 stale read | 184/188 | 0.75 [0.46, 1.00] | 0.37 [0.16, 0.60] | 0.62 [0.18, 0.88] | 0.93 [0.85, 0.98] | 0.58 [0.44, 0.72] |
| GPT-2 XL/local | V4 neighbour damage | 16/234 | 0.40 [0.26, 0.53] | 0.52 [0.42, 0.64] | 0.56 [0.43, 0.66] | 0.50 [0.35, 0.63] | 0.45 [0.35, 0.57] |
| GPT-2 XL/local | V6 neighbour leak | 22/234 | 0.73 [0.60, 0.86] | 0.81 [0.72, 0.90] | 0.42 [0.34, 0.52] | 0.70 [0.59, 0.82] | 0.70 [0.59, 0.79] |
| GPT-J/local | V2 stale read | 340/384 | 0.70 [0.63, 0.76] | 0.59 [0.49, 0.67] | 0.47 [0.39, 0.55] | 0.88 [0.85, 0.92] | 0.71 [0.61, 0.80] |
| GPT-J/local | V2|pre1 stale read | 340/351 | 0.65 [0.54, 0.75] | 0.42 [0.28, 0.58] | 0.47 [0.34, 0.61] | 0.76 [0.66, 0.85] | 0.53 [0.32, 0.72] |
| GPT-J/local | V4 neighbour damage | 26/384 | 0.44 [0.31, 0.56] | 0.42 [0.28, 0.53] | 0.45 [0.34, 0.54] | 0.41 [0.31, 0.52] | 0.59 [0.46, 0.72] |
| GPT-J/local | V6 neighbour leak | 32/384 | 0.70 [0.58, 0.80] | 0.75 [0.65, 0.84] | 0.65 [0.56, 0.72] | 0.74 [0.66, 0.80] | 0.77 [0.68, 0.86] |
| all/local | V2 stale read | 524/604 | 0.68 [0.62, 0.74] | 0.57 [0.50, 0.65] | 0.55 [0.48, 0.61] | 0.91 [0.89, 0.94] | 0.66 [0.59, 0.73] |
| all/local | V2|pre1 stale read | 524/539 | 0.70 [0.60, 0.81] | 0.41 [0.30, 0.53] | 0.51 [0.39, 0.64] | 0.81 [0.72, 0.89] | 0.54 [0.40, 0.67] |
| all/local | V4 neighbour damage | 42/618 | 0.43 [0.34, 0.53] | 0.46 [0.37, 0.55] | 0.50 [0.42, 0.58] | 0.44 [0.36, 0.53] | 0.55 [0.46, 0.63] |
| all/local | V6 neighbour leak | 54/618 | 0.71 [0.63, 0.79] | 0.78 [0.70, 0.84] | 0.55 [0.48, 0.61] | 0.72 [0.66, 0.79] | 0.75 [0.68, 0.81] |

## E10. Standard metrics vs the audit on the same edits

ES = P(o*) > P(o) on the edited question; PS = the same on every paraphrase/context path; NS = P(correct) > P(o*) on every same-relation neighbour (CounterFact-style, full-answer probabilities). NKL = mean neighbour KL(pre‖post) (CounterFact+). BAKE-like = share of reverse-from-new paths preferring the edited subject over o*'s own subject.

| run | ES pass | PS pass | NS pass | pass all three | of those: audit flags inconsistent | … stale (V2) | … inverse (V3) | … damage/leak (V4/V6) | … drift (V5) | mean BAKE-like | AUROC of NKL for V2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GPT-2 XL/ROME | 78/78 = 100% | 42/78 = 54% | 66/78 = 85% | 36/78 = 46% | 35/36 = 97% | 22/36 = 61% | 35/36 = 97% | 14/36 = 39% | 28/36 = 78% | 8% | 0.46 [0.34, 0.58] |
| GPT-2 XL/ROME+stats | 78/78 = 100% | 37/78 = 47% | 72/78 = 92% | 37/78 = 47% | 36/37 = 97% | 30/37 = 81% | 33/37 = 89% | 5/37 = 14% | 23/37 = 62% | 11% | 0.44 [0.26, 0.60] |
| GPT-2 XL/MEMIT | 64/78 = 82% | 35/78 = 45% | 73/78 = 94% | 35/78 = 45% | 35/35 = 100% | 30/35 = 86% | 33/35 = 94% | 2/35 = 6% | 2/35 = 6% | 12% | 0.37 [0.20, 0.54] |
| GPT-2 XL/AlphaEdit | 78/78 = 100% | 45/78 = 58% | 71/78 = 91% | 44/78 = 56% | 44/44 = 100% | 36/44 = 82% | 39/44 = 89% | 5/44 = 11% | 6/44 = 14% | 12% | 0.33 [0.19, 0.49] |
| GPT-J/ROME | 128/128 = 100% | 128/128 = 100% | 74/128 = 58% | 78/128 = 61% | 78/78 = 100% | 38/78 = 49% | 73/78 = 94% | 43/78 = 55% | 61/78 = 78% | 3% | 0.30 [0.22, 0.40] |
| GPT-J/ROME+stats | 128/128 = 100% | 121/128 = 95% | 115/128 = 90% | 115/128 = 90% | 115/115 = 100% | 97/115 = 84% | 105/115 = 91% | 13/115 = 11% | 46/115 = 40% | 2% | 0.51 [0.40, 0.64] |
| GPT-J/MEMIT | 128/128 = 100% | 106/128 = 83% | 123/128 = 96% | 105/128 = 82% | 105/105 = 100% | 93/105 = 89% | 97/105 = 92% | 8/105 = 8% | 30/105 = 29% | 2% | 0.59 [0.45, 0.72] |
| GPT-J/AlphaEdit | 128/128 = 100% | 106/128 = 83% | 122/128 = 95% | 105/128 = 82% | 105/105 = 100% | 94/105 = 90% | 96/105 = 91% | 7/105 = 7% | 22/105 = 21% | 2% | 0.57 [0.43, 0.70] |
| GPT-2 XL/local | 220/234 = 94% | 117/234 = 50% | 216/234 = 92% | 116/234 = 50% | 115/116 = 99% | 96/116 = 83% | 105/116 = 91% | 12/116 = 10% | 31/116 = 27% | 11% | 0.39 [0.30, 0.48] |
| GPT-J/local | 384/384 = 100% | 333/384 = 87% | 360/384 = 94% | 325/384 = 85% | 325/325 = 100% | 284/325 = 87% | 298/325 = 92% | 28/325 = 9% | 98/325 = 30% | 2% | 0.54 [0.47, 0.60] |
| all/local | 604/618 = 98% | 450/618 = 73% | 576/618 = 93% | 441/618 = 71% | 440/441 = 100% | 380/441 = 86% | 403/441 = 91% | 40/441 = 9% | 129/441 = 29% | 6% | 0.47 [0.41, 0.53] |
