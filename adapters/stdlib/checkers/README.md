<!-- willow-addon
section: Play
line: Checkers played on the record: the code holds the rules, and a draw is only the one who holds the key sealing it.
source: new
added: 2026-11-14
version: 0.1.0
writes: record
network: none
role: tools
-->
# checkers

A game of checkers, every move a row, so nobody can say a move was
different. The code knows the rules and nothing more. What the rules leave
to the people at the table is theirs, and the one who holds the box's key
rules the table.

    python adapters/stdlib/checkers/checkers.py --box DIR new
    python adapters/stdlib/checkers/checkers.py --box DIR show
    python adapters/stdlib/checkers/checkers.py --box DIR move 11-15
    python adapters/stdlib/checkers/checkers.py --box DIR resign
    python adapters/stdlib/checkers/checkers.py --box DIR offer
    python adapters/stdlib/checkers/checkers.py --box DIR settle
    python adapters/stdlib/checkers/checkers.py --box DIR check

**The rules** are English draughts (American checkers). The 32 dark squares
are numbered as checkers notation numbers them: black on 1 to 12 moves
first, down the board, and white on 21 to 32 moves up, so black's first
move is one of the seven, 9-13 to 12-16.

- A move is `11-15`. A jump is `15x24`, and a jump of several pieces names
  each landing, `15x24x31`, or just its start and end when only one jump
  does that.
- Jumping is a must, and a jump is taken whole. A man moves and jumps
  forward only. A man reaching the far row is crowned there, and its move
  ends, even if it could jump on.
- A king (`B`, `W`) moves and jumps one square in any diagonal direction.
  The square a piece jumps from is empty while it jumps, so a king can come
  back to it.
- A side with no piece, or no move, has lost.

`show` prints the board, whose turn it is and every move they may make. A
move the rules don't allow is refused, with the moves there are, and
nothing is written.

**A draw is the table's.** The rules end a game in a draw only by agreement,
so the code never calls one, at any count of moves. `offer` hands in "this
game is a draw" as a proposal through the kernel's own `bite` and `propose`,
and the game stops. While it waits nothing is played. The one who holds the
key answers with the kernel's `seal` (a draw) or `decline` (play on), and
`settle` reads that answer back and writes it. A seal made with another key,
a seal over some other proposal, or a proposal changed after it was sealed,
moves nothing. `resign` ends the game for the side to move.

**Rows**, each through the kernel's own `append`: `checkers-open`, one
`checkers-move` a move (its side, the move written whole and how the game
stands after it), `checkers-resign`, `checkers-ask` for a draw handed in
and `checkers-ruling` for its answer. One game is played at a time, and a
new one opens once the last is over.

`check` plays every game on the record again from its first row. Every move
must be one the rules allow, by the side whose turn it was, written whole,
with the ending the board gives; nothing may follow the end, or be played
while a draw waits; and every ruling must be the answer the key gave. The
first row that doesn't hold is named, and while one doesn't, nothing else is
played.

Exit codes, the kernel's: 0 done, or every game holds; 42 a draw waits on
the seal; 2 refused.

**Where it comes from:** the-table's checkers in safe-app-store, over
game-lab's rules. The rules here were checked against game-lab's on 22,039
positions from 300 seeded games, all the same. Left out: game-lab's ending
at 300 moves, or 60 with no jump, judged on the pieces left. That was a
cutoff for its self-play, not a rule of the game. Also changed: game-lab
leaves the square a piece jumps from full while it jumps, which misses a
king's jump back to where it started.

**Never:** seals, declines or calls a draw, reads the key, or writes the
record except through the kernel.
