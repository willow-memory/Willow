# For agents

What an AI agent working on willow needs before its first change. The rules
are [CONTRIBUTING.md](CONTRIBUTING.md) and [adapters/README.md](adapters/README.md);
read both. This page is the part of them that is easy to miss, and what CI
catches when it is missed. It adds no rule of its own.

[CLAUDE.md](CLAUDE.md) only points here, so there is one copy to keep.

## Never

- **Approve anything.** Code may search, suggest and record. It never writes
  a seal and never reads the person's key. Merging is the maintainer's call;
  CI's rows are evidence for it, not the decision.
- **Change `kernel.py` for an add-on.** The arrow points one way: an add-on
  uses the kernel, the kernel never names an add-on.
- **Loosen a check to get green.** No skipped test, no loosened card, no
  entry in `adapters/stdlib/mutants/accepted.json` to quiet a failure, and no
  code rewritten only so a harmless mutant stops surviving.
- **Edit two files by hand:** the verdicts in `constitution/declarations.json`
  and the answers in `constitution/reach.json` are the maintainer's.

## Set up

CI calls its tools as Python modules, so they must import, not just be on
the path. A tool that won't import is recorded as unreachable, which never
counts as a pass:

    pip install pytest ruff==0.16.7

The ruff version is the one `.github/workflows/ci.yml` pins.

`adapters/stdlib/ci/ci.py` calls them through the Python that runs it,
not whichever is first on the path. If they live in a virtual environment,
run it with that environment's Python and nothing else changes:

    VENV/bin/python adapters/stdlib/ci/ci.py run --box /tmp/ci-main

Run with a Python that lacks them, every lint, tests and mutants row comes
back unreachable.

## Before changing anything, take a baseline

    python adapters/stdlib/ci/ci.py run --box /tmp/ci-main
    python adapters/stdlib/ci/ci.py show --box /tmp/ci-main

Run it on `main` before your change, and again after. Compare the two by
gate and state, not row number: the only difference should be the rows your
change adds. Without the baseline, a tool your machine lacks looks like your
failure. To run one part, name it: `lint`, `tests`, `ports`, `demo`,
`deps`, `mutants` or `tools`. Keep the record folder outside the repo.

## An add-on, step by step

Each of these has been missed at least once, and each is a check that fails.

1. **Its folder** in `adapters/stdlib/` or `adapters/deps/`: the code, its
   tests, and its card, `README.md`, whose header is the idea's entry from
   `adapters/planned.json` with the same `writes` and `network` promises.
2. **Its command line in `COMMANDS`**, in `adapters/stdlib/ci/test_contract.py`,
   if a person runs it. Missing, it fails the contract test, and every other
   add-on's mutants then report their accepted breaks as stale.
3. **Its idea out of `adapters/planned.json`**, deletions only.
4. **Its place in FILES.md's tree**, alphabetically.
5. **The add-on list regenerated**, never edited:
   `python adapters/stdlib/readme/readme.py write`.
6. **A CHANGELOG.md entry** under `## Unreleased`, opening with the name in
   backticks, and ending with the pull request's number once it has one.
7. **Mutants**: `python adapters/stdlib/mutants/mutants.py run NAME` must
   kill every break. CI makes the six lowest-id breaks, and an entry in
   `adapters/stdlib/mutants/accepted.json` for a break those six don't
   include fails as stale: list only what CI's own run shows surviving.
   Run this **after** step 2 (its line in `COMMANDS`) and on a clean tree:
   a mutant is killed when the run's tests exit non-zero, so an add-on not
   yet in `COMMANDS`, or a stray uncommitted add-on folder, fails the
   contract test and marks every mutant killed — a false pass that CI, on
   the committed tree, then shows as the real survivors.
8. **Real data, not only fixtures.** Run it on the demo folders
   (`python demo/odile/make_life.py`, and the same for hollis, teodora and
   bernadette). An add-on can pass every test on hand-made files and still be
   wrong on a real folder; a test written from what the code does checks only
   that.
9. **If it goes online**, its tests use a server it starts on 127.0.0.1:
   the guard narrows only `none` and `loopback`, so a card naming a site
   lets the tests use this machine. Its `COMMANDS` row must still answer
   without the network, by an argument that settles the question before any
   fetch (an empty window of days, a closed local port); a row that reaches
   the real site is a test that goes online.
10. **Placeholders on its card.** `test_docs.py` reads a backticked name with
    a slash or a file extension as a path that must exist. Write a
    placeholder with angle brackets, as the pdf card writes
    `MIRROR/<same path>.txt`.

## The guard

An add-on's tests run under `adapters/stdlib/ci/guard/sitecustomize.py`,
which holds every write the add-on's own code makes to its card's `writes`,
and raises the moment it breaks one:

- **`to` means under the path in `--to` on the command line.** It reads
  `sys.argv`, so a test that calls `main()` in-process passes `--to` there
  too, or the write is judged as outside it.
- **Making a missing folder is a write.** An add-on that creates the parent
  of its `--to` file has written outside `to`; refuse a missing folder
  instead.
- **A box is written only through the kernel**, and any folder holding a
  kernel.json counts as one.
- **Scratch made with `tempfile` is the add-on's own**; a folder it names
  itself, even under /tmp, is not.
