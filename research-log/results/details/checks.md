# Verification checks and update norms per run

| run | facts | edit steps | worst check A (repeat read) | smallest check B (weight change) | worst check C (restore) | update norm per step: min / median / max | final cumulative norm |
|---|---|---|---|---|---|---|---|
| gpt2-xl/AlphaEdit/independent/E4 | 78 | 78 | 0 | 0.0107 | 0 | 3.03 / 10.5 / 19.4 | 6.75 |
| gpt2-xl/MEMIT/independent/E4 | 78 | 78 | 0 | 0.00844 | 0 | 1.87 / 5.65 / 7.58 | 4.21 |
| gpt2-xl/ROME/independent/E4 | 78 | 78 | 0 | 0.0111 | 0 | 1.64 / 5.52 / 6.24 | 5.2 |
| gpt-j-6B/MEMIT/independent/E5 | 128 | 128 | 0 | 0.00747 | 0 | 3.02 / 4.75 / 6.15 | 4.99 |
| gpt-j-6B/ROME/independent/E5 | 128 | 128 | 0 | 0.0162 | 0 | 3.57 / 4.01 / 4.91 | 4.22 |
| gpt-j-6B/AlphaEdit/independent/E5 | 128 | 128 | 0 | 0.00529 | 0 | 3.38 / 5.4 / 8.33 | 5.57 |
| gpt2-xl/AlphaEdit/sequential/E7 | 78 | 78 | 0 | 0.0101 | 0 | 2.86 / 9.76 / 21.8 | 106 |
| gpt2-xl/MEMIT/sequential/E7 | 78 | 78 | 0 | 0.00608 | 0 | 1.68 / 5.01 / 8.1 | 48.2 |
| gpt2-xl/ROME/sequential/E7 | 78 | 78 | 0 | 0.0217 | 0 | 2.39 / 9.17 / 18.9 | 96.2 |
| gpt2-xl/AlphaEdit/sequential/E7v2 | 78 | 60 | 0 | 0.0101 | 0 | 3.25 / 10 / 21.3 | 91.3 |
| gpt2-xl/MEMIT/sequential/E7v2 | 78 | 60 | 0 | 0.00608 | 0 | 1.83 / 5.07 / 7.9 | 42.1 |
| gpt2-xl/ROME/sequential/E7v2 | 78 | 60 | 0 | 0.0217 | 0 | 2.39 / 8.81 / 18.9 | 82.2 |
