<!-- willow-addon
section: Keeping track
line: Mood scores you write in a journal, over weeks and months.
source: new
added: 2026-10-29
writes: nothing
network: none
tags: no-install, offline, read-only, tracking
-->
# mood

The mood scores you write in a journal, gathered over weeks and months, on
this machine and nowhere else.

```
python adapters/stdlib/mood/mood.py --box DIR [--by week]

2026-02  avg 6.0  2 days  low 3 on 2026-02-09, high 9 on 2026-02-20
2026-03  avg 6.5  2 days  low 4 on 2026-03-02, high 9 on 2026-03-28  up 0.5
2 months, 4 days
```

**A score** is a line that says "mood" and a number straight after it: "mood:
7", "Mood 7/10", "mood - 4 out of 5". The number is out of 10 unless the line
gives another top (/5, out of 100); it is shown on a scale of 10, and a number
over its top is not read. A day with several scores counts as their average.
A line's day is the latest date it says (the kernel's `newest`), else the
nearest date written above it in its file, else the date its file is named
for; a line no day reaches is not counted.

Each month (or week, with `--by week`; ISO weeks) shows its average, how many
days were scored, the lowest and highest day, and how the average moved from
the period before. Nothing is diagnosed, flagged or told to anyone: these are
the numbers you wrote, added up. Oldest first.

It only reads. Exit codes, the kernel's: 0 scores found; 42 none; 2 refused.

**Uses:** the kernel's `chunks`, `newest` and `config`, and
[habits](../habits/)' `file_lines`.

**Never:** changes your files; writes anything, even the record; sends a
number anywhere.
