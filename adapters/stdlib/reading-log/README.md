<!-- willow-addon
section: Keeping track
line: A child's reading log: books, pages and minutes, week by week.
source: new
added: 2026-10-29
writes: nothing
network: none
tags: no-install, offline, read-only, tracking
-->
# reading-log

A child's reading log: books, pages and minutes, week by week, from the lines
you wrote.

```
python adapters/stdlib/reading-log/reading_log.py --box DIR

2026-W10  3 days  100 pages  80 min  Charlotte's Web; The BFG
2026-W11  1 day  135 pages  90 min  The BFG
Charlotte's Web  60 pages, 45 min  (2026-03-02 to 2026-03-04)
The BFG  175 pages, 120 min  (2026-03-05 to 2026-03-13)
2 books, 4 days read, 235 pages, 170 min
```

**What counts.** A line, on a day, that says read, reads or reading and a
length: pages ("30 pages", "12pp") or time ("20 minutes", "1h", "1h30", "2
hours"). A line with both counts both; the times on a line add. The book is the
title in quotes, "like this" or _like this_ or *like this*, else the
capitalised words after read / reading ("read Charlotte's Web, 20 pages"); a
line that names none is added to its week without a book. A line's day is the
latest date it says (the kernel's `newest`), else the nearest date written above
it in its file, else the date its file is named for; a line no day reaches is
not counted.

**A week** is an ISO week, oldest first; "days" is the number of different days
read that week. Books are in the order they were first read. Nothing is graded,
and a missing week is simply not listed: the log shows what was written down.

It only reads. Exit codes, the kernel's: 0 reading found; 42 none; 2 refused.

**Uses:** the kernel's `chunks`, `newest` and `config`, and
[habits](../habits/)' `file_lines`.

**Never:** changes your files; writes anything, even the record.
