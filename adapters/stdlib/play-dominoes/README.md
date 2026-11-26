<!-- willow-addon
section: Play
line: All Fives dominoes on the record, shuffled by the record's tip: the first double a spinner, every multiple of five scored, to 250.
source: new
added: 2026-11-26
version: 0.1.0
writes: record
network: none
role: tools
-->
# play-dominoes

All Fives, the dominoes game played to fives with a spinner, for two seats
on a double-six set. Nobody shuffles: the record's tip does.

    python adapters/stdlib/play-dominoes/play_dominoes.py --box DIR new
    python adapters/stdlib/play-dominoes/play_dominoes.py --box DIR show [--seat SEAT]
    python adapters/stdlib/play-dominoes/play_dominoes.py --box DIR play TILE [ARM]
    python adapters/stdlib/play-dominoes/play_dominoes.py --box DIR draw
    python adapters/stdlib/play-dominoes/play_dominoes.py --box DIR pass
    python adapters/stdlib/play-dominoes/play_dominoes.py --box DIR auto
    python adapters/stdlib/play-dominoes/play_dominoes.py --box DIR check

**The deal.** North and south, nine tiles each; the other ten are the
boneyard. Each hand is shuffled from willow's seeded stream (sha256-stream
v1, the one dice uses), seeded by the hash of the row before the deal.

**The lead.** The first hand, and a hand after a block, is led by the
highest double dealt (the 6|6 when it's out), or the heaviest tile when no
double is. After a seat goes out, it leads the next hand with any tile.

**The spinner.** The first double played, led or not, is the spinner: tiles
go against its four arms, `left`, `right`, `up` and `down`, in any order.
Later doubles go on like any tile and don't branch. A tile is written
either way round, `6|5`, `6-5` or `65`; its arm is said when it fits more
than one, `play 6|3 up`.

**A turn.** A seat that can play must. One that can't draws, a tile a row,
until it can; with the boneyard empty, it passes.

**The count.** After every play the open ends are added up: a double at an
end counts both halves, and so does the spinner, while either side of it
along the line is still open; up and down count once played on. A count
that is a multiple of five scores itself.

**The end of a hand.** A seat that plays its last tile scores the other's
pips to the nearest five. When nobody can play, the seat holding fewer pips
scores the other's, to the nearest five; tied, nobody does. The game is over
the moment a seat holds 250, mid-hand or not; until then the next hand is
dealt at once.

`show` prints the layout, arm by arm from the lead out, the spinner in
braces, each arm's end and the count, then the hands, the boneyard and the
score. `--seat north` shows only north's tiles, the other seat's as a
count. The record holds every hand, so this is for a table that agrees not
to look, not a secret.

`auto` plays the turn for the seat to move, by a fixed rule: it draws until
it can play, then plays what scores most, then the heaviest tile, then the
first arm in left, right, up, down, and says only what it did. A person
can play against it without anyone seeing its tiles.

**Rows**, each through the kernel's own `append`: `dominoes-open` (the
seats, the hand, the target), `dominoes-deal` (the seed, the hands, the
boneyard in the order it is drawn, who leads and with what),
`dominoes-play` (the tile, its arm, what it scored), `dominoes-draw` (the
tile drawn) and `dominoes-pass`. Each play and pass names the score and
how the game stands after it.

`check` plays every game on the record again from its first row: every
deal what its seed gives, seeded by the row before it; every tile one the
seat held and the layout took, on its turn; every draw the next in the
boneyard and only when nothing could be played; every pass one the seat had
to make; every score the count gives. The first that isn't is named, and
while one doesn't hold, nothing else is played.

Exit codes, the kernel's: 0 done, or every game holds; 2 refused.

**Where it comes from:** a game played at Die-Namic's table on 2026-11-26,
and the rules of All Fives as [pagat](https://www.pagat.com/domino/cross/all_fives.html)
gives them, with the table's own: the first hand led by the highest double,
no order to the spinner's arms, and a seat that can't play drawing until it
can. Two seats for now; three and four wait on their deals.

**Never:** shuffles any way but the seed's, scores a count any way but the
tiles', reads the key, or writes the record except through the kernel.
