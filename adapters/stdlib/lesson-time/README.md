<!-- willow-addon
section: Keeping track
line: Lesson plans whose timed parts don't add up to the time the plan says it takes, each part's minutes shown beside the total.
source: new
added: 2026-10-29
writes: nothing
network: none
tags: teaching
-->
# lesson-time

Lesson plans whose timed parts don't add up to the period: the plan says
50 minutes, its parts say 45.

    python adapters/stdlib/lesson-time/lesson_time.py --box DIR [--period N]

    off  45 of 50 min  lessons/hs-03-the-consent-ledger.md  8+12+20+5  (said on line 47)
    ok   50 of 50 min  lessons/hs-01-the-oracle.md          10+15+15+7+3  (said on line 43)
    2 plans read, 1 off

**A part is a heading that carries its minutes**, `### Part 2 — The
Mechanic (15 min)`, or a range, `## Discussion (15–20 min)`, and then the
plan's total is a range too. A part marked optional, extension, additive or
"if time" is left out of the sum. Minutes written inside a part's text (a
five minute debrief within the role-play) are not counted, so a plan that
times its steps there shows as off, and the line says where to look.

**The time a plan says** is the first line that starts with Time, Duration,
Length, Period or Suggested time (`**Time:** 45–55 minutes`). A plan is ok
when its total, or any part of its range, falls inside that time. A plan
that says no time is held to `--period N` when it is given, and left out
when it isn't. A file with fewer than two timed headings is not a lesson
plan by this reading.

On the DispatchesFromReality lessons it found the two 9 to 12 plans whose
parts sum to 45 and 47 against a stated 50, and held the 6 to 10 plans'
ranged parts as ranges.

It only reads, and the same folder gives the same bytes. Exit codes, the
kernel's: 0 a plan is off; 42 every plan adds up, or none was found; 2
refused.

**Uses:** the kernel's `chunks`, `config` and `REFUSED`, `ESCALATE` and
`ALIVE`.

**Never:** changes your files; writes anything, even the record; counts
minutes that aren't on a part's own heading.
