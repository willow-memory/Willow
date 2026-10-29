<!-- willow-addon
section: Keeping track
line: A teacher's gradebook, kept on this machine: each student's marks by assignment, and who is falling behind.
source: new
added: 2026-10-29
writes: nothing
network: none
tags: no-install, offline, read-only, tracking
-->
# gradebook

A teacher's gradebook that stays on this machine: each student's marks, read
from the lines you wrote, and who is falling behind.

```
python adapters/stdlib/gradebook/gradebook.py --box DIR [--below PCT]

Ben Ruiz    45%  2 marks  latest 50% (Quiz 2, 2026-03-02)  below 50%
Cy          69%  4 marks  latest 45% (Essay 4, 2026-03-09)  falling
Maya Chen   88%  2 marks  latest 90% (Essay 2, 2026-03-02)
3 students, 2 behind
```

**A mark** is a line that opens with a student's name (one to three words
that start with a capital) and a colon, and then gives a score: 17/20,
17 out of 20, or 85%. "Maya Chen: Essay 2 - 17/20" is Maya's 85% for Essay 2.
A name has a lowercase letter in it, and what follows the colon is short
(eight words at most) and has no colon of its own, so a hive's "H6: 5 fr bees,
eggs yes, mites 1/300" and an email's "Subject: Re: ... 38%" are not marks.
Words like Total, Average, Page and Note are never names. A date such as
3/4/2026 is not a score. A line's day is the latest date it says (the
kernel's `newest`), else the nearest date written above it in its file, else
the date its file is named for; a line no day reaches is not counted.

**Behind** means one of two things, both plain arithmetic on the marks: the
average is below `--below` percent (50 unless told), or, with three marks or
more, the last two marks average at least 15 points under the marks before
them ("falling"). Nothing is graded, rounded up or sent to anyone; it is what
your own lines add up to. Lowest average first. Names are the students' and
never leave this machine: nothing here is written or sent.

It only reads. Exit codes, the kernel's: 0 marks found; 42 none; 2 refused.

**Uses:** the kernel's `chunks`, `newest` and `config`, and
[habits](../habits/)' `file_lines`.

**Never:** changes your files; writes anything, even the record.
