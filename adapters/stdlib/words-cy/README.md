<!-- willow-addon
section: Your own words
line: Welsh common words ("a", "y", "yn").
source: new
added: 2026-10-29
writes: record
network: none
tags: welsh
-->
# words-cy

Questions in Welsh, matched on the words that say something. The kernel
leaves English's common words out of a match ("the", "when", "is"). A
Welsh question keeps all of its words, so the common ones count toward a
match, and nearly every Welsh passage holds them.

    python adapters/stdlib/words-cy/words_cy.py bite --box DIR "Pryd mae fy apwyntiad gyda'r deintydd?"

That asks the kernel "apwyntiad deintydd". Everything else is the kernel's own `bite`:
the record row, the passages served, the exit code. The record still keeps
no words, only the question's fingerprint.

`list` prints the 92 words it leaves out: conjunctions, prepositions,
particles, pronouns, the verb "be", question words, yes and no. That's what
the kernel's own list covers for English.

Letters typed as a letter plus an accent mark (â, ŵ, ŷ) are joined first, so a word matches however a keyboard sent it. The apostrophe splits "gyda'r" as the kernel does; the "r" left over is kept out as a common word.

**What it doesn't do:** match word forms. Welsh mutates the start of a word ("deintydd", "ddeintydd"), and the kernel matches the letters as written. A words list can say `ddeintydd = deintydd`.

**Uses:** the kernel's `words` and `bite`.

**Never:** changes the kernel's list, or what a question in English matches.
