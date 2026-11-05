# For agents

What an AI agent working on willow needs before its first change. The rules
are [CONTRIBUTING.md](CONTRIBUTING.md) and [adapters/README.md](adapters/README.md);
read both. This page is the part of them that is easy to miss, and what CI
catches when it is missed. It adds no rule of its own.

[CLAUDE.md](CLAUDE.md) imports this with `@AGENTS.md`; [GEMINI.md](GEMINI.md)
tells Gemini CLI to read this file (it has no `@` import). One copy to keep.
The longer how-tos are in [docs/agents/](docs/agents/), one page a job.

## Never

- **Approve anything.** Code may search, suggest and record. It never writes
  a seal and never reads the person's key. Merging is the maintainer's call;
  CI's rows are evidence for it, not the decision.
- **Change `kernel.py` for an add-on.** The arrow points one way: an add-on
  uses the kernel, the kernel never names an add-on.
- **Loosen a check to get green.** No skipped test, no loosened card, no
  entry in `adapters/stdlib/mutants/accepted.json` to quiet a failure, and no
  code rewritten only so a harmless mutant stops surviving.
- **Loosen the kernel's rank for recall.** It serves a passage only when it
  holds half the question's content words, so an answer the folder doesn't
  have is never invented ([searching](docs/agents/searching.md)).
- **Edit two files by hand:** the verdicts in `constitution/declarations.json`
  and the answers in `constitution/reach.json` are the maintainer's.

## Set up

CI calls its tools as Python modules, so they must import, not just be on
the path. A tool that won't import is recorded as unreachable, which never
counts as a pass:

    pip install pytest ruff==0.16.7

The ruff version is the one `.github/workflows/ci.yml` pins.
`adapters/stdlib/ci/ci.py` calls them through the Python that runs it, not
whichever is first on the path; if they live in a virtual environment, run
it with that environment's Python:

    VENV/bin/python adapters/stdlib/ci/ci.py run --box /tmp/ci-main

**Know what this machine can't run** (no Java, no .NET, an editor that isn't
installed) before a change, so a missing tool isn't taken for your failure.
It runs nothing and takes a second:

    python adapters/stdlib/ci/ci.py needs

Don't run every gate to find out: one after another they take well over an
hour, and all at once on every core (`adapters/stdlib/ci/cores.py`) most of
one. That's CI's job, on every pull request.

## After a change, run what it can move

Then push, and let CI's run be the full one:

- **Always:** lint (`adapters/stdlib/ci/ci.py run lint`), and once the PR
  has its number, the changelog check (`adapters/stdlib/ci/changelog.py`).
- **What you changed:** its own tests (`pytest adapters/stdlib/NAME`) and
  its mutants (`adapters/stdlib/mutants/mutants.py run NAME`).
- **What you wrote about it:** `test_docs.py` when prose changed, and
  `adapters/stdlib/readme/readme.py check` when a card did.
- **What leans on it, when everything does:** a change to `kernel.py` or the
  ports adds `tests:kernel`, `tests:vectors` and `ports`; to `ui/`,
  `tests:ui`; to `adapters/stdlib/ci/`, its own tests. A file a demo freezes
  (its FROZEN.json says which) adds that demo's tests, since a red PR there
  waits on someone else's freeze commit.

Name a part or a gate to run just that: `ci.py run lint`, `ci.py run
tests:kernel`. A gate that fails here and that `needs` names as unreachable
is the machine, not you; any other is yours.

**Edits that miss say nothing.** `ruff format` reflows lines, so a scripted
find-and-replace written against the text before formatting matches nothing,
silently. Check each one matched (assert the old text occurs once), never
replace a string that could be empty, and read the result or run the test
that should now pass.

## The job you're doing

- **An add-on.** Ten steps, each a check that fails when missed;
  `python adapters/stdlib/ci/new.py NAME` does four of them. Its tests run
  under a guard that holds every write to its card's promises. Read
  [docs/agents/add-ons.md](docs/agents/add-ons.md) before the first file.
- **A study**, like demo/php2shell: freeze the sources, questions, hit rule
  and pass rules in one commit before any question is asked, and dry-run it
  first with every question replaced by nonsense.
  [docs/agents/studies.md](docs/agents/studies.md) has the rest, and what a
  dry run misses.
- **A pull request.** Open it with
  `python adapters/stdlib/github/create_pr.py`, and leave the checkout alone
  while it runs. When main moves under a branch, regenerate what is made
  (`python adapters/stdlib/ci/made.py write`) and merge CHANGELOG.md by hand.
  [docs/agents/pull-requests.md](docs/agents/pull-requests.md), with a new CI
  row.
- **Search.** The kernel's rank is for answering; pointing at where to look
  and comparing texts are other jobs, with other tools.
  [docs/agents/searching.md](docs/agents/searching.md).
