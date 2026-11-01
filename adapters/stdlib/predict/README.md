<!-- willow-addon
section: Keeping track
line: Write down what a question will come to before you ask it, and grade it after; the record counts how often it was right.
source: bot
added: 2026-11-01
writes: record
network: none
tags: no-install, offline, records, tracking
-->
# predict

Before a question is asked, what it will come to, written on the record;
after, whether that held.

    python adapters/stdlib/predict/predict.py ask   --box DIR "bees swarm"
    python adapters/stdlib/predict/predict.py score --box DIR

    3 of 4 predictions right
      said empty      1 of 1 held
      said populated  2 of 3 held

`ask` counts what the box's earlier bites came to: `sealed` (an answer you
sealed), `populated` (passages served), or `empty` (nothing found). The
likeliest is written as a `predict` row, so it is on the chain before the
question is asked and can't be changed after to fit. Then the kernel's own
bite, and a `graded` row naming the prediction and the bite, what the bite
came to, and whether it was right. The bite's JSON is printed with a
`predicted` field beside it.

**Counted, never guessed.** A tie goes to `empty`, the answer that asks the
person, then by name. The first bite has nothing to count: it is written as
no prediction, and not graded right or wrong.

`score` reads the record back: how many predictions were graded, how many
right, and for each answer it said, how often that held. It writes nothing.
It also reads the one script's own `predict` rows, which carry their grade
in the same row.

The record keeps no words, so neither does this: a prediction is one of
three states and the counts behind it.

Exit codes, the kernel's: for `ask`, the bite's own (0 served or sealed, 42
nothing found, 2 refused); for `score`, 0, or 42 when nothing is graded yet;
2 refused (a record that doesn't verify, a folder that isn't a box, a bad
command line).

**Uses:** the kernel's `read`, `append`, `bite` and its exit codes.

**Never:** reads your key, seals, or writes anything but the record's rows,
through the kernel.

**Where it comes from:** [willow-bot's one script](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/predict.py),
whose second part declares the next bite before the work and grades it
after. Its [rebuild on willow's pieces](https://github.com/willow-memory/willow-bot/blob/main/one-script/rebuilt/one.py) writes
the prediction and grade as one row after the bite; here the prediction goes
on the chain first.
