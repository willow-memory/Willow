# ui

Willow's own UI: put your willow together on a page, on this machine only.
No install beyond Python, the same as the kernel.

    python ui/canvas.py [--to DIR] [--folder PATH]... [--port N] [--no-open]

It prints a link on `127.0.0.1` and opens it. The page is three panels:
the steps of your stack on the left, the one you're on in the middle with the
add-ons that can go in it, and your stack on the right as a tree, what runs
on your page in its order apart from what's set up alongside. It goes the
way a person does:

1. **Your folders.** Choose the ones willow may read, from a folder list. It
   only ever reads them.
2. **What the kernel does on its own.** Each folder read the kernel's way,
   before any add-on, as counts: how many files it can read, the passages
   that makes, and how many it can't, by kind, with the readers that could
   read them, one click to add. Never a passage, never a file's name.
3. **Start from an example**, the folders the stack add-on ships, each step
   with the options it runs with (hover one to see in the tree what it
   would add), or **pick add-ons** by what you want done, in your own words,
   by tag, or step by step, ticked or dragged into place. A piece comes with
   what its card `uses`, as a language pack comes with its program, and
   taking out a piece another needs asks first. Undo takes back each change.
4. **Save what you picked as a batch**, to bring back on any folder. Your
   folders aren't part of it, and a deleted batch is gone.
5. **Look it over, and seal it**, the last step. Nothing runs until you do.
   Then **Put it together** copies the add-ons into your stack, and **Start
   it** sets up your record over your folders, runs each add-on's own tests
   and your flow once, and opens [browse](../adapters/stdlib/browse/) on your
   record. The stack's header says "sealed" while your pick is the stack
   last sealed on its record, wherever that seal was made, and "changed
   since you sealed it" once it isn't.

The steps are **roles**, the part a piece plays: what it reads, what runs on
your page, what suggests answers, where
you ask from, what guards an assistant, what it makes for elsewhere, and
tools you run yourself. A card says what a piece is about, its `section`,
not its role, so `role` in [canvas.py](canvas.py) guesses it from what the
card does say, and every card on the page says which fact it went by. A way
in or a hook, run with no options of its own, is set up alongside and not
run on the page, even when it could be: run so, it only says how to set
itself up. The steps on your page run in their order, but the page shows
what says most first, as [stack](../adapters/stdlib/stack/) does, so their
order only breaks ties, and matters only for a step that writes the record.

## For an agent or a terminal

The page's steps are commands too, over the same stack and from the same
cards, so an agent builds a stack the way a person does and stops where a
person seals:

    python ui/canvas.py make     [--to DIR]                  # a stack, as the first run makes it
    python ui/canvas.py pieces   [--role ROLE] [--json]      # what there is, by role, and why
    python ui/canvas.py needs    NAME...                     # what a piece brings along
    python ui/canvas.py examples                             # the stack add-on's examples
    python ui/canvas.py plan     NAME... [--example FILE] [--folder PATH]...  # prints a stack file
    python ui/canvas.py look     STACKFILE                   # what Look it over says of it
    python ui/canvas.py propose  STACKFILE                   # to the kernel; exits 42, waiting for your seal

A stack file is the one [stack](../adapters/stdlib/stack/) runs. Look it over
shows the same file, and these commands for it, under "For an agent or a
terminal". There is no `seal`: sealing stays yours, on the page or with your
key. `pieces --role repo` lists the commands that work on willow's own
repository rather than a stack, with their command lines from their cards.

## Your stack

Kept in `--to`, `~/willow-stack` unless you say, and never inside this
repository. The first run makes it from this willow: `kernel.py`, the law,
the kernel's vectors, and the stack and browse add-ons. Each file is hashed
in its `STACK.json`, and every add-on put in is a row on the stack's own
kernel record. [assemble.py](assemble.py) does that, and is a command line of
its own:

    python ui/assemble.py status            # what's in it, what's looked for and absent
    python ui/assemble.py add NAME...       # an add-on, and what its card uses
    python ui/assemble.py remove NAME...    # an add-on out again, said on the record
    python ui/assemble.py check             # every file still the one put in
    python ui/assemble.py kernel --python EXE  # this willow's kernel and vectors in place of the stack's

A deps add-on (kart, forge, pdf) comes in too, to `adapters/deps/`, but only
when the Python you name with `--python` already has each package it needs, at
its floor or newer. Nothing is installed for it: one missing is refused, and
says which, so you install it where you choose.

`remove` takes an add-on out: its folder and its line in `STACK.json`, and
one row on the stack's record naming the files it held, so the record still
says it was there. Not one an add-on that stays imports (take them out
together), and not one whose files changed since it was put in, so nothing
of yours is deleted.

A stack keeps the kernel it was made with until you swap it. `kernel` does,
and keeps the new one only if the stack's record verifies under it and every
add-on's tests pass on it; else the old one is back and nothing is written.

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
