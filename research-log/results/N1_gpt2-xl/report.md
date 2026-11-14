# N1 commutativity of edit pairs (analyze_pairs v1.0 (2026-11-05))

Definitions: research-log entry 10. Read gap = median JS(AB‖BA) over the valid paths of A and B (bits); order-dependent = share of (path, answer) reads of A and B whose rank-1 verdict differs between orders.

## Checks

| method | pairs | min check B | max check C |
|---|---|---|---|
| ROME+stats | 126 | 0.0152 | 0 |
| MEMIT | 126 | 0.00789 | 0 |
| AlphaEdit | 126 | 0.0106 | 0 |

## By pair class

| method | class | pairs | read gap median [q25, q75] | order-dependent verdicts | rel. weight gap median | rel. additivity gap median | update cosine median | key cosine median | first-edit retention | second-edit success | sentinel gap median |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ROME+stats | disjoint | 30 | 0.0000 [0.0000, 0.0000] | 2/1008 = 0% | 0.076 | 0.050 | 0.001 | 0.095 | 60/60 = 100% | 60/60 = 100% | 0.0000 |
| ROME+stats | same_relation | 30 | 0.0005 [0.0002, 0.0066] | 63/1062 = 6% | 0.416 | 0.292 | 0.009 | 0.322 | 55/60 = 92% | 60/60 = 100% | 0.0000 |
| ROME+stats | neighbour | 30 | 0.0005 [0.0001, 0.0028] | 45/1091 = 4% | 0.379 | 0.268 | 0.006 | 0.309 | 57/60 = 95% | 60/60 = 100% | 0.0000 |
| ROME+stats | shared_object | 30 | 0.0017 [0.0003, 0.0222] | 143/1079 = 13% | 0.525 | 0.373 | 0.000 | 0.347 | 43/60 = 72% | 60/60 = 100% | 0.0000 |
| ROME+stats | same_new | 6 | 0.0003 [0.0002, 0.0007] | 8/218 = 4% | 0.420 | 0.297 | 0.045 | 0.299 | 12/12 = 100% | 12/12 = 100% | 0.0000 |
| MEMIT | disjoint | 30 | 0.0000 [0.0000, 0.0000] | 1/1008 = 0% | 0.049 | 0.032 | 0.000 | 0.073 | 48/48 = 100% | 48/48 = 100% | 0.0000 |
| MEMIT | same_relation | 30 | 0.0000 [0.0000, 0.0002] | 6/1062 = 1% | 0.218 | 0.150 | 0.006 | 0.183 | 56/57 = 98% | 56/57 = 98% | 0.0000 |
| MEMIT | neighbour | 30 | 0.0001 [0.0000, 0.0003] | 7/1091 = 1% | 0.191 | 0.134 | 0.002 | 0.194 | 57/58 = 98% | 57/58 = 98% | 0.0000 |
| MEMIT | shared_object | 30 | 0.0001 [0.0000, 0.0008] | 51/1079 = 5% | 0.222 | 0.155 | -0.002 | 0.196 | 46/57 = 81% | 55/57 = 96% | 0.0000 |
| MEMIT | same_new | 6 | 0.0001 [0.0000, 0.0003] | 2/218 = 1% | 0.249 | 0.174 | 0.024 | 0.172 | 11/11 = 100% | 11/11 = 100% | 0.0000 |
| AlphaEdit | disjoint | 30 | 0.0000 [0.0000, 0.0000] | 1/1008 = 0% | 0.060 | 0.043 | 0.000 | 0.073 | 60/60 = 100% | 60/60 = 100% | 0.0000 |
| AlphaEdit | same_relation | 30 | 0.0000 [0.0000, 0.0004] | 9/1062 = 1% | 0.198 | 0.143 | 0.005 | 0.183 | 60/60 = 100% | 60/60 = 100% | 0.0000 |
| AlphaEdit | neighbour | 30 | 0.0000 [0.0000, 0.0003] | 7/1091 = 1% | 0.213 | 0.149 | 0.003 | 0.194 | 60/60 = 100% | 60/60 = 100% | 0.0000 |
| AlphaEdit | shared_object | 30 | 0.0001 [0.0000, 0.0025] | 19/1079 = 2% | 0.279 | 0.185 | -0.001 | 0.196 | 60/60 = 100% | 60/60 = 100% | 0.0000 |
| AlphaEdit | same_new | 6 | 0.0000 [0.0000, 0.0002] | 4/218 = 2% | 0.261 | 0.193 | 0.019 | 0.172 | 12/12 = 100% | 12/12 = 100% | 0.0000 |

Read gap relative to disjoint pairs (median / median):

