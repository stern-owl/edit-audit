# Largest rises of the new value o* on same-relation neighbour reads (independent runs)

Each row: the edited fact, the neighbour route, the control fact (empty for runs before run_audit v1.2), the new value o*, its first-token rank on the neighbour's question before → after, and whether the neighbour's correct answer stayed rank 1. Sorted by rank after the edit.

## gpt2-xl/AlphaEdit/independent/E4

| edited fact | control route | control fact | o* | rank before → after | correct answer still rank 1 |
|---|---|---|---|---|---|
| amazon | same_relation |  | Mark Zuckerberg | 30 → 1 | False |
| cap_poland | same_relation_2 |  | Jerusalem | 201 → 2 | True |
| com_ebay | same_relation_2 |  | Evan Spiegel | 126 → 2 | False |
| com_whatsapp | same_relation |  | John D. Rockefeller | 17 → 2 | True |
| microsoft | same_relation |  | Steve Jobs | 8 → 2 | True |
| telephone | same_relation_2 |  | Thomas Edison | 3 → 2 | True |
| war_peace | same_relation_2 |  | Fyodor Dostoevsky | 4 → 3 | True |
| google | same_relation_2 |  | Bill Gates | 41 → 4 | True |
| com_snapchat | same_relation_2 |  | Eric Yuan | 33 → 4 | True |
| cur_venezuela | same_relation_2 |  | riel | 17 → 4 | True |
| nov_on_the_road | same_relation |  | Robert Louis Stevenson | 5 → 4 | True |
| apple | same_relation |  | Bill Gates | 41 → 6 | True |
| chr_harry_potter | same_relation_2 |  | P. G. Wodehouse | 9 → 6 | True |
| cur_malaysia | same_relation |  | dong | 9 → 6 | True |
| com_spacex | same_relation |  | Jan Koum | 164 → 8 | True |

New value in a neighbour's top 5: 11/114; at rank ≤ 2: 6/114; new value displaces the neighbour's correct answer (rank 1): 1/114.

## gpt2-xl/MEMIT/independent/E4

| edited fact | control route | control fact | o* | rank before → after | correct answer still rank 1 |
|---|---|---|---|---|---|
| amazon | same_relation |  | Mark Zuckerberg | 30 → 1 | False |
| telephone | same_relation_2 |  | Thomas Edison | 3 → 2 | True |
| nov_on_the_road | same_relation |  | Robert Louis Stevenson | 5 → 3 | True |
| war_peace | same_relation_2 |  | Fyodor Dostoevsky | 4 → 3 | True |
| microsoft | same_relation |  | Steve Jobs | 8 → 4 | True |
| chr_harry_potter | same_relation_2 |  | P. G. Wodehouse | 9 → 6 | True |
| com_whatsapp | same_relation |  | John D. Rockefeller | 17 → 7 | True |
| cur_venezuela | same_relation_2 |  | riel | 17 → 7 | True |
| nov_fahrenheit_451 | same_relation |  | Mark Twain | 10 → 7 | True |
| cur_malaysia | same_relation |  | dong | 9 → 7 | True |
| com_ebay | same_relation_2 |  | Evan Spiegel | 126 → 8 | False |
| chr_snoopy | same_relation |  | Thomas Harris | 21 → 9 | True |
| nov_fahrenheit_451 | same_relation_2 |  | Mark Twain | 16 → 10 | True |
| com_ikea | same_relation_2 |  | Jack Ma | 10 → 10 | True |
| nov_don_quixote | same_relation |  | J. D. Salinger | 11 → 11 | True |

New value in a neighbour's top 5: 5/114; at rank ≤ 2: 2/114; new value displaces the neighbour's correct answer (rank 1): 1/114.

## gpt2-xl/ROME/independent/E4

| edited fact | control route | control fact | o* | rank before → after | correct answer still rank 1 |
|---|---|---|---|---|---|
| nov_the_handmaid_s_tale | same_relation |  | Chinua Achebe | 1653 → 1 | False |
| nov_one_hundred_years_of_solitude | same_relation |  | Frank Herbert | 661 → 1 | False |
| com_ebay | same_relation_2 |  | Evan Spiegel | 126 → 1 | False |
| nov_uncle_tom_s_cabin | same_relation_2 |  | Daniel Defoe | 71 → 1 | False |
| nov_catch_22 | same_relation |  | Ernest Hemingway | 52 → 1 | False |
| nov_lolita | same_relation |  | Charles Dickens | 35 → 1 | False |
| amazon | same_relation |  | Mark Zuckerberg | 30 → 1 | False |
| cap_poland | same_relation_2 |  | Jerusalem | 201 → 2 | True |
| nov_atlas_shrugged | same_relation |  | Fyodor Dostoevsky | 160 → 2 | True |
| nov_wuthering_heights | same_relation |  | William Golding | 26 → 2 | True |
| com_whatsapp | same_relation |  | John D. Rockefeller | 17 → 2 | True |
| nov_fahrenheit_451 | same_relation_2 |  | Mark Twain | 16 → 2 | True |
| nov_fahrenheit_451 | same_relation |  | Mark Twain | 10 → 2 | True |
| microsoft | same_relation |  | Steve Jobs | 8 → 2 | True |
| nov_on_the_road | same_relation |  | Robert Louis Stevenson | 5 → 2 | True |

