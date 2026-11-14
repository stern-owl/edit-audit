# 2026-10-31 · 06 · Phase 2: v3 fact set, relation contract, model-agnostic screening

**Plan items:** 2.2 (fact set), 2.3 (relation cardinality / consistency contract), 2.4 (GPT-J screening, projection)

## Why CounterFact alone does not work for this audit
The audit's reverse paths ask for the subject given the object ("Mary Shelley is best known for writing the novel").
Screening admits a fact only if the unedited model returns the subject within the top 3 on a reverse path that names
the old object. That condition holds only when the object points back to a recognisable subject. CounterFact
(`counterfact.json`, 21,919 records, 34 relations, md5 `61a58af5b69d612183f3efb7b1edba19`, downloaded 2026-10-31 from
`https://rome.baulab.info/data/dsets/counterfact.json` to `C:\Desktop\edit-audit\data\counterfact\`) is dominated by
relations where it does not:
- P103 mother tongue, P27 citizenship, P413 position, P1412 languages spoken: the object has thousands of subjects.
- P37 official language (891): mostly Finnish towns (Virrat, Alavus): "Finnish is the official language of" → Finland.
- P176 manufacturer (911): 735 subjects contain the object's name ("Honda NSX" → Honda); P178 developer: 220 of 579.
  For the rest, each company has at most one canonical product, so at most one fact per object can pass.
- P449 original network, P159 headquarters, P138 named after, P127 owned by: same problem.
- **P36 capital (139)** is 1:1 in both directions and is used.

This is itself a finding for the paper: the access-path catalogue is relation-dependent; a reverse read is a valid
access path only where the inverse relation is (near) functional or the subject is the object's canonical exemplar.

## Relations in v3 (`experiments/retrieval_poc/relation_templates_v3.json`)
| Relation | Forward | Inverse | Source |
|---|---|---|---|
| novel_author | functional | non-functional | draft (8) + own (46) |
| company_founder | multi-valued (co-founders; edit replaces the named founder) | non-functional | draft (5) + own (28) |
| invention_inventor | multi-valued (contested priority) | non-functional | draft (5) + own (21) |
| country_capital | functional | **functional (1:1)** | CounterFact P36 (111 after filters, 33 duplicate-capital groups) |
| painting_painter | functional | non-functional | own (32) |
| character_creator | functional | non-functional | own (29) |
| country_currency | functional | **functional** (only single-country currencies) | own (31) |

Templates of novel_author and invention_inventor are identical to v1, company_founder to v2; validity rules identical
to v1/v2. No edit prompt starts with the subject (lesson of jobs 3462/3467).

## Consistency contract (plan 2.3), frozen in the templates file before scoring
- Edits are UPDATEs: (s, r, o) is replaced by (s, r, o*).
- Q1: every valid forward path must return o* at rank 1; o at rank 1 is a stale read.
- Q2 reverse-from-old: s at rank 1 is a stale read for **every** relation (the tuple was deleted); another subject of o at
  rank 1 is legitimate. So cardinality does not excuse the draft's main finding.
- Q3 reverse-from-new: if the inverse is functional (capital, currency), s must reach rank 1, else violation; and the edit
  request itself violates the constraint (o* would have two subjects), reported as an integrity-constraint conflict.
  If the inverse is non-functional (authors, founders, painters, creators, inventors), s need not reach rank 1, but its
  log-probability must not fall (the draft found it falls on 23/24 such paths).
- Controls: neighbours keep their correct answer at rank 1; the rise of o* is reported as drift.
This addresses `next-steps.txt` Exp 5 and gives the labels needed later for false-positive analysis (Exp 7).

## Fact construction (`build_candidates_v3.py` v1.0, deterministic)
- **Draft facts (18):** copied verbatim from `candidate_facts_v2.csv`.
- **Own facts (187 written, 187 kept):** `facts_v3/own_facts.csv`, hand-written true (relation, subject, object) with notes
  on co-founders, contested priority, etc. New object by seeded cyclic shift within each relation (seed `v3-2026-10-31`):
  each new object is the true object of another fact of the same relation; the "new object's own fact" control always
  exists; no two edits swap objects. **These facts still need a human check** (see open items).
- **CounterFact P36:** subject, true capital and counterfactual capital as published. Dropped 28 whose subject contains the
  old or new object's name ("Mumbai City district" → Mumbai). Duplicate capitals: the first-by-case_id rule would have
  kept Nazi Germany (Berlin), Empire of Japan (Tokyo), Qing dynasty (Beijing), "Seine" for Paris under a shortest-name
  rule, so instead all are kept with `dup_group` and screening keeps one included fact per group (highest reverse-old
  subject log-probability on the unedited model; ties: lowest case_id). Rule added to the templates file before scoring.
- **Result:** `facts_v3/candidate_facts_v3.csv` = **316 candidates**, md5 `08036d94b3ef86ded6581cee2fd5c4f9`;
  11 without a new-object control (CounterFact capitals that are nobody's true capital in P36); manifest with all
  inputs' md5s and every dropped row in `candidate_facts_v3.csv.manifest.json`.

## Screening v4 (`screen_facts_v4.py` v1.0)
Same routes, rules and output format as `screen_facts.py` (unchanged), plus: any model (AutoModel/AutoTokenizer,
scorer v4, no EasyEdit); **two** same-relation neighbour controls per fact chosen by a hash of the two fact ids (the v1
rule "first eligible in file order" would make a few facts everybody's neighbour at this scale); dup-group resolution.
Offline test `tests/test_screen_v4.py`: probe structure for all 316 candidates (4 forward + 4 reverse, edit prompt never
starts with the subject, neighbours distinct, no shared answers, stable choice), tiny-model screen end to end, dup-group
rule on constructed cases (winner by log-prob, tie by case_id, invalid routes ignored, non-included facts ignored).

## Model-agnostic AlphaEdit projection (`compute_alphaedit_P_v2.py`, `cluster/csis/compute_P.sbatch`)
AutoModel + EasyEdit's own `get_project` (same CPU SVD numerics), writes `P_loc` (EasyEdit's fallback writes
`./null_space_project.pt` instead). GPT-J: 6 layers × 16384², cpu-long, 32 CPUs, 96 GB.

## Jobs
| Job | What | Depends on | Status |
|---|---|---|---|
| 16986 | AlphaEdit projection for GPT-J | | running (started 01:37, csis.cn2) |
| 16989 | tests (shipped + phase 2 incl. `test_screen_v4`) | | submitted |
| 16990 | screening v3 on GPT-2 XL | afterok 16989 | submitted |
| 16991 | screening v3 on GPT-J 6B | afterok 16989 | submitted |

## Open items
- **Human check of `own_facts.csv`** (187 facts) before results from them are reported. Screening only shows the model
  knows a fact; it does not show the fact is true.
- Modern model (D4) still to be decided.

## Results: screening v3 on GPT-2 XL (job 16990, 18:02, peak GPU 5.96 GiB)
Copies of `fact_summary.csv`, `screen_report.csv` in `research-log/results/E4_screen_v3_gpt2-xl_16990/`.
**78 / 316 included**; 7 dup groups resolved (capitals).

| Relation | n | edit prompt valid | ≥2 other fwd valid | ≥1 rev-old valid | ≥1 rev-new valid | ≥1 control valid | **included** |
|---|---|---|---|---|---|---|---|
| novel_author | 54 | 42 | 38 | 51 | 46 | 53 | **30** |
| company_founder | 33 | 23 | 20 | 27 | 33 | 33 | **18** |
| country_capital | 111 | 54 | 30 | 32 | 110 | 99 | **13** |
| country_currency | 31 | 20 | 14 | 14 | 30 | 29 | **9** |
| character_creator | 29 | 12 | 11 | 18 | 29 | 23 | **6** |
| invention_inventor | 26 | 7 | 3 | 18 | 26 | 20 | **2** |
| painting_painter | 32 | 1 | 1 | 20 | 16 | 2 | **0** |

Observations (descriptive; no decision taken yet):
1. **Paintings fail on the template, not on knowledge.** "The painting X was painted by" is continued with " the artist John
   Singer Sargent, in…" for most paintings, so the true painter's *first token* ranks low (Rembrandt 59, Vermeer 305)
   even where the model knows the work; reverse reads are often fine ("Edvard Munch is best known for painting" → The
   Scream, rank 1; 20/32 have a valid reverse-old path). The first-token-rank rule cannot see a correct answer that
   follows an article. Inventions likely suffer similarly ("invented by the…").
2. **Capitals:** 54/111 edit prompts valid, but only 32 reverse-old valid: many CounterFact P36 subjects are historical
   states or regions ("Tughlaq dynasty", "Uusimaa") whose capital the model may name but which it does not return from
   the capital.
3. **Neighbour choice decides borderline facts.** The draft's 12 vs v3 on the same templates: 11 of the draft's 12 are
   included again; `www` is lost (its hash-chosen neighbours, cotton gin/Whitney rank 300 and steam engine/Watt rank 16,
   are unknown to GPT-2 XL; the draft's neighbour was the telephone) and `telephone` is gained (its v3 neighbour,
   telegraph/Morse, is valid; the draft's was not). A fact can thus be excluded because its *neighbour* is unknown.

## Results: screening v3 on GPT-J 6B (job 16991, 22:18, peak GPU 22.6 GiB)
Copies in `research-log/results/E4_screen_v3_gpt-j-6B_16991/`. **128 / 316 included**; 8 dup groups resolved.

| Relation | n | edit prompt valid | ≥2 other fwd valid | ≥1 rev-old valid | ≥1 rev-new valid | ≥1 control valid | **included** (GPT-2 XL) |
|---|---|---|---|---|---|---|---|
| novel_author | 54 | 50 | 51 | 53 | 49 | 54 | **44** (30) |
| company_founder | 33 | 29 | 28 | 31 | 33 | 33 | **27** (18) |
| character_creator | 29 | 23 | 22 | 26 | 29 | 29 | **20** (6) |
| country_capital | 111 | 62 | 74 | 35 | 110 | 100 | **17** (13) |
| invention_inventor | 26 | 16 | 16 | 25 | 26 | 26 | **14** (2) |
| painting_painter | 32 | 13 | 13 | 22 | 24 | 28 | **5** (0) |
| country_currency | 31 | 11 | 7 | 21 | 29 | 21 | **1** (9) |

- The larger model admits far more facts in most relations; 16 of the draft's 18 facts are included (all five inventions,
  incl. `www` and `telephone`), so GPT-2 XL's low yield is partly model size.
- **Currency is the exception (1 vs 9):** GPT-J's reverse reads are strong ("The rupiah is the currency of" → Indonesia,
  rank 1, for 21/31), but the forward template fails (11/31 edit prompts valid). Likely cause: GPT-J completes "The
  currency of Japan is the" with an adjective (" Japanese yen"), so the bare currency's first token ranks low: the same
  first-token template artefact as paintings on GPT-2 XL. Not revised (decision D5); a stated limitation of v3.

## Proposed revision (NOT applied: user decision D5, 'no reruns')
Both changes use pre-edit reads only, like the draft's v2 template revision (written after screening, before any edit):
- **R1 neighbours from known facts:** two-pass screening; neighbours are hash-chosen only among facts whose edit prompt
  is valid on this model. Removes observation 3.
- **R2 article-tolerant templates for painting and invention:** e.g. "The painting {subject} was painted by the artist",
  "The {subject} was invented by the inventor"? (to be worded so the next token is the name), written down with a
  prediction before re-screening. Removes observation 1.
- Alternative: keep v3 as frozen and accept fewer relations on GPT-2 XL; check GPT-J first (larger model, job 16991).
