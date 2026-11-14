<!-- willow-addon
section: Play
line: Crazy Eights on the record, hands open and the deck seeded by the record's tip: every card, draw and pass held to the rules.
source: new
added: 2026-11-14
version: 0.1.0
writes: record
network: none
role: tools
-->
# crazy-eights

A hand of Crazy Eights for four seats, played face up, where nobody
shuffles: the record's tip deals it.

    python adapters/stdlib/crazy-eights/crazy_eights.py --box DIR new
    python adapters/stdlib/crazy-eights/crazy_eights.py --box DIR show
    python adapters/stdlib/crazy-eights/crazy_eights.py --box DIR play CARD [SUIT]
    python adapters/stdlib/crazy-eights/crazy_eights.py --box DIR draw
    python adapters/stdlib/crazy-eights/crazy_eights.py --box DIR pass
    python adapters/stdlib/crazy-eights/crazy_eights.py --box DIR check

**The deal.** North, east, south and west, five cards each. The deck is
shuffled from willow's seeded stream (sha256-stream v1, the one dice uses),
seeded by the hash of the row before the deal; one card is turned up to
start the pile and the rest is the stock. The hands are open: the deal row
holds every seat's cards and the stock in the order it is drawn.

**A turn**, north first, then round to the left:

- Play a card of the suit to follow, or of the top card's rank.
- An 8 is wild, and names the suit to follow: `play 8H S`.
- With nothing to play, `draw` one card from the stock, and go again.
- With nothing to play and no stock, `pass`.

The first seat to play its last card wins the hand. Four passes in a row
with no stock and the hand is stalled: nobody wins. `show` prints the
hands, the pile, the suit to follow and what the seat to play may do.

Cards are rank then suit: 2C, 10H (or TH), JD, QS, KC, AH.

**Rows**, each through the kernel's own `append`: `crazy-eights-deal` (the
seed, the hands, the card turned up, the stock), `crazy-eights-play` (a card,
and the suit an 8 names), `crazy-eights-draw` (the card drawn) and
`crazy-eights-pass`. Each names how the hand stands after it.

`check` plays every hand on the record again from its deal: every deal what
its seed gives, every card one the rules allow by the seat whose turn it
was, every draw the card on top of the stock and only when nothing could be
played, every pass one the seat had to make, and every ending the one the
cards give. The first that isn't is named, and while one doesn't hold,
nothing else is played.

Exit codes, the kernel's: 0 done, or every hand holds; 2 refused.

**Where it comes from:** the-table's crazy eights in the SAFE App Store,
over game-lab's rules, with the-table's turn: one card drawn at a time,
each its own row. Its legal cards were checked against game-lab's
`legal_cards` in 159,776 states from 3,000 hands, all the same. The hands
are open for now; hidden hands wait on a way to deal a seat cards only it
can read.

**Never:** shuffles without the record's seed, plays a card the rules don't
allow, reads the key, or writes the record except through the kernel.
