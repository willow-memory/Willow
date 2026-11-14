<!-- willow-addon
section: Play
line: Hearts on the record, hands open and every deal seeded by the record's tip: the passes, the tricks and the moon held to the rules.
source: new
added: 2026-11-14
version: 0.1.0
writes: record
network: none
role: tools
-->
# hearts

A game of Hearts for four seats, played face up, where nobody shuffles: the
record's tip deals every hand.

    python adapters/stdlib/hearts/hearts.py --box DIR new
    python adapters/stdlib/hearts/hearts.py --box DIR show
    python adapters/stdlib/hearts/hearts.py --box DIR pass SEAT CARD CARD CARD
    python adapters/stdlib/hearts/hearts.py --box DIR play CARD
    python adapters/stdlib/hearts/hearts.py --box DIR deal
    python adapters/stdlib/hearts/hearts.py --box DIR check

**The deal.** North, east, south and west. Each hand is shuffled from
willow's seeded stream (sha256-stream v1, the one dice uses), seeded by the
hash of the row before the deal, and every seat's thirteen cards are written
on the deal row. The hands are open: this is a table playing face up, or a
game master holding every hand.

**A hand.** Each seat passes three of its cards, `pass west 2C QS AH`: to
the left, then the right, then across, and every fourth hand none. The 2C
leads the first trick. Then the rules, held whole:

- Follow the suit led if you can.
- Hearts can't be led until one has been played, unless you hold nothing
  else.
- No heart or QS on the first trick, unless you hold nothing else.
- The highest card of the suit led takes the trick and leads the next.

`play` plays the card of the seat whose turn it is; `show` prints the hands,
the scores, the trick on the table and what the seat to play may play.

**The score.** Each heart taken is a point, the QS thirteen. A seat that
takes every heart and the QS shoots the moon: it scores nothing and every
other seat takes 26. `deal` deals the next hand. When a hand ends with a
seat on 100 or more the game is over, and the lowest score wins; a tie for
lowest is a tie.

Cards are rank then suit: 2C, 10H (or TH), JD, QS, KC, AH.

**Rows**, each through the kernel's own `append`: `hearts-open` (the
seats), `hearts-deal` (the hand's number, its seed, which way it passes,
the four hands), `hearts-pass` (a seat's three cards) and `hearts-play` (a
card, and the scores on the hand's last card).

`check` plays every game on the record again from its first row: every deal
what its seed gives, every pass three cards of the seat's own, every card
one the rules allow by the seat whose turn it was, and the scores the
tricks give. The first that isn't is named, and while one doesn't hold,
nothing else is played.

Exit codes, the kernel's: 0 done, or every game holds; 2 refused.

**Where it comes from:** the-table's hearts in the SAFE App Store, over
game-lab's rules. Its legal plays were checked against game-lab's
`legal_plays` in 104,000 states from 2,000 hands, and its scoring on the
same hands, 19 of them moons: all the same. The hands are open for now;
hidden hands wait on a way to deal a seat cards only it can read.

**Never:** shuffles without the record's seed, plays a card the rules don't
allow, reads the key, or writes the record except through the kernel.
