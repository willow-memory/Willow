# Decisions

What's settled, why, and what holds it. A pull request can reopen any of
these, but it does so here, by changing this file and saying why, rather
than by working around one in the code.

Where a decision is a promise to the person using willow, the README's
[guarantees table](README.md#guarantees-and-the-tests-behind-them) names the
test behind it. A decision with nothing to hold it says so.

## The kernel

**One file, standard library only, Python 3.9 or newer.** Anyone can copy
it anywhere and read all of it; there is nothing to install and nothing
else to trust. *Held by:* `test_kernel.py` fails on any import from outside
Python's own library, add-ons included; `test_strip.py` runs the kernel
with `adapters/` deleted; and CI runs the tests on every Python from 3.9 to
3.14.

**It never goes online.** A tool trusted with someone's own files has no
business with a network. *Held by:* `test_kernel.py` fails on any network
module, `eval`, `exec`, `compile` or `__import__`.

**It answers only in your own lines, or says it can't.** An answer quoted
with its file and line can be checked by opening the file; anything else
asks to be trusted. When the files don't hold it, the exit code is 42, not
a guess. *Held by:* `kernel.py test`, the eight beats.

**Nothing becomes an answer until a person approves it with their key.**
An AI model, a script or another person can suggest; only the key holder
approves. *Held by:* `kernel.py test` rejects a forged approval, even one
with a re-hashed chain.

**The record never holds your words.** A question is kept as a fingerprint
and the places it found, so copying the record copies no one's files.
*Held by:* the guarantees table.

**There is no index.** The folder is read fresh on every question, so
nothing goes stale and nothing is left behind to leak. The cost, time
growing with the folder, is in [LIMITS.md](LIMITS.md); an index belongs in
an add-on. *Held by:* nothing but the kernel itself: a change here is a
pull request against this file.

**Three exit codes: 0, 42, 2.** 0 a person said it, 42 not enough to say,
2 refused. A script can act on them without reading the words.
*Held by:* `kernel.py test`, and `adapters/stdlib/ci/test_contract.py` for
every add-on's refusal.

## Add-ons

**The arrow points one way.** An add-on uses the kernel; the kernel never
uses an add-on, and runs the same with `adapters/` deleted. *Held by:* the
standard-library test above, which fails on an import of `adapters`.

**Every add-on says what it writes and where it goes online, and is held
to it.** A card is a promise, so something has to check it. *Held by:* the
guard, `adapters/stdlib/ci/guard/sitecustomize.py`.

**Every add-on's tests can fail.** A test that can't fail checks nothing.
*Held by:* `adapters/stdlib/mutants/mutants.py`; a break the tests miss
fails CI unless `adapters/stdlib/mutants/accepted.json` gives the reason,
and a reason gone stale fails too.

**What needs installing is tested at its oldest, too.** Each dependency is
tested at its pin and at its floor: its last release of 2020, or its first,
or higher with a reason on the card. Old machines are real. *Held by:*
`adapters/stdlib/ci/ci.py`, the `deps` part.

## The ports

**Four languages, one behaviour.** Java, TypeScript and C# answer the same
cases as `kernel.py`, byte for byte. *Held by:* `vectors/compare.py`, one CI gate per
port.

## How the repo works

**CI's record is a kernel record, the same every run.** Checks are written
the way willow writes anything, so `verify` holds them, and the same files
give the same record. *Held by:* `adapters/stdlib/ci/test_ci.py`.

**A failing check is a finding, never a reason to change the check.**
*Held by:* review. CI can't tell a weakened check from a fixed one; the
pull request template asks for Evidence, and what wasn't checked, so a
reviewer can.

**The docs are held to the repo.** A file named, a number quoted or a tree
drawn in a doc is checked against what's there. *Held by:* `test_docs.py`,
and `test_docs_fires.py`, which shows each of its checks fails on a planted
violation.

**A known bug is a test.** [BUGS.md](BUGS.md) is made from tests marked as
expected to fail, strictly, so a bug can't be listed without a test or leave
the list without a fix. *Held by:* `adapters/stdlib/ci/bugs.py`, run by
`test_docs.py`.

**Every change says what it changed.** A pull request that changes more
than the docs adds an entry to [CHANGELOG.md](CHANGELOG.md) ending with its
number, and one that fixes a known bug names it under `### Fixed`.
*Held by:* `adapters/stdlib/ci/changelog.py`, its own CI job.

**Security problems are reported in public.** Willow runs only on a
person's own machine, so a private report protects nothing and a public one
reaches everyone at once, including whoever wrote the lines at fault.
*Held by:* review; on GitHub, the security issue form, and a workflow that
tags the author of the pull request behind each line a report points to.
See [SECURITY.md](SECURITY.md).

**Where the repo is hosted is an add-on.** GitHub is one host, not part of
willow: what needs it is in `adapters/stdlib/github/`, with `.github/`, and
another host gets a folder of its own beside it. Who wrote a line is a
question for git (`adapters/stdlib/ci/whose.py`); only how a site numbers
its pull requests is the host's, in its host.json. *Held by:*
`test_strip.py`, which deletes the GitHub add-on and `.github/`, then all
of `adapters/`, and runs what's left.
