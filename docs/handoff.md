# Handoff: make-it-so, words-tlh and the stewart-crossover study

A note for the next session on branch `ccr-c47382e6-ea02ra`. Delete it
before the branch merges.

## State

- **make-it-so** (`adapters/stdlib/make-it-so/`): built, tested, mutants 6
  of 6, on this branch; no pull request yet. Its CHANGELOG entry needs the
  pull request's number once one is open.
- **words-tlh**: merged to main as #88.
- **demo/stewart-crossover**: freeze 1 (`b6cc2e2`) and run 1, 15 of 17
  held; freeze 2 (`0bd8719`) and run 2, 16 of 18 held. Its README has both
  runs and what failed in each. A freeze 3 is the person's call.
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

- Bug #89, filed: the kernel drops a line's text past its 500th character.
  A strict expected-to-fail test in test_kernel.py holds it; BUGS.md lists it.
- The person said "not yet" to the make-it-so pull request.

## Rules that bite

Never approve anything, never read the key, never change `kernel.py` for an
add-on, never loosen a check or add to the accepted list of mutants, never
hand-edit the verdicts in `constitution/declarations.json` or the answers
in the reach file. Fetch before you push, never force-push, merge commits
only.
