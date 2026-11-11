# Trial 1: the rules, written before any agent was started

Not the study. A first, small try of the blind handover in
[the plan](../README.md), on a run already made: the 29-step stack of
[demo/kept](../../kept/README.md), on its pinned pile.

- [report.txt](report.txt) is the script's report: what the handover
  add-on says of the run, the kernel's verify line, the log's last line,
  and the first line each step printed. No agent wrote any of it.
- [key.json](key.json) is the answer to each of the twelve questions in
  [questions.txt](questions.txt), read off the run's files by
  [trial.py](../trial.py). Two answers are `not said`: the report holds
  no time and no count of machines.
- **Agent A** is given [brief-a.txt](brief-a.txt) and the report, and
  writes an account. **Agent B** is given [brief-b.txt](brief-b.txt), the
  questions, and A's account after the strike, and answers. **Agent C**,
  the control, is given the same brief and questions as B, with the report
  itself in place of an account.
- **The strike**: a sentence of A's account that says a figure the report
  never says is taken out before B sees it, and counted.
- A, B and C are three different models, chosen for cost: the smallest
  for A and C, one size up for B.

What will be counted, with no threshold, since this is a first try:

- **T1**: sentences struck from A's account.
- **T2**: B's answers that are right, `not said`, and wrong, of twelve.
- **T3**: the same for C. The gap between T2 and T3 is what the handover
  lost.
- **T4**: the two questions whose key is `not said`: whether B and C left
  them unsaid.

What it cannot show: blindness is by instruction only. An agent started
here can read this repository, where the answers are. Each brief says not
to and asks it to say if it did; nothing enforces that.
