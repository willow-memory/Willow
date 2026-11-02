<!-- willow-addon
section: Play
line: Readings written by a Tracery grammar, every branch picked by the seeded stream, so each one can be replayed.
source: new
added: 2026-10-29
writes: nothing
network: none
-->
# oracle-text

Readings written from a grammar, where nothing is random: every branch is
picked by the seeded stream, so any reading can be made again, by anyone, and
come out the same.

```
python adapters/stdlib/oracle-text/oracle_text.py --seed TEXT [--grammar FILE] [--count N] [--origin NAME]

An owl will cross your path today, carrying a letter.
```

A grammar is a JSON object of symbols, each a string or a list of strings to
choose from, as [Tracery](https://tracery.io/) writes them:

```
{"origin": ["#animal.a.capitalize# will cross your path, #mood#."],
 "animal": ["owl", "heron", "otter"],
 "mood": ["and say nothing", "carrying #thing.s#"],
 "thing": ["stone", "apple"]}
```

`#name#` is replaced by one of that symbol's rules, expanded in turn. The
modifiers `.a` (an owl, a heron), `.s` (plural), `.ed` (past tense),
`.capitalize`, `.capitalizeAll` and `.allCaps` follow a name and chain
(`#name.s.capitalize#`). `[who:#animal#]` sets a name for the rest of the
reading, so `#who#` says the same animal again. Text that is none of those is
kept as written. With no `--grammar`, a small grammar of its own is used.

**Every branch is picked by willow's seeded stream** (sha256-stream version 1, the
one [tarot](../tarot/) deals from): SHA-256 over the seed and a counter, and
`below(k)` by rejection. The reading numbered i is made from the seed
`TEXT:oracle:i` alone, so the same seed, grammar and number give the same
reading on any machine, and a reading can be made again to check it. Nothing is
predicted: it is a toy that can't be rigged. `--count N` prints N readings, one
to a line; `--origin` names the symbol to start from.

It reads the grammar file if you name one, and writes nothing. Exit codes, the
kernel's: 0 readings printed; 2 refused: a bad command line, a grammar that
isn't a JSON object of strings and lists of strings, a symbol or modifier it
doesn't have, or rules that expand without end.

**Uses:** tarot's `Stream` (the seeded stream), and the kernel's exit codes.

**Never:** reads the key; writes anything; uses a clock or a random source.
