<!-- willow-addon
section: Play
line: Dice shaken into a cup: only a hash on the record until it's lifted, so no roll is foreseen, steered or shopped for.
source: new
added: 2026-11-20
version: 0.1.0
writes: record, to
network: none
role: tools
uses: play-dice, play-dice5e
-->
# cup

Dice shaken into a cup, the way a table hides a roll until the moment it's
called: only a hash on the record until it's lifted, then the roll, checked.

    python adapters/stdlib/cup/cup.py --box DIR shake --dice 2d6 --to <cupfile> --for "Mira climbs"
    the die is in the cup (row 41): 2d6, for Mira climbs, under 3f9a0c7d21e4

    python adapters/stdlib/cup/cup.py --box DIR lift --cup <cupfile>
    2d6: 4 + 6 = 10, lifted from the cup at row 41   (row 47)

    python adapters/stdlib/cup/cup.py --box DIR check
    1 cup lifted, every one holds; 1 still down (row 52, 1d20, "the screen roll")

**Why a cup.** [play-dice](../play-dice/) and [play-dice5e](../play-dice5e/)
seed a roll by the record's tip, the hash of the row before. Nobody picks the
faces, and every roll is checked; but the tip is public the moment its row is
written, so the next roll can be read off the record before it's thrown, and
anyone who can write a row first (a ruling, a note, an offer) chooses which
roll comes. Die-Namic found it at a game table: a game master saying yes or no
to a ruling was also choosing the next roll. A cup is the other way.

**Shake.** A fresh 256-bit secret is drawn. Its SHA-256 goes on the record in
a `cup` row through the kernel's own `append`, with the dice and what the
roll is for; the secret goes to the cup file, written new (never over one
that's there), readable only by you, and never inside the box: a folder that
doesn't exist, a file that's there, or a path under the box is refused.

**Lift.** The cup file's secret goes on the record in a `cup-lift` row, and
the dice are thrown from it, in play-dice5e's notation (`2d6`, `adv+5`,
`4d6kh3`) and stream (sha256-stream/v1), seeded by the secret alone. So:

- **Nobody can foresee it.** Until the lift, the record holds only the hash.
- **Nobody can steer it.** No row written between the shake and the lift
  changes the faces: they were settled at the shake, by a secret nobody
  reading the record has.
- **Nobody can shop for it.** A cup is lifted once; a second lift is refused.

**Check.** Every lift is held to its cup: a `cup` row before it, the secret's
SHA-256 the one shaken in, one lift a cup, the dice the cup's, and the faces
what the secret gives, thrown again. Every cup still down is named, with its
dice and what it's for, so ten shaken and the one liked lifted is there to
see.

**What a cup is not.** Whoever holds the cup file can look under it. At a
table that's the game master's screen, not a seal: keep the file where the
table doesn't look. Hiding a roll from the one who shook it too (each seat's
dice readable only by that seat) is [blind-deal](../../../ADDONS.md)'s, an
idea still waiting.

**Uses:** [play-dice5e](../play-dice5e/)'s `parse`, `throw` and `said`; the
kernel's `read` and `append`.

**Never:** writes anything but the record, through the kernel, and the cup
file at `--to`; reads the key; goes online.

**Exit codes:** 0 shaken, lifted, or every lift holds; 2 refused: dice it
can't read, a cup file that isn't one or is already there, a cup lifted
twice or not this box's, a record that doesn't verify, or a lift that
doesn't hold.