- **Never the key.** No add-on reads it, not even to copy it.

## An idea, not yet built

- **Ask the list first:**
  `python adapters/stdlib/similar/similar.py near "your idea in a sentence"`.
  It asks both ways: entries that hold half of your sentence's words, and
  entries half of whose words your sentence holds, so a long line still
  finds a short entry it contains. It shows, never refuses: you decide.
- **`adapters/planned.json` is sorted by name and written as
  `json.dumps(entries, indent=1, ensure_ascii=False)` plus a newline.**
  Rewritten any other way, every line of it changes.

## The kernel's rank is for answering

`kernel.rank` serves a passage only when it holds half the question's
content words. That is the promise that an answer the folder doesn't have is
never invented, and the eight beats in `test_kernel.py` test it.

- **Don't loosen it for recall.** A third of the words, or any two, finds a
  few more on code, but answers questions about something else several
  times as often, and breaks the beat where a folder holding only the
  question says so.
- **Pointing at where to look** is another job: `scan --rank bm25`, which
  always serves its top passages.
- **Comparing two texts** is another job again: count against the shorter
  one, so a long line doesn't hide a short one it contains.
- **Use the kernel's public names.** A page's text is `kernel.html_text`,
  not `_TAG` and `_lines_kept`.

## A new CI row

A gate added to `gates()` in `adapters/stdlib/ci/ci.py` (a demo, say) is
also named in the two lists of gates in `adapters/stdlib/ci/test_ci.py`.
Missed, `tests:adapters-*` fails, and `tests:strip-*` with it, since it runs
the same tests. A new test file needs nothing: the chunks are cut from the
files there are, and one not in `adapters/stdlib/ci/test-times.json` counts
as the median.

## A deps add-on's floor

The deps gate installs each add-on's pins, then its floor pins
(`adapters/deps/mcp/requirements-floor.txt`, say), again on the one Python the
deps job runs (`3.13` in `.github/workflows/ci.yml`). The floor rule names a
2020-era release, but such a pin often won't install on that Python: raise the
floor to the first version that does and say why on the card's `floor:` line
(twenty characters or more once the version is struck out, or `deps:floors`
fails). mcp's floor is raised this way.

A new deps package is also named by hand in one test fixture: the `uploaded`
dict in `test_a_floor_above_the_rule_needs_a_reason_on_its_card`
(`adapters/stdlib/ci/test_ci.py`). It stands in for PyPI, and `floors()` reads
it for every add-on's floor pins, so a package it doesn't list is a `KeyError`,
not a clean failure. Give it a release dated before 2021 and your floor's
version with its own date, so the rule picks the old one and your raised floor
still has to carry its reason.

## Edits that miss say nothing

`ruff format` reflows lines. A scripted find-and-replace written against
the text before formatting then matches nothing, and says nothing: the edit
just isn't there. Check each one matched (assert the old text occurs once),
and never replace a string that could be empty, which inserts the new text
between every character. Read the result, or run the test that should now
pass.

## A study, like demo/php2shell

A result tested against what anyone can rerun, as in
[demo/php2shell/README.md](demo/php2shell/README.md):

- **Freeze first.** The source hashes, the questions, the hit rule and every
  pass rule go in a FROZEN.json held by a test, as
  `demo/php2shell/FROZEN.json` is, committed alone before any question is
  asked. That commit is the pre-registration; a later change is a new
  freeze, with its reason.
- **Find the bugs without the results.** Run the pipeline once with every
  question replaced by nonsense ("qqqq zzzz"), so wiring breaks show up
  before the freeze, and say in the README what that dry run could see.
- **Verdicts are kernel rows**, one per pass rule, appended to a box outside
  the repo with the answers' and tools' SHA-256; `kernel.py verify` on it
  goes in the README.
- **Sources that aren't the repo's** (news, a company's pages) are kept by
  address, time and SHA-256, never their text, with a script that fetches
  them again and checks the hashes offline.
- **Write down what failed** with its frozen numbers, beside what held, and
  what was written after reading the sources.

## Pull requests

- **Several sessions can share a branch.** Fetch before you push, merge
  what's new, and never force-push.
- **Merging makes a merge commit**; squash isn't allowed on this repo.
- **Open it, then write its number** in CHANGELOG.md. Another pull request
  may take the number you guessed.
- **Work that needs another unmerged branch stacks on it.** An add-on whose
  idea, or whose card's link, exists only on another branch is built from
  that branch, and its pull request's base is that branch; built from
  `main`, it fails `test_docs.py` and clashes on `adapters/planned.json`.
- **In a Claude Code cloud session**, `gh pr create` is refused (GitHub's
  GraphQL isn't reachable); open it through the REST API instead:

      gh api repos/willow-memory/Willow/pulls --method POST \
          -f title=... -f head=BRANCH -f base=main -f body=...

  A shallow clone fetches only `main`, so a pushed branch shows as never
  pushed until its own fetch refspec is added.

## When main moves under a branch

Merge or rebase, then regenerate rather than hand-merge what is generated:
ADDONS.md and the README's add-on sections come from `readme.py write`, and
BUGS.md from `python adapters/stdlib/ci/bugs.py write`. CHANGELOG.md and
FILES.md are merged by hand: both sides' lines, in their order.
