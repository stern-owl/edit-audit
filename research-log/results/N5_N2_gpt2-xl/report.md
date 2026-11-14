# N5 compensation and N2 cascade (analyze_programs v1.0 (2026-11-05))

Definitions: research-log entry 11.

## Checks

| method | program steps | min check B | max check C |
|---|---|---|---|
| ROME+stats | 420 | 0.0152 | 0 |
| MEMIT | 429 | 0.00434 | 0 |
| AlphaEdit | 429 | 0.0103 | 0 |

## N5 compensating edits

| method | facts | edit ok | compensated (of edit ok) | over-compensated (of compensated) | median Δlog P(o) | verdicts restored | median JS A after edit → after undo | neighbour JS after edit → after undo | median neighbour residue ratio | sentinel JS after undo | median weight residue |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ROME+stats | 72 | 72/72 = 100% | 72/72 = 100% | 70/72 = 97% | 0.67 | 1216/1242 = 98% | 0.0169 → 0.0107 | 0.0178 → 0.0245 | 1.13 | 0.0001 | 1.311 |
| MEMIT | 72 | 60/72 = 83% | 60/60 = 100% | 57/60 = 95% | 0.61 | 1040/1046 = 99% | 0.0112 → 0.0049 | 0.0034 → 0.0052 | 0.95 | 0.0000 | 1.080 |
| AlphaEdit | 72 | 72/72 = 100% | 72/72 = 100% | 71/72 = 99% | 0.65 | 1225/1242 = 99% | 0.0169 → 0.0071 | 0.0043 → 0.0063 | 1.12 | 0.0001 | 1.625 |

Late compensation (5 unrelated edits between the edit and its compensation), compared with the reference state (the 5 edits alone):

| method | facts | compensated | median JS A's paths: late vs reference | same facts: immediate undo vs unedited | median JS X facts | median JS sentinels |
|---|---|---|---|---|---|---|
| ROME+stats | 20 | 20/20 = 100% | 0.0169 | 0.0081 | 0.0003 | 0.0003 |
| MEMIT | 20 | 19/20 = 95% | 0.0052 | 0.0052 | 0.0000 | 0.0000 |
| AlphaEdit | 20 | 20/20 = 100% | 0.0066 | 0.0078 | 0.0001 | 0.0001 |

## N2 cascading repair (swap)

