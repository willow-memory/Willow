<!-- willow-addon
section: Your own words
line: Arabic common words ("في", "من", "على").
source: new
added: 2026-10-29
writes: record
network: none
tags: no-install, offline, records, words, arabic
-->
# words-ar

Questions in Arabic, matched on the words that say something. The kernel
leaves English's common words out of a match ("the", "when", "is"). A
Arabic question keeps all of its words, so the common ones count toward a
match, and nearly every Arabic passage holds them.

    python adapters/stdlib/words-ar/words_ar.py bite --box DIR "متى موعدي عند طبيب الأسنان؟"

That asks the kernel "موعدي طبيب الأسنان". Everything else is the kernel's own `bite`:
the record row, the passages served, the exit code. The record still keeps
no words, only the question's fingerprint.

`list` prints the 60 words it leaves out: conjunctions, prepositions,
particles, pronouns, the verb "be", question words, yes and no. That's what
the kernel's own list covers for English.

Short vowel marks and the tatweel stretch are taken out of the question first, since the kernel would split a word at each one. A passage written with them is still split that way by the kernel, so a word with vowel marks in your files is found only by the letters between them. A letter and its separate hamza (أ as ا and a hamza) are joined too.

**What it doesn't do:** match word forms. Arabic joins prefixes and the article to a word ("الأسنان", "للأسنان"), and the kernel matches whole words. A words list can say `للأسنان = الأسنان`.

**Uses:** the kernel's `words` and `bite`.

**Never:** changes the kernel's list, or what a question in English matches.
