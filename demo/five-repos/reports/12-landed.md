# Report 7: landed in Willow, 2026-11-03

Pull request **#211** on willow-memory/Willow, from the branch
`ccr-f3b8798e-hkrn0a` onto main: nine commits, one per piece, nothing
squashed, nothing force-pushed.

## What landed

| commit | piece |
|---|---|
| stack: an eighth example, a folder of repositories | `adapters/stdlib/stack/examples/repos.md`, with the stack card's count and FILES.md's tree |
| git-history: `--messages` writes each commit without its diff | the diff-dates lead from the history stack; a test that the diff is out and the subject stays |
| three-two-one: a copy that holds but is behind the box says how far | `holds (1 row, 2 rows behind the box)`; a test with a box that moved on |
| in-process: a reply that only cites is proposed to no one | a bare `[1]` or a path in brackets; a test over three such replies |
| hook-fail-closed: one line when the hook breaks, never its traceback | the hook-fuzz disagreement; the test now asserts no traceback |
| hosts: `show claude-code` says where Claude Code's way in is | the refusal names the prompt hook; a test |
| changelog: six entries | under Unreleased, Added and Changed |
| three-two-one: accept the one surviving break | `box_rows`' starting number, with its reason, in accepted.json |
| changelog: #211 | the number on all six entries |

Not landed: the a11y heading in `adapters/stdlib/ci/README.md`, which
exists only on #199's branch and is named in the pull request body for
that branch's author.

## What held it to the rules

- The edited add-ons' tests, 51 across five add-ons and the stack; the
  docs test (every path a card names exists); 338 contract tests.
- Mutants on the four stdlib add-ons: 6 of 6 killed on three, 5 of 6 on
  three-two-one with the survivor accepted and reasoned (the box always
  sets `box_rows` before any copy is compared). in-process is a deps
  add-on, which mutants doesn't cover.
- CI on main, the full run with `cores.py` in a separate worktree: 384
  satisfied, 11 unreachable (tools this machine lacks), 2 failing
  (`deps:ocr`, no tesseract here). On the branch, every gate the change
  reaches by test-impact's import graph, plus lint: all satisfied, the
  same states as on main. The full run took 100 minutes on four CPUs,
  which is why the branch run was cut to what the change can reach, and
  the pull request body says so.

## Loose ends in the scratch folder, not in any repo

Nine suggestions wait on a seal in `proof-box` (six from the stacks'
findings, three empty ones from the model, the first casebook one the
wrong version). A served scope and a session bundle wait likewise. One
daily-word guess is left on `play-box`. The model, its server extras and
the 193 MB GGUF are in the scratch folder and nowhere else.
