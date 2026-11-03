# The five repos in time, and in their own words, 2026-11-03

A third kind of stack. Not what's wrong (the first) or what's shared (the
second), but when each repo moved and what its code admits. Two mirrors
were written outside every repo: each repo's commits as dated files
(git-history, after deepening the three shallow clones) and its comments
and docstrings as passages (code-comments). A second box, hist-box, has
the mirror folder as its pile. The stack ran as three files: `history.md`
(45 steps, 4 min 27 s), then `voice.md` and `commits.md` to redo the two
pools that the first run showed were asked wrong.

## When each repo moved

| repo | commits | span | per day at the peak | name Claude as co-author | merges |
|---|---|---|---|---|---|
| Willow | 1,233 | 2026-10-22 to 11-02, 12 days | 289 (Nov 2), 278 (Oct 24) | 1,045 | 342 |
| redential-cli | 93 | 2026-07-08 to 07-24, 17 days | 13 | 80 | 0 |
| socratic-fork | 71 | 2026-02-28 to 08-14 | 39 in July | 6 | 3 |
| glapagos | 15 | 2026-06-04 to 06-06, 3 days | 9 | 0 | 0 |
| NaturalConv | 19 | 2021-02-26 to 03-18 | 3 | 0 | 0 |

Two repos were written in a burst with Claude on nearly every commit.
Willow merges and redential-cli never does. socratic-fork sat for four
months between its first README and its real start in July. glapagos is
three days old in git terms, whatever its documents say. The counts are
read from the mirror files, not from a step; `people` found the same
thing its own way: Claude is the most named person across the five
histories, in 1,252 files.

**No repo has ever reverted.** Zero of 1,431 commit subjects say revert.
The seven mentions of the word are all inside diffs and comments.

**Firsts, by subject line.** Willow: "Release v0.1.0" on 2026-10-23 and
"Security: pin Pillow and pypdf past their advisories" on 10-31.
redential-cli: "Scaffolding: principles, bundle schema v1, security and
contributing policies" on its first day, 07-08, and "Release 0.6.0" on
07-22. glapagos: "ci: add GitHub Actions" on its first day. socratic-fork:
"Add initial README" on 2026-02-28. NaturalConv: "Initial commit" on
2021-02-26, then README edits.

**On this day.** Nothing in any repo's history fell on a November 3rd in
an earlier year. The only hit is a demo calendar's car registration.

## What the code admits, each repo in turn

socratic-fork is prose only and NaturalConv's one script has no comment,
so this is Willow, redential-cli and glapagos. glapagos answered one
question of twelve: its eleven commented files are mostly placeholders,
and `tests/integration/test_placeholder.py` says so ("will be replaced by
real integration tests once the API endpoints ... exist").

- **Not implemented yet.** redential-cli `src/login.ts:102`: "RFC
  8628-shaped device authorization grant. Nothing on the server side of
  this exists yet." The login command is written for a server that isn't.
- **We assume.** redential-cli `src/git.ts:133` escapes author emails
  "ASSUMING POSIX". Willow `adapters/stdlib/ci/alone.py:6` assumes an
  add-on is a folder anyone can copy beside the kernel, and tests that.
- **False positive.** redential-cli `src/import-detect.ts:7`: "Deliberately
  regex-based, not a real parser per language (that would mean 5 new
  dependencies)", and line 67 names the false positive it then can't catch.
- **On purpose, by design.** redential-cli `src/explain-command.ts:24`: "NO
  --json / NO machine-readable output / NO file writes, ON PURPOSE".
  Willow `adapters/stdlib/serve/serve.py:7`: "The model never sees a box."
- **Never.** redential-cli's explain command: progress goes "ALWAYS stderr,
  NEVER the log callback". Willow's warranties: a date that reads either
  way round "is never guessed".
- **Slow.** redential-cli `src/scan.ts:303` loops instead of spreading
  tens of thousands of values into `Math.max`. Willow has a whole add-on
  for it, slow-tests.
- **Deprecated.** redential-cli `src/proof-graph/infer.ts:135` keeps a
  deprecated alias for the Stripe slug. Willow's only use is the outdated
  add-on reading registries.
- **Workaround, hack.** No comment in any of the three says either word.
- **Careful.** Only Willow, once, in hook-fuzz's test.

**One lead.** redential-cli `src/config.ts:23` reads: Public by design
(CLAUDE.md: "solo SITE_URL (pública)"). That is a Spanish fragment in a
source comment, which the repo's own CLAUDE.md forbids ("a single Spanish
comment breaks the professional impression ... translate it"), and it
quotes a line the current CLAUDE.md no longer holds.

## Where the stack was asked wrong, and what that says

**Diffs drown subjects.** git-history writes each commit with its full
diff, so Willow's 1,233 commits are 52 MB of mostly other people's words.
Asked "revert" or "the first commit", fair-merge served diff hunks. Asked
"subject: revert", it served headers, because the field name is in every
header and the kernel's half-the-words rule then lets a header through
on one word. That is the trick's limit too: NaturalConv's "Update
README.md" answered all twelve questions, since its headers hold
"subject" and little else.

**Diffs re-date commits.** first-mention dated "privacy" and "words list"
to 1958-12-03 and "constitution" to 2025-06-18. Those are dates inside
diffs (a demo character's birthday, a fixture), and the kernel dates a
line by the nearest date above it in the file, so a diff's own dates
re-date the commit's lines beneath them. The `date:` field on line 2 is
read as a field, not a date line, and `gaps` doesn't see the mirror as a
log for the same reason.

Both are chunks for Willow's git-history to fill, found by using it: a
`--messages` option that writes subject and body without the diff, and a
date written where the kernel reads one (at a line start, or on each
line), so a commit pile dates and gaps like a diary. Neither needed an
agent to find; the stack shows exactly which rule produced which answer.

## Files

| file | what |
|---|---|
| `history.md`, `voice.md`, `commits.md` | the three stacks |
| `runs-20261103T014709Z.out`, `…015251Z.out`, `…015327Z.out` | their pages |
| `mirror/commits/<repo>/`, `mirror/comments/<repo>/` | the two mirrors, 1,431 and 846 files |
| `hist-box/` | the box over the mirror folder |
