<!-- willow-addon
section: Your own words
line: Spanish common words ("el", "y").
source: new
added: 2026-10-24
writes: record
network: none
tags: no-install, offline, records, words, spanish
-->
# words-es

Questions in Spanish, matched on the words that say something. The kernel
leaves English's common words out of a match ("the", "when", "is"). A
Spanish question keeps all of its words, so the common ones count toward a
match, and nearly every Spanish passage holds them.

    python adapters/stdlib/words-es/words_es.py bite --box DIR "¿Cuándo es la cita con el dentista?"

That asks the kernel "cita dentista". Everything else is the kernel's own `bite`:
the record row, the passages served, the exit code. The record still keeps
no words, only the question's fingerprint.

`list` prints the 125 words it leaves out: articles, conjunctions,
prepositions, pronouns, the verbs "be" and "have" and the modals, question
words, yes and no. That's what the kernel's own list covers for English.

Letters typed as a letter plus an accent mark are joined first, so
"cuándo" matches however a keyboard sent it. "son" (they are) is an English word too: in a Spanish question it's left out.

**What it doesn't do:** match word forms. "Termine" won't find "Termin"
here; the kernel's endings are English's. A words list (see
[starter-words](../starter-words/)) can say `termine = termin`.

**Uses:** the kernel's `words` and `bite`.

**Never:** changes the kernel's list, or what a question in English matches.
