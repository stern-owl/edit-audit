# Sequential runs: order, held-out facts, update norms, damaging edits

## gpt2-xl/AlphaEdit/sequential/E7

- order (first 15 of 78): nov_the_grapes_of_wrath, chr_snoopy, cap_austria_hungary, com_netflix, chr_superman, cur_nigeria, cur_russia, cap_philippines, telephone, nov_uncle_tom_s_cabin, pride_prejudice, cap_germany, com_alibaba, com_twitter, cap_chile
- held out (never edited): none
- checkpoints with a full re-read: [1] (+ last step)

| step | edited fact | update norm | cumulative norm |
|---|---|---|---|
| 1 | nov_the_grapes_of_wrath | 7.79 | 7.79 |
| 2 | chr_snoopy | 9.06 | 11.9 |
| 3 | cap_austria_hungary | 10.4 | 15.9 |
| 4 | com_netflix | 11.1 | 19.4 |
| 5 | chr_superman | 12.9 | 23.3 |
| 10 | nov_uncle_tom_s_cabin | 8.51 | 40.4 |
| 20 | com_ikea | 8.81 | 53.7 |
| 30 | cur_israel | 15.3 | 66.1 |
| 40 | com_yahoo | 14.5 | 75 |
| 50 | apple | 12.9 | 85 |
| 60 | amazon | 12.9 | 91.3 |
| 70 | microsoft | 19.1 | 99.3 |
| 78 | chr_harry_potter | 12.8 | 106 |

- after the first edit (nov_the_grapes_of_wrath): 0/77 untouched facts no longer give their correct answer at rank 1 on the edited question

## gpt2-xl/MEMIT/sequential/E7

- order (first 15 of 78): nov_the_grapes_of_wrath, chr_snoopy, cap_austria_hungary, com_netflix, chr_superman, cur_nigeria, cur_russia, cap_philippines, telephone, nov_uncle_tom_s_cabin, pride_prejudice, cap_germany, com_alibaba, com_twitter, cap_chile
- held out (never edited): none
- checkpoints with a full re-read: [1] (+ last step)

| step | edited fact | update norm | cumulative norm |
|---|---|---|---|
| 1 | nov_the_grapes_of_wrath | 4.83 | 4.83 |
| 2 | chr_snoopy | 6.08 | 7.77 |
| 3 | cap_austria_hungary | 4.94 | 9.22 |
| 4 | com_netflix | 6.15 | 11.1 |
| 5 | chr_superman | 7.42 | 13.4 |
| 10 | nov_uncle_tom_s_cabin | 4.93 | 19.1 |
| 20 | com_ikea | 5.29 | 25.9 |
| 30 | cur_israel | 6.02 | 30.9 |
| 40 | com_yahoo | 7.9 | 34.7 |
| 50 | apple | 6.02 | 39 |
| 60 | amazon | 5.77 | 42.1 |
| 70 | microsoft | 8.1 | 45.5 |
| 78 | chr_harry_potter | 6.5 | 48.2 |

- after the first edit (nov_the_grapes_of_wrath): 0/77 untouched facts no longer give their correct answer at rank 1 on the edited question

## gpt2-xl/ROME/sequential/E7

- order (first 15 of 78): nov_the_grapes_of_wrath, chr_snoopy, cap_austria_hungary, com_netflix, chr_superman, cur_nigeria, cur_russia, cap_philippines, telephone, nov_uncle_tom_s_cabin, pride_prejudice, cap_germany, com_alibaba, com_twitter, cap_chile
- held out (never edited): none
- checkpoints with a full re-read: [1] (+ last step)

| step | edited fact | update norm | cumulative norm |
|---|---|---|---|
| 1 | nov_the_grapes_of_wrath | 5.5 | 5.5 |
| 2 | chr_snoopy | 7.13 | 9.07 |
| 3 | cap_austria_hungary | 7.96 | 12.2 |
| 4 | com_netflix | 8.4 | 14.9 |
| 5 | chr_superman | 13 | 19.8 |
| 10 | nov_uncle_tom_s_cabin | 5.53 | 35.1 |
| 20 | com_ikea | 4.75 | 41.4 |
| 30 | cur_israel | 13 | 49.4 |
| 40 | com_yahoo | 13.3 | 60.2 |
| 50 | apple | 13 | 72.6 |
| 60 | amazon | 13.9 | 82.2 |
| 70 | microsoft | 13.5 | 90.5 |
| 78 | chr_harry_potter | 13.2 | 96.2 |

- after the first edit (nov_the_grapes_of_wrath): 9/77 untouched facts no longer give their correct answer at rank 1 on the edited question: nov_uncle_tom_s_cabin, nov_slaughterhouse_five, nov_wuthering_heights, nov_the_catcher_in_the_rye, nov_treasure_island, nov_lord_of_the_flies, nov_one_hundred_years_of_solitude, nov_madame_bovary, nov_jane_eyre

## gpt2-xl/AlphaEdit/sequential/E7v2

