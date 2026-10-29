# known-gaps: the fleet's own security gaps, asked of the code their fixes changed

This is [php2shell](../php2shell/README.md)'s method pointed at the fleet's
own twelve known security gaps. php2shell asked questions in the words of a
PHP advisory and checked whether the code a fix changed came back. Here the
"advisory" is the gap as its finder wrote it (a gap record, an audit finding)
or, for four of them, as the fixer wrote it (a commit message).

**This page is the state at the first freeze.** It holds the claim, the
threats, what is frozen, the two rules that will judge it and the dry run.
There are no results yet: no real question has been written, and no scored
phase has run. They come in later bites, each frozen before it runs.

## The claim

For each of twelve security gaps the fleet found, fixed and recorded, a
question written from the gap's own text, asked of the code as it was just
before the fix, finds the code the fix changed more often than chance: in the
changed passages it ranks the hit early, and asked of the whole old tree it
reaches the fixed file.

Nothing in this folder yet tests that. What it holds is the apparatus: the
gaps, the fixes pinned by hash, and the scripts that fetch, ask, score and
record, checked end to end on questions that mean nothing (the dry run below).

## The gaps

`gaps.json` holds the twelve, redacted. Each names where its text came from,
the class of flaw, its fix (a merge, or a lone commit) and how strong the
source is:

| Kind | Gaps | What the question is written from |
|---|---|---|
| strong | KG01 to KG08 | a gap record or an audit finding: written by whoever found the flaw, before the fix |
| weaker | KG09 to KG12 | only the fixer's own commit message, written with the fix in hand, like php2shell's NEWS entries |

Every table reports the two kinds apart. KG03 and KG07 were fixed in two
repositories each, so the twelve gaps are fourteen units in `pins.json`
(KG03-kartikeya, KG03-willow-mcp, KG07-kartikeya, KG07-willow-mcp, and the
other ten by their gap id).

Three gaps are scored on some of their fix's files only (`files_scored`), each
chosen before any run:

- KG12's commit also carries two changes that are not security, so only the
  two files of its security findings count.
