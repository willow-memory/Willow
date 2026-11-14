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
| [worlds/](worlds/) | two stories, every name a character: [the lantern fair](worlds/lantern-fair.json), and [the clockwork cellar](worlds/clockwork-cellar.json), a boss room that turns on its dice | [game-master](../../adapters/stdlib/game-master/), rolling with [dice](../../adapters/stdlib/dice/) and [odds](../../adapters/stdlib/odds/) |
| checkers | a board game, a draw only on the seal | [checkers](../../adapters/stdlib/checkers/) |
| a logic grid | one cat a row, column and region | [catgrid](../../adapters/stdlib/catgrid/) |
| [table/check.md](table/check.md) | the table's own check: every game played again, every house rule's standing | [stack](../../adapters/stdlib/stack/) |
| [open_table.py](open_table.py) | the box's code: lays a table, and runs its check | the kernel and the add-ons above |
| [session.py](session.py) | the game master's bookkeeping, done by code: plays a story as far as it goes without the person, and says what the table made true | game-master |

## Laying a table

    python demo/game-box/open_table.py open  --table DIR --key FILE
    python demo/game-box/open_table.py check --table DIR

`open` copies the box's pile to `DIR/pile` and the worlds to `DIR/worlds`,
and starts a record over the pile at `DIR/record`. The worlds stay out of
the pile: they are the game master's script, and the record reads only what
the table may ask about. The kernel makes the key at FILE, which must be outside DIR,
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

## A session, played by code

    python demo/game-box/session.py --table DIR --world clockwork-cellar
    python demo/game-box/session.py --table DIR canon

`session.py` is the game master's bookkeeping with no model in it. It rolls
each action beat for the character whose beat it is, leaning into the
approach the beat suggests, and hands each ruling in for the seal. Then it
stops (exit 42) until the person seals or declines. Run it again and it
settles their answer and plays on. A story played to its end prints each
roll's line and each ruling. A whole night in the clockwork cellar, the
table laid and three rulings sealed along the way, takes under two seconds.

`canon` is the table's memory. It lists every ruling sealed on the record
whose seal still holds, and every one declined. It reads only seals, never
the worlds, so what it says is what the person made true.

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
- **A session waits for the person.** It plays to the first ruling and
  stops, and plays nothing more until the ruling is answered.
- **The dice turn the story.** With a copy of the cellar whose Brann always
  answers the riddle, the prince's freeing is put to the person. With one
  whose Brann never does, it never is. On every real night, canon says the
  prince is free only if a riddle was answered.
- **Canon is the seals.** A ruling declined shows as a no. Asking the record
  about a ruling, or a scene not played yet, serves nothing from the worlds.

## What the box found in its pieces

Each is fixed, and its own tests now hold it.

- **stack** printed "N of M steps flagged (exit 42)" after every run, even
  when nothing was flagged and it exited 0. The line now says the exit it
  makes.
- **game-master's beats ran in one line, whatever the dice did.** In the
  cellar's first night the riddle roll was a miss ("the cage holds"), and
  the next ruling put to the person was still "the prince is free". A beat
  can now say `when`: it is played only if an earlier beat came out one of
  its ways.
- **game-master's turns went round the seats whatever the beat said.** "Brann
  answers the riddle" was rolled by Juno. Once a story can branch, nobody
  can count turns ahead. A beat can now say `by`: whose beat it is.
- **The box put its worlds in the pile.** Asked "is the red button bait?",
  the record served the world file's own line, the same whether the person
  had sealed it or said no, and anyone at the table could read scenes not
  played yet. The worlds now sit beside the pile, and `canon` answers from
  seals alone.

## Not in the box yet

- **An AI game master.** A model proposing beats and rulings on loopback,
  the human sealing them. `session.py` is the bookkeeping it would sit on.
- **Asking canon in your own words.** The kernel serves a sealed answer to
  the question it was sealed for. game-master asks under its own name for
  each beat, so "is the prince free?" finds nothing. `canon` lists what's
  true, but doesn't yet answer a question about it.
- **A player's own guest.** The Lantern Man is written into the world ahead
  of time. A guest a player thinks of at the table has no beat to ride in on.
- **Games with hidden hands** (Liar's Dice, Hearts). Anyone at the table can
  read the record, so a hand dealt onto it is not hidden.
- **More of the-table's games:** backgammon, game-master's puzzle beats, and
  more than one world.
