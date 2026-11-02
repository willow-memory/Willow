# ui

Willow's own UI: put your willow together on a page, on this machine only.
No install beyond Python, the same as the kernel.

    python ui/canvas.py [--to DIR] [--folder PATH]... [--port N] [--no-open]

It prints a link on `127.0.0.1` and opens it. The page goes the way a person
does:

1. **Your folders.** Choose the ones willow may read, from a folder list. It
   only ever reads them.
2. **What the kernel does on its own.** Each folder read the kernel's way,
   before any add-on, as counts: how many files it can read, the passages
   that makes, and how many it can't, by kind, with the readers that could
   read them, one click to add. Never a passage, never a file's name.
3. **Start from an example**, the folders the stack add-on ships, each step
   with the options it runs with, or **pick add-ons** by what you want done,
   in your own words, by tag, or from each part of the flow. A piece comes
   with what its card `uses`, as a language pack comes with its program, and
   taking out a piece another needs asks first.
4. **Save what you picked as a batch**, to bring back on any folder. Your
   folders aren't part of it, and a deleted batch is gone.
5. **Look it over, and seal it.** Nothing runs until you do. Then **Put it
   together** copies the add-ons into your stack, and **Start it** sets up
   your record over your folders, runs each add-on's own tests and your flow
   once, and opens [browse](../adapters/stdlib/browse/) on your record.

Every card on the page folds to a line; it remembers which you opened.

## Your stack

Kept in `--to`, `~/willow-stack` unless you say, and never inside this
repository. The first run makes it from this willow: `kernel.py`, the law,
the kernel's vectors, and the stack and browse add-ons. Each file is hashed
in its `STACK.json`, and every add-on put in is a row on the stack's own
kernel record. [assemble.py](assemble.py) does that, and is a command line of
its own:

    python ui/assemble.py status            # what's in it, what's looked for and absent
    python ui/assemble.py add NAME...       # an add-on, and what its card uses
    python ui/assemble.py check             # every file still the one put in

Batches are kept beside it, in `batches.json`, not on the record, so a
deleted one is gone. The words people use for what they want, and the words
the cards use, are in [search-words.txt](search-words.txt), in the kernel's
words-list format: when a search misses what you meant, that's the file to
add a line to.

## What it never does

It never reaches the network: it binds `127.0.0.1` and answers only under a
fresh random path, with the Host it was given and the page's own Origin, so
another site can't drive it. It never shows what a file says or what it's
called. It never writes inside this repository or your folders: only your
stack, your record over your folders and the batches file, all under
`--to`. It never approves anything: the seal is the kernel's own, made with
your key.

What it can't stop: a program running as you can read the link it prints,
or run `kernel.py seal` itself. The seal is willow's key file, as it is
everywhere today; `seal_step` in [canvas.py](canvas.py) is the one place a
better one would go.

## Its tests

[test_ui.py](test_ui.py) runs its server in-process over a stack made in a
scratch folder. CI runs them as `tests:ui`.
