<!-- willow-addon
section: Play
line: A seeded tarot draw on the record, replayable by anyone with the seed.
source: new
added: 2026-10-27
writes: record
network: none
-->
# tarot

A tarot spread dealt on the record: no one picks the cards, anyone can deal
them again, and what they mean stays yours.

```
python adapters/stdlib/tarot/tarot.py --box DIR draw [N] [--now TS]
1. The Moon, reversed
2. Six of Cups
3. The Tower
(row 9; replayable from its seed by anyone)

python adapters/stdlib/tarot/tarot.py --box DIR check
2 draws on the record; every one holds.
```

**No one picks the cards.** The seed is the record's tip, the hash of the
row before: fixed the moment that row was written, chosen by no one. The
cards come from willow-bot's seeded stream (sha256-stream/v1), dealt
without replacement by rejection, a coin from the same stream turning each,
so the same seed deals the same spread on any machine — which is the whole
of the trick, and the reason a reading can be shown to a friend who can
deal it herself and find the same cards.

**`check` replays every draw.** Each `draw` row holds its seed, its count
and its cards; `check` deals each one again from its row — the seed must be
the hash of the row before it, the cards must be what that seed deals — and
every draw holds, or the first that doesn't is named. A draw can't be
changed after the fact. As [dice](../dice/) rolls, so this deals.

**What the cards mean is yours.** The deck is the standard 78, named in
full — the 22 majors, Ace to King in Wands, Cups, Swords and Pentacles —
and this says nothing about any of them: it deals honestly, writes the
`draw` row through the kernel's own `append`, never a seal, and leaves the
reading to the person holding the cards.

It never changes your files and never reads them either: the deck is the
deck whatever the folder holds. Exit codes, the kernel's: 0 dealt, or every
draw holds; 2 refused: a count the deck hasn't (1 to 78), a record that
doesn't verify, or a draw that doesn't hold.

**Uses:** the kernel's `read`, `append`, `canon`, `h256` and `GENESIS`;
willow-bot's seeded stream, as [dice](../dice/) throws it.

**Never:** changes or reads your files; writes a seal; picks a card by
hand; says what a card means.
