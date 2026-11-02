<!-- willow-addon
section: Keeping track
line: Your child's firsts, words and heights, from your notes, by age.
source: new
added: 2026-10-29
writes: nothing
network: none
-->
# milestones

Your child's firsts, words and heights, from your notes, each with the child's
age on the day.

```
python adapters/stdlib/milestones/milestones.py --box DIR --born YYYY-MM-DD [--name NAME]

0y 0m 3d   2026-03-02  2026-03-02 first smile  (notes/baby.md:1)
0y 10m 13d 2027-01-09  2027-01-09 first steps  (notes/baby.md:2)
0y 10m 13d 2027-01-09  2027-01-09 height 74 cm  (notes/baby.md:3)
3 milestones
```

**What counts.** A line, on a day on or after `--born`, that is about a child
(the line or the path of its file says baby, bub, toddler, child, kid, son,
daughter, milestone, newborn or infant, or names `--name`) and says a first
("first word", "first steps", "first tooth", "first smile", "first day", "first
haircut", and the like), a milestone (rolled over, sat up, crawled, pulled
herself up, walked, waved, clapped, babbled, slept through) or a measurement
(height, length or weight, with a number and a unit: 74 cm, 9.6 kg, 12 lb). A
line's day is the latest date it says (the kernel's `newest`), else the nearest
date written above it in its file, else the date its file is named for.

**Age** is whole years, whole months and days since `--born`, counted on the
calendar: born on the 31st, a month later is the last day of the next month.
Oldest first. Nothing is compared to anyone else's child; there is no chart and
no norm. This is your own record of when things happened.

It only reads. Exit codes, the kernel's: 0 milestones found; 42 none; 2
refused (a bad command line, `--born` not a date).

**Uses:** the kernel's `chunks`, `newest` and `config`, and
[habits](../habits/)' `file_lines`.

**Never:** changes your files; writes anything, even the record; compares a
child to a norm.
