<!-- willow-addon
section: Play
line: A quiz from your own files: a passage with a word missing, and you fill it in.
source: new
added: 2026-10-27
writes: record
network: none
tags: no-install, offline, records, play
-->
# quiz

A passage of your own life with a word missing, for you to fill in from
memory; the record cuts the puzzle, holds the answer's hash, and keeps your
score.

```
python adapters/stdlib/quiz/quiz.py --box DIR ask [--now TS]
hives/2021.txt:4
Ferris came by for the ______. Two supers on the strong hive.
(row 13; answer with: quiz.py --box DIR answer WORD)

python adapters/stdlib/quiz/quiz.py --box DIR answer frames [--now TS]
Right: the word is frames.
7 right of 11 answered on this record.
```

**No one picks the puzzle.** The passage and the word are drawn by the
record's tip — the hash of the row before — through willow-bot's seeded
stream (sha256-stream/v1), so the same box asks everyone the same
question, and the next `ask` cuts a new one only after an answer moves the
tip. One quiz is open at a time; asked again, it shows again, byte for byte.

**The record can't tell you the answer.** The quiz row holds where the
passage is and the SHA-256 of the word, never the word; `answer` takes one
guess, reads the word back from your folder, holds it to the committed
hash, and writes the outcome. A folder that changed under the quiz is said,
and no one is marked wrong. The score at the foot is the record's own count
of its answer rows, so it survives any session.

**What can be quizzed is your own writing**: a passage of eight words or
more, no line of it opening as markup or a field, none shouting throughout —
an email's font-family and a calendar's DTSTART are nobody's memory. The
blank is a word of four letters or more, no digit, not one of the kernel's
common words, standing exactly once in its passage, shown as underscores of
its length. On willow's demo folders the puzzles come out as lived moments:
Loretta asking Odile "is it time for the piano _____?", Hollis billing "The
Blue ______", Bernadette's bowls-club "Committee _______ Tuesday 9 August".

It writes the record only through the kernel's own `append` — a `quiz` row
and an `answer` row, never a seal — and never changes your files. Exit
codes, the kernel's: 0 asked, shown again, or answered, right or not; 42
nothing to quiz, or no quiz open; 2 refused, a record that doesn't verify
among the refusals.

**Uses:** the kernel's `read`, `append`, `chunks`, `words`, `h256`,
`FUNCTION`, `GENESIS` and `config`; willow-bot's seeded stream, as
[dice](../dice/) throws it.

**Never:** changes your files; writes a seal; stores an answer; picks a
puzzle by hand; marks you wrong on a folder that changed.
