<!-- willow-addon
section: Play
line: A die dropped in a tower: only a hash on the record until it's out, so no roll is foreseen, steered or shopped for.
source: new
added: 2026-11-20
version: 0.1.1
writes: record, to
network: none
role: tools
uses: play-dice, play-dice5e
-->
# dice-tower

A dice tower, the way a table keeps a roll honest: everyone sees the die go
in, nobody sees it tumble, and it lands in the tray for all. On the record:
only a hash until it's out, then the roll, checked.

    python adapters/stdlib/dice-tower/dice_tower.py --box DIR drop --dice 2d6 --to <diefile> --for "Mira climbs"
    in the tower (row 41): 2d6, for Mira climbs, under 3f9a0c7d21e4

    python adapters/stdlib/dice-tower/dice_tower.py --box DIR out --die <diefile>
    2d6: 4 + 6 = 10, out of the tower from row 41   (row 47)

    python adapters/stdlib/dice-tower/dice_tower.py --box DIR check
    1 die out of the tower, every one holds; 1 still inside (row 52, 1d20, "the screen roll")

    python adapters/stdlib/dice-tower/dice_tower.py --box DIR page --to <tower.html>
    the tower is drawn at <tower.html>: 1 out, 1 inside

**Why a tower.** [play-dice](../play-dice/) and [play-dice5e](../play-dice5e/)
seed a roll by the record's tip, the hash of the row before. Nobody picks the
faces, and every roll is checked; but the tip is public the moment its row is
written, so the next roll can be read off the record before it's thrown, and
anyone who can write a row first (a ruling, a note, an offer) chooses which
roll comes. Die-Namic found it at a game table: a game master saying yes or no
to a ruling was also choosing the next roll. A tower is the other way. Under
the drawing it's a commitment and its reveal, a cup.

**Drop.** A fresh 256-bit secret is drawn and kept first, whole, in the die
file: made new in one step (never over one that's there, even one that
appears a moment before), readable only by you from its first byte, and never
inside the box: a folder that doesn't exist, a file that's there, or a path
under the box is refused. Then its SHA-256 goes on the record in a
`tower-drop` row through the kernel's own `append`, with the dice and what the
roll is for. If the record won't take the row, the die file is taken away
again: no die is ever on the record that nobody holds.

**Out.** The die file's secret finds its drop (the row whose hash it is; a die
file from 0.1.0 names its row), goes on the record in a `tower-out` row, and
the dice are thrown from it, in play-dice5e's notation (`2d6`, `adv+5`,
`4d6kh3`) and stream (sha256-stream/v1), seeded by the secret alone. So:

- **Nobody can foresee it.** Until it's out, the record holds only the hash.
- **Nobody can steer it.** No row written between the drop and the out
  changes the faces: they were settled at the drop, by a secret nobody
  reading the record has.
- **Nobody can shop for it.** A die comes out once; a second time is refused.

**Check.** Every die out is held to its drop: a `tower-drop` row before it,
the secret's SHA-256 the one dropped in, one out a drop, the dice the drop's,
and the faces what the secret gives, thrown again. Every die still inside is
named, with its dice and what it's for, so ten dropped and the one liked
taken out is there to see.

**Page.** The tower drawn as one HTML page, written new at `--to`, outside the
box: the dice still inside (what they're for, their dice, the start of their
hash), the tray (each roll as said, newest first), and whether every die out
holds, or the first that doesn't. One file, its own styles, light and dark,
nothing fetched: any front end can show it.

**What a tower is not.** Whoever holds the die file can look inside. At a
table that's the game master's screen, not a seal: keep the file where the
table doesn't look. Hiding a roll from the one who dropped it too (each
seat's dice readable only by that seat) is [blind-deal](../../../ADDONS.md)'s,
an idea still waiting.

**Uses:** [play-dice5e](../play-dice5e/)'s `parse`, `throw` and `said`, which
draws on [play-dice](../play-dice/)'s stream; the kernel's `read` and `append`.

**Never:** writes anything but the record, through the kernel, and the die
file or page at `--to`; reads the key; goes online.

**Exit codes:** 0 dropped, out, drawn, or every die holds; 2 refused: dice it
can't read, a die file that isn't one or is already there, a die out twice or
not this box's, a page already there, a record that doesn't verify, or a die
that doesn't hold.
