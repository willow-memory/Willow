<!-- willow-addon
section: Keeping track
line: Approved question-and-answer pairs become cards, scheduled by spaced repetition.
source: box
added: 2026-11-01
writes: record
network: none
-->
# flashcards

Approved question-and-answer pairs become cards, scheduled by spaced repetition.

```
python adapters/stdlib/flashcards/flashcards.py --box DIR due [--all] [--now TS]
python adapters/stdlib/flashcards/flashcards.py --box DIR show ID [--now TS]
python adapters/stdlib/flashcards/flashcards.py --box DIR review ID GRADE [--now TS]
python adapters/stdlib/flashcards/flashcards.py --box DIR check

4f0c2a91d3  sun hours  new
1 cards; 1 due

reviewed 4f0c2a91d3 good: next in 3 days, 2026-11-04T09:00:00Z
```

**Cards come only from your seals.** A card is an approval you sealed, still
the bytes that were sealed (a broken one is counted, never studied). The
back is the answer you approved. The front is the words of its file name,
because the record keeps no question words, only their hash: name a proposal for
the question ("why runs a and b diverged", in dashes) and that is what you
are asked. A name with no letters
in it (a session digest, 0-15) asks nothing, so the front is its whole path.

**A review is a record row.** `review` writes one `review` row through the
kernel's own `append`: the card, your grade (1 again, 2 hard, 3 good, 4
easy, or the word), and the interval and due date it produced. Nothing else
is stored. Every card's state is replayed from its review rows in order, so
`--now` fixes "today" for a test and the same record gives the same
schedule on every machine. `check` replays them all and names the first row
that doesn't match its grades, or a review of a card not sealed before it.
`due` and the others refuse to schedule from a record that fails `check`.
A review dated before the card's seal or its last review is refused.

**The algorithm is FSRS-5**, the Free Spaced Repetition Scheduler by Open
Spaced Repetition (MIT licence, copyright 2022 Open Spaced Repetition), written
out here from its published formulas and checked against py-fsrs's numbers;
no code is copied. A card holds stability S and difficulty D.

- Parameters: w = 0.40255, 1.18385, 3.173, 15.69105, 7.1949, 0.5345,
  1.4604, 0.0046, 1.54575, 0.1192, 1.01925, 1.9395, 0.11, 0.29605, 2.2698,
  0.2315, 2.9898, 0.51655, 0.6621: FSRS-5's defaults, **not fitted to your
  reviews**. Desired retention 0.9; forgetting curve R = (1 + (19/81)·t/S)^-0.5.
- First review: S = max(w[grade-1], 0.1), D = clamp(w4 - e^(w5·(grade-1)) + 1, 1, 10).
- Later: t is whole days since the last review. Under a day, S = S·e^(w17·(grade-3+w18)).
  Otherwise a lapse (again) gives S' = min(w11·D^-w12·((S+1)^w13 - 1)·e^((1-R)·w14),
  S/e^(w17·w18)); hard, good or easy gives S' = S·(1 + e^w8·(11-D)·S^-w9·(e^((1-R)·w10) - 1)·penalty),
  with penalty w15 for hard and w16 for easy. D' = w7·D0(easy) + (1-w7)·(D + (10-D)·(-w6·(grade-3))/9), clamped to 1 to 10.
  S is never under 0.1.
- Interval: round(S) whole days at 0.9 retention, at least 1, at most 36500.
  A new card is due the moment it is sealed.
- Left out: learning steps in minutes, fuzz, and the optimizer. Every
  interval is whole days, so the first "again" comes back in a day.

Exit codes, the kernel's: 0 listed, shown, reviewed, or every review holds;
42 nothing is due; 2 refused (a record that doesn't verify, a card or grade
it can't use, or a review that doesn't hold).

**Uses:** the kernel's `read`, `append`, `sealed`, `standing` and `now`.

**Never:** writes a seal, or anything but a `review` row; schedules from a
review the grades don't give; studies a card whose proposal changed; reads
your key.
