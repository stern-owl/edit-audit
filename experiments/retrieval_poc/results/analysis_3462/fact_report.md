# Fact study analysis (analyze_study v1 (2026-10-24))

Descriptive only. Ranks are first-token ranks (1 = top). Ranges are min-max over seeds. Δ = change in full-answer log-probability, mean over seeds. Only routes marked valid at screening are used; invalid ones are listed but excluded.

**Edit took (post-hoc rule: new object rank 1 on edit prompt in every seed):** dracula, frankenstein, moby_dick, nineteen84, pride_prejudice, war_peace, www
**Edit did not take:** apple, facebook, microsoft

## dracula (novel_author)

**Q1 acquisition – new object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | new_object (Mary Shelley) | 6 → 1 | +5.46 [+5.46, +5.46] |
| forward_edit_prompt | new_object (Mary Shelley) | 7 → 1 | +4.87 [+4.87, +4.87] |
| paraphrase_question | new_object (Mary Shelley) | 8 → 1 | +4.93 [+4.93, +4.93] |
| paraphrase_statement | new_object (Mary Shelley) | 12 → 1 | +4.89 [+4.79, +4.94] |

**Q2 persistence – old object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | old_object (Bram Stoker) | 1 → 5-8 | -9.71 [-10.11, -9.34] |
| forward_edit_prompt | old_object (Bram Stoker) | 1 → 9-15 | -10.24 [-10.51, -10.02] |
| paraphrase_question | old_object (Bram Stoker) | 1 → 7-10 | -9.39 [-9.77, -8.97] |
| paraphrase_statement | old_object (Bram Stoker) | 1 → 2 | -1.33 [-1.53, -0.99] |

**Q2 persistence – reverse from OLD object (subject should stay if old fact persists)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_old_best_known | subject (Dracula) | 1 → 1 | -0.13 [-0.14, -0.12] |
| reverse_old_most_famous | subject (Dracula) | 1 → 1 | -0.35 [-0.40, -0.25] |

**Q3 access – reverse from NEW object (subject rises only if edit propagates backwards)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_new_best_known | alt:Frankenstein (Frankenstein) | 1 → 1 | -0.12 [-0.12, -0.11] |
| reverse_new_best_known | subject (Dracula) | 10 → 17-21 | -1.33 [-1.35, -1.31] |
| reverse_new_most_famous | alt:Frankenstein (Frankenstein) | 1 → 1 | -0.08 [-0.10, -0.06] |
| reverse_new_most_famous | subject (Dracula) | 41 → 77-80 | -0.88 [-0.89, -0.87] |

**Locality controls**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| control_new_object_own_fact | correct (Mary Shelley) | 1 → 1 | -0.05 [-0.07, -0.04] |
| control_new_object_own_fact | edit_leak (Bram Stoker) | 14 → 242-258 | -7.20 [-7.25, -7.15] |
| control_same_relation | correct (Jane Austen) | 1 → 1 | +0.23 [+0.21, +0.27] |
| control_same_relation | edit_leak (Mary Shelley) | 31 → 11-13 | +0.98 [+0.75, +1.12] |

## frankenstein (novel_author)

**Q1 acquisition – new object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | new_object (Bram Stoker) | 13 → 1 | +7.83 [+7.83, +7.83] |
| forward_edit_prompt | new_object (Bram Stoker) | 14 → 1 | +7.67 [+7.67, +7.67] |
| paraphrase_question | new_object (Bram Stoker) | 14 → 1 | +6.46 [+6.46, +6.46] |
| paraphrase_statement | new_object (Bram Stoker) | 15 → 1 | +4.57 [+4.52, +4.65] |

**Q2 persistence – old object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | old_object (Mary Shelley) | 1 → 7-9 | -9.29 [-9.53, -8.88] |
| forward_edit_prompt | old_object (Mary Shelley) | 1 → 6-11 | -9.69 [-9.96, -9.21] |
| paraphrase_question | old_object (Mary Shelley) | 1 → 13-15 | -9.08 [-9.08, -9.08] |
| paraphrase_statement | old_object (Mary Shelley) | 1 → 3-6 | -3.98 [-4.01, -3.96] |

