# Trial 3: the rules, written before the run

Not the study. [Trial 2](../trial-2/RESULTS.md) had three agents each add
a step to a stack. This puts code in the agents' place, from the same
start, and compares.

- **The start** is trial 2's: [chain.py](../chain.py) `start`, a fresh box
  over the pinned pile and the same seven steps.
- **The link is [rules.py](../rules.py)**: three rules, each reading what
  a step printed and naming the add-on whose job that is. Its reply has
  the form an agent's has, and goes through the same `apply`: the same
  refusals, the same run, the same hook-handoff row.
- **It runs until no rule fits**, or three turns, whichever is first. "No
  rule fits" is a turn's answer, and is kept as one.
- **And once more, where link 3 stood**: rules.py is asked for the next
  step of trial 2's own project as the agents left it, with the failed
  step still on it.

What will be counted, beside trial 2's numbers:

- **V1**: steps refused by the script.
- **V2**: how each added step ended.
- **V3**: whether the two questions that found nothing are explained when
  the chain stops, and in how many turns.
- **V4**: what it does where link 3 stood.
- **V5**: tokens.

What to hold against it, said before the run:

- **The rules were written after trial 2**, by the session that built the
  hand-made stack and read what the agents did. They hold what was
  learned there. Whether three rules written with that hindsight beat
  three agents without it is not a fair race, and is not the question.
  The question is how much of the choosing a rule can carry once someone
  knows what to choose.
- **Three rules cover three situations.** What the agents were asked to do
  was open. Where no rule fits, the code stops; an agent goes on.
