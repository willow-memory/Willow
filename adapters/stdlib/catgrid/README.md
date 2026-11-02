<!-- willow-addon
section: Play
line: A seeded logic grid with one cat in every row, column and colour region and a unique answer, replayed from its moves.
source: new
added: 2026-11-01
writes: record
network: none
-->
# catgrid

A cat in every row, every column and every colour region, no two touching.
The board is built so there is exactly one answer, and the game is on the
record, so nobody can say a move was different.

    python adapters/stdlib/catgrid/catgrid.py --box DIR play --moves A1,B3,C5
    python adapters/stdlib/catgrid/catgrid.py --box DIR play --seed "my board" --size 6
    python adapters/stdlib/catgrid/catgrid.py --box DIR check

**The board:** `--size` squares a side (5 unless said, 4 to 8; 2x2 and 3x3
have no placement at all), cut into that many connected colour regions,
shown as letters. Rows are letters and columns numbers: A1 is the corner.
Cats may not touch, even at a corner. A search counts the answers while the
board is made and moves cells between regions until only one is left, so a
board is only handed out with a unique answer.

**How a board is seeded:** by `--seed`, or without one by the record's tip,
the hash of the row before, so nobody picks it. The draws come from
willow-bot's seeded stream, sha256-stream v1 (see [dice](../dice/)): the
same seed and size give the same board on every Python.

**Moves:** `--moves` are the cats you try, in order. A cat on the answer
stays. A cat off it costs one of three hearts and isn't placed. All cats
placed wins; no hearts left loses; a move after either is refused. With no
moves the board is written still open.

`play` prints the board and writes one `catgrid` row through the kernel's
own `append`: the seed, the size, the regions, each move and whether it was
right, the hearts left and how it ended. The answer is never written; it is
what the seed gives.

`check` builds every board on the record again from its own seed and plays
its moves again. The regions, every verdict and the ending must be what the
seed gives, and a seed taken from the tip must be the hash of the row before
it. The first game that doesn't hold is named.

**What was left out of the original:** the source app's hints, trivia, hidden
napkins, daily boards, duels, ratings and boards of two or three cats a row.
This keeps the rules and the proof. It also draws from sha256-stream rather
than the source's xorshift, so a board for a seed is not the source's.

**Where it comes from:** the `catgrid` app in safe-app-store, rebuilt here
against willow's record and stream.

**Never:** shows or writes the answer, plays without writing the row, or
rewrites a game.