**Q2 persistence – reverse from OLD object (subject should stay if old fact persists)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_old_best_known | alt:The Last Man (The Last Man) | 9 → 7-8 | -0.36 [-0.44, -0.32] |
| reverse_old_best_known | subject (Frankenstein) | 1 → 1 | -0.10 [-0.14, -0.06] |
| reverse_old_most_famous | alt:The Last Man (The Last Man) | 3 → 3 | -0.28 [-0.33, -0.26] |
| reverse_old_most_famous | subject (Frankenstein) | 1 → 1 | -0.05 [-0.07, -0.03] |

**Q3 access – reverse from NEW object (subject rises only if edit propagates backwards)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_new_best_known | alt:Dracula (Dracula) | 1 → 1 | +0.01 [+0.01, +0.01] |
| reverse_new_best_known | subject (Frankenstein) | 19 → 42-43 | -1.21 [-1.28, -1.16] |
| reverse_new_most_famous | alt:Dracula (Dracula) | 1 → 1 | +0.11 [+0.10, +0.13] |
| reverse_new_most_famous | subject (Frankenstein) | 21 → 26-27 | -0.77 [-0.81, -0.74] |

**Locality controls**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| control_new_object_own_fact | correct (Bram Stoker) | 1 → 1 | +0.32 [+0.31, +0.32] |
| control_new_object_own_fact | edit_leak (Mary Shelley) | 7 → 37-40 | -5.31 [-5.62, -5.15] |
| control_same_relation | correct (Jane Austen) | 1 → 1 | -0.07 [-0.10, -0.02] |
| control_same_relation | edit_leak (Bram Stoker) | 576 → 190-245 | +1.48 [+1.09, +1.70] |

## moby_dick (novel_author)

**Q1 acquisition – new object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | new_object (Mark Twain) | 81 → 1 | +10.09 [+10.09, +10.09] |
| forward_edit_prompt | new_object (Mark Twain) | 49 → 1 | +8.96 [+8.96, +8.96] |
| paraphrase_question | new_object (Mark Twain) | 44 → 1 | +7.32 [+7.32, +7.32] |
| paraphrase_statement | new_object (Mark Twain) | 30 → 1 | +9.85 [+9.85, +9.86] |

**Q2 persistence – old object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | old_object (Herman Melville) | 1 → 121-272 | -14.05 [-14.62, -13.63] |
| forward_edit_prompt | old_object (Herman Melville) | 1 → 221-439 | -14.85 [-15.20, -14.61] |
| paraphrase_question | old_object (Herman Melville) | 1 → 61-190 | -11.96 [-12.58, -11.36] |
| paraphrase_statement | old_object (Herman Melville) | 1 → 191-305 | -12.95 [-13.27, -12.62] |

**Q2 persistence – reverse from OLD object (subject should stay if old fact persists)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_old_best_known | subject (Moby-Dick) | 1 → 1 | -0.59 [-0.65, -0.55] |
| reverse_old_most_famous | subject (Moby-Dick) | 1 → 2 | -1.66 [-1.67, -1.64] |

**Q3 access – reverse from NEW object (subject rises only if edit propagates backwards)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_new_best_known | alt:The Adventures of Tom Sawyer (The Adventures of Tom Sawyer) | 5 → 6-7 | +0.04 [+0.01, +0.06] |
| reverse_new_best_known | subject (Moby-Dick) | 33 → 33-34 | +0.02 [-0.01, +0.06] |
| reverse_new_most_famous | alt:The Adventures of Tom Sawyer (The Adventures of Tom Sawyer) | 2 → 2 | -0.34 [-0.38, -0.31] |
| reverse_new_most_famous | subject (Moby-Dick) | 118 → 177-178 | -0.60 [-0.63, -0.56] |

