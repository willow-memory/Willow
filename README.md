# willow

`kernel.py` answers questions from your own files, and from nothing else.

You point it at a folder: notes, logs, letters, exports, whatever you keep. You
ask in plain words, "how are the bees". It shows you the lines in your files
that hold those words, newest first, each with the file and line it came
from. If no file holds them, it says so rather than guessing.

It can also take answers from somewhere else, an AI model for instance, but it
holds each one until you approve it with a key only you have. Once approved,
that answer comes back the next time you ask. Nothing you haven't approved is
ever given as an answer.

Every question, suggested answer and approval is written to a record you can
check later. The record holds fingerprints (hashes) and file positions, never
your words, and any change to it after the fact is caught.

One file, Python 3.9+, standard library only. Nothing to install, and it never
touches the network.

## Try it on someone else's files first

```
python demo/odile/make_life.py
python kernel.py init --box odile-record --pile demo/odile/life --key odile.key
python kernel.py bite --box odile-record "how are the bees"
```

Odile is made up. `make_life.py` writes six years of her files, the same bytes
every time. The question brings back her latest hive inspections.

## Then on your own

```
python kernel.py init --box my-record --pile path/to/your/folder --key my.key
python kernel.py bite --box my-record "your own words"
```

`--pile` is your folder; it is only read, never written. `--box` is a new
folder where the record is kept. `--key` is your key file. `init` makes the
record folder and the key wherever you point them, and refuses a key inside
the record folder: keep the two apart.

The answer is printed as JSON: each line it found, the file and line number,
and the text.

## What each command does

| Command | What it does |
|---|---|
| `init` | starts a record for your folder, and makes your key |
| `bite` | asks a question: an approved answer first, else the lines in your files that hold your words, newest first |
| `propose` | hands in suggested answers (from a model, say), each citing lines the last question found; they wait for you |
| `seal` | approves one suggested answer with your key; only then is it kept and given |
| `verify` | checks the whole record and every approval |
| `out` | lists what's waiting for your approval |
| `test` | runs every step once, in eight steps, on a throwaway record |

| Exit code | Means |
|---|---|
| 0 | a person said it: your files hold it, or you approved it |
| 42 | not enough to say a person said it |
| 2 | refused: a bad command, a record that isn't yours, a record that has been changed |

## What it never does

Each of these is a test that fails if it stops being true.

- **Never goes online.** The file imports nothing that can reach the network,
  and has no `eval`, `exec`, `compile` or `__import__` to get there another
  way.
- **Never stores your words.** The record keeps fingerprints and positions
  only.
- **Never gives an answer you didn't approve,** and never accepts a forged
  approval.
- **Never writes past a change.** If the record has been edited, it stops.

## Where it falls short

It matches words, not meanings. Ask "who owes me money" when your files say
"invoice outstanding" and it finds nothing. A list of your own words closes
that gap one person at a time: a file with lines like
`owes = invoice, outstanding`, readable only by you (`chmod 600`), kept
outside the record folder, and given to `init --words FILE`. When it changes
an answer, the answer says so.

In blind tests on folders it wasn't built from, it found what was asked in the
files' own words and missed the rest. `demo/` has the results, misses
included.

## What else is here

| Folder | What it is |
|---|---|
| `adapters/` | add-ons built on top of `kernel.py` |
| `ports/` | `kernel.py` rewritten in Java, TypeScript and C# |
| `vectors/` | 4,463 test cases every rewrite must answer exactly as `kernel.py` does |
| `demo/` | three made-up people, the needs hidden in their files, and what `kernel.py` found |

## Adding to it

**An add-on** uses `kernel.py`; `kernel.py` never uses it. It writes to the
record only through `kernel.py`, so `verify` still holds. Its folder has the
code, a short card (what it's for, what it never does) and tests that CI runs.
See [adapters/](adapters/).

**A rewrite in another language** passes `vectors/compare.py` with zero
unexplained differences, and every other version checks its records. See
[vectors/](vectors/).

## Licence

Apache-2.0. See [LICENSE](LICENSE).
