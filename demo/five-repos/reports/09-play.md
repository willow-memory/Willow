# Report 4: play on the record, 2026-11-03

A fresh box over the five repos, `play-box`, and five games on it. Every
move is a row, every draw is seeded by the row before it so nobody picks
it, and each game's `check` replays the record and says whether it holds.
The chain verifies: 15 rows, nothing sealed, nothing approved.

## daily-word: a five-letter word from the five repos' own words

Five guesses, one left, the word not found. The clue pattern after five:

| guess | result |
|---|---|
| crane | `.y.yG` |
| model | `...y.` |
| chain | `.G..y` |
| seals | `.y...` |
| proof | `.y...` |

So: `h` second, `e` last, `r` and `n` somewhere else. Two guesses were
refused at no cost, "your folder doesn't hold 'there'" and the same for
"where": the game's vocabulary is the folder's words less the kernel's
common ones, and both are common. The word is the same for anyone asking
this folder today, so someone on another session can take the last guess.

## quiz: a passage with a word missing

- `Willow/adapters/stdlib/opml/opml.py:307`: `return inner == outer or
  outer in inner._______` Answered `parents`: right.
- `Willow/adapters/stdlib/car/car.py:81`: "the latest date it ____ before
  any due". Answered `kernel`: not it, the word is `says`.

1 right of 2 on this record. The quiz cuts the puzzle, keeps the answer's
hash, and the score lives on the record, so it can't be argued with.

## tarot, dice, life, catgrid

- tarot, three cards: Two of Cups; Two of Pentacles, reversed; Three of
  Wands, reversed. Row 10, replayable from its seed by anyone.
- dice, 4d6: 3 + 1 + 4 + 6 = 14. Row 11.
- life, seeded "five repos", 12 wide, 30 generations: 60 alive and still
  running. Row 13.
- catgrid, seeded "five repos", a 5×5 board in five colour regions with a
  unique answer. Solved by hand (A4, B1, C3, E2, and the fifth cat on row D, column 5): won with 3 hearts
  left, 5 of 5 cats placed. Rows 12 and 14.

Every check: "every one holds". The record's history is fifteen plain
sentences, each saying which add-on wrote the row and never the words.

## What the games say about the box

The games are the proof layer in miniature. A draw nobody picked, a
score nobody can edit, a board that any machine deals again from the
seed: the same hash chain that holds the audit findings holds a tarot
spread, and `check` is `verify` with a game's rules on top.

## Files

`play-box/` (the record), and the games' rows in it.