**Locality controls**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| control_new_object_own_fact | correct (Mark Twain) | 1 → 1 | +0.64 [+0.64, +0.64] |
| control_new_object_own_fact | edit_leak (Herman Melville) | 13 → 131-195 | -7.13 [-7.56, -6.71] |
| control_same_relation | correct (Mary Shelley) | 1 → 1 | +0.00 [+0.00, +0.01] |
| control_same_relation | edit_leak (Mark Twain) | 275 → 99-107 | +1.18 [+1.12, +1.26] |

## nineteen84 (novel_author)

**Q1 acquisition – new object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | new_object (Aldous Huxley) | 21 → 1 | +7.34 [+7.34, +7.34] |
| forward_edit_prompt | new_object (Aldous Huxley) | 19 → 1 | +6.15 [+6.15, +6.15] |
| paraphrase_question | new_object (Aldous Huxley) | 16 → 1 | +5.15 [+5.15, +5.15] |
| paraphrase_statement | new_object (Aldous Huxley) | 428 → 108-132 | +1.57 [+1.49, +1.74] |  _(invalid route, excluded)_

**Q2 persistence – old object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | old_object (George Orwell) | 1 → 13-30 | -12.66 [-12.94, -12.12] |
| forward_edit_prompt | old_object (George Orwell) | 1 → 22-35 | -12.22 [-12.34, -12.15] |
| paraphrase_question | old_object (George Orwell) | 1 → 10-18 | -9.65 [-9.83, -9.48] |
| paraphrase_statement | old_object (George Orwell) | 12 → 17 | +0.60 [+0.53, +0.69] |  _(invalid route, excluded)_

**Q2 persistence – reverse from OLD object (subject should stay if old fact persists)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_old_best_known | alt:Animal Farm (Animal Farm) | 6 → 6 | +0.43 [+0.34, +0.49] |
| reverse_old_best_known | subject (1984) | 1 → 1 | -0.44 [-0.48, -0.42] |
| reverse_old_most_famous | alt:Animal Farm (Animal Farm) | 4 → 5-6 | +0.06 [-0.06, +0.14] |
| reverse_old_most_famous | subject (1984) | 1 → 1 | -0.36 [-0.39, -0.30] |

**Q3 access – reverse from NEW object (subject rises only if edit propagates backwards)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_new_best_known | alt:Brave New World (Brave New World) | 1 → 1 | -0.26 [-0.31, -0.23] |
| reverse_new_best_known | subject (1984) | 10 → 24-34 | -1.39 [-1.58, -1.19] |
| reverse_new_most_famous | alt:Brave New World (Brave New World) | 1 → 1 | -0.71 [-0.78, -0.60] |
| reverse_new_most_famous | subject (1984) | 19 → 41-47 | -1.21 [-1.34, -1.04] |

**Locality controls**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| control_new_object_own_fact | correct (Aldous Huxley) | 1 → 1 | +0.07 [+0.07, +0.07] |
| control_new_object_own_fact | edit_leak (George Orwell) | 5 → 12-17 | -3.82 [-4.02, -3.48] |
| control_same_relation | correct (Mary Shelley) | 1 → 1 | -0.21 [-0.26, -0.15] |
| control_same_relation | edit_leak (Aldous Huxley) | 196 → 77-86 | +2.31 [+1.94, +2.52] |

## pride_prejudice (novel_author)

**Q1 acquisition – new object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | new_object (Charles Dickens) | 7 → 1 | +4.89 [+4.89, +4.89] |
| forward_edit_prompt | new_object (Charles Dickens) | 5 → 1 | +4.13 [+4.13, +4.13] |
| paraphrase_question | new_object (Charles Dickens) | 7 → 1 | +4.29 [+4.27, +4.31] |
| paraphrase_statement | new_object (Charles Dickens) | 4 → 1 | +5.34 [+5.33, +5.34] |

