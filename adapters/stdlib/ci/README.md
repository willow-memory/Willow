<!-- willow-addon
section: For maintainers
line: This repo's checks as verdict rows on a kernel record, the same every run.
source: box
added: 2026-10-23
writes: record, BUGS.md
network: PyPI, to read each dependency floor's release date
tags: no-install, online, records, maintainers
-->
# ci

This repo's checks as a kernel record. Each check runs one fixed command and
is written as one `verdict` row through the kernel's own `append`, so the CI
record is hash-chained like any other and the kernel's `verify` checks it.

    python adapters/stdlib/ci/ci.py run    [lint|tests|ports|demo|deps|mutants ...] [--box DIR]
    python adapters/stdlib/ci/ci.py verify [--box DIR]
    python adapters/stdlib/ci/ci.py show   [--box DIR]

`run` with no part runs all six. The record goes in `.ci-record/` by default
(git ignores it), and the key `init` makes goes beside it in
`.ci-record.key`. A record or key inside the repo where git would count it is
refused: it would be hashed into the very files it records. CI keeps its
record in the runner's temp folder.

| Part | Gates, in this order |
|---|---|
| lint | `lint:check`, `lint:format` (ruff) |
| tests | `tests:beats` (`kernel.py test`), `tests:kernel`, `tests:docs` (`test_docs.py`, and `test_docs_fires.py`, which shows each docs check fails on a planted violation), `tests:adapters` (the add-ons in `adapters/stdlib/`, under the guard), `tests:vectors` (pytest) |
| ports | `ports:java`, `ports:ts`, `ports:csharp`: `vectors/compare.py`, one port at a time |
| demo | `demo:hollis`, `demo:odile`, `demo:teodora`: each person's files made in a temporary folder and held to their `demo/*/PLANTED.md` |
| deps | `deps:mcp`, `deps:mcp@floor`, `deps:pdf`, `deps:pdf@floor`, two per add-on in `adapters/deps/`: its tests, under the guard, in a fresh virtual environment with only its own pinned requirements (then its floor's) and pytest; an install that can't be done is unreachable. Then `deps:floors`: each floor against the floor rule, by PyPI's upload dates; PyPI out of reach is unreachable |
| mutants | `mutants:again`, `mutants:all`, … one per stdlib add-on: [mutants.py](../mutants/) breaks its code a few ways and runs its tests against each break; a break they miss fails, unless [accepted.json](../mutants/accepted.json) gives the reason it's harmless |

Each verdict row holds the gate, its state, a hash of every file in the repo
it ran on, a hash of what the command printed, the Python version, and a
reason when it didn't pass.

**States, never collapsed:** `satisfied`; `failing` (the command failed, or
its output didn't show what it must, such as a port that `vectors/compare.py`
skipped); `unreachable` (a tool isn't installed). Neither of the last two is a
pass.

**Exit codes, the kernel's:** 0 every gate satisfied; 42 a gate unreachable
and none failing; 2 a gate failing, or a record that doesn't verify.

**Deterministic:** every row's time is the commit's, and what changes between
runs (durations, temporary folders, where the repo sits) is taken out before
the output is hashed. The same files give the same record, byte for byte.

**The changelog:** [changelog.py](changelog.py) runs as its own CI job on
every pull request, outside the record (it needs the pull request's number
and its base branch). When anything but Markdown changed, CHANGELOG.md's
`## Unreleased` section must gain an entry ending with that number, `(#N)`,
and a bug [BUGS.md](../../../BUGS.md) stopped listing must be named in one
under `### Fixed`, `bug #12`. Exit 0 every entry owed is there, or nothing is
owed; 42 git couldn't compare with the base; 2 an entry is missing.

**Known bugs:** [bugs.py](bugs.py) makes BUGS.md from the tests marked as
expected to fail, `strict=True` with a reason `bug #N: …`, and refuses any
other such mark. `test_docs.py` fails when BUGS.md and the tests disagree.

**Whose lines:** [whose.py](whose.py) takes `PATH:FIRST-LAST` places and
prints the pull request that wrote each, by git blame and the merge that
brought the commit in. The security workflow runs it on a report's "Where it
is" section and tags each pull request's author on the report. It refuses
any place that isn't a line range in a file git tracks, since a report's
text is anyone's.

**The contract:** [test_contract.py](test_contract.py) holds every add-on to
what they all promise alike. Run with nothing, or with one argument too many
against a real box, an add-on refuses (exit 2) and names itself; every reader
keeps the readers' contract (the summary line, the same bytes twice,
originals untouched, hidden files unread, 42 for nothing to read, refusals
that write nothing). A new add-on with a command line has to be listed there.

**The guard:** the add-ons' tests, and each deps add-on's, run with
[guard/sitecustomize.py](guard/sitecustomize.py) on `PYTHONPATH`, so it is
loaded into every Python process they start. It holds each add-on to its
card's `writes` and `network` and to the rules no card loosens (no original
changed, no box written but through the kernel, no key read), and writes
each breach to a log. A gate whose log isn't empty is `failing`, even when
every test passed: a breach the add-on caught and hid is still a breach.
[test_guard.py](test_guard.py) breaks each promise on purpose and checks the
guard catches it.

**Uses:** the kernel's `init`, `append`, `read`, `verify`, `h256` and its exit
codes.

**Never:** writes a `seal` row, or a field a seal reader looks at (`proof`,
`subject`). Its verdicts are draft. What makes a tree count is a person
merging it.

In CI (`.github/workflows/ci.yml`) each part is its own job with its own
record, verified and uploaded as that run's artifact.
