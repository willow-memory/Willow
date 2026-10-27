<!-- willow-addon
section: Your own words
line: Swedish common words ('och', 'att').
source: new
added: 2026-10-27
writes: record
network: none
tags: no-install, offline, records, words, swedish
-->
# words-sv

Questions in Swedish, matched on the words that say something. The kernel
leaves English's common words out of a match ("the", "when", "is"). A
Swedish question keeps all of its words, so the common ones count toward a
match, and nearly every Swedish passage holds them.

    python adapters/stdlib/words-sv/words_sv.py bite --box DIR "När är tiden hos tandläkaren?"

That asks the kernel "tiden tandläkaren". Everything else is the kernel's
own `bite`: the record row, the passages served, the exit code. The record
still keeps no words, only the question's fingerprint.

`list` prints the 134 words it leaves out: articles, conjunctions,
prepositions, pronouns, the verbs "be", "have" and "become" and the modals,
question words, yes and no. That's what the kernel's own list covers for
English.

Letters typed as a letter plus an accent mark are joined first, so "för"
matches however a keyboard sent it. "men" and "all" are English words too:
in a Swedish question they're left out, and so is "man", which Swedish uses
as English uses "one" — a question about someone's husband should name him.

**What it doesn't do:** match word forms. "Tider" won't find "tiden" here;
the kernel's endings are English's. A words list (see
[starter-words](../starter-words/)) can say `tider = tiden`.

**Uses:** the kernel's `words` and `bite`.

**Never:** changes the kernel's list, or what a question in English matches.