| method | class | ratio |
|---|---|---|
| ROME+stats | same_relation | 112.3× |
| ROME+stats | neighbour | 114.2× |
| ROME+stats | shared_object | 411.8× |
| ROME+stats | same_new | 78.3× |
| MEMIT | same_relation | 74.5× |
| MEMIT | neighbour | 127.5× |
| MEMIT | shared_object | 174.2× |
| MEMIT | same_new | 181.1× |
| AlphaEdit | same_relation | 17.5× |
| AlphaEdit | neighbour | 17.8× |
| AlphaEdit | shared_object | 60.2× |
| AlphaEdit | same_new | 39.1× |

## Conflict predictors (all pairs; Spearman ρ with 95% bootstrap interval)

| method | key cosine vs rel. weight gap | key cosine vs read gap | update cosine vs read gap | rel. weight gap vs read gap |
|---|---|---|---|---|
| ROME+stats | 0.94 [0.90, 0.96] | 0.92 [0.88, 0.95] | 0.80 [0.72, 0.85] | 0.96 [0.93, 0.97] |
| MEMIT | 0.87 [0.79, 0.91] | 0.81 [0.72, 0.87] | 0.79 [0.71, 0.85] | 0.94 [0.90, 0.96] |
| AlphaEdit | 0.88 [0.80, 0.92] | 0.86 [0.79, 0.91] | 0.72 [0.60, 0.81] | 0.94 [0.90, 0.96] |

## Pairs with the largest read gap (per method, top 8)

**ROME+stats**

| pair | class | A | B | read gap | order-dependent | rel. weight gap | key cosine | first edit held (AB, BA) |
|---|---|---|---|---|---|---|---|---|
| p028 | shared_object | cap_belgium | cap_poland | 0.5176 | 15/32 | 0.905 | 0.673 | [False, False] |
| p023 | shared_object | google | microsoft | 0.2022 | 17/38 | 1.028 | 0.751 | [False, False] |
| p026 | shared_object | apple | microsoft | 0.1946 | 16/40 | 1.061 | 0.739 | [False, False] |
| p025 | shared_object | amazon | facebook | 0.1228 | 19/36 | 0.969 | 0.645 | [False, False] |
| p077 | same_relation | com_ebay | facebook | 0.1144 | 12/36 | 0.921 | 0.633 | [False, False] |
| p022 | shared_object | com_linkedin | com_yahoo | 0.0841 | 7/35 | 0.849 | 0.554 | [False, True] |
| p060 | neighbour | com_netflix | com_walmart | 0.0827 | 2/36 | 0.815 | 0.609 | [True, True] |
| p071 | same_relation | cap_denmark | cap_poland | 0.0641 | 8/32 | 0.831 | 0.653 | [False, True] |

**MEMIT**

| pair | class | A | B | read gap | order-dependent | rel. weight gap | key cosine | first edit held (AB, BA) |
|---|---|---|---|---|---|---|---|---|
| p077 | same_relation | com_ebay | facebook | 0.0049 | 0/36 | 0.668 | 0.603 | [True, True] |
| p026 | shared_object | apple | microsoft | 0.0041 | 8/40 | 0.831 | 0.697 | [False, False] |
| p023 | shared_object | google | microsoft | 0.0037 | 4/38 | 0.729 | 0.732 | [False, True] |
| p025 | shared_object | amazon | facebook | 0.0034 | 5/36 | 0.726 | 0.596 | [False, False] |
| p093 | same_relation | com_netflix | facebook | 0.0029 | 1/34 | 0.606 | 0.590 | [False, True] |
| p015 | shared_object | com_ebay | com_snapchat | 0.0026 | 3/36 | 0.660 | 0.528 | [True] |
| p017 | shared_object | com_spacex | com_whatsapp | 0.0025 | 2/35 | 0.495 | 0.468 | [False, True] |
| p022 | shared_object | com_linkedin | com_yahoo | 0.0013 | 0/35 | 0.596 | 0.529 | [True, True] |

**AlphaEdit**

| pair | class | A | B | read gap | order-dependent | rel. weight gap | key cosine | first edit held (AB, BA) |
|---|---|---|---|---|---|---|---|---|
| p025 | shared_object | amazon | facebook | 0.0180 | 4/36 | 1.067 | 0.596 | [True, True] |
| p062 | neighbour | com_walmart | com_yahoo | 0.0062 | 1/35 | 0.799 | 0.507 | [True, True] |
| p015 | shared_object | com_ebay | com_snapchat | 0.0060 | 2/36 | 0.962 | 0.528 | [True, True] |
| p022 | shared_object | com_linkedin | com_yahoo | 0.0052 | 2/35 | 0.909 | 0.529 | [True, True] |
| p071 | same_relation | cap_denmark | cap_poland | 0.0045 | 0/32 | 0.846 | 0.633 | [True, True] |
| p024 | shared_object | cur_china | cur_thailand | 0.0043 | 0/30 | 0.953 | 0.607 | [True, True] |
| p033 | shared_object | com_alibaba | com_walmart | 0.0042 | 0/38 | 0.783 | 0.538 | [True, True] |
| p049 | neighbour | amazon | microsoft | 0.0033 | 2/38 | 0.927 | 0.619 | [True, True] |

