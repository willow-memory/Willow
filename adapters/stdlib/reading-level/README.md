<!-- willow-addon
section: Finding things
line: How hard a passage reads (sentence length, word length, Flesch), so a teacher can find texts for a class.
source: new
added: 2026-10-27
writes: nothing
network: none
-->
# reading-level

How hard each file of your folder reads, easiest first: its Flesch reading
ease, said in a word, with the two lengths the score is made of, so a
teacher can find texts for a class, or you can see which of your own letters
turned into legalese.

    python adapters/stdlib/reading-level/reading_level.py --box DIR

      97  very easy     7.5 words a sentence  1.21 syllables a word     412 words  stories/frog.md
      54  fairly hard  19.8 words a sentence  1.58 syllables a word    1890 words  letters/bank.md
    too short to score (3 words)  notes/one-liner.md
    2 files scored, 1 too short

**The score is Flesch's**, by the book: 206.835 − 1.015 (words a sentence)
− 84.6 (syllables a word), rounded. 90 or over reads very easy, 80 easy,
70 fairly easy, 60 plain, 50 fairly hard, 30 hard, and under 30 very hard.
A file's score is from all its passages together: one number a teacher can
weigh a whole text by.

**Counted as written.** A sentence ends at `.`, `!` or `?`, or at its
line's end, so a list of notes is read as its items. A word is its letters
("don't" is one word, a bare number is none), and its syllables are counted
by a rule of thumb (runs of vowels, a silent final e taken off), not a
dictionary, so the score is within a point or two of one counted by hand,
not to the decimal.

**Where the number says little, the lengths say more.** Flesch was made
for English prose: on another language, a table or a calendar, the score
means little, and the words-a-sentence and syllables-a-word beside it are
the honest part. A file under 30 words is listed, not scored: too little
text says nothing about how it reads.

On willow's demo folders, Bernadette's WhatsApp chats read very easy (seven
words a sentence) and 69 of her files are too short to score; Odile's
folder, mostly one-line memos, scores 58 files and lists 196 as too short,
each with its count.

It only reads, and the same folder gives the same bytes. Exit codes, the
kernel's: 0 files scored; 42 nothing long enough to score; 2 refused.

**Uses:** the kernel's `chunks` and `config`.

**Never:** changes your files; writes anything, even the record; scores a
file too short to say anything.
