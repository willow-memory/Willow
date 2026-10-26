<!-- willow-addon
section: Your own words
line: A word typed without its accent read as your files write it, and the words-list lines that make it last.
source: new
added: 2026-10-25
writes: nothing
network: none
tags: no-install, offline, read-only, words
-->
# accents

To the kernel a word is its letters, so "zoe" isn't "zoë" and "branza" isn't
"brânză". This reads a question's words the way your files write them.

    python adapters/stdlib/accents/accents.py --box DIR "where is zoe"
    read zoe as zoë: 2 passages hold it
    ask:  where is zoë

    python adapters/stdlib/accents/accents.py words --box DIR
    cafe = café
    zoe = zoë

**How a word is read.** A word of your question that no file holds is
compared with your files' words with every accent taken off both sides: é is
e, ø is o, ß is ss, æ is ae. It's read as the way the most passages write it,
a tie going to the first in sorted order. Both ways round: "cafe" finds
"café", and "café" finds "cafe". A word you typed that your files hold, as
typed, is left alone, as is one your words list already reads.

**It never asks for you.** The question as read is printed, for you to ask.

**`words` is the lasting fix.** One [words-list](../../../docs/how-it-works.md)
line for each word of your files that has an accent, the word without it on
the left. Add them to your words list and the kernel reads each one that way
every time, by itself. The lines go to standard output, for you to read before
you keep them; nothing is written.

On willow's demo folders, `words` gives 51 lines for Teodora, whose
grandmother's recipes are in Romanian (`branza = brânză`, `bors = borș`), one
each for Odile and Bernadette, and none for Hollis. None of the sixty demo
questions is read differently: no one in them typed a word their files only
have with an accent. Bernadette's "did i promise siobhan anything" looked like
one, and wasn't (her STRIP.md says why).

It reads only, and writes nothing, not even the record. Exit codes, the
kernel's: 0 every word is held, or a reading is offered (`words`: always);
42 a word no file holds, accent or not; 2 refused.

Spelling slips are [typos](../typos/)'s; an accent is this one's, so the two
never read the same word.
