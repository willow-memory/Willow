# Trial 4: what will be counted, written before the two runs were compared

Not the study. The plan's R2 asks whether two machines give the same bytes
for a simulation, and another session measured it: 27 of 44 between a
laptop and Kaggle. This asks the same of willow's own work, and takes the
smallest step first: one machine, two folders.

- **The two runs** are [demo/kept](../../kept/README.md)'s 30-step stack,
  run by its `rebuild.sh` into two scratch folders, on the pile pinned at
  one commit, with one Python, minutes apart.
- **[same.py](../same.py)** reads the two and says, for each of the 29
  steps before the last:

| | what is counted |
|---|---|
| W1 | steps the stack marked the same in both runs, as they ran |
| W2 | steps marked the same when the mark is made from the step as the stack file writes it |
| W3 | steps that printed the same bytes |
| W4 | steps that printed the same once each run's own folders are written as the stack file writes them |
| W5 | for each step still different, the first line that differs, and why |

What is expected, said now so it can be wrong: W1 none, since a step's
arguments hold the folder it ran in; W2 all; W3 few; W4 most, with the
ones left being steps that print a time or something made from the record,
whose rows carry the time.

What it cannot show: another machine, another Python, another processor.
It isolates one thing, the place a run happens in. If a step differs here,
it will differ everywhere. If it agrees here, another machine is the next
question, and this does not answer it.