- order (first 15 of 78): nov_the_grapes_of_wrath, chr_snoopy, cap_austria_hungary, com_netflix, chr_superman, cur_nigeria, cur_russia, cap_philippines, telephone, nov_uncle_tom_s_cabin, pride_prejudice, cap_germany, com_alibaba, com_twitter, cap_chile
- held out (never edited): nov_one_hundred_years_of_solitude, nov_the_time_machine, cur_malaysia, nov_dune, moby_dick, cap_belgium, nov_madame_bovary, cap_poland, com_snapchat, microsoft, nov_lolita, nov_jane_eyre, nov_on_the_road, chr_conan_the_barbarian, com_xiaomi, cap_hawaii, nov_ulysses, chr_harry_potter
- checkpoints with a full re-read: [1, 2, 5, 10, 20, 30, 40, 50, 60] (+ last step)

| step | edited fact | update norm | cumulative norm |
|---|---|---|---|
| 1 | nov_the_grapes_of_wrath | 7.79 | 7.79 |
| 2 | chr_snoopy | 9.06 | 11.9 |
| 3 | cap_austria_hungary | 10.4 | 15.9 |
| 4 | com_netflix | 11.1 | 19.4 |
| 5 | chr_superman | 12.9 | 23.3 |
| 10 | nov_uncle_tom_s_cabin | 8.51 | 40.4 |
| 20 | com_ikea | 8.81 | 53.7 |
| 30 | cur_israel | 15.3 | 66.1 |
| 40 | com_yahoo | 14.5 | 75 |
| 50 | apple | 12.9 | 85 |
| 60 | amazon | 12.9 | 91.3 |

- after the first edit (nov_the_grapes_of_wrath): 0/77 untouched facts no longer give their correct answer at rank 1 on the edited question

## gpt2-xl/MEMIT/sequential/E7v2

- order (first 15 of 78): nov_the_grapes_of_wrath, chr_snoopy, cap_austria_hungary, com_netflix, chr_superman, cur_nigeria, cur_russia, cap_philippines, telephone, nov_uncle_tom_s_cabin, pride_prejudice, cap_germany, com_alibaba, com_twitter, cap_chile
- held out (never edited): nov_one_hundred_years_of_solitude, nov_the_time_machine, cur_malaysia, nov_dune, moby_dick, cap_belgium, nov_madame_bovary, cap_poland, com_snapchat, microsoft, nov_lolita, nov_jane_eyre, nov_on_the_road, chr_conan_the_barbarian, com_xiaomi, cap_hawaii, nov_ulysses, chr_harry_potter
- checkpoints with a full re-read: [1, 2, 5, 10, 20, 30, 40, 50, 60] (+ last step)

| step | edited fact | update norm | cumulative norm |
|---|---|---|---|
| 1 | nov_the_grapes_of_wrath | 4.83 | 4.83 |
| 2 | chr_snoopy | 6.08 | 7.77 |
| 3 | cap_austria_hungary | 4.94 | 9.22 |
| 4 | com_netflix | 6.15 | 11.1 |
| 5 | chr_superman | 7.42 | 13.4 |
| 10 | nov_uncle_tom_s_cabin | 4.93 | 19.1 |
| 20 | com_ikea | 5.29 | 25.9 |
| 30 | cur_israel | 6.02 | 30.9 |
| 40 | com_yahoo | 7.9 | 34.7 |
| 50 | apple | 6.02 | 39 |
| 60 | amazon | 5.77 | 42.1 |

- after the first edit (nov_the_grapes_of_wrath): 0/77 untouched facts no longer give their correct answer at rank 1 on the edited question

## gpt2-xl/ROME/sequential/E7v2

- order (first 15 of 78): nov_the_grapes_of_wrath, chr_snoopy, cap_austria_hungary, com_netflix, chr_superman, cur_nigeria, cur_russia, cap_philippines, telephone, nov_uncle_tom_s_cabin, pride_prejudice, cap_germany, com_alibaba, com_twitter, cap_chile
- held out (never edited): nov_one_hundred_years_of_solitude, nov_the_time_machine, cur_malaysia, nov_dune, moby_dick, cap_belgium, nov_madame_bovary, cap_poland, com_snapchat, microsoft, nov_lolita, nov_jane_eyre, nov_on_the_road, chr_conan_the_barbarian, com_xiaomi, cap_hawaii, nov_ulysses, chr_harry_potter
- checkpoints with a full re-read: [1, 2, 5, 10, 20, 30, 40, 50, 60] (+ last step)

| step | edited fact | update norm | cumulative norm |
|---|---|---|---|
| 1 | nov_the_grapes_of_wrath | 5.5 | 5.5 |
| 2 | chr_snoopy | 7.13 | 9.07 |
| 3 | cap_austria_hungary | 7.96 | 12.2 |
| 4 | com_netflix | 8.4 | 14.9 |
| 5 | chr_superman | 13 | 19.8 |
| 10 | nov_uncle_tom_s_cabin | 5.53 | 35.1 |
| 20 | com_ikea | 4.75 | 41.4 |
| 30 | cur_israel | 13 | 49.4 |
| 40 | com_yahoo | 13.3 | 60.2 |
| 50 | apple | 13 | 72.6 |
| 60 | amazon | 13.9 | 82.2 |

- after the first edit (nov_the_grapes_of_wrath): 9/77 untouched facts no longer give their correct answer at rank 1 on the edited question: nov_uncle_tom_s_cabin, nov_slaughterhouse_five, nov_wuthering_heights, nov_the_catcher_in_the_rye, nov_treasure_island, nov_lord_of_the_flies, nov_one_hundred_years_of_solitude, nov_madame_bovary, nov_jane_eyre

