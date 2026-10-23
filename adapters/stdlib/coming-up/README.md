<!-- willow-addon
section: Keeping track
line: Dates written in your files in the next N days: appointments, renewals, deadlines.
source: box
added: 2026-10-23
writes: nothing
network: none
tags: no-install, offline, read-only, tracking
-->
# coming-up

Dates written in your files that fall in the next few days: appointments,
renewals, deadlines, a log's next visit, a calendar's events.

    python adapters/stdlib/coming-up/coming_up.py --box DIR [--days N] [--now TS]

    2026-10-28  calendar.ics:1968  DTSTART;VALUE=DATE:20261028  SUMMARY:Tune - Benedikt Ybarra
    2026-11-01  calendar.ics:1974  DTSTART;VALUE=DATE:20261101  SUMMARY:Dad - pharmacy refills

Soonest first, 14 days by default. A date is read the way the kernel reads one
for "newest first": 2026-10-28, 20261028, and 28/10/2026 only when it can't be
read the other way round. 11/03/2026 is never guessed, and a line with several
dates counts by its latest. A line that is little more than its date (a
calendar's start line) is shown with the next line that says something, even
across the kernel's cut between two passages.

**Exit codes:** 0 something is coming up; 42 nothing in the window; 2 refused.

**Uses:** the kernel's `chunks`, `newest`, `words`, `config` and `now`.

**Never:** writes anything.
