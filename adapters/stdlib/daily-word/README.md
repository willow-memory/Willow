<!-- willow-addon
section: Play
line: A five-letter word game drawn from your own files' words: a new word each day, the same for anyone asking the same folder.
source: new
added: 2026-10-27
writes: record
network: none
-->
# daily-word

Each day your folder sets one five-letter word of its own, and you get six
guesses, marked the familiar way and kept on the record.

```
python adapters/stdlib/daily-word/daily_word.py --box DIR guess crane [--now TS]
crane  .y..G
5 guesses left.

python adapters/stdlib/daily-word/daily_word.py --box DIR today [--now TS]
crane  .y..G
frame  .GGGG
flame  GGGGG
Solved in 3. Back tomorrow.
```

**The same box asks everyone the same word.** The day's word is drawn from
the folder's own five-letter words (letters only, the kernel's common words
left out) by the seeded stream, seeded with the day and those words
themselves: two copies of the same folder ask the same word on the same
day, whatever either record holds, so a family can race on the same puzzle.
The word moves with the day and with the folder — Teodora's folder asks
from her invoices and chats, Bernadette's from hers.

**Your folder is the dictionary too.** A guess must be a five-letter word
the folder holds, the same rule the answer keeps; one it doesn't hold is
refused without costing a guess. Marking is G in its place, y elsewhere in
the word, a dot not in it, each letter of the answer spent once, greens
first — the familiar rule for doubled letters.

**The record keeps the honest score, not the secret.** Anyone who holds the
folder can derive the day's word, so the game is played on honour, as a
crossword is; what the record holds is each day's guesses and their marks,
written through the kernel's own `append`, never a seal, and the word is
shown only when the day is done — solved, or six guesses out.

It never changes your files. Exit codes, the kernel's: 0 marked, or the day
shown; 42 the day is done, or the folder has no five-letter words to play;
2 refused, a guess the folder doesn't hold among the refusals.

**Uses:** the kernel's `read`, `append`, `chunks`, `words`, `FUNCTION` and
`config`; willow-bot's seeded stream, as [dice](../dice/) throws it.

**Never:** changes your files; writes a seal; shows the word while the day
is open; spends a guess on a word the folder doesn't hold.