- KG05 and KG06 share one fix commit. Each is scored on the one file its own
  finding names (the operator's ruling, 2026-10-28): KG05 on
  `trust_owner_verbs.py`, KG06 on `ci_lint_pin.py`, with their full paths as
  the diff has them. `test_known_gaps.py` checks each is in the fix's diff and
  that its name is in the gap's text. `pins.json` records the files each diff
  touches.

## The threats

| Threat | What answers it |
|---|---|
| The questions are written with the fix in hand | The strong set's text predates its fix; the weaker set is reported apart. Questions are written from the redacted gap text only, by writers who never see the fix, and frozen before any run (a later bite). |
| The hit rule is chosen after seeing results | The rule is php2shell's rule 2 by position (see "The hit rule"), plus a short list of files that never count. `score.py` and the php2shell modules it runs on are frozen before any scored phase, and `test_known_gaps.py` re-hashes them. |
| The pass rule is chosen after seeing results | It was changed once, after the dry run and before any real question: see "Why phase 1 is judged by rank". The change is recorded here, and the dry run that prompted it is kept below. |
| The fix is a different diff on another machine | `resolve.py` pins the vulnerable and fixed commit, each side's git tree hash and the SHA-256 of the diff (php2shell's flags). `trees.py check` re-hashes all of it without git. |
| A tree is not what git stored | `trees.py` writes each tree as git stores it (php2shell's `write_tree`), then compares its hash to the pin. |
| Few changed passages make chance high | Phase 1 no longer asks for a hit in the top 3 of 3 to 60 passages. It judges the rank of the first hit against random orderings, and phase 2 asks the whole tree, where chance is small. |
| The apparatus finds things by accident | A null set is asked of every unit in phase 2, and that phase fails if the null questions' line hits are above exact chance. Phase 1 asks none: its sets are too small for a null to miss them by anything but luck. |
| An open gap leaks into a public branch | Only fixed gaps are in `gaps.json`. Candidates and unfixed gaps live in a private place and never enter this folder. |
| A model has seen the code | The fleet's repositories are newer than any model's training and were written largely by models; this is a different threat from php2shell's old CVEs and is named, not solved. |

## What is frozen

At freeze 1, FROZEN.json holds the SHA-256 of `gaps.json`, `pins.json`,
`resolve.py`, `trees.py`, `ask.py`, `score.py`, `origin.py` and `run.py`, and
of every tool file they run on, by import graph: `kernel.py`,
`adapters/stdlib/scan/scan.py`, `adapters/stdlib/todo/todo.py`,
`adapters/stdlib/ci/whose.py`, and php2shell's `make_trees.py`, `phase2.py`,
`phase3.py`, `phase4.py`, `score.py` and `score2.py` (the hit rule's real
code, the chance and the baselines). `test_known_gaps.py` re-hashes every one,
and fails on a change; a change is a new freeze, in its own commit, before the
phase that needs it runs. This means a php2shell re-freeze fails this folder's
test until this folder is frozen again, which is the point.

The freeze file is the operator's commit. Until it lands the freeze test skips
and says so. The commit that adds FROZEN.json also adds its line to FILES.md,
and from then on a missing FROZEN.json fails the test rather than skipping.

**Freeze 2** (the questions) adds to the same file, before any question is
asked of any code: the blind questions, byte for byte as the writers wrote them
(headers included), in `questions/local/` and `questions/claude/` (eight a gap
for each of the twelve, from the redacted gap text only) and
`questions/null/null.txt` (fifty about nothing to do with security, written
with no input); `questions/inputs.md`, the only thing the blind writers were
given; and `flag.py`, the rule that flags question lines holding identifiers.
It also changes three files frozen at freeze 1, `ask.py`, `run.py` and
`score.py`, only to read the questions per writer and tally them (below); no
gate is changed. The set is committed by the operator, with FROZEN.json
rebuilt over it.

`spread.py` and `outside.py` are stubs that exit 2. They are not frozen, and
are written in their own bites.

### The questions and the flagged-line rule

The writers were told to write without identifiers. A question line is
`flagged` when it still holds one, by a single pattern fixed before any
question was asked: an underscore between letters or digits, a dot between
lowercase letters, `()`, a lowercase letter followed by a capital, a slash,
`:` or `#` before a digit, or seven or more hex digits in a row. One exception:
`allow_localhost` is a flag a user types, so a line whose only match is that
word is not flagged. Fixed on these counts, which `test_known_gaps.py` asserts:
the local writer 48 of 96 lines flagged (46 after the exception), the Claude
writer 1 of 96 (0 after), the null set 0 of 50.

`ask.py --questions` takes the `questions` folder: a gap's questions are its
`questions/{writer}/{ID}.txt` lines with headers skipped, and the null set (in
phase 2 only) is `questions/null/null.txt`. Each answer row carries its
`writer` and whether it is `flagged`. The gates pool both writers' lines as one
set, flagged or not, by the rules already frozen: a pair a line. Phase 4,
the writers compared, is reported and never judged: `run.py found` and
`run.py before` print, per ranker and writer, the questions asked and those that
hit (in the top 3 for phase 1, the top 10 for phase 2), twice: with every line,
and with the flagged lines left out.

## The scripts

All stdlib, each takes its paths as arguments, writes only what it is told,
and exits 0, 42 or 2 as the kernel does.

| Script | Does |
|---|---|
| `resolve.py` | gaps.json to pins.json, from the fleet's own local repositories (`--repos`). Refuses a merge that does not name its pull request, and a scored file that is not in the diff. |
| `trees.py` | `fetch` writes each unit's vulnerable (old) and fixed (new) tree and the fix diff; `check` holds them to the pins. No network. |
| `ask.py` | per unit, holds each tree to its pinned git tree hash (a missing or different tree is refused), builds its index afresh with `scan.py` into a temporary folder and renames it into place, every run, never reusing one, and asks the unit's questions three ways: the kernel's rank, BM25, a grep baseline. `found` ranks every passage the fix changed; `--mode before` asks the whole old tree, top 10. Also writes the unit's counts, its chance, and the tree hashes it checked and a SHA-256 over each index it asked, so a verdict names what was asked. |
| `score.py` | the hit rule below, per answer, with the rank of the first hit and the `path:first-last` ranges that hit. |
| `origin.py` | for every hit range, `whose.py` at the vulnerable commit: the commit that wrote it, its date, the gap, audit and pull request ids its message cites, and the days before the fix. |
| `run.py` | `found` (phase 1) and `before` (phase 2): scores the answers, applies the pass rules per kind, writes each rule as a kernel verdict row. |
| `spread.py`, `outside.py` | not in this bite. |

### The hit rule

Rule 2 of php2shell (`demo/php2shell/phase3.py`'s `changed`), by position: a
passage hits when its line range in the old file, from its first line to its
last, overlaps a line the fix removed, or the one unchanged line just before
or just after a run of added lines, taking the old-side line numbers from the
diff (a merge's first parent is the old side). A line counts when it is at
least 8 characters and 2 of the kernel's words long.

**This departs from php2shell's rule.** php2shell's `hit` matches a passage's
lines to the changed lines by their stripped text, anywhere in the file, so a
line that reads like a changed line counted wherever it sat. Loki's audit of
this folder found that 68 of the 159 hit passages over the old trees lay
entirely outside every hunk of their fix, which makes "line level" mean "a
line that reads like one the fix changed", not "the lines the fix changed".
Position is the rule here. The text match stays as a reported column:
`hit_by_text` (passages it would count), `text_only` (of those, not a hit by
position) and `text_outside_hunks` (of those, in no hunk at all), per unit in
ask.py's stats line and in the dry run below. Phase 1's changed sets use the
same rule, and origin.py blames only the positional hit ranges.

**Lines are counted the way git counts them**: a newline ends a line and
nothing else does. The diff is read that way, and so is a passage's span.
The kernel is not: it cuts a file into passages with `str.splitlines()`,
which also breaks on a vertical tab, a form feed, the control characters
0x1c to 0x1e, 0x85, U+2028, U+2029 and a carriage return not followed by a
newline. After one of those its passage line numbers run ahead of git's, so a
position in that file would be wrong, silently. The kernel is a frozen tool and
is not edited; instead, a counted file of a vulnerable tree that holds one of
those characters is **unreachable**: `trees.py check` lists it per file,
`ask.py` records it (`unreachable_files` in the stats line) and gives it no
positions, and `score.py` does the same, so no passage of it is ever a hit,
rather than a hit on a shifted line. None of the 13 distinct vulnerable trees
holds one in a counted file: 3,195 counted files, 0 with such a character
(Loki found that KG09's two are in a test file, which never counts). The first outside
control (phase 6, cpython) has form feeds, so this matters there.

A known limit of the reported `hit_by_text` column, which is not the rule:
php2shell's parser reads a removed line that begins `-- ` (shown in the diff as
`--- `) as a file header and drops that file's removed lines, so the text
column can undercount. Positions are read by the hunk header's counts and are
not affected.

Never counted: a path with a folder named test, tests, testing, spec or
changes; test_*.py, *_test.py, conftest.py; NEWS, UPGRADING, ChangeLog,
CHANGES, CHANGELOG files, RELEASE-NOTES.md; version.h, VERSION, version.txt,
version.py, _version.py and the release manifest. php2shell's own list is
kept and added to, because the fleet writes its tests beside its code.

A passage is `hit`, `file` (its file is one the fix changed, no counted line)
or `miss`. This differs from php2shell's `core` / `any` / `file` / `miss`:
php2shell's CORE list was chosen by hand for one bug and there is no such list
here. Line level means `hit`; file level means `hit` or `file`.

### Phase 1: found it (rule A)

Each question is asked of the passages the fix changed, and all of them are
ranked. For a unit with `files_scored` (KG05, KG06, KG12), the changed set,
its random ordering and its chance hold only passages of those files; a
passage of any other file the fix touched is never in it (a test holds this).
For a (question, unit) pair the statistic is the rank of the first
passage that hits; a passage the ranker does not return counts as last, which
is conservative. The null is a uniform random ordering of the same passages,
so a pair's chance of each first-hit rank is exact: with n passages, h of them
hits, C(n-r, h-1) / C(n, h). A group's statistic is the sum of 1/rank over its
pairs, and its p-value is Monte Carlo over 100,000 random orderings with a
fixed seed, both recorded in the output. The top-3 hit rate stays in the
output, with each unit's random-draw chance beside it.

| Rule | Passes when |
|---|---|
| rank, bm25, strong | the strong set's sum of 1/rank beats random orderings, one-sided p < 0.01 |
| rank, bm25, weaker | the same for the weaker set |

The kernel's and grep's results are reported beside, never gates. Phase 1 asks
no null question (Loki's audit: with a changed set of 3 to 60 passages, and
some wholly hits, any null question with one common word puts a hit in its top
3, so a rule that fails on that fails by construction). Nulls are judged in
phase 2.

### Phase 2: before the fix (the main judged test)

Each question is asked of the whole vulnerable tree, top 10, and scored at the
line level (a passage overlapping a changed line, by position) and the file
level (any passage of a scored file). The chance is exact: php2shell's phase4
`chance_one` for a pair, `poisson_binomial_tail` for a group, and `recall_at`
for the hits. The null questions are asked here, of every unit.

| Rule | Passes when |
|---|---|
| line level above chance, bm25, strong | questions with a line hit in the top 10 beat chance, one-sided p < 0.01 |
| line level above chance, bm25, weaker | the same for the weaker set |
| null questions not above chance, bm25 | at least one null question was asked and the null set retrieved something (a set that retrieves nothing is "unreachable: the null set retrieved nothing", never a pass), and the null line hits are not above exact chance for the passages each question was actually served: the same tail, p >= 0.01 |

The file level, and the kernel's and grep's results, are reported, never gates.
For a unit with `files_scored`, only passages of those files count at either
level.

Which level gates, in order. The first amendment put the gate at the file
level; the desk did that without asking the operator. The operator then ruled
(2026-10-28, "I'll take your recommendation on both") that phase 2 is judged
at the line level, which asks for the lines the fix changed, not just their
file. The file level stays in every table because it is the weaker claim and
the cheaper one to hit.

### Why phase 1 is judged by rank

The first plan judged phase 1 by the top-3 hit rate against 10,000 random
draws of 3 changed passages. The dry run below showed that rule cannot be won:
a fix changes only 3 to 60 passages, so three random ones already hit its
lines 71% to 100% of the time (90% pooled for the strong set), and at 100%
(KG01, KG04, KG09, KG11) no ranking could beat chance. The operator chose rule
A on 2026-10-28, after the dry run and before any real question was asked, and
made phase 2 the main test: asked of a whole tree of 1,000 to 39,000 passages,
chance is 0.1% to 9% a question (the table below, now by position).

## Reproduce

Needs git and the fleet's repositories checked out side by side (they are
read, never written). Python 3.9 or newer.

    python demo/known-gaps/resolve.py --repos REPOS --out pins.json
    python demo/known-gaps/trees.py fetch --to WORK --repos REPOS
    python demo/known-gaps/trees.py check --to WORK
    python demo/known-gaps/ask.py --to WORK --ix WORK/ix/UNIT --questions QUESTIONS --out WORK/ans/UNIT.jsonl --unit UNIT
    python demo/known-gaps/ask.py --to WORK --ix WORK/ix/UNIT --questions QUESTIONS --out WORK/ans/UNIT.jsonl --unit UNIT --mode before
    python demo/known-gaps/run.py found --to WORK --answers ANSWERS --box BOX --out SCORED
    python demo/known-gaps/run.py before --to WORK --answers ANSWERS --box BOX --out SCORED
    python demo/known-gaps/origin.py --repos REPOS --scored SCORED --out ORIGINS
    python -m pytest demo/known-gaps

Run `ask.py` once a unit and a mode: Kart kills a task at 300 seconds, and the
slowest unit rebuilt its indexes in under 7 seconds (below).

## The dry run

Run on Kart on 2026-10-28 over the fourteen pins, with one meaningless
question for every gap and one for the null set (`qqqq zzzz`). Its purpose is
plumbing: every tree fetched and checked, every index built, every answer
scored, the verdict rows written and the record verified. It was run twice:
the first time, with the top-3 rule, found the problem above; the second,
after the amendment, ran both phases.

| Step | Result |
|---|---|
| `trees.py fetch` (14 units, 28 trees) | 4 s; all 14 old, new and fix lines `matches`, exit 0 |
| `ask.py`, first run (14 tasks, found, top 3) | all exit 0; timings below |
| `ask.py`, second run (14 units, found and before) | all 28 exit 0; 0.08 to 1.3 s each, the indexes already cached |
| `run.py found` | exit 42, as it must be: no hits, so the rank statistic sits far below random (strong 1.42 against 7.50 expected, p 1.0; weaker 0.81 against 3.17, p 1.0). Run after the amendments: the `files_scored` limit, positional hits, no null question. |
| `run.py before` | exit 42, as it must be: 0 line hits against 0.35 expected (strong) and 0.010 (weaker); file level 0 against 4.52 and 0.39, reported. The 14 null questions: 0 line hits, and the null gate passes only barely: the meaningless words matched something in 2 of 14 trees, so bm25 served 2 passages in all (12 questions served nothing) and the chance for what was served is 0.0003. A real null question serves ten. |
| `trees.py check` | after the N1 change, lists any counted file with a character that shifts the kernel's lines: none of the 3,195 counted files in the 13 distinct vulnerable trees |
| `ask.py`, third run (amendment 5, every index rebuilt from the pinned tree) | all 28 exit 0; the rebuild takes 0.1 to 6.7 s a unit (below); every count unchanged, and an index rebuilt for `before` has the same SHA-256 as the one rebuilt for `found` |
| verdict rows | 5 written (2 for phase 1, 3 for phase 2); the record's chain holds |
| `origin.py` | 0 ranges to look up, so 0 rows (nothing hit) |

Rebuild time per unit in the third run (the vulnerable index, plus the fixed
one for `found`; the units ran in seven Kart tasks, some at once):

| Unit | found | before |
|---|---|---|
| KG01 | 0.1 s | 0.1 s |
| KG02 | 0.1 s | 0.1 s |
| KG03-kartikeya | 0.2 s | 0.1 s |
| KG03-willow-mcp | 4.8 s | 2.8 s |
| KG04 | 2.4 s | 1.2 s |
| KG05 | 5.0 s | 3.7 s |
| KG06 | 5.0 s | 3.9 s |
| KG07-kartikeya | 0.2 s | 0.1 s |
| KG07-willow-mcp | 6.7 s | 3.4 s |
| KG08 | 0.3 s | 0.2 s |
| KG09 | 3.1 s | 1.5 s |
| KG10 | 2.5 s | 1.3 s |
| KG11 | 2.3 s | 1.1 s |
| KG12 | 5.5 s | 1.8 s |

Per-unit timings of the first run (index and ask are `ask.py`'s own; the 14
tasks ran at once on one machine, so each is slower than it would be alone):

| Unit | Old tree files | Indexed | Asked | Task total |
|---|---|---|---|---|
| KG01 | 36 | 0.2 s | 0.1 s | 0.4 s |
| KG02 | 39 | 0.3 s | 0.1 s | 0.4 s |
| KG03-kartikeya | 52 | 0.4 s | 0.1 s | 0.6 s |
| KG03-willow-mcp | 836 | 10.3 s | 0.6 s | 11.0 s |
| KG04 | 644 | 5.8 s | 0.3 s | 6.3 s |
| KG05 | 857 | 15.9 s | 1.1 s | 17.2 s |
| KG06 | 857 | 23.3 s | 2.2 s | 25.8 s |
| KG07-kartikeya | 51 | 0.9 s | 0.2 s | 1.3 s |
| KG07-willow-mcp | 821 | 22.8 s | 1.9 s | 25.0 s |
| KG08 | 107 | 1.5 s | 0.3 s | 2.0 s |
| KG09 | 380 | 10.9 s | 0.4 s | 11.5 s |
| KG10 | 333 | 6.8 s | 0.4 s | 7.5 s |
| KG11 | 297 | 5.9 s | 0.4 s | 6.5 s |
| KG12 | 640 | 9.4 s | 0.5 s | 10.1 s |

### What the dry run could see

- **The plumbing, nothing else.** The questions are nonsense, so every answer
  is empty and every score is `miss`. No number says anything about the
  method. It shows that a fresh checkout can fetch, index, ask, score and
  record both phases, and that each unit fits well inside Kart's limit.
- **Hits by position and by text, per unit.** Phase 1 columns are the changed
  set before and after the `files_scored` limit, and its hit passages by
  position (the rule), by text (php2shell's, reported) and the text hits in no
  hunk at all. Phase 2 columns are the old tree's passages, hits by position,
  by text, the text hits that are not hits by position, those in no hunk, the
  passages in a scored file, and the chance that 10 drawn at random hold a
  positional hit:

| Unit | Changed, before limit | After | By position | By text | Text, no hunk | Tree passages | By position | By text | Text only | Text, no hunk | In a scored file | Chance (line) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KG01 | 3 | 3 | 1 | 1 | 0 | 1072 | 6 | 5 | 0 | 0 | 193 | 0.055 |
| KG02 | 16 | 16 | 7 | 7 | 0 | 1158 | 8 | 15 | 7 | 7 | 235 | 0.067 |
| KG03-kartikeya | 33 | 33 | 18 | 19 | 1 | 2036 | 20 | 30 | 11 | 11 | 294 | 0.094 |
| KG03-willow-mcp | 8 | 8 | 3 | 3 | 0 | 36734 | 4 | 7 | 3 | 3 | 75 | 0.001 |
| KG04 | 4 | 4 | 4 | 4 | 0 | 22456 | 6 | 6 | 0 | 0 | 140 | 0.003 |
| KG05 | 18 | 4 | 4 | 4 | 0 | 39143 | 5 | 15 | 10 | 10 | 276 | 0.001 |
| KG06 | 18 | 4 | 4 | 4 | 0 | 39143 | 5 | 5 | 0 | 0 | 76 | 0.001 |
| KG07-kartikeya | 12 | 12 | 5 | 5 | 0 | 1766 | 5 | 6 | 1 | 1 | 266 | 0.028 |
| KG07-willow-mcp | 60 | 60 | 20 | 20 | 0 | 35090 | 21 | 79 | 58 | 58 | 2497 | 0.006 |
| KG08 | 43 | 43 | 22 | 23 | 1 | 2445 | 23 | 52 | 29 | 29 | 153 | 0.090 |
| KG09 | 3 | 3 | 1 | 1 | 0 | 15318 | 1 | 1 | 0 | 0 | 89 | 0.001 |
| KG10 | 6 | 6 | 3 | 3 | 0 | 13191 | 3 | 3 | 0 | 0 | 214 | 0.002 |
| KG11 | 7 | 7 | 6 | 6 | 0 | 11717 | 6 | 11 | 5 | 5 | 169 | 0.005 |
| KG12 | 18 | 6 | 5 | 6 | 1 | 26109 | 5 | 10 | 5 | 5 | 116 | 0.002 |

  Over the 14 old trees the text rule counts 245 passages and the position
  rule 118; 129 of the text hits (the "text only" column) lie in no hunk at
  all. Loki's 159 and 68 are the same count over the 12 units it probed,
  without the two willow-mcp trees (245 less 86 is 159; 129 less 58 and 3 is
  68). The far hits are in the big files: KG07-willow-mcp 58 of 79, KG08 29 of
  52, KG03-kartikeya 11 of 30. A few units hit by position in a
  passage the text rule does not count (KG01 6 against 5): a line longer than
  the kernel's 500-character chunk is cut short in the passage, so its text no
  longer reads like the diff's line, but its position still does. No file in
  the hit rule's files holds a line separator Python splits on and git does
  not (checked), so passage line numbers and the diff's agree.

  The limit (amendment 2) changes three rows: KG05 and KG06 from 18 to 4
  changed passages and KG12 from 18 to 6, each the passages of its own scored
  file or files. KG05, KG06 and KG04 have every passage of the set a hit, so in
  phase 1 a pair on those units has its first hit at rank 1 under every
  ordering and adds nothing to the statistic that chance does not already give
  (KG12 has 5 of 6). Phase 2, which asks the whole tree, is where those units
  are tested.
- **The file level's chance is large in places.** Phase 2's file level counts
  any passage of a scored file: 75 to 2,497 passages of a tree. Its chance
  for 10 passages, summed over the dry run's pairs, is 4.52 file hits expected
  from the 10 strong pairs and 0.39 from the 4 weaker ones, against 0.35 and
  0.01 for the line level. The file level can be won, but is a weaker claim
  than the line level; both are reported.
- **The nulls.** The 14 null questions (one a unit) hit nothing, because no
  question meant anything. The null gate passes on 0 hits against 0.36
  expected, and the test that it fails on hits above chance runs on a fixture.
  That is not yet a test of the null rule on real questions.

## What the first real run still owes

Questions (a later freeze), the real runs of phases 1 and 2, phases 3, 4 and 7,
the spread and the outside control. None is run, and nothing here claims a
result.
