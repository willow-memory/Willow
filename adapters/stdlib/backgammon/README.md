<!-- willow-addon
section: Play
line: Backgammon on the record, every throw dice's own row: the rules held whole, gammons and backgammons scored.
source: new
added: 2026-11-14
version: 0.1.0
writes: record
network: none
role: tools
uses: dice
-->
# backgammon

A game of backgammon where every throw is a row nobody picked and every
turn is checked against it.

    python adapters/stdlib/backgammon/backgammon.py --box DIR new
    python adapters/stdlib/backgammon/backgammon.py --box DIR show
    python adapters/stdlib/backgammon/backgammon.py --box DIR roll
    python adapters/stdlib/backgammon/backgammon.py --box DIR move "24/18 13/11"
    python adapters/stdlib/backgammon/backgammon.py --box DIR resign
    python adapters/stdlib/backgammon/backgammon.py --box DIR check

**The board.** White and black, fifteen checkers each, every point counted
from the mover's own side: 24 is the far end, 1 to 6 is home. `new` throws
the opening roll, one die each, again on a tie, and the higher plays both.
After that a turn is `roll`, then `move`. Every throw is
[dice](../dice/)'s own `2d6` roll row, seeded by the record's tip.

**A turn** names every checker it moves, in order: 24/18 13/11, bar/22,
6/off, a hit marked or not (13/7*). The same checkers in another order
are the same turn. The rules are the game's, held whole:

- A doublet is played four times.
- A turn uses as many dice as it can. When only one of two can be used, it
  is the larger, if the larger can be.
- A checker on the bar enters before any other moves.
- A point held by two or more of the other side is closed; a lone checker
  there is hit, to the bar.
- Borne off only once every checker is home, by the exact number, or a
  higher one from the highest point.
- A side with no legal move writes `move none`.

`show` prints the board, whose turn, and every way the throw can be played.

**The ending.** Fifteen off wins: a single game, 1 point; a gammon, 2, when
the loser bore none off; a backgammon, 3, when the loser bore none off and
still has one on the bar or in the winner's home. `resign` ends it for the
side to move. The doubling cube is left out.

**Rows**, each through the kernel's own `append`: `backgammon-open` (the
opening throws, who plays first and with what), `backgammon-roll` (a turn's
throw, naming dice's row straight before it), `backgammon-move` (the turn
written whole, how the game stands, the points) and `backgammon-resign`.

`check` plays every game on the record again from its first row: dice's
own check throws every roll again from its seed; the opening must be the
throws it names; every turn one the rules allow with that turn's throw, by
the side whose turn it was, written whole; every ending the one the board
gives. The first that isn't is named, and while one doesn't hold, nothing
else is played.

Exit codes, the kernel's: 0 done, or every game holds; 2 refused.

**Where it comes from:** the-table's backgammon in the SAFE App Store, over
game-lab's rules. Its single-die moves were checked against game-lab's
`bg_leg` on 216,372 positions and dice from 300 seeded games, all the same.
game-lab's self-play did not hold a turn to using as many dice as it can,
or to the larger die; here both are held, as the game's rules have them.

**Never:** throws without writing the row, plays a turn the throw doesn't
allow, reads the key, or writes the record except through the kernel and
dice.
