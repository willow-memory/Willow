<!-- willow-addon
section: Your own words
line: Word forms for 20+ languages, so "häuser" finds "haus" and "книги" finds "книга".
source: new
added: 2026-10-29
needs: snowballstemmer; BSD-3-Clause
floor: snowballstemmer 2.0.0
writes: nothing
network: none
tags: needs-install, offline, read-only, words
-->
# stems

The kernel's own stem knows a few English endings, and only for words of
plain ASCII letters: "owes" finds "owe", but "häuser" isn't "haus" and
"книги" isn't "книга". This reads a question's words through Snowball's
stemmer for your language, the way your files write them.

    pip install -r adapters/deps/stems/requirements.txt
    python adapters/deps/stems/stems.py --box DIR --lang german "häuser am see"
    read häuser as haus: 2 passages hold it
    ask:  haus am see

**How a word is read.** A word of your question that no file holds is cut to
its stem, and so is every word of your files; it's read as the form of that
stem the most passages hold, a tie going to the first in sorted order. A
word your files hold as typed, or that your words list reads, is left alone.
`--lang` is english unless you say: Snowball has some thirty, from arabic,
danish and dutch to swedish, tamil and turkish; a name it doesn't have is
refused.

**It never asks for you.** The question as read is printed, for you to ask.

**Can't:** read an irregular form ("paid" isn't "pay", "went" isn't "go"):
that's your [words list](../../../docs/how-it-works.md)'s job. A stemmer
cuts by rules, so now and then two different words share a stem; the
reading is printed, never asked, so you see it first.

On willow's four demo folders, of the 116 quoted lines in their STRIP.md
files, english by default, four of Bernadette's are read differently, and
none of the others. "what did the jeweler say", which her STRIP.md missed on
a spelling, is read as "what did the jewellers say", and serves the
jeweller's reply. "dermatoligist referal letter" reads "referal" as
"reference", which is wrong: she meant "referral", and a typo is
[typos](../../stdlib/typos/)'s to read. That is why a reading is printed,
never asked.

**Without snowballstemmer** it refuses and names the install: exit 2, never a
quiet skip.

**Uses:** `chunks`, `words`, `toks`, `held_by`, `read`, `config`,
`read_words`, and the kernel's exit codes: 0 every word is held, or a reading
is offered; 42 a word no file holds in any form; 2 refused.

**Never:** writes anything, not even the record, or goes online.
