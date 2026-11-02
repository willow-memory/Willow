<!-- willow-addon
section: Keeping track
line: Hours worked or volunteered, per client or group, from your notes.
source: new
added: 2026-10-29
writes: nothing
network: none
uses: habits
-->
# hours

Hours worked or volunteered, added up for each client or group your notes
name.

```
python adapters/stdlib/hours/hours.py --box DIR [--since DATE] [--until DATE]

    12.5 h  acme  (2 entries, 2026-03-01 to 2026-03-20)
       6 h  the food bank  (1 entry, 2026-03-07 to 2026-03-07)
     1.5 h  (no one named)  (1 entry, 2026-03-12 to 2026-03-12)
3 groups, 20 h in 4 entries
```

**What counts.** A line that says a work word (worked, volunteered, shift,
billed, billable, logged, consulting, meeting, session) and a length of time:
2.5 hours, 3h, 1h30, 45 min, 2 hrs 15 min. The times on one line add; a line
counts once. A time with no work word ("slept 8 hours") is not counted. A
line's day is the latest date it says, read as the kernel reads one (its
`newest`), else the nearest date written above it in its file, else the date
its file is named for; a line no day reaches is not counted.

**Whom it is for** is the words after "for", "at", "with" or "@", up to a
comma, a digit or a word like "on" or "from": "worked 3 hours for Acme on the
site" is acme. A line that names no one is added up under "(no one named)",
so nothing is left out. It never guesses a client from the file's name.

`--since` and `--until` (YYYY-MM-DD) keep to those days, both ends included.
Biggest total first. The same folder gives the same bytes; no clock is
consulted.

It only reads. Exit codes, the kernel's: 0 hours found; 42 none; 2 refused.

**Uses:** the kernel's `chunks`, `newest` and `config`, and
[habits](../habits/)' `file_lines` to put a file's passages back together.

**Never:** changes your files; writes anything, even the record.