New value in a neighbour's top 5: 24/114; at rank ≤ 2: 17/114; new value displaces the neighbour's correct answer (rank 1): 7/114.

## gpt-j-6B/MEMIT/independent/E5

| edited fact | control route | control fact | o* | rank before → after | correct answer still rank 1 |
|---|---|---|---|---|---|
| com_instagram | same_relation_2 |  | Jack Dorsey | 36 → 1 | False |
| nov_the_scarlet_letter | same_relation_2 |  | George Eliot | 1 → 1 | True |
| microsoft | same_relation |  | Steve Jobs | 29 → 2 | True |
| telephone | same_relation_2 |  | Thomas Edison | 8 → 2 | True |
| com_twitter | same_relation |  | Travis Kalanick | 2111 → 3 | False |
| apple | same_relation_2 |  | Bill Gates | 53 → 3 | True |
| inv_ak_47 | same_relation |  | the Montgolfier brothers | 4 → 4 | True |
| inv_ak_47 | same_relation_2 |  | the Montgolfier brothers | 4 → 4 | True |
| nov_brave_new_world | same_relation_2 |  | H. G. Wells | 5 → 5 | True |
| amazon | same_relation |  | Mark Zuckerberg | 86 → 6 | True |
| nov_on_the_road | same_relation |  | Robert Louis Stevenson | 13 → 7 | True |
| inv_airplane | same_relation_2 |  | Nikola Tesla | 10 → 9 | True |
| chr_jack_reacher | same_relation |  | Ian Fleming | 74 → 10 | True |
| com_huawei | same_relation |  | Kevin Systrom | 27 → 10 | True |
| nov_dune | same_relation_2 |  | Miguel de Cervantes | 18 → 11 | True |

New value in a neighbour's top 5: 9/207; at rank ≤ 2: 4/207; new value displaces the neighbour's correct answer (rank 1): 1/207.

## gpt-j-6B/ROME/independent/E5

| edited fact | control route | control fact | o* | rank before → after | correct answer still rank 1 |
|---|---|---|---|---|---|
| cap_peru | same_relation |  | Winchester | 28323 → 1 | False |
| cap_south_korea | same_relation_2 |  | Constantinople | 15144 → 1 | False |
| com_uber | same_relation |  | Lei Jun | 9441 → 1 | False |
| com_spotify | same_relation |  | Jensen Huang | 7257 → 1 | False |
| nov_madame_bovary | same_relation |  | Vladimir Nabokov | 6574 → 1 | False |
| cap_ireland | same_relation_2 |  | Cairo | 6504 → 1 | False |
| com_yahoo | same_relation |  | Ma Huateng | 6252 → 1 | False |
| com_twitter | same_relation |  | Travis Kalanick | 2111 → 1 | False |
| com_netflix | same_relation |  | Drew Houston | 1688 → 1 | False |
| com_alibaba | same_relation |  | Sam Walton | 1615 → 1 | False |
| cap_belgium | same_relation |  | Warsaw | 1422 → 1 | False |
| cap_norway | same_relation |  | Rome | 1158 → 1 | False |
| cap_ireland | same_relation |  | Cairo | 1088 → 1 | False |
| chr_mickey_mouse | same_relation_2 |  | Roald Dahl | 958 → 1 | False |
| nov_jane_eyre | same_relation |  | Aldous Huxley | 893 → 1 | False |

New value in a neighbour's top 5: 97/207; at rank ≤ 2: 67/207; new value displaces the neighbour's correct answer (rank 1): 50/207.

## gpt-j-6B/AlphaEdit/independent/E5

| edited fact | control route | control fact | o* | rank before → after | correct answer still rank 1 |
|---|---|---|---|---|---|
| com_instagram | same_relation_2 |  | Jack Dorsey | 36 → 1 | False |
| nov_the_scarlet_letter | same_relation_2 |  | George Eliot | 1 → 1 | True |
| com_twitter | same_relation |  | Travis Kalanick | 2111 → 2 | False |
| apple | same_relation_2 |  | Bill Gates | 53 → 2 | True |
| microsoft | same_relation |  | Steve Jobs | 29 → 2 | True |
| telephone | same_relation_2 |  | Thomas Edison | 8 → 2 | True |
| inv_ak_47 | same_relation |  | the Montgolfier brothers | 4 → 4 | True |
| inv_ak_47 | same_relation_2 |  | the Montgolfier brothers | 4 → 4 | True |
| nov_brave_new_world | same_relation_2 |  | H. G. Wells | 5 → 5 | True |
| amazon | same_relation |  | Mark Zuckerberg | 86 → 6 | True |
| nov_on_the_road | same_relation |  | Robert Louis Stevenson | 13 → 8 | True |
| inv_airplane | same_relation_2 |  | Nikola Tesla | 10 → 9 | True |
| com_huawei | same_relation |  | Kevin Systrom | 27 → 10 | True |
| com_samsung | same_relation_2 |  | Marc Benioff | 293 → 11 | True |
| microsoft | same_relation_2 |  | Steve Jobs | 255 → 13 | True |

New value in a neighbour's top 5: 9/207; at rank ≤ 2: 6/207; new value displaces the neighbour's correct answer (rank 1): 1/207.

