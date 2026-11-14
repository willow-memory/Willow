# The game box

A table to sit down at. The box is a pile, a kernel record over it, and the
add-ons that play games on that record. Whoever holds the key rules the
table: a player, a script or a model may propose, and only their seal makes
anything stand. Nothing about the people at the table is written down.
The record keeps characters and seats.

This is the box built as a demo, so that the pieces and the code that puts
them together are checked together. The pieces stay add-ons in willow, and
the box is what will ship on its own, from Die-Namic.

## What's in the box

| Part | What it is | Played by |
|---|---|---|
| [table/house-rules.md](table/house-rules.md) | the table's rules, one heading a rule | [rules](../../adapters/stdlib/rules/): each sealed section answers "rule NAME" word for word |
| [table/worlds/lantern-fair.json](table/worlds/lantern-fair.json) | a story, two scenes, every name a character | [game-master](../../adapters/stdlib/game-master/), rolling with [dice](../../adapters/stdlib/dice/) and [odds](../../adapters/stdlib/odds/) |
| checkers | a board game, a draw only on the seal | [checkers](../../adapters/stdlib/checkers/) |
| a logic grid | one cat a row, column and region | [catgrid](../../adapters/stdlib/catgrid/) |
| [table/check.md](table/check.md) | the table's own check: every game played again, every house rule's standing | [stack](../../adapters/stdlib/stack/) |
| [open_table.py](open_table.py) | the box's code: lays a table, and runs its check | the kernel and the add-ons above |

## Laying a table

    python demo/game-box/open_table.py open  --table DIR --key FILE
    python demo/game-box/open_table.py check --table DIR

`open` copies the box's pile to `DIR/pile` and starts a record over it at
`DIR/record`. The kernel makes the key at FILE, which must be outside DIR,
so the record never reads it. Then `open` hands each house rule in for the
seal and opens the story. It seals nothing. It ends with seven house rules
waiting and the first scene set (exit 42).

From there the night is the add-ons' own commands, on `DIR/record`:

- **The house rules.** Seal each with `kernel.py seal`. Then `rules.py ask
  --box DIR/record Draws` gives the section back, word for word.
- **The story.** `game_master.py act Grit`, `ask` and `settle`. An action is
  2d6 plus the character's stat. A ruling waits for the seal or the decline,
  and either one moves the story on.
- **Checkers.** `checkers.py new`, `move 11-15`, `offer` and `settle`. A draw
  is offered, and only the seal ends the game drawn.
- **A grid.** `catgrid.py play`, seeded by the record's tip.

`check` runs [table/check.md](table/check.md) through the stack add-on.
Every game on the record is played again from its first row, and each house
rule shows as sealed or waiting. Then the kernel verifies the chain. It
exits 42 while a rule waits or a game doesn't hold, and 2 when the chain is
broken.

## What the tests hold

[test_game_box.py](test_game_box.py) plays the table through, with a key
made for the test, the test standing in for the one who rules:

- **Opening seals nothing.** `open` lays the table with seven proposals and
  no seal. The key is outside the table, and the pile holds only the box's
  files.
- **The check shows what waits.** It flags the house rules until they're
  sealed, then holds.
- **A whole night.** Seven rules sealed, the story played to its end (one
  ruling sealed, one declined), checkers drawn by the seal, and a grid. The
  table's check then holds every piece: nine seals, all the person's.
- **Forgeries are caught.** A forged checkers move fails the table's check.
  An edited row breaks the chain.
- **Refusals.** A table laid over one already there, or with the key inside
  it, is refused.

## What the box found in its pieces

- **stack** printed "N of M steps flagged (exit 42)" after every run, even
  when nothing was flagged and it exited 0. The line now says the exit it
  makes, and stack's own tests hold that.

## Not in the box yet

- **An AI game master.** A model proposing beats and rulings on loopback,
  the human sealing them.
- **Games with hidden hands** (Liar's Dice, Hearts). Anyone at the table can
  read the record, so a hand dealt onto it is not hidden.
- **More of the-table's games:** backgammon, game-master's puzzle beats, and
  more than one world.
