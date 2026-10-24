<!-- willow-addon
section: Play
line: Conway's Game of Life as rows: a fully deterministic world on the record.
source: bot
added: 2026-10-24
writes: record
network: none
tags: no-install, offline, records, play
-->
# life

Conway's Game of Life, played on the record. It's the most deterministic
game there is: the first board fixes every later one.

    python adapters/stdlib/life/life.py --box DIR play
    python adapters/stdlib/life/life.py --box DIR play --seed "my soup" --size 20 --generations 200
    python adapters/stdlib/life/life.py --box DIR check

`play` draws a square soup of cells from willow-bot's seeded stream:
- `--size` cells a side (16 unless said), each alive at `--density` percent (35 unless said);
- seeded by `--seed`, or by the record's tip so nobody picks it;
- run for `--generations` steps (64 unless said, at most 500) on an unbounded plane, under `--rule` (B3/S23, Life itself, unless said).

It prints the last board and writes one `life` row: the seed and rule, and
for every generation its population, where it sits and the board's hash,
then how it ended:

| Fate | Means |
|---|---|
| dies | nothing left |
| still | the same board, in place |
| oscillator | back to an earlier board, in place, every P generations |
| spaceship | back to an earlier board, moved, every P generations (a glider: 4) |
| running | no board repeated within the generations played |

A board's hash is of its cells counted from its top-left live cell, so one
shape has one hash wherever it sits. That's how a spaceship is known.

`check` plays every game on the record again from its own seed and rule,
and names the first generation that doesn't match.

**Checked against:** the glider, the blinker, the block, and the
R-pentomino's 116 cells at generation 1103, the same figure willow-bot's own
test holds.

**Where it comes from:** [willow-bot's life](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/life.py), which writes the same rows
through its game table; this writes them through the kernel's `append`.

**Never:** writes anything but its row.
