<!-- willow-addon
section: Keeping track
line: Where a log you keep stops: the days a daily note, reading or diary skipped, said as gaps, not left out.
source: new
added: 2026-10-24
writes: nothing
network: none
tags: journal
-->
# gaps

Where a log you keep stops: the days your daily notes, reading log or diary
skipped, said as gaps rather than left out.

    python adapters/stdlib/gaps/gaps.py --box DIR [--now TS]

    diary.md  lines that start with a date  5 entries, 2026-01-05 to 2026-02-02, typical spacing 7 days
      no gap
    notes/  files named by a date  10 entries, 2026-03-01 to 2026-03-16, typical spacing 1 day
      GAP       2026-03-04 to 2026-03-11  6 days with no entry
      UNDATED   notes/index.md  no date in its name or at the start of a line, not counted
    reading.md  lines that start with a date  2 entries: too few for a rhythm (it needs 4)
    1 gap in 1 of 2 logs with a rhythm; 1 log too short for a rhythm.
    A gap is days with no entry written, not days when nothing happened.

**What a log is.** A folder of files named by a date (daily notes, each
named like 2026-03-04.md) is one log, and each date is an entry. A file not
named by a date is a log of its own lines when some of them start with a date,
after any heading marks or bullet: `## 2026-03-04`, `- 2026-03-04 walked`. A
date in the middle of a line ("saw Ana on 2026-02-09") isn't an entry. A file
named by a date counts only for its folder, never for the dates inside it.

**The rule.** Put a log's dates in order and take the spacing, in days,
between each one and the next. Sort those spacings; the middle one is the
log's typical spacing (with an even count, the smaller of the two middle
ones). A gap is a spacing more than three times the typical one: in a daily
log, four days or more from one entry to the next; in a weekly one, more
than three weeks. A gap's two dates are the entries on either side, and its
days with no entry are the days between them.

- **A gap is "no entry written", never "nothing happened".** Your files can
  say only what was written down.
- **Too few is said, not judged.** A log needs 4 dates for a rhythm; one
  with fewer is listed with its count.
- **Undated is said, not dropped.** A file in a log's folder with no date in
  its name or at the start of a line is listed as not counted.
- **No date is guessed.** Dates are read the way the kernel reads them (its
  `newest`): 2026-03-04, 20260304, and 28/10/2026 only when it can't be read
  the other way round; 11/03/2026 is never read. 2026-02-31 isn't a day, so
  it isn't an entry. An empty file has nothing the kernel reads, so it isn't
  one either.
- **No clock.** Without `--now`, nothing after a log's last entry is judged.
  With it, the days since the last entry count by the same rule, shown as
  `SINCE`.

Logs come in name order.

**Exit codes:** 0 found some gaps; 42 none, or no log has enough dates for a
rhythm (the last line says which); 2 refused.

**Uses:** the kernel's `chunks`, `newest` and `config`.

**Never:** writes anything, guesses a date, or reads a gap as nothing having
happened.
