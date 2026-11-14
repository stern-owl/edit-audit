# Audit report (analyze_audit v1.0 (2026-10-31))

Rates are over valid paths; brackets are 95% bootstrap intervals over facts. rev_new_violation applies the relation contract of the templates file.

## Sequential / batch edits

### ROME (sequential, model gpt2-xl, 78 facts, full re-reads at steps [1, 78])

| step k | edited facts | edit_ok (edited) | rev_old_stale (edited) | retention (unedited) | ctl_correct1 (all) | ctl JS median (all) |
|---|---|---|---|---|---|---|
| 1 | 1 | 1/1 = 100% [100%, 100%] | 0/1 = 0% [0%, 0%] | 68/77 = 88% [81%, 95%] | 142/164 = 87% [80%, 92%] | 0.0044 |
| 78 | 78 | 14/78 = 18% [9%, 27%] | 0/148 = 0% [0%, 0%] | – | 0/164 = 0% [0%, 0%] | 0.8806 |

Persistence of the edited question: 78/78 edits took at their own step; of those, 14 still hold at step 78 and 64 were lost.

### MEMIT (sequential, model gpt2-xl, 78 facts, full re-reads at steps [1, 78])

| step k | edited facts | edit_ok (edited) | rev_old_stale (edited) | retention (unedited) | ctl_correct1 (all) | ctl JS median (all) |
|---|---|---|---|---|---|---|
| 1 | 1 | 1/1 = 100% [100%, 100%] | 0/1 = 0% [0%, 0%] | 77/77 = 100% [100%, 100%] | 164/164 = 100% [100%, 100%] | 0.0000 |
| 78 | 78 | 51/78 = 65% [54%, 76%] | 106/148 = 72% [63%, 79%] | – | 62/164 = 38% [31%, 45%] | 0.6249 |

Persistence of the edited question: 71/78 edits took at their own step; of those, 51 still hold at step 78 and 20 were lost.

### AlphaEdit (sequential, model gpt2-xl, 78 facts, full re-reads at steps [1, 78])

| step k | edited facts | edit_ok (edited) | rev_old_stale (edited) | retention (unedited) | ctl_correct1 (all) | ctl JS median (all) |
|---|---|---|---|---|---|---|
| 1 | 1 | 1/1 = 100% [100%, 100%] | 0/1 = 0% [0%, 0%] | 77/77 = 100% [100%, 100%] | 164/164 = 100% [100%, 100%] | 0.0000 |
| 78 | 78 | 78/78 = 100% [100%, 100%] | 107/148 = 72% [64%, 80%] | – | 48/164 = 29% [22%, 37%] | 0.9497 |

Persistence of the edited question: 78/78 edits took at their own step; of those, 78 still hold at step 78 and 0 were lost.

