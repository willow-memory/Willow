<!-- willow-addon
section: Keeping track
line: Streaks from the lines you write each day: how many days in a row, and which you missed.
source: new
added: 2026-10-27
writes: nothing
network: none
tags: no-install, offline, read-only, tracking
-->
# habits

The short lines your files write day after day — walked the dog, no sugar,
practised — gathered into habits, most days first, each with its runs and
its misses.

```
python adapters/stdlib/habits/habits.py --box DIR

 212 days  longest run 44  ends on 12  walked the dog  (2026-01-02 to 2026-10-22; missed 38, last 2026-10-10)
  31 days  longest run 31  ends on 31  no sugar  (2026-09-22 to 2026-10-22; missed none)
2 habits, written on 4 days or more
```

**What makes a habit.** The same short line on four or more distinct days. A
line is read as its words, in order, case and punctuation aside, any word
holding a digit dropped, so "2026-03-01 Ran 5k" and "ran" tick the same
habit; one to six such words, since a sentence of more than six is prose,
not a tick. A line's day is the latest date it says, read as the kernel
reads one (its `newest`), else the nearest date written above it in its
file, else the date its file is named for; a line no day reaches ticks
nothing, and the same line twice in a day is one day.

**A line you wrote has a lowercase letter in it.** One that shouts
throughout (a statement's WOOLWORTHS), one whose first word carries a
field's mark (a calendar's DTSTART, a note's tags:), and one that opens as
markup are a machine's, and never tick. What slips past the shapes is still
shown, for you to weigh: on willow's demo folders Hollis's sign-off "thank
you" stands as a 146-day habit of his mail, which is true, if not the kind
you meant.

**Runs and misses are plain counting.** A run is consecutive calendar days.
"Ends on" is the run the habit's last day closes, however long ago that was:
no clock is consulted, so the same folder gives the same bytes, and whether
a streak is alive today is yours to say, looking at its last day. The
missed days are the gaps between a habit's first day and its last, with the
most recent named; days before you started and after you stopped aren't
misses.

On willow's demo folders, Hollis's "errands", "supply run" and "hardware
store" are the recurring lines of his tuning rounds; Bernadette's weather
notes ("blue sky cold as charity", "fog till eleven") are the habit her
daily files really keep; Odile's recurring tuning measurements lead hers.

It only reads. Exit codes, the kernel's: 0 habits found; 42 none on four
days or more; 2 refused.

**Uses:** the kernel's `chunks`, `words`, `newest` and `config`.

**Never:** changes your files; writes anything, even the record; consults a
clock; reads a machine's line as yours.
