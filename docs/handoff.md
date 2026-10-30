# Handoff: make-it-so, words-tlh and the stewart-crossover study

A note for the next session on branch `ccr-c47382e6-ea02ra`. Delete it
before the branch merges.

## State

- **make-it-so** (`adapters/stdlib/make-it-so/`): built, tested, mutants 6
  of 6, on this branch; no pull request yet. Its CHANGELOG entry needs the
  pull request's number once one is open.
- **words-tlh**: merged to main as #88.
- **demo/stewart-crossover**: freeze 1 (`b6cc2e2`), Wren's files after it,
  and run 1: 15 of 17 rules held. Read its README's results and "What failed".
  The study uses make-it-so, so it stacks on this branch.

## Established

Patrick Stewart died on 28 October 2026: Deadline, Variety and CNN, each
held in `demo/stewart-crossover/sources.json`. (An earlier note here called
it unverified; the reports came on 29 October.)

## Decided by the person

Wren Castellano, 2020 to 2023; all four traps; published public sources
are outside willow-mcp's consent gate; the Gerald parody stays in ("if
Gerald shows up, we're on the right track").

## Open

- The kernel keeps a line's first 500 characters and drops the rest
  (`kernel.py`, `chunks`, `line[:MAX_CHUNK]`). Found by run 1; not in
  LIMITS.md or BUGS.md. The kernel is the maintainer's to change.
- Whether to make a freeze 2 for the two failed rules. A new freeze is its
  own commit with its reason; run 1 stays as it is.

## Rules that bite

Never approve anything, never read the key, never change `kernel.py` for an
add-on, never loosen a check or add to the accepted list of mutants, never
hand-edit the verdicts in `constitution/declarations.json` or the answers
in the reach file. Fetch before you push, never force-push, merge commits
only.
