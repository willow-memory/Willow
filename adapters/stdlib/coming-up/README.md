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

**A date that repeats comes up on each repeat**, not only its first: a
calendar event with a rule (the [calendar](../calendar/) reader's `repeats:`
line, or a raw file's `RRULE:`), and a birthday (`birthday:`, or a card's
`BDAY:`):

    2026-10-30  Contacts/contacts.vcf.txt:73  birthday: 1957-10-30  (every year)
    2026-11-03  Calendar/Home.ics.txt:44      2022-11-03  Car rego due  (yearly, from this date)

A rule's FREQ (yearly, monthly, weekly, daily), INTERVAL, UNTIL and COUNT
are kept to, and a 31st or a 29 February comes up only in a month that has
it. A rule that names days within its period (BYDAY, BYMONTHDAY and the
like) isn't counted out rather than counted wrong; its first date still shows
as written. A rule belongs to its event's start: a raw file's DTSTART, else
the first line of its paragraph.

Before this, a yearly event or a birthday came up only in the year it began:
in Bernadette's demo, her car's registration on 3 November and her friend's
birthday on 30 October were both missing from her next thirty days.

**Exit codes:** 0 something is coming up; 42 nothing in the window; 2 refused.

**Uses:** the kernel's `chunks`, `newest`, `words`, `config` and `now`.

**Never:** writes anything.
