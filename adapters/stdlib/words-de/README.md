<!-- willow-addon
section: Your own words
line: German common words, so questions aren't matched on "der" and "und".
source: new
added: 2026-10-24
writes: record
network: none
tags: no-install, offline, records, words, german
-->
# words-de

Questions in German, matched on the words that say something. The kernel
leaves English's common words out of a match ("the", "when", "is"). A
German question keeps all of its words, so the common ones count toward a
match, and nearly every German passage holds them.

    python adapters/stdlib/words-de/words_de.py bite --box DIR "Wann ist der Termin beim Zahnarzt?"

That asks the kernel "termin zahnarzt". Everything else is the kernel's own `bite`:
the record row, the passages served, the exit code. The record still keeps
no words, only the question's fingerprint.

`list` prints the 160 words it leaves out: articles, conjunctions,
prepositions, pronouns, the verbs "be" and "have" and the modals, question
words, yes and no. That's what the kernel's own list covers for English.

Letters typed as a letter plus an accent mark are joined first, so
"für" matches however a keyboard sent it. "die" and "will" are English words too: in a German question they're left out.

**What it doesn't do:** match word forms. "Termine" won't find "Termin"
here; the kernel's endings are English's. A words list (see
[starter-words](../starter-words/)) can say `termine = termin`.

**Uses:** the kernel's `words` and `bite`.

**Never:** changes the kernel's list, or what a question in English matches.
