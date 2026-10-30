<!-- willow-addon
section: Your own words
line: Klingon common words ("'ej", "nuq").
source: new
added: 2026-10-30
writes: record
network: none
tags: no-install, offline, records, words, klingon
-->
# words-tlh

Questions in Klingon, matched on the words that say something. The kernel
leaves English's common words out of a match ("the", "when", "is"). A
Klingon question keeps all of its words, so the common ones count toward a
match, and nearly every Klingon passage holds them.

    python adapters/stdlib/words-tlh/words_tlh.py bite --box DIR "nuqDaq 'oH yIH'e'?"

That asks the kernel "yih" (where is the tribble?). Everything else is the
kernel's own `bite`: the record row, the passages served, the exit code. The
record still keeps no words, only the question's fingerprint.

`list` prints the 37 forms it leaves out, the kernel's reading of 27 words:
the pronouns (`jIH`, `SoH`, `ghaH`, `'oH`, `maH`, `tlhIH`, `chaH`, `bIH`,
which also stand for "be", and `'e'`), the conjunctions (`je`, `joq`,
`ghap`, `'ej`, `qoj`, `pagh`, `'ach` and its short form `'a`), the question
words (`nuq`, `'Iv`, `nuqDaq`, `ghorgh`, `qatlh`, `chay'`, `'ar`), and yes
and no (`HIja'`, `HISlaH`, `ghobe'`). That's what the kernel's own list
covers for English.

## Where the words come from

A word is on the list only where two of these agree on it, spelling and
meaning. Each is kept here by address and SHA-256, never its text.

| Source | Pinned at | SHA-256 of the bytes fetched 2026-10-30 | Gives |
|---|---|---|---|
| boQwI' dictionary data, github.com/De7vID/klingon-assistant-data (Apache-2.0) | commit `0f6018ece74a3f5a4b61ddcd4c7a28b010bb7fd0` | each of its 30 `mem-*` files has its own; the commit pins them | all 27, with their part of speech |
| Wikipedia, "Klingon grammar", raw wikitext | revision `1333803070` | `29f7df80f9b424d3ce8141046f234badc081492cf17d4a074c372404d311da59` | the pronouns, `'e'`, the conjunctions, yes and no |
| Wikibooks, "Klingon/Grammar/Questions", raw wikitext | revision `4446920` | `63bc19c573ec9045bf908051c7d9171150120a6b4f76f9b83a51a3df5605802d` | the question words |

**Where they disagree, or one stands alone:**

- Wikibooks spells "how" `chay`, boQwI' `chay'`. The kernel reads both as
  `chay`, so the list holds it; `chayʼ`, the modifier-letter spelling, rests
  on boQwI' alone.
- `net` ("that"), `'arlogh` ("how many times"), `luq` and `lu'` ("yes,
  okay") are in boQwI' only, so they are not on the list.
- The Klingon Language Institute's page on questions agrees with six of the
  seven question words (`'ar` isn't on it), but its bytes change at every
  fetch (its fonts are listed in a new order each time), so it can't be held
  by a hash and isn't counted.
- *The Klingon Dictionary* (Okrand; Wikipedia cites its second edition,
  1992) is the source the others cite. It is a book in print, so it is
  named here, never fetched or copied.

## What it doesn't do

**Tell q from Q.** Klingon writes some letters in capitals and they are
different letters; the kernel lowercases every word, in the question and in
your files alike. So leaving out `qatlh` ("why") also leaves out `Qatlh`
("be difficult"), `nuq` ("what") takes `nuQ` ("annoy"), `qoj` ("or") takes
`Qoj` ("make war"), and `joq` ("or") takes `joQ` ("rib").

**Keep a word that sounds the same.** `jIH` is also "viewing screen" and
"monitor", `pagh` "nothing" and "zero", `qoj` "cliff", `joq` "flap", `'Iv`
"altitude". A question about the viewing screen loses the screen; ask in
English, or name it another way.

**Read an apostrophe one way.** The apostrophe is a letter in Klingon. The
kernel splits a word at a plain ' or a curly ’, so `Qapla'` is read as
`qapla` and `yIH'e'` as `yih` and `e`. The modifier letter ʼ, which
Wikipedia types, is a letter to the kernel, so `yIHʼeʼ` stays one word and
finds only a file that spells it the same way. The list holds each word
typed both ways; nothing here changes how a passage is read.

**Match word forms.** Klingon builds a word with prefixes and suffixes:
`yIH` won't find `yIHmey`. A words list (see
[starter-words](../starter-words/)) can say `yIHmey = yIH`.

**Uses:** the kernel's `words` and `bite`.

**Never:** changes the kernel's list, or what a question in English matches.
