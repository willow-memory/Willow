<!-- willow-addon
section: Your own words
line: French common words ("le", "et").
source: new
added: 2026-10-24
writes: record
network: none
tags: french
-->
# words-fr

Questions in French, matched on the words that say something. The kernel
leaves English's common words out of a match ("the", "when", "is"). A
French question keeps all of its words, so the common ones count toward a
match, and nearly every French passage holds them.

    python adapters/stdlib/words-fr/words_fr.py bite --box DIR "Quand est le rendez-vous chez le dentiste ?"

That asks the kernel "rendez dentiste". Everything else is the kernel's own `bite`:
the record row, the passages served, the exit code. The record still keeps
no words, only the question's fingerprint.

`list` prints the 116 words it leaves out: articles, conjunctions,
prepositions, pronouns, the verbs "be" and "have" and the modals, question
words, yes and no. That's what the kernel's own list covers for English.

Letters typed as a letter plus an accent mark are joined first, so
"où" matches however a keyboard sent it. "or" (now) and "car" (because) are kept: they're English words a French folder may hold too, and a French question rarely needs them.

**What it doesn't do:** match word forms. "Termine" won't find "Termin"
here; the kernel's endings are English's. A words list (see
[starter-words](../starter-words/)) can say `termine = termin`.

**Uses:** the kernel's `words` and `bite`.

**Never:** changes the kernel's list, or what a question in English matches.
