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
8. **Real data, not only fixtures.** Run it on the demo folders
   (`python demo/odile/make_life.py`, and the same for hollis and teodora).
   An add-on can pass every test on hand-made files and still be wrong on a
   real folder; a test written from what the code does checks only that.

## When main moves under a branch

Merge or rebase, then regenerate rather than hand-merge what is generated:
ADDONS.md and the README's add-on sections come from `readme.py write`, and
BUGS.md from `python adapters/stdlib/ci/bugs.py write`. CHANGELOG.md and
FILES.md are merged by hand: both sides' lines, in their order.