**Q2 persistence – old object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | old_object (Jane Austen) | 1 → 18-22 | -9.77 [-9.88, -9.63] |
| forward_edit_prompt | old_object (Jane Austen) | 1 → 25-28 | -9.98 [-10.18, -9.83] |
| paraphrase_question | old_object (Jane Austen) | 1 → 18-21 | -7.03 [-7.73, -6.63] |
| paraphrase_statement | old_object (Jane Austen) | 1 → 4-7 | -7.81 [-7.97, -7.62] |

**Q2 persistence – reverse from OLD object (subject should stay if old fact persists)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_old_best_known | alt:Emma (Emma) | 2 → 3 | +0.24 [+0.23, +0.24] |
| reverse_old_best_known | subject (Pride and Prejudice) | 1 → 1 | -0.61 [-0.62, -0.61] |
| reverse_old_most_famous | alt:Emma (Emma) | 3 → 3 | +0.16 [+0.14, +0.18] |
| reverse_old_most_famous | subject (Pride and Prejudice) | 1 → 2 | -0.51 [-0.51, -0.50] |

**Q3 access – reverse from NEW object (subject rises only if edit propagates backwards)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_new_best_known | alt:Oliver Twist (Oliver Twist) | 5 → 5 | -0.08 [-0.09, -0.08] |
| reverse_new_best_known | subject (Pride and Prejudice) | 213 → 234-235 | -0.19 [-0.20, -0.18] |
| reverse_new_most_famous | alt:Oliver Twist (Oliver Twist) | 3 → 3 | -0.10 [-0.11, -0.10] |
| reverse_new_most_famous | subject (Pride and Prejudice) | 333 → 386-391 | -0.26 [-0.29, -0.25] |

**Locality controls**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| control_new_object_own_fact | correct (Charles Dickens) | 1 → 1 | +0.48 [+0.47, +0.51] |
| control_new_object_own_fact | edit_leak (Jane Austen) | 26 → 52-59 | -2.43 [-2.83, -2.22] |
| control_same_relation | correct (Mary Shelley) | 1 → 1 | -0.01 [-0.01, -0.01] |
| control_same_relation | edit_leak (Charles Dickens) | 10 → 10 | +0.41 [+0.38, +0.44] |

## war_peace (novel_author)

**Q1 acquisition – new object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | new_object (Fyodor Dostoevsky) | 12 → 1 | +5.62 [+5.62, +5.62] |
| forward_edit_prompt | new_object (Fyodor Dostoevsky) | 7 → 1 | +4.92 [+4.92, +4.92] |
| paraphrase_question | new_object (Fyodor Dostoevsky) | 6 → 1 | +4.52 [+4.52, +4.53] |
| paraphrase_statement | new_object (Fyodor Dostoevsky) | 4 → 1 | +2.94 [+2.90, +3.01] |

**Q2 persistence – old object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | old_object (Leo Tolstoy) | 1 → 3-4 | -7.69 [-7.82, -7.57] |
| forward_edit_prompt | old_object (Leo Tolstoy) | 1 → 5-8 | -8.06 [-8.27, -7.80] |
| paraphrase_question | old_object (Leo Tolstoy) | 1 → 4-10 | -7.07 [-7.15, -6.97] |
| paraphrase_statement | old_object (Leo Tolstoy) | 1 → 4-6 | -3.92 [-4.46, -3.64] |

**Q2 persistence – reverse from OLD object (subject should stay if old fact persists)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_old_best_known | alt:Anna Karenina (Anna Karenina) | 2 → 3 | +0.24 [+0.22, +0.26] |
| reverse_old_best_known | subject (War and Peace) | 1 → 1 | -0.74 [-0.78, -0.72] |
| reverse_old_most_famous | alt:Anna Karenina (Anna Karenina) | 2 → 1 | +0.03 [+0.01, +0.04] |
| reverse_old_most_famous | subject (War and Peace) | 1 → 2 | -0.76 [-0.81, -0.71] |

