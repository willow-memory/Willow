<!-- willow-addon
section: Play
line: Seeded dice rolls as rows: every roll replayable and checkable.
source: bot
added: 2026-10-24
writes: record
network: none
-->
# dice

Dice rolled on the record, so nobody can say the roll was picked.

    python adapters/stdlib/dice/dice.py --box DIR roll 2d6+1
    2d6+1: 4 + 6 + 1 = 11   (row 12)

    python adapters/stdlib/dice/dice.py --box DIR check
    3 rolls on the record; every one holds.

**How a roll is seeded:** with the record's tip (the hash of the row before)
followed by the dice. Nobody picks the seed, and it's fixed the moment the
row before is written.

**How the faces are drawn:** willow-bot's seeded stream, sha256-stream v1:
SHA-256 over the seed and a counter, read by rejection so no face is likelier
than another, and the same on every Python.

Each roll is one `roll` row through the kernel's own `append`: the dice,
each die's face, the total, the seed.

`check` throws every roll again from its row. Its seed must be the hash of
the row before it, and its faces must be what that seed gives; the first
roll that doesn't hold is named. A roll can't be changed after the fact,
and anyone holding the record can throw it again.

Dice notation is [odds](../odds/)'s: `2d6`, `1d20+3`, `1d8+1d6`, `d6`.

**Where it comes from:** [willow-bot's stream](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/stream.py), ported
draw for draw.

**Never:** rolls without writing the row, or rewrites a roll.
