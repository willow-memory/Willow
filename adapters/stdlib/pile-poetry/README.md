<!-- willow-addon
section: Play
line: Verse from the word pairs your own files use most, in your own dialect.
source: new
added: 2026-10-29
writes: nothing
network: none
tags: no-install, offline, read-only, play
-->
# pile-poetry

Verse from the word pairs your own files use most: no word in it that your
files don't have, no two words side by side that your files never put there.

```
python adapters/stdlib/pile-poetry/pile_poetry.py --box DIR [--seed TEXT] [--lines N]

Bees eggs yes brood fr bees eggs yes
Young chang grand
...
```

(That first line is Odile's hive log, on willow's demo folder.)

Your files are read line by line, and the pairs of words that sit side by side
more than once are counted: "tomatoes want", "want six", "six hours". A poem is
walked along those pairs, each next word drawn with the weight of how often
your files put it there. Every draw is made by willow's seeded stream (the one
[tarot](../tarot/) deals from) from the seed and a counter, so the same
folder, seed and line count give the same poem on any machine, and it can be
made again to check. The seed is "poem" unless `--seed` says; `--lines` is 8
unless it says (1 to 40), set in stanzas of four.

**What counts as a pair.** Two words next to each other on one line, as the
kernel reads words (lower case, punctuation gone), seen at least twice across
your files. A word with a digit in it is left out, so a date or an id never
gets in, and the words round it meet. A pair never crosses the end of a line or
of a file. A line that shouts throughout (a calendar's DTSTART) or opens as a
field ("From:", "UID=") is a machine's and is not read. Pairs are counted from
the folder alone: no list of the world's words, no model.

A line of verse starts at a word that begins a pair, and goes on up to eight
words, stopping early where a word has no pair to follow. With fewer than
twelve different pairs seen twice there is too little to write from, and it
says so (exit 42) instead of padding from anywhere else.

It only reads. Exit codes, the kernel's: 0 a poem; 42 too little repeated to
write from; 2 refused.

**Uses:** tarot's `Stream` (the seeded stream), and the kernel's `chunks`,
`words` and `config`.

**Never:** changes your files; writes anything; reads the key; uses a clock or
a random source.