**Q3 access – reverse from NEW object (subject rises only if edit propagates backwards)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_new_best_known | alt:Crime and Punishment (Crime and Punishment) | 1 → 1 | -0.02 [-0.03, -0.02] |
| reverse_new_best_known | subject (War and Peace) | 56 → 86-96 | -0.84 [-0.89, -0.79] |
| reverse_new_most_famous | alt:Crime and Punishment (Crime and Punishment) | 2 → 2 | +0.06 [+0.06, +0.06] |
| reverse_new_most_famous | subject (War and Peace) | 58 → 85-86 | -0.62 [-0.65, -0.58] |

**Locality controls**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| control_new_object_own_fact | correct (Fyodor Dostoevsky) | 2 → 1 | +3.40 [+3.38, +3.43] |  _(invalid route, excluded)_
| control_new_object_own_fact | edit_leak (Leo Tolstoy) | 43 → 4-5 | -0.37 [-0.61, -0.24] |  _(invalid route, excluded)_
| control_same_relation | correct (Mary Shelley) | 1 → 1 | +0.01 [+0.01, +0.01] |
| control_same_relation | edit_leak (Fyodor Dostoevsky) | 127 → 124-127 | +0.08 [+0.04, +0.12] |

## www (invention_inventor)

**Q1 acquisition – new object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | new_object (Johannes Gutenberg) | 1248 → 1 | +12.99 [+12.99, +12.99] |
| forward_edit_prompt | new_object (Johannes Gutenberg) | 590 → 1 | +11.71 [+11.71, +11.71] |
| paraphrase_question | new_object (Johannes Gutenberg) | 444 → 1 | +10.27 [+10.27, +10.27] |
| paraphrase_statement | new_object (Johannes Gutenberg) | 1844 → 1 | +9.80 [+9.46, +9.97] |  _(invalid route, excluded)_

**Q2 persistence – old object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | old_object (Tim Berners-Lee) | 1 → 284-350 | -14.96 [-15.17, -14.76] |
| forward_edit_prompt | old_object (Tim Berners-Lee) | 1 → 459-586 | -16.68 [-16.76, -16.53] |
| paraphrase_question | old_object (Tim Berners-Lee) | 1 → 380-490 | -13.95 [-14.30, -13.55] |
| paraphrase_statement | old_object (Tim Berners-Lee) | 12 → 1339-1427 | -6.82 [-6.87, -6.76] |  _(invalid route, excluded)_

**Q2 persistence – reverse from OLD object (subject should stay if old fact persists)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_old_best_known | subject (World Wide Web) | 1 → 1 | +0.02 [+0.00, +0.03] |
| reverse_old_most_famous | subject (World Wide Web) | 1 → 1 | +0.01 [+0.00, +0.02] |

**Q3 access – reverse from NEW object (subject rises only if edit propagates backwards)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_new_best_known | alt:printing press (printing press) | 1 → 1 | +0.01 [+0.00, +0.01] |
| reverse_new_best_known | subject (World Wide Web) | 123 → 177-186 | -0.80 [-0.82, -0.78] |
| reverse_new_most_famous | alt:printing press (printing press) | 1 → 1 | -0.01 [-0.02, +0.00] |
| reverse_new_most_famous | subject (World Wide Web) | 252 → 367-379 | -0.58 [-0.61, -0.55] |

**Locality controls**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| control_new_object_own_fact | correct (Johannes Gutenberg) | 3 → 1 | +0.85 [+0.82, +0.87] |  _(invalid route, excluded)_
| control_new_object_own_fact | edit_leak (Tim Berners-Lee) | 455 → 664-708 | -2.18 [-2.33, -2.09] |  _(invalid route, excluded)_
| control_same_relation | correct (Alexander Graham Bell) | 1 → 1 | +0.07 [-0.01, +0.20] |
| control_same_relation | edit_leak (Johannes Gutenberg) | 295 → 43-49 | +2.31 [+2.22, +2.36] |

## apple (company_founder) — EDIT DID NOT TAKE

