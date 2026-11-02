<!-- willow-addon
section: Play
line: Full tabletop dice notation (4d6kh3, advantage), rolled on the record and checkable like dice.
source: bot
added: 2026-11-01
writes: record
network: none
uses: dice
-->
# dice5e

Full tabletop dice notation, rolled on the record so nobody can say the roll
was picked, and every roll checkable.

    python adapters/stdlib/dice5e/dice5e.py --box DIR roll 4d6kh3
    4d6kh3: [2, 6, 6, 2] keep 2 + 6 + 6 = 14   (row 12)

    python adapters/stdlib/dice5e/dice5e.py --box DIR roll adv+5
    adv+5: [16, 19] keep 19 + 5 = 24   (row 13)

    python adapters/stdlib/dice5e/dice5e.py --box DIR check
    2 rolls on the record; every one holds.

The notation is [dice](../dice/)'s (`2d6`, `1d20+3`, `1d8+1d6`) plus
keeping: `4d6kh3` keeps the highest three of four, `2d20kl1` the lowest one,
and `adv` and `dis` are `2d20kh1` and `2d20kl1`. Any term can be kept, added
or taken away: `3d6kl2-1d4kh1+2`.

**Seeded as dice is:** the record's tip, the hash of the row before, with
the dice written after it, and the faces drawn from dice's own stream
(sha256-stream/v1). Plain dice give dice's own faces. Every die is drawn
and written, kept or not, so the dropped ones are on the record too; among
equal faces the first drawn is kept.

Each roll is one `roll5e` row through the kernel's own `append`: the dice,
every face, which were kept, the total and the seed. `check` throws every
one again from its row: its seed must be the hash of the row before it, and
its faces, kept dice and total what that seed gives. dice's own `check`
reads only its `roll` rows, so the two never trip each other.

Exit codes, the kernel's: 0 rolled, or every roll holds; 2 refused: dice it
can't read (`4d6kh5` keeps more than it rolls), a record that doesn't verify,
or a roll that doesn't hold.

**Uses:** the kernel's `read`, `append` and its exit codes, and dice's
stream and limits.

**Never:** rolls without writing the row, or rewrites a roll.

**Where it comes from:** [willow-bot's one script](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/dice5e.py),
which hands 5e notation to the MIT `dice` library over a generator passed
in. Here no library: keeping is a few lines over dice's stream, and the
seed is the record's.