| method | state | cases | A holds | S holds | both hold | s' still answers o* (FD violated) | o*→s | o*↛s' | o→s' | o↛s | fully consistent | median neighbour JS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ROME+stats | A alone | 9 | 9/9 = 100% | 0/9 = 0% | 0/9 = 0% | 9/9 = 100% | 0/18 = 0% | 13/18 = 72% | 0/18 = 0% | 5/18 = 28% | 0/9 = 0% | 0.0317 |
| ROME+stats | A then S | 9 | 2/9 = 22% | 9/9 = 100% | 2/9 = 22% | 0/9 = 0% | 0/18 = 0% | 13/18 = 72% | 0/18 = 0% | 6/18 = 33% | 0/9 = 0% | 0.0478 |
| ROME+stats | S then A | 9 | 9/9 = 100% | 4/9 = 44% | 4/9 = 44% | 5/9 = 56% | 0/18 = 0% | 13/18 = 72% | 0/18 = 0% | 6/18 = 33% | 0/9 = 0% | 0.0719 |
| MEMIT | A alone | 9 | 4/9 = 44% | 0/9 = 0% | 0/9 = 0% | 9/9 = 100% | 0/18 = 0% | 13/18 = 72% | 0/18 = 0% | 4/18 = 22% | 0/9 = 0% | 0.0062 |
| MEMIT | A then S | 9 | 1/9 = 11% | 3/9 = 33% | 1/9 = 11% | 6/9 = 67% | 0/18 = 0% | 13/18 = 72% | 0/18 = 0% | 4/18 = 22% | 0/9 = 0% | 0.0101 |
| MEMIT | S then A | 9 | 1/9 = 11% | 4/9 = 44% | 1/9 = 11% | 5/9 = 56% | 0/18 = 0% | 13/18 = 72% | 0/18 = 0% | 4/18 = 22% | 0/9 = 0% | 0.0163 |
| MEMIT | batch A+S | 9 | 1/9 = 11% | 4/9 = 44% | 1/9 = 11% | 5/9 = 56% | 0/18 = 0% | 13/18 = 72% | 0/18 = 0% | 4/18 = 22% | 0/9 = 0% | 0.0101 |
| AlphaEdit | A alone | 9 | 9/9 = 100% | 0/9 = 0% | 0/9 = 0% | 9/9 = 100% | 0/18 = 0% | 13/18 = 72% | 0/18 = 0% | 6/18 = 33% | 0/9 = 0% | 0.0232 |
| AlphaEdit | A then S | 9 | 9/9 = 100% | 9/9 = 100% | 9/9 = 100% | 0/9 = 0% | 0/18 = 0% | 13/18 = 72% | 0/18 = 0% | 6/18 = 33% | 0/9 = 0% | 0.0307 |
| AlphaEdit | S then A | 9 | 9/9 = 100% | 9/9 = 100% | 9/9 = 100% | 0/9 = 0% | 0/18 = 0% | 13/18 = 72% | 0/18 = 0% | 6/18 = 33% | 0/9 = 0% | 0.0568 |
| AlphaEdit | batch A+S | 9 | 9/9 = 100% | 9/9 = 100% | 9/9 = 100% | 0/9 = 0% | 0/18 = 0% | 13/18 = 72% | 0/18 = 0% | 5/18 = 28% | 0/9 = 0% | 0.0435 |

Per case (A / S = that edit holds; ! = s' still answers o*):

| method | case | A alone | A then S | S then A | batch |
|---|---|---|---|---|---|
| ROME+stats | cap_belgium | A-! | -S | A-! | n/a |
| ROME+stats | cap_chile | A-! | -S | AS | n/a |
| ROME+stats | cap_hawaii | A-! | AS | AS | n/a |
| ROME+stats | cap_poland | A-! | AS | AS | n/a |
| ROME+stats | cur_china | A-! | -S | A-! | n/a |
| ROME+stats | cur_israel | A-! | -S | A-! | n/a |
| ROME+stats | cur_japan | A-! | -S | A-! | n/a |
| ROME+stats | cur_nigeria | A-! | -S | AS | n/a |
| ROME+stats | cur_russia | A-! | -S | A-! | n/a |
| MEMIT | cap_belgium | --! | --! | --! | --! |
| MEMIT | cap_chile | --! | -S | -S | -S |
| MEMIT | cap_hawaii | --! | -S | -S | -S |
| MEMIT | cap_poland | A-! | AS | AS | AS |
| MEMIT | cur_china | A-! | --! | --! | --! |
| MEMIT | cur_israel | --! | --! | --! | --! |
| MEMIT | cur_japan | A-! | --! | -S | -S |
| MEMIT | cur_nigeria | --! | --! | --! | --! |
| MEMIT | cur_russia | A-! | --! | --! | --! |
| AlphaEdit | cap_belgium | A-! | AS | AS | AS |
| AlphaEdit | cap_chile | A-! | AS | AS | AS |
| AlphaEdit | cap_hawaii | A-! | AS | AS | AS |
| AlphaEdit | cap_poland | A-! | AS | AS | AS |
| AlphaEdit | cur_china | A-! | AS | AS | AS |
| AlphaEdit | cur_israel | A-! | AS | AS | AS |
| AlphaEdit | cur_japan | A-! | AS | AS | AS |
| AlphaEdit | cur_nigeria | A-! | AS | AS | AS |
| AlphaEdit | cur_russia | A-! | AS | AS | AS |
