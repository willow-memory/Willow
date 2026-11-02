<!-- willow-addon
section: Your own words
line: Polish common words ('i', 'w').
source: new
added: 2026-10-27
writes: record
network: none
tags: polish
-->
# words-pl

Questions in Polish, matched on the words that say something. The kernel
leaves English's common words out of a match ("the", "when", "is"). A
Polish question keeps all of its words, so the common ones count toward a
match, and nearly every Polish passage holds them.

    python adapters/stdlib/words-pl/words_pl.py bite --box DIR "Kiedy jest termin u dentysty?"

That asks the kernel "termin dentysty". Everything else is the kernel's own
`bite`: the record row, the passages served, the exit code. The record
still keeps no words, only the question's fingerprint.

`list` prints the 157 words it leaves out: conjunctions, prepositions,
pronouns and their cases, demonstratives, the verbs "be" and "have" and the
modals, question words, yes and no. That's what the kernel's own list
covers for English, with the cases Polish declines its pronouns through.

Letters typed as a letter plus an accent mark are joined first, so "się"
matches however a keyboard sent it. "i", "to" and "a" are English words
too: in a Polish question they're left out.

**What it doesn't do:** match word forms. "Terminy" won't find "termin"
here; the kernel's endings are English's, and Polish declines far past
them. A words list (see [starter-words](../starter-words/)) can say
`terminy = termin`.

**Uses:** the kernel's `words` and `bite`.

**Never:** changes the kernel's list, or what a question in English matches.
