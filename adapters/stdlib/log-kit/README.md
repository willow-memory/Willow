<!-- willow-addon
section: Keeping track
line: The engine the logs share: your notes' dated lines read by a short spec of words, numbers and a period, so a new log is a spec, not code.
source: new
added: 2026-11-06
version: 0.1.0
writes: nothing
network: none
role: tools
uses: habits
-->
# log-kit

The engine the logs share: your notes' dated lines, read by a short spec of
words, numbers and a period, so a new log is a spec, not a program.

    python adapters/stdlib/log-kit/log_kit.py --box DIR --words WORD[,WORD...] [--by day|week|month|year]

**Every log reads the same way**: the lines of your notes, each with the day it
falls on; the ones holding its words; a value or a kind for each; grouped by a
period. This does that once. A log is then a spec, as
[food-log](../food-log/)'s is, a few lines naming its words, its kinds and how
each period is summed up:

    SPEC = {
        "name": "food-log",
        "words": ["ate", "eaten", "eating"],
        "kinds": {"breakfast": ["breakfast"], "lunch": ["lunch"], "dinner": ["dinner", "supper"]},
        "summary": "lines",
        "by": "day",
        "bys": ("day", "week", "month"),
        "none": "No line of your folder says what you ate.",
    }

| Key | What it says |
|---|---|
| `words` | a line counts when it holds one, whole and case aside |
| `kinds` | the first kind whose word a line holds is its kind; a line holding one counts too |
| `value` | a function of the line giving its number, or None, and then the line doesn't count |
| `summary` | `lines`: each line under its period, its kind and where it is; `total`: the values added, in the spec's `unit`; `average`: a day's values averaged, then each period's average, its lowest and highest day and the change from the period before |
| `by`, `bys` | the period it groups by unless `--by` says another, and the ones it takes |
| `none` | what it says when no line counts |

**A line's day** is the latest date it says, else the nearest date written
above it in its file, else the date its file is named for; a line no day
reaches is not counted. This is the `entries` that each log kept a copy of;
[mood](../mood/) is the first log moved onto it, its output the same bytes.

**Run on its own** it is a log of any words: `--words run,ran,jog --by week`
gives every line holding one, week by week, each with where it is.

**Exit codes:** 0 lines found; 42 none; 2 refused (a bad command line, no
`--words`, not a box).

**Uses:** [habits](../habits/)'s `file_lines`, the kernel's `chunks`, `config`
and `newest`.

**Never:** writes anything, or goes online.
