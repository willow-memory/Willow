<!-- willow-addon
section: Play
line: Liar's Dice on the record, every cup dice's own throw: the bids, the wild ones and every call counted as the dice give.
source: new
added: 2026-11-14
version: 0.1.0
writes: record
network: none
role: tools
uses: dice
-->
# liars-dice

A game of Liar's Dice for four seats where every cup is a throw nobody
picked, and every call is counted from it.

    python adapters/stdlib/liars-dice/liars_dice.py --box DIR new
    python adapters/stdlib/liars-dice/liars_dice.py --box DIR show
    python adapters/stdlib/liars-dice/liars_dice.py --box DIR bid QUANTITY FACE
    python adapters/stdlib/liars-dice/liars_dice.py --box DIR call
    python adapters/stdlib/liars-dice/liars_dice.py --box DIR check

**The cups.** North, east, south and west, five dice each. Each round every
seat still in throws its cup, and each throw is [dice](../dice/)'s own roll
row (`5d6`, then fewer), seeded by the record's tip, thrown straight before
the round's row. The cups are open: the throws are on the record as they
fall, as at a table with the cups lifted, or a game master who sees them
all.

**A round.**

- A bid, `bid 3 5`, says there are at least three 5s on the whole table.
- Ones are wild, counted as any face, except in a bid on ones.
- The round's opener bids. Each seat after raises (more dice, or as many of
  a higher face) or calls the last bid with `call`.
- On a call the face is counted: if the bid holds, the caller loses a die;
  if not, the bidder does. A seat with no dice left is out.
- The loser opens the next round, or the next seat still in if the loser is
  out. The last seat with dice wins.

`show` prints the cups, the last call, and the bid standing. After a call,
the next round is thrown at once.

**Rows**, each through the kernel's own `append`: `liars-dice-open` (the
seats), `liars-dice-round` (the round, its opener, dice's rows for each cup
and the faces they threw), `liars-dice-bid` and `liars-dice-call` (the bid
called, the count, who lost a die, how the game stands).

`check` plays every game on the record again from its first row: dice's own
check throws every cup again from its seed; every round's cups the throws
straight before it, one a seat still in, as many dice as it holds; every
bid a raise by the seat whose turn it was; every call counted as the dice
give. The first that isn't is named, and while one doesn't hold, nothing
else is played.

Exit codes, the kernel's: 0 done, or every game holds; 2 refused.

**Where it comes from:** the-table's liar's dice in the SAFE App Store, over
game-lab's rules, with game-lab's simplifications: no palifico, no exact
call, a bid on ones ordered like any other. Its raises were checked against
game-lab's `bids_above` on 159,920 bids, its counts against `count_face` on
100,000 tables, and 3,000 whole games against game-lab's round loop (whose
turn, who loses, who opens, who wins): all the same. The cups are open for
now; hidden cups wait on a way to throw dice only one seat can read.

**Never:** throws without writing the row, counts a call any way but the
dice's, reads the key, or writes the record except through the kernel and
dice.