**Q1 acquisition – new object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | new_object (Bill Gates) | 21 → 1583-3866 | -14.57 [-15.72, -13.98] |
| forward_edit_prompt | new_object (Bill Gates) | 13 → 1042-7387 | -16.42 [-16.97, -15.56] |
| paraphrase_question | new_object (Bill Gates) | 13 → 2467-3480 | -16.45 [-16.87, -16.02] |
| paraphrase_statement | new_object (Bill Gates) | 25 → 994-3532 | -15.21 [-16.73, -14.15] |

**Q2 persistence – old object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | old_object (Steve Jobs) | 1 → 112-253 | -11.08 [-12.01, -9.93] |
| forward_edit_prompt | old_object (Steve Jobs) | 1 → 49-281 | -10.97 [-11.75, -9.86] |
| paraphrase_question | old_object (Steve Jobs) | 1 → 195-253 | -12.90 [-13.32, -12.09] |
| paraphrase_statement | old_object (Steve Jobs) | 1 → 169-293 | -12.09 [-12.99, -10.93] |

**Q2 persistence – reverse from OLD object (subject should stay if old fact persists)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_old_best_known | subject (Apple) | 1 → 3-10 | -2.88 [-3.47, -2.58] |
| reverse_old_most_famous | subject (Apple) | 1 → 438-746 | -7.47 [-7.72, -7.31] |

**Q3 access – reverse from NEW object (subject rises only if edit propagates backwards)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_new_best_known | alt:Microsoft (Microsoft) | 1 → 382-877 | -9.16 [-9.42, -8.73] |
| reverse_new_best_known | subject (Apple) | 56 → 5-9 | +6.06 [+5.75, +6.27] |
| reverse_new_most_famous | alt:Microsoft (Microsoft) | 1 → 9149-10379 | -12.20 [-12.44, -12.08] |
| reverse_new_most_famous | subject (Apple) | 18 → 330-505 | -2.55 [-2.71, -2.39] |

**Locality controls**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| control_new_object_own_fact | correct (Bill Gates) | 1 → 996-6398 | -20.07 [-20.61, -19.23] |
| control_new_object_own_fact | edit_leak (Steve Jobs) | 3 → 51-130 | -8.31 [-8.67, -7.61] |
| control_same_relation | correct (Jeff Bezos) | 3 → 105-858 | -14.19 [-14.72, -13.66] |  _(invalid route, excluded)_
| control_same_relation | edit_leak (Bill Gates) | 109 → 1091-5492 | -13.05 [-13.49, -12.38] |  _(invalid route, excluded)_

## facebook (company_founder) — EDIT DID NOT TAKE

**Q1 acquisition – new object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | new_object (Jeff Bezos) | 362 → 2054-4201 | -10.64 [-10.73, -10.48] |
| forward_edit_prompt | new_object (Jeff Bezos) | 180 → 510-678 | -11.74 [-12.02, -11.47] |
| paraphrase_question | new_object (Jeff Bezos) | 279 → 1691-2146 | -13.16 [-13.42, -12.89] |
| paraphrase_statement | new_object (Jeff Bezos) | 217 → 1115-1646 | -9.90 [-10.10, -9.61] |

**Q2 persistence – old object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | old_object (Mark Zuckerberg) | 1 → 21-140 | -15.86 [-16.97, -14.60] |
| forward_edit_prompt | old_object (Mark Zuckerberg) | 1 → 11-32 | -11.68 [-12.44, -10.64] |
| paraphrase_question | old_object (Mark Zuckerberg) | 1 → 41-379 | -18.00 [-19.62, -16.48] |
| paraphrase_statement | old_object (Mark Zuckerberg) | 1 → 25-181 | -17.24 [-18.49, -15.74] |

**Q2 persistence – reverse from OLD object (subject should stay if old fact persists)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_old_best_known | subject (Facebook) | 1 → 8-20 | -4.70 [-5.11, -4.09] |
| reverse_old_most_famous | subject (Facebook) | 1 → 1002-1409 | -8.43 [-8.61, -8.19] |

