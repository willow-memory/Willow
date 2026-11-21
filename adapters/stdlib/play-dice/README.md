<!-- willow-addon
section: Play
line: Seeded dice rolls as rows: every roll replayable and checkable.
source: bot
added: 2026-10-24
version: 0.1.0
writes: record
network: none
role: tools
-->
# play-dice

Dice rolled on the record, so nobody can say the roll was picked.

    python adapters/stdlib/play-dice/play_dice.py --box DIR roll 2d6+1
    2d6+1: 4 + 6 + 1 = 11   (row 12)

    python adapters/stdlib/play-dice/play_dice.py --box DIR said 2d6 4,6
    2d6: 4 + 6 = 10, as said   (row 13)

    python adapters/stdlib/play-dice/play_dice.py --box DIR check
    3 rolls on the record; every one holds. 1 of them said, kept as said.

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

**A roll said, not thrown.** At a real table a kid throws a real die and
says the number. `said DICE FACES` keeps that, as the person enters it on
purpose to be recorded (the constitution's VI.8): a `roll` row whose
generator is `said`, with no seed, the faces one for each die and each on
it (`4,6` for 2d6; a 7 on a d6 is refused), and the total theirs. Nothing on
the record chose it and nothing can throw it again: its honesty is the
table watching, not a seed, and every way it's shown says "as said". `check`
holds a said roll to its dice. A game that holds its rolls to seeds alone,
where a said roll would let a player pick their dice, asks `check(rows)`,
which refuses one; [game-master](../game-master/), whose tables throw real
dice, asks `check(rows, said=True)`.

Dice notation is [play-odds](../play-odds/)'s: `2d6`, `1d20+3`, `1d8+1d6`, `d6`.

**Where it comes from:** [willow-bot's stream](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/stream.py), ported
draw for draw.

**Never:** rolls without writing the row, rewrites a roll, or passes a said
roll off as thrown.
