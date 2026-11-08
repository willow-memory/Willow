# Use the kernel alone

The end of the [tour](../tour.md) points it at a folder of your own, with
`init` and `bite`. Your folder is only ever read, and the key stays outside
the record folder. This page is the rest of the cycle on your own files.

**Check the record.** Every step is a row on a hash chain; `verify` checks
every row, every approval and every No:

```
$ python kernel.py verify --box my-record
```

**Your own words.** A words list reads your word as the words your files
use, one line a word (`owes = invoice, outstanding`), kept like the key:
readable only by you, outside the record folder. Name it at `init` with
`--words FILE`; the tour's [Teach it her words](../tour.md#4-teach-it-her-words)
shows one at work.

**Suggestions from a model or a script.** A suggestion is one JSON line,
`{path, data, cites, claim}`, and may cite only what the last `bite` returned,
so ask first. It waits for you; nothing is given as an answer until you seal
it with your key:

```
$ python kernel.py bite    --box my-record "your question"
$ python kernel.py propose --box my-record --file suggestions.jsonl
$ python kernel.py out     --box my-record
$ python kernel.py seal    --box my-record proposal:<sha256>
```

`propose` and `out` end at 42 while something waits on you. `decline` is
your No, proved with the key the same way: it isn't offered again.

Every command and exit code: the README's [Commands](../../README.md#commands).
How it ranks, and what the record keeps: [how-it-works.md](../how-it-works.md).
