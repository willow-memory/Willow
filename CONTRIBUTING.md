# Contributing

Thanks for looking. Most changes here are a new add-on, and
[adapters/README.md](adapters/README.md) says how to build one. This page has
the rules every change follows, and how to show that yours does.

## Run what CI runs

CI is one script, and you can run all of it on your own machine:

    python adapters/stdlib/ci/ci.py run --box /tmp/ci-record
    python adapters/stdlib/ci/ci.py show --box /tmp/ci-record

Each check is written down as one row: `satisfied`, `failing` or
`unreachable`. Unreachable means a tool isn't installed (no Java, no
network), and it never counts as a pass. To run one part, name it: `lint`,
`tests`, `ports`, `demo` or `deps`. Keep the record folder outside the repo;
the script refuses one inside it unless git ignores it.

Paste the `show` output into your pull request. A green run you can show is
worth more than a sentence saying it passed.

## The rules

**The kernel stays small.** `kernel.py` needs nothing but Python 3.9 or
newer. An add-on may use the kernel; the kernel never uses an add-on, and it
runs the same without any. A change that adds an import to `kernel.py` beyond
the standard library won't be merged.

**Only a person approves.** Code may search, suggest and record. It never
writes an approval (a `seal`), and it never reads the person's key. An add-on
writes to the record only through the kernel's own commands, so `verify`
still holds afterwards.

**A check has to be able to fail.** Before you say a test covers something,
break that thing on purpose and watch the test go red. A test that can't
fail, or that skips quietly when something is missing, looks like a pass and
checks nothing. If something needed isn't installed, refuse with a message
that names it.
CI checks this for you: `mutants` breaks each add-on's code a few ways and
fails when its tests don't notice. If a break truly changes nothing a person
could see, list it in `adapters/stdlib/mutants/accepted.json` with the reason;
the maintainer decides whether it stands.

**Say what's missing.** "Nothing found", "nothing there" and "couldn't
reach it" are three different answers, and an add-on reports which one it
has. If something is absent, write that down as a value; don't leave the line
out.

**The same input gives the same bytes.** Reading the same files twice gives
the same output: no clock times, no machine paths, and no ordering that
depends on the file system.

**An add-on keeps its card's promises.** Its card says what it writes and
whether it goes online, and CI holds it to that while its tests run. No card
can loosen three rules: an add-on never changes your files, never writes the
record except through the kernel, and never reads the key itself.

**The docs match the files.** `test_docs.py` checks that the file tree in
the README lists every file in the repo and nothing else, that every path a
document names exists, and that the numbers the README quotes are the
repo's. If you add a file, add it to the tree. If you change a number, the
test will tell you which document still has the old one.

**Plain words.** Write the README, the cards and the error messages for
someone who has never seen the project. Name the thing, then say what it
does.

## Add an idea

The add-on list in the README is open. To add an idea, open a pull request
that adds one entry to [adapters/planned.json](adapters/planned.json):

```json
{
 "name": "bank",
 "kind": "stdlib",
 "section": "Reading more kinds of files",
 "line": "Bank CSV and OFX statements as dated lines, with spending by month.",
 "source": "new",
 "writes": "to",
 "network": "none",
 "tags": "no-install, offline, writes-output, file-reader, money"
}
```

- `kind` is `stdlib` if it needs nothing installed, else `deps`, with a
  `needs` line naming each install and its licence.
- `tags` are up to five; leave them out and `readme.py tags` fills in four
  from the rest, or write your own.
- `writes` and `network` are its promises, set out in
  [adapters/README.md](adapters/README.md#its-promises-checked). Whoever
  builds it is held to them.

Before you add it, see what's already near it:

    python adapters/stdlib/similar/similar.py near "your idea in a sentence"

If something built is close, connecting to it may be the better idea. On the
pull request, CI's run summary lists what's near each idea you add, and
willow-bot posts the same list as a comment. That list is a suggestion; only
the maintainer decides. CI does refuse an idea with the same line as one
already listed.

## Pick one up

Anyone can build any idea on the list; you don't need to ask first. To let
others know you've started, open a draft pull request that names it.

1. Make its folder in `adapters/stdlib/` or `adapters/deps/`, with the code,
   its card and its tests.
2. Give the card the idea's fields and the same promises. If building it
   shows a promise was wrong, change it in the card and say why in the pull
   request, where the maintainer can see it.
3. Take its entry out of `adapters/planned.json` in the same change, and regenerate
   the README's list.

Your add-on's tests run under the guard, which holds it to its card. A test
that never runs a path is a path the guard never checks, so test what your
add-on actually does.

## Add-ons that need installs

An add-on in `adapters/deps/` carries everything set out in
[adapters/deps/README.md](adapters/deps/README.md):

- **Two pinned requirements files.** `requirements.txt` pins every package
  with `==`. `requirements-floor.txt` pins the same packages at their floor.
- **What it needs, on its card.** The card names each package and its
  licence. The licence has to be one an Apache-2.0 project can depend on.
- **Whether it goes online.** If it goes online at all, the card says so.

**The floor rule.** Every dependency is also tested at its last release on
or before 2020-12-31, or at its first release if it had none by then. If your
add-on can't run that far back, raise the floor and give the reason in one
sentence on the card's `floor:` line. CI runs the tests at both the pinned
versions and the floor, and checks each floor against PyPI's release dates.

## Pull requests

- One idea per pull request.
- Regenerate the README's add-on list with
  `python adapters/stdlib/readme/readme.py write`, never by hand;
  `test_docs.py` fails if it's stale.
- Merging is the maintainer saying the change is good enough for now. CI's
  rows are evidence for that decision, not the decision itself.

## Licence

Everything here is Apache-2.0 ([LICENSE](LICENSE)). By opening a pull
request you agree your contribution is offered under the same licence.
