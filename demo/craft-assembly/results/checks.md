# What willow's tools say of the report

Written by [report.py](../report.py) `write`, after [REPORT.md](../REPORT.md), the same bytes every run.

## The record, read by the kernel

`kernel.read` on [record.jsonl](record.jsonl): the chain holds, 16 rows.

- run 1: [run-1.json](run-1.json) hashes to `6acabe8abcfbc5be…`, named by 5 rows (1, 2, 3, 4, 5)
- run 2: [run-2.json](run-2.json) hashes to `dbba33f2ca620d7e…`, named by 5 rows (6, 7, 8, 9, 10)
- run 3: [run-3.json](run-3.json) hashes to `a287e07f312bbe26…`, named by 5 rows (11, 12, 13, 14, 15)

## Every reference in the folder, by xref

    python adapters/stdlib/xref/xref.py --from demo/craft-assembly

    71 references checked, 0 don't hold; 10 leading out of your folder, not checked.

## The counts, looked for in the README by claim-check

Each claim below is counted from the results by report.py, and looked for in [README.md](../README.md) alone, a box made of it in a scratch folder. `all parts` means a passage of the README holds every word of it; anything else is said as claim-check said it.

| Claim | claim-check | Where |
|---|---|---|
| all 21 sources rebuilt from the store | all parts | README.md:290 |
| 135 packages build in their own app; none builds in the composite | all parts | README.md:290 |
| 127 pass their tests in their own app; none in the composite | all parts | README.md:296 |
| all 24 sources rebuilt from the store | all parts | README.md:191 |
| all 134 packages build in it | all parts | README.md:191 |
| 125 of the 127 pass their tests | all parts | README.md:234 |
| all 127 pass their tests in it | all parts | README.md:197 |
| 19,743 pieces | all parts | README.md:211 |
| 22,961 files | all parts | README.md:236 |
| 1,662 of them in two or more sources | all parts | README.md:236 |
| 136 packages | all parts | README.md:211 |
| 42 crates | all parts | README.md:211 |
| moved 53 crates | all parts | README.md:161 |
| refused 11 moves | all parts | README.md:205 |

14 of 14 found whole.