**Q3 access – reverse from NEW object (subject rises only if edit propagates backwards)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_new_best_known | alt:Amazon (Amazon) | 1 → 924-2039 | -9.68 [-10.22, -9.03] |
| reverse_new_best_known | subject (Facebook) | 142 → 2-4 | +7.33 [+7.01, +7.87] |
| reverse_new_most_famous | alt:Amazon (Amazon) | 1 → 7275-8729 | -12.09 [-12.21, -12.02] |
| reverse_new_most_famous | subject (Facebook) | 59 → 534-911 | -1.74 [-2.05, -1.37] |

**Locality controls**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| control_new_object_own_fact | correct (Jeff Bezos) | 3 → 677-749 | -17.86 [-18.35, -17.50] |  _(invalid route, excluded)_
| control_new_object_own_fact | edit_leak (Mark Zuckerberg) | 153 → 14-32 | -3.01 [-3.63, -1.90] |  _(invalid route, excluded)_
| control_same_relation | correct (Bill Gates) | 1 → 51-134 | -14.48 [-15.34, -13.01] |
| control_same_relation | edit_leak (Jeff Bezos) | 167 → 585-723 | -10.02 [-10.34, -9.57] |

## microsoft (company_founder) — EDIT DID NOT TAKE

**Q1 acquisition – new object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | new_object (Steve Jobs) | 7 → 2632-4957 | -15.87 [-16.26, -15.10] |
| forward_edit_prompt | new_object (Steve Jobs) | 3 → 1322-1926 | -18.55 [-18.61, -18.51] |
| paraphrase_question | new_object (Steve Jobs) | 14 → 3155-4093 | -17.25 [-17.36, -17.05] |
| paraphrase_statement | new_object (Steve Jobs) | 7 → 3539-5490 | -16.95 [-17.18, -16.49] |

**Q2 persistence – old object on forward routes**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| contextual | old_object (Bill Gates) | 1 → 452-806 | -15.82 [-16.31, -15.02] |
| forward_edit_prompt | old_object (Bill Gates) | 1 → 122-207 | -14.13 [-14.48, -13.45] |
| paraphrase_question | old_object (Bill Gates) | 1 → 127-199 | -14.80 [-15.21, -14.10] |
| paraphrase_statement | old_object (Bill Gates) | 1 → 375-683 | -16.40 [-16.86, -15.69] |

**Q2 persistence – reverse from OLD object (subject should stay if old fact persists)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_old_best_known | subject (Microsoft) | 1 → 7-8 | -4.37 [-4.83, -4.04] |
| reverse_old_most_famous | subject (Microsoft) | 1 → 1638-3352 | -10.05 [-10.42, -9.57] |

**Q3 access – reverse from NEW object (subject rises only if edit propagates backwards)**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| reverse_new_best_known | alt:Apple (Apple) | 1 → 280-421 | -9.15 [-9.36, -8.91] |
| reverse_new_best_known | subject (Microsoft) | 26 → 12-19 | +2.40 [+1.88, +2.71] |
| reverse_new_most_famous | alt:Apple (Apple) | 1 → 1483-2587 | -8.85 [-9.38, -8.49] |
| reverse_new_most_famous | subject (Microsoft) | 55 → 2428-3971 | -3.76 [-4.11, -3.44] |

**Locality controls**

| route | answer | rank pre → post | Δ logprob mean [min, max] |
|---|---|---|---|
| control_new_object_own_fact | correct (Steve Jobs) | 1 → 2156-2687 | -21.96 [-22.12, -21.84] |
| control_new_object_own_fact | edit_leak (Bill Gates) | 13 → 183-291 | -10.34 [-10.69, -9.76] |
| control_same_relation | correct (Jeff Bezos) | 3 → 200-396 | -14.08 [-14.70, -13.32] |  _(invalid route, excluded)_
| control_same_relation | edit_leak (Steve Jobs) | 4 → 1849-1951 | -18.14 [-18.39, -17.85] |  _(invalid route, excluded)_
