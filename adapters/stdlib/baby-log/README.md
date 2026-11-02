<!-- willow-addon
section: Keeping track
line: Feeds, sleeps and nappies from your notes, by day: when was the last one?
source: new
added: 2026-10-29
writes: nothing
network: none
-->
# baby-log

Feeds, sleeps and nappies from your notes, counted by day: when was the last
one?

```
python adapters/stdlib/baby-log/baby_log.py --box DIR [--days N]

last feed    2026-03-02 14:10
last sleep   2026-03-02 13:00
last nappy   2026-03-02 14:35
2026-03-02  feeds 2  sleeps 1  nappies 2
2026-03-01  feeds 2  sleeps 1  nappies 1
2 days shown
```

**What counts.** A line that says a feed (feed, fed, bottle, nursed,
breastfed), a sleep (sleep, slept, nap) or a nappy (nappy, diaper, poo, wee),
on a day, and is about a baby: the line or the path of its file says baby, bub,
newborn, infant, toddler, nappy or diaper (so feeding the bees, or a friend who
can't sleep, is not the baby's). The day is the line's latest date (the kernel's `newest`), else the nearest date
written above it in its file, else the date its file is named for. The first
time on the line ("07:30", "7.30pm", "13:00-14:30") is when; a line with no
time still counts for its day, and a last that has none says "(no time
written)". A line is the first of the three it names, so "fed, then nappy" is a
feed. Nothing is summed from amounts or lengths.

The newest N days with entries are shown (7 unless `--days`). This is your own
count, for you and whoever shares the night; it is not advice.

It only reads. Exit codes, the kernel's: 0 entries found; 42 none; 2 refused.

**Uses:** the kernel's `chunks`, `newest` and `config`, and
[habits](../habits/)' `file_lines`.

**Never:** changes your files; writes anything, even the record.
