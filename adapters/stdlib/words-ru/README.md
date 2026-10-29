<!-- willow-addon
section: Your own words
line: Russian common words ("и", "в", "на").
source: new
added: 2026-10-29
writes: record
network: none
tags: no-install, offline, records, words, russian
-->
# words-ru

Questions in Russian, matched on the words that say something. The kernel
leaves English's common words out of a match ("the", "when", "is"). A
Russian question keeps all of its words, so the common ones count toward a
match, and nearly every Russian passage holds them.

    python adapters/stdlib/words-ru/words_ru.py bite --box DIR "Когда у меня приём у стоматолога?"

That asks the kernel "приём стоматолога". Everything else is the kernel's own `bite`:
the record row, the passages served, the exit code. The record still keeps
no words, only the question's fingerprint.

`list` prints the 117 words it leaves out: conjunctions, prepositions, particles, pronouns, the verb "be", question words, yes and no. That's what the kernel's own list covers for English.

Letters typed as a letter plus an accent mark (й as и and a breve) are joined first, so "что" and "й" match however a keyboard sent them. "е" and "ё" stay two letters, as the kernel has them.

**What it doesn't do:** match word forms. Russian is heavily inflected: "стоматолога" won't find "стоматолог" here. A words list (see
[starter-words](../starter-words/)) can say `стоматолога = стоматолог`.

**Uses:** the kernel's `words` and `bite`.

**Never:** changes the kernel's list, or what a question in English matches.
