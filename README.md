# willow

`kernel.py` is the smallest script that runs the whole loop, for anyone. It
searches your own folder, serves what you wrote, writes down only what you
seal, and keeps every step on a chain you can check.

One file, Python 3.9+, standard library only. Nothing to install, and it never
touches the network.

## Try it on someone else's life first

```
python demo/odile/make_life.py
python kernel.py init --box odile-box --pile demo/odile/life --key odile.key
python kernel.py bite --box odile-box "how are the bees"
```

Odile is made up. `make_life.py` writes six years of her files, the same bytes
every time. The bite serves her latest hive inspections.

## Then on your own

```
python kernel.py init --box my-box --pile path/to/your/folder --key my.key
python kernel.py bite --box my-box "your own words"
```

`init` makes `my-box` and `my.key` wherever you point it. Your folder is only
read, never written. Keep the key somewhere the box isn't: `init` refuses a
key inside the box.

`bite` prints JSON: each passage it serves, where it is (file and line), and
what it says.

## The loop

| Command | What it does |
|---|---|
| `init` | makes a box, and a key that is yours alone, kept outside the box |
| `bite` | your words against your files: a sealed answer first, else the passages that hold your words, newest first |
| `propose` | someone else's suggested answers (a model's, say), held at the door until you look |
| `seal` | your key over one proposal; only then is it written and served |
| `verify` | re-checks the whole chain and every seal |
| `out` | what's waiting on you |
| `test` | runs the whole loop once, in eight steps, on a throwaway box |

| Exit | Means |
|---|---|
| 0 | a human said it: your files hold it, or your seal does |
| 42 | not enough to say a human said it |
| 2 | refused: a bad command, a box that isn't yours, a chain that doesn't verify |

## What it never does

Each of these is a test that fails if it stops being true.

- **Never dials out.** The file imports nothing that can reach the network,
  and has no `eval`, `exec`, `compile` or `__import__` to get there another
  way.
- **Never stores your words.** The record keeps hashes and places only.
- **Never writes an answer you didn't seal,** and never serves a forged seal.
- **Never appends past a break.** An edited record is refused.

## Where it falls short

It matches words, not meanings. Ask "who owes me money" when your files say
"invoice outstanding" and it finds nothing. A words list (`init --words FILE`)
closes that gap one person at a time.

In blind tests on folders it wasn't built from, it found what was asked in the
files' own words and missed the rest. `demo/` has the results, misses
included.

## What else is here

| Folder | What it is |
|---|---|
| `adapters/` | things built on top of the kernel |
| `ports/` | the kernel in Java, TypeScript and C# |
| `vectors/` | the 4,463 cases every port must answer exactly as `kernel.py` does |
| `demo/` | three made-up people, the needs planted in their files, and what the kernel found |

## Adding to it

**An adapter** uses the kernel; the kernel never uses it. It writes only
through the kernel, so `verify` still holds. Its folder has the code, a card
(what it's for, what it never does) and tests that CI runs. See
[adapters/](adapters/).

**A port** passes `vectors/compare.py` with zero unexplained differences, and
every other implementation verifies its boxes. See [vectors/](vectors/).

## Licence

Apache-2.0. See [LICENSE](LICENSE).
