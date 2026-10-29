<!-- willow-addon
section: Keeping track
line: Attendance for a class, club or group, from your register, by week.
source: new
added: 2026-10-29
writes: nothing
network: none
tags: no-install, offline, read-only, tracking
-->
# attendance

Attendance for a class, club or group, from your register: who was there, by
person or by week.

```
python adapters/stdlib/attendance/attendance.py --box DIR [--by week]

Ben  1 of 3  33%  (2 absent, 1 late)  last absent 2026-03-04
Dee  1 of 2  50%  (1 absent)  last absent 2026-03-04
Cy   2 of 3  67%  (1 absent, 1 late)  last absent 2026-03-09
Ana  3 of 3  100%  (0 absent)
4 people, 11 marks
```

**A mark** is a line, on a day, in one of two shapes: a status and a list of
names ("Absent: Ben, Cy"; "Present: Ana and Dee"; "Late - Eve"), or a name and
a status ("Ana present"; "Ben: absent"; "Cy - late"), after any date. Names
start with a capital (one or two words). Statuses: present (present,
attended), late, and absent (absent, away, sick, missed, excused); beside a
name only present, attended, late, absent, sick and excused are read, so
"Click away" is no mark. Late counts as there. A person marked twice on a day has the later mark. A line's day is
the latest date it says (the kernel's `newest`), else the nearest date written
above it in its file, else the date its file is named for; a line no day
reaches is not counted.

Each person shows the days they were there out of the days they were marked,
the percentage, how many were absent or late, and the last day absent. Lowest
attendance first. With `--by week` each ISO week shows the marks made, oldest
first:

```
2026-W10  present 2, late 1, absent 1  (4 marks)
2026-W11  present 1, late 0, absent 0  (1 mark)
```

Names stay on this machine; nothing is graded or reported to anyone.

It only reads. Exit codes, the kernel's: 0 marks found; 42 none; 2 refused.

**Uses:** the kernel's `chunks`, `newest` and `config`, and
[habits](../habits/)' `file_lines`.

**Never:** changes your files; writes anything, even the record.
