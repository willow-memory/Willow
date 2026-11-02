<!-- willow-addon
section: Finding things
line: Forgives misspellings in questions.
source: new
added: 2026-10-25
writes: nothing
network: none
-->
# typos

A question with a slip in it, read the way your files spell it.

    python adapters/stdlib/typos/typos.py --box DIR "what did the jeweler say"
    read jeweler as jeweller: 4 passages hold it
    ask:  what did the jeweller say

**How a word is read.** Only a word that no file of yours holds, in any form
the kernel looks for, is tried. It's tried at every spelling one edit inside
it: a letter dropped, added, changed, or two side by side swapped, the first
and last letters kept as you typed them. The spelling the most passages hold
wins; a tie goes to the first alphabetically. A word your words list already
reads as one of yours is left alone.

**It never asks for you.** It prints the question as it would be read, for
you to ask with `kernel.py bite` (or any way in). So a word you spelt right,
that your files just don't use, can't quietly become an answer to something
you didn't ask: "how much do I owe dev", when your files say Dev "lent",
comes back as `no file has owe, nor anything one edit from it`, with nothing
offered. It reads only, and writes nothing, not even the record.

**What it leaves alone, and why.**

| Left as typed | Why |
|---|---|
| a word under six letters | it has too many neighbours that are other words: "gave" and "give", "spend" and "send" |
| a change to the first or last letter | a slip lands inside a word; on the demo questions an edit at either end read "gave" as "have", "along" as "long" |
| a letter outside a to z | an accent is the [accents](../accents/) add-on's to read |

Those limits were measured on the sixty questions Hollis, Teodora and
Bernadette ask in `demo/`. With them, it reads the three real misspellings
("jeweler", "dermatoligist", "referal") and one word that isn't a slip,
"forget" as "forgot", a change of tense.

Exit codes, the kernel's: 0 every word is held, or a spelling is offered; 42
a word no file holds and nothing one edit away does; 2 refused.

**Where it comes from:** [willow-bot's one script](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/pile.py)
(`Cached.repair`, its rung 2), whose `edits1` this is word for word. The one
script repairs the bite and asks; here the reading is offered and the person
asks, since a kernel answer is only ever to the words given.

The idea was planned with rapidfuzz; one edit needs nothing installed.
