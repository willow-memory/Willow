<!-- willow-addon
section: Keeping track
line: Oakenscroll's Office calibration ledger: what you believed, how hard, and how it resolved, as dated passages.
source: new
added: 2026-11-01
writes: to
network: none
tags: no-install, offline, writes-output, tracking
-->
# oakenscroll

An [Oakenscroll's Office](https://github.com/hornbook-knowledge/oakenscrolls-office)
calibration ledger (what you believed, how hard, and how it resolved), as
plain text the kernel can ask questions of.

    python adapters/stdlib/oakenscroll/oakenscroll.py mirror --from FOLDER --to MIRROR

The office keeps its ledger in one SQLite file, `office.db`: a `predictions`
table (each claim as first stated, with its confidence, due date and tags) and
an append-only `events` table (revised, resolved, voided, reopened). Every
file named office.db under FOLDER is read, opened read-only and immutable, so
not even a lock file appears beside it.

Each claim becomes one paragraph, oldest statement first, opening with the
day it was stated. Every event follows in the order it was appended, then the
state they fold to, the way the office folds them:

    2026-10-01: the PR merges this week (a1b2c3d4)
    said 70% on 2026-10-01; due 2026-10-08; tags: work, review
    2026-10-03: revised to 80%
    2026-10-09: graded true; note: merged Thursday; evidence: entry_id=tides, kind=almanac-data
    now: resolved true, at 80%

The first line names the ledger and counts its claims by state. A claim with
no due date says `open-ended` and one with no tags says `no tags`: absence is
written, not left out. A grade that was later reopened stays in the history
and the claim reads `now: open`. Dates are UTC days. A ledger from before the
evidence column was added is read as it is.

This scores nothing. The office's own log score and Brier score are not
reimplemented here; to score claims, write them to [forecasts](../forecasts/),
which settles them with your seal and counts how often you were right.

Each ledger is written to MIRROR at the same relative path with .txt added:
`FOLDER/<path>/office.db` becomes `MIRROR/<path>/office.db.txt`. A file named
office.db that isn't a ledger (not SQLite, or no predictions and events
tables) is skipped and counted.
Point the kernel at MIRROR to ask questions of it:
`kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`) in
`oakenscroll.py`; the tests run the kernel's `init` and `bite` on the mirror
(`kernel.py`). No kernel function is called by the mirror itself.

**Never:** writes inside FOLDER, modifies a ledger, writes anything outside
MIRROR, computes a score, or judges whether a claim was right.
