<!-- willow-addon
section: Keeping track
line: A course syllabus as dates: readings, assignments and exams due, each cited.
source: new
added: 2026-10-29
writes: nothing
network: none
uses: habits
-->
# syllabus

A course syllabus as dates: the readings, assignments and exams that fall due,
soonest first, each with the file and line it was written on.

```
python adapters/stdlib/syllabus/syllabus.py --box DIR [--now TS]

2026-03-02  reading     2026-03-02 Read Ch. 1-2: Introduction  (course/syllabus.md:2, 7 days ago)
2026-03-09  assignment  2026-03-09 Essay 1 due                 (course/syllabus.md:3, today)
2026-03-16  exam        2026-03-16 Midterm exam                (course/syllabus.md:4, in 7 days)
2 readings, 2 assignments, 2 exams; next 2026-03-09
```

**What counts.** A line, on a day, about a course (the line or the path of its
file says syllabus, course, class, lecture, semester, term, module or unit) that
says what is due: a reading (read, reading, chapter, ch., pp.), an assignment
(assignment, essay, paper, problem set, homework, hw, project, lab, report,
quiz, due) or an exam (exam, midterm, final, test). A line is the first of the
three that it names, exam before assignment before reading. A line's day is the
latest date it says (the kernel's `newest`), else the nearest date written above
it in its file (a week's heading), else the date its file is named for.

Distances are counted from `--now` (an ISO timestamp, the kernel's kind; today
if not given). "Next" is the first day that is today or later. Nothing is marked
done and nothing is reminded; the file and line are cited so you can read what
it says.

It only reads. Exit codes, the kernel's: 0 something due found; 42 none; 2
refused.

**Uses:** the kernel's `chunks`, `newest`, `config` and `now`, and
[habits](../habits/)' `file_lines`.

**Never:** changes your files; writes anything, even the record.
