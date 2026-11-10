# Contributing

Thanks for looking. Most changes here are a new add-on, and
[adapters/README.md](adapters/README.md) says how to build one. This page has
the rules every change follows, and how to show that yours does.

A question is welcome: open an issue and say what you tried. A security
problem is reported in public too; [SECURITY.md](SECURITY.md) says what
counts and how. What's settled and why is in
[DECISIONS.md](DECISIONS.md), and what willow doesn't do in
[LIMITS.md](LIMITS.md). Everyone here keeps the
[code of conduct](CODE_OF_CONDUCT.md).

## Run what CI runs

CI is one script, and you can run any of it on your own machine. CI runs
all of it on every pull request, so run the parts your change can move
([AGENTS.md](AGENTS.md) says which), and ask what this machine can't run,
which takes a second and runs nothing:

    python adapters/stdlib/ci/ci.py needs
    python adapters/stdlib/ci/ci.py run lint --box /tmp/ci-record
    python adapters/stdlib/ci/ci.py show --box /tmp/ci-record

Each check is written down as one row: `satisfied`, `failing` or
`unreachable`. Unreachable means a tool isn't installed (no Java, no
network), and it never counts as a pass. To run one part, name it: `lint`,
`tests`, `ports`, `demo`, `deps` or `mutants`. Keep the record folder outside
the repo; the script refuses one inside it unless git ignores it.

**Receipts, not claims.** Paste the `show` output into your pull request's
Evidence: only what you actually ran, with its result. A green run you can
show is worth more than a sentence saying it passed, and a part you didn't
run is said, not left out; CI's own checks on the pull request are the run
of everything.

## The rules

**The kernel stays small.** `kernel.py` needs nothing but Python 3.9 or
newer. An add-on may use the kernel; the kernel never uses an add-on, and it
runs the same without any. An import in `kernel.py` from beyond the standard
library, or from an add-on, fails `test_kernel.py`.

**Only a person approves.** Code may search, suggest and record. It never
writes an approval (a `seal`), and it never reads the person's key. An add-on
writes to the record only through the kernel's own commands, so `verify`
still holds afterwards.

