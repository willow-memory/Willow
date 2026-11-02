<!-- willow-addon
section: Your own words
line: Turkish common words ("ve", "bir").
source: new
added: 2026-10-29
writes: record
network: none
tags: turkish
-->
# words-tr

Questions in Turkish, matched on the words that say something. The kernel
leaves English's common words out of a match ("the", "when", "is"). A
Turkish question keeps all of its words, so the common ones count toward a
match, and nearly every Turkish passage holds them.

    python adapters/stdlib/words-tr/words_tr.py bite --box DIR "Benim diş hekimi randevum ne zaman?"

That asks the kernel "diş hekimi randevum zaman". Everything else is the kernel's own `bite`:
the record row, the passages served, the exit code. The record still keeps
no words, only the question's fingerprint.

`list` prints the 78 words it leaves out: conjunctions, postpositions, particles, pronouns, question words. That's what the kernel's own list covers for English.

A capital dotted İ is read as i first, since lowercased it would split a
word in two ("İstanbul" would be "i" and "stanbul"). The kernel reads a
passage that spells it that way the split way, and nothing here changes how a
passage is read, so such a word in your files is found only as written with a
plain i. Letters typed as a letter plus an accent mark are joined first.

**What it doesn't do:** match word forms. Turkish adds endings to a word: "randevum" won't find "randevusu" here. A words list (see
[starter-words](../starter-words/)) can say `randevusu = randevum`.

**Uses:** the kernel's `words` and `bite`.

**Never:** changes the kernel's list, or what a question in English matches.
