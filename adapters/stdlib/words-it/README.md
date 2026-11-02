<!-- willow-addon
section: Your own words
line: Italian common words ("il", "e").
source: new
added: 2026-10-24
writes: record
network: none
tags: italian
-->
# words-it

Questions in Italian, matched on the words that say something. The kernel
leaves English's common words out of a match ("the", "when", "is"). A
Italian question keeps all of its words, so the common ones count toward a
match, and nearly every Italian passage holds them.

    python adapters/stdlib/words-it/words_it.py bite --box DIR "Quando è l'appuntamento dal dentista?"

That asks the kernel "appuntamento dentista". Everything else is the kernel's own `bite`:
the record row, the passages served, the exit code. The record still keeps
no words, only the question's fingerprint.

`list` prints the 148 words it leaves out: articles, conjunctions,
prepositions, pronouns, the verbs "be" and "have" and the modals, question
words, yes and no. That's what the kernel's own list covers for English.

Letters typed as a letter plus an accent mark are joined first, so
"perché" matches however a keyboard sent it. "l'", "dell'" and the other joined articles are left out as their own words.

**What it doesn't do:** match word forms. "Termine" won't find "Termin"
here; the kernel's endings are English's. A words list (see
[starter-words](../starter-words/)) can say `termine = termin`.

**Uses:** the kernel's `words` and `bite`.

**Never:** changes the kernel's list, or what a question in English matches.