**A chain of add-ons starts at the Forge, and the person seals it.** When
you put add-ons together for someone (a demo's stack, a study, a page that
walks a pile through add-on after add-on), ask the forge add-on with their
words first (`python adapters/deps/forge/suggest.py suggest --box DIR
"their sentence"`), settle each fork it names with `propose --choose
WORD=NAME --why WORD=...`, and leave the seal to them: the chain they keep
is the one they sealed, with a reason for each choice, not one picked by
hand and written up after. When their words miss an add-on they meant, add
the line to `ui/search-words.txt`, so the next person's words reach it too.
A sealed stack is shared with `adapters/stdlib/stack-share`, on
[Show your stack](https://github.com/willow-memory/Willow/issues/87).
Where the Forge can't run (it needs forge-play and Python 3.11), say so,
and write the stack file by hand with each step's reason beside it.

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

**The law, both ways.** The law never names your code; your code names
the law. If what you build enforces a clause of
[CONSTITUTION.md](CONSTITUTION.md), name the clause by its Trace ID
(`CONST-0-3`) in the code that does it, and in a test that tries to break
it. `test_docs.py` holds both directions:

- **code to law:** every Trace ID cited anywhere is a clause the law has,
  and every clause cited in code is also cited by a test, since enforcing
  a clause with nothing trying to break it is a wish;
- **law to code:** every clause is cited by code or a test, or answered in
  `constitution/reach.json`: *out of reach* (it governs something willow
  doesn't have) or *open* (willow does something like it, but no check
  shows it yet), with the reason. An answer for a clause the code already
  cites fails too, so the file can't go stale;
- **the README:** each guarantee names the clause it holds, or `none`, and
  every eternity clause is one of them.

A change to the law, or to what the code cites, brings its answers in the
same pull request. Two files are the maintainer's call, never yours for your
own work: the verdicts in `constitution/declarations.json`, and the answers
in `constitution/reach.json`. Propose them in the pull request; the witness
is not the actor.

**Amending the law.** The constitution is always a draft, and anyone may
propose an amendment. Write the clause into its article in
`CONSTITUTION.md`, add the next numbered file to `constitution/amendments/`
with the same text under its header (the next draft, the date, your pull
request's number, the articles, the clauses, a one-line summary), and run
`python constitution/amend.py write`. In the same pull request, cite each
clause it brings in the code that enforces it and in a test that tries to
break it: an amendment that doesn't leave the law better enforced is
refused. The Preamble and Article 0 can't be amended. To replace an
earlier amendment, name it in `supersedes`; never edit or delete one. An
urgent fix can go in as an emergency amendment, with `expires:` in its
header; a full amendment has to keep or undo it within 90 days, or the
checks fail.
[constitution/README.md](constitution/README.md) has the rest.

**The docs match the files.** `test_docs.py` checks that the file tree in
[FILES.md](FILES.md) lists every file in the repo and nothing else, that the
README's short tree is the repo's top level, that every path a document names
exists, and that the numbers the README quotes are the repo's. If you add a
file, add it to FILES.md's tree (`python adapters/stdlib/ci/files.py write`
does it). If you change a number, the test will tell
you which document still has the old one.

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
 "tags": "money"
}
```

- `kind` is `stdlib` if it needs nothing installed, else `deps`, with a
  `needs` line naming each install and its licence.
- `tags` is optional: one tag of your own. The rest (needs an install or not,
  goes online or not, two topic words) are worked out from the card each time
  the list is written; `similar.py tags NAME` shows them.
- `uses` and `looks-for` name the add-ons it leans on: what it needs beside it,
  and what it uses only when it's there (it says so when it isn't). CI runs
  its tests in a copy holding only it and what it `uses`
  ([adapters/README.md](adapters/README.md#what-a-folder-holds)).
- `role` is the part it plays in a stack (what it reads, what runs on your
  page, where you ask from...), one of those in
  [adapters/README.md](adapters/README.md#what-a-folder-holds).
- `from` is optional: where the idea or its code came from, when another
  project's, as `how, address, licence` (`shape, https://github.com/wagtail/Willow, BSD-3-Clause`).
  How is `shape`, `code` or `dep`; [adapters/README.md](adapters/README.md#what-a-folder-holds)
  says what each may take.
- `reads`, on a reader's card (`role: reads`), is what it reads: kinds of
  file by extension, or a file it looks for by name, `reads: .eml, .mbox`,
  or `none`. The UI offers a reader by it, and the contract test holds each
  kind to the reader's own code.
- `writes` and `network` are its promises, set out in
  [adapters/README.md](adapters/README.md#its-promises-checked). Whoever
  builds it is held to them.

Before you add it, see what's already near it:

    python adapters/stdlib/similar/similar.py near "your idea in a sentence"

If something built is close, connecting to it may be the better idea. On the
pull request, CI's run summary lists what's near each idea you add, and
willow-bot posts the same list in its status comment, read from the run's
`similar` artifact. That list is a suggestion; only
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
   the add-on list.

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

## Where it's hosted

Everything that needs GitHub is in [adapters/stdlib/github/](adapters/stdlib/github/),
with `.github/`, and nothing else uses them. Run `adapters/stdlib/ci/ci.py` on your own machine
and you need no host at all; `test_strip.py` deletes both and shows the rest
still passes. To work on willow somewhere else, add a folder for that host
beside the GitHub one: a host.json for `adapters/stdlib/ci/whose.py`, and that site's CI file.

## Pull requests

- One idea per pull request.
- Look at the open pull requests before you start, whatever you branch
  from: one may already be building your idea, or changing the files
  you'll change. Branching from `main` is where your work starts, not a
  sign that nothing else is in flight. The check below holds your branch to
  them once it has a commit.
- A change to anything but the docs adds its changelog entry in a file of
  its own, `changes/+<branch>.<kind>.md`, towncrier's shape
  ([changes/README.md](changes/README.md)): <kind> is `added`, `changed`,
  `fixed` or `removed`, and the file holds the entry's text. Not in
  CHANGELOG.md: no two pull requests write the same fragment, so none
  conflicts with another, and a release folds them in. CI checks it on
  every pull request but Dependabot's: a bot's dependency update can't
  write an entry, and those updates aren't listed.
- Regenerate the add-on list (ADDONS.md, and the README's one feature) with
  `python adapters/stdlib/readme/readme.py write`, never by hand;
  `test_docs.py` fails if it's stale.
- Branch from `main`, and name the changelog fragment in the first push:
  open the pull request, rename `changes/+<branch>.<kind>.md` to
  `changes/<number>.<kind>.md`, and push once, so the first run is not
  thrown away. `adapters/stdlib/github/create_pr.py` does all of it. Every
  push after the first starts a run of every check, and a stack of
  branches re-runs them all whenever one of them moves.
- CI's `against` job holds your pull request to the other open ones, and its
  summary says what it found. **A duplicate fails it:** a name both pull
  requests add (an add-on folder, an idea on `adapters/planned.json`, a key
  of `COMMANDS`, a path in FILES.md). The two of you settle it between
  yourselves on the pull requests first, one withdrawing or the two joining,
  before more is built; it comes to the maintainer only when you can't.
  **A collision is a warning:**
  a file you both change that git cannot merge, named with the pull request
  to merge first (CHANGELOG.md, the generated lists, FILES.md,
  `adapters/planned.json` and the `COMMANDS` table are settled by
  `adapters/stdlib/restack/restack.py`, and it only says so). Run it yourself
  with `python adapters/stdlib/against/against.py check --base origin/main HEAD OTHER ...`.
- **Stack only when the check names a pull request to merge first.** Then
  merge that pull request's branch into yours and make its branch your
  pull request's base, not `main`. With several named, merge each and name
  the newest as the base. Regenerate what's generated after the merge, and
  merge CHANGELOG.md by hand, newest first. When the one below merges and
  its branch is deleted, GitHub moves yours onto `main`; if its branch
  stays, change your base to `main` yourself.

## Bugs

Report one as an issue (on GitHub, the **Something is wrong** form). A
security problem is reported the same way, in public: see
[SECURITY.md](SECURITY.md).

**A known bug is a test.** To put one on [BUGS.md](BUGS.md), write a test
that shows it, and mark it as expected to fail, strictly, naming its issue:

```python
@pytest.mark.xfail(strict=True, reason="bug #12: what goes wrong, in a sentence")
def test_a_date_written_day_first_is_read_day_first(): ...
```

Then run `python adapters/stdlib/ci/bugs.py write`. `test_docs.py` fails if
BUGS.md and the tests disagree, and refuses any expected-to-fail mark that
isn't strict or doesn't name a bug: a loose one would let a fixed bug pass
unnoticed.

**Fixing one.** Once the bug is fixed its test passes, and because the
mark is strict, that fails the run until you take the mark off. Regenerate
BUGS.md, and write a `fixed` fragment (`changes/+<branch>.fixed.md`) that
names it, `bug #12`; CI refuses the pull request without it.

## Releases

A release is a version number and a date on what has merged since the last
one, `vMAJOR.MINOR.PATCH`:

- **major:** a record, a command or an exit code changes in a way an older
  script or record can't follow;
- **minor:** something new: a command, an option, an add-on;
- **patch:** fixes only.

To make one, open a pull request that changes only the docs:

1. Fold the fragments in: `pipx run towncrier build --version X.Y.Z --date
   YYYY-MM-DD --yes` writes `## vX.Y.Z · YYYY-MM-DD` into
   [CHANGELOG.md](CHANGELOG.md) from changes/ and deletes them
   ([towncrier.toml](towncrier.toml) holds its settings). Entries still
   under `## Unreleased`, from before the fragments, move into that
   section by hand, leaving `## Unreleased` empty above it.
2. In [CITATION.cff](CITATION.cff), set `version: X.Y.Z` and
   `date-released: YYYY-MM-DD` to match.

`test_docs.py` fails if the two disagree, and the changelog check owes
nothing for it.

**Add-ons and ideas are versioned the same way**, each on its own: `version:`
on its card, and `"version"` on its entry in `adapters/planned.json`. An
idea starts at 0.0.1 and steps a patch each time its entry changes; its
first build is 0.1.0; a built add-on steps a patch for a fix, a minor step
for something added, and a major one when something that relied on it no
longer can. Below 1.0 a breaking change is a minor step, as the standard
says, and 1.0 comes when its author judges the add-on has settled; it is
not an end. One pull request is one step, however many commits it has.
`adapters/stdlib/ci/versions.py check` holds it on every pull request, and
`write` (one of ready's steps) takes the smallest step each change owes; a
bigger one is yours to write. Once it merges, tag the merge commit `vX.Y.Z` and publish a
release whose notes are that section of the changelog.

## After you open it

- **CI runs every part** as its own job, one row per check, and keeps the
  record as the run's artifact. A pull request's run summary also lists
  what's already on the add-on list near anything it adds (`similar`).
- **willows-bot** posts one status comment and keeps it current, and labels
  the pull request (its size, and that it's been looked at). It never
  approves or merges.
- **The maintainer merges.** Merging is the maintainer saying the change is
  good enough for now. CI's rows are evidence for that decision, not the
  decision itself.

## What CI will not do

A failing check is a finding to fix or to talk about on the pull request,
never a reason to change the check until it passes. So CI never:

- adds a break to `adapters/stdlib/mutants/accepted.json`: a person does,
  with the reason, and the maintainer decides whether it stands;
- loosens an add-on's card, its `writes` or `network`, to fit what the code
  does: if the card was wrong, the pull request says so;
- approves anything: only a person does;
- skips a test to get green: a skipped check still looks like a pass. A
  test marked as expected to fail is a known bug, with its number, on
  BUGS.md, never a way to quiet a failure.

## Licence

Everything here is Apache-2.0 ([LICENSE](LICENSE)). By opening a pull
request you agree your contribution is offered under the same licence.
