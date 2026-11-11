# Trial 4: what happened

Run 2026-11-11, after [what would be counted](RULES.md) and
[same.py](../same.py) were committed alone (`caee72c`). The stack was run
into two scratch folders on one machine. [cold.jsonl](cold.jsonl) is the
first comparison, [warm.jsonl](warm.jsonl) the second, each a line a step.

| | what was counted | expected | found |
|---|---|---|---|
| W1 | steps the stack marked the same, as they ran | none | 10 of 30 |
| W2 | marked the same, from the step as written | all | 30 of 30 |
| W3 | printed the same bytes | few | 17 of 30 |
| W4 | printed the same without the place | most | 23 of 30 cold, 27 of 30 warm |

Every step ended the same way in both runs.

## What was wrong in what was expected

- **Ten steps were already marked the same.** The stack makes a step's
  mark before it fills in where the record is, so a step that names only
  the record has no place in its mark. The twenty that differ name a
  scratch folder or the pile, which this stack's own rebuild script fills
  in before the stack ever sees them.
- **Seventeen printed the same bytes as kept**, more than few. A step
  that asks an index, checks a claim or hashes the folder prints what it
  found and not where.
- **Four differences were not about the place at all.** The first folder
  had run before and kept its indexes; the second was new. So three
  index steps and the passage store printed "current" in one and
  "rebuilt" in the other. Run again with both warm, they agree. This was
  not foreseen, and it is the more useful finding: see below.

## W5: the three that still differ, and why

| step | first line that differs | why |
|---|---|---|
| 21 merkle | the root | it is a hash over the record's rows, and each row carries the time it was written |
| 23 tip-pin | the tip | the hash of the last row, for the same reason |
| 28 history | "07:44 You started your record" against "08:05" | it prints the rows' times |

All three print something made from the record's clock. Nothing that reads
only the folder differs.

## What the step printed and what it made are two things

Cold, the index steps printed different lines in the two folders. What
they made was the same: all six index files, three of passages and three
of words, hash the same in both folders, 41,976 passages among them. So a
step can report differently (it worked here, it remembered there) and
leave the same bytes behind.

A memory keyed on what a step printed would call those two different. One
keyed on what the step made would not.

## What it says for sharing a stack between machines

- **The name is nearly there.** A mark made from the step as written is
  the same in both runs for all thirty. The stack already does this for
  the record. It would need to do it for the folder being asked and the
  folder being written to.
- **Twenty-seven of thirty steps are the same work in another place.**
  That is on one machine. It is the ceiling for another machine, not the
  answer.
- **The record cannot be compared as it is.** Two people who ran the same
  stack on the same pile hold records with nothing in common but the
  kinds of their rows, because every row carries its time. The rows that
  stack-row wrote agree on 16 of 29 output hashes. Ten more differ
  only by a folder's name in a line, and three by the clock. A row's identity
  without its clock, and a step's output without its place, are what
  would let two records find each other.
- **A step's report is not its result.** What to remember, and compare,
  is what a step made.

## What to hold against it

- **One machine, one Python, minutes apart.** Nothing here speaks to
  another processor. The simulation trial in the plan found 27 of 44
  between two machines; this found 27 of 30 between two folders, and the
  numbers are alike by chance.
- **"Without the place" is this script's own rewriting**, four literal
  replacements. A step that printed a path some other way would be
  missed, and counted as different.
- **The thirtieth step is counted**, and it records the other
  twenty-nine. Left out, it is 26 of 29 warm.
