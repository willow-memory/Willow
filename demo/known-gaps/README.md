# known-gaps: the fleet's own security gaps, asked of the code their fixes changed

This is [php2shell](../php2shell/README.md)'s method pointed at the fleet's
own twelve known security gaps. php2shell asked questions in the words of a
PHP advisory and checked whether the code a fix changed came back. Here the
"advisory" is the gap as its finder wrote it (a gap record, an audit finding)
or, for four of them, as the fixer wrote it (a commit message).

**This page is the state after the first real runs.** It holds the claim, the
threats, what is frozen, the rules that judge it, the dry run, and, at the end,
the results of phases 1, 2, 3, 4 and 7 on the frozen questions. Phase 1 failed
its gates; phase 2 passed all of its. Phases 5 and 6 have not run.

## The claim

For each of twelve security gaps the fleet found, fixed and recorded, a
question written from the gap's own text, asked of the code as it was just
before the fix, finds the code the fix changed more often than chance: in the
changed passages it ranks the hit early, and asked of the whole old tree it
reaches the fixed file.

The Results section at the end tests that: the second half held (asked of the
whole old tree, the questions reach the fix's lines far above chance) and the
first half did not (ranking inside the changed passages is no better than a
random order). The dry run below shows the apparatus on questions that mean
nothing, before any real question was asked.

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

## Results

Run on Kart on 2026-10-28 at freeze 2 (d8d741a): the working tree clean, the
suite green (41 passed), every tree matching its pin. Every question is the
frozen set, unedited: eight a gap from each writer (local, Claude), 96 each,
and fifty null questions. Phase 1 asked each gap's 16 questions of its
changed passages (a pair is a question and a unit: 160 strong, 64 weaker);
phase 2 asked them of the whole old tree, and the fifty nulls of every unit
(700 null pairs a ranker). Nothing was re-asked or reworded, and every output
sits in a private folder; this page quotes the numbers.

The verdict rows are in a kernel record made for the run, and
`kernel.py verify` of it says: `the chain holds: 6 rows, 0 sealed`. Its 5
verdict rows are phase 1's two rules and phase 2's three, each stamped with the
SHA-256 of the answers file and of the tools below.

| What | SHA-256 |
|---|---|
| phase 1 answers (14 units, joined) | 2c244eea248acffb654e2ea9bef664f859f315cd2cf0762bdd2308d6ade70206 |
| phase 2 answers | ffe482eaef1aacc438c311329045fe74eace7b6704c6cbba26b66f1106aaf02a |
| phase 1 scored rows | aa728ee273b08f162c39af68729ced05faf32849411faa41d1545b8e79f25318 |
| phase 2 scored rows | 5bdcb4d0fb236162d8c59d65efd2cb08460d9f03646a8262136fe5fe08231f9f |
| phase 1 result | 47f1886dcdb9f2c038fc3829f681e12e55a3dd8deed0938cbe2237e8d4f18f6e |
| phase 2 result | 171ff256fc436008d41bd826bc586aa41ba3800e6ecf6d1d99ad4f0e2215cd23 |

The tools, as FROZEN.json holds them (first 12 digits): kernel.py be6e99a1952d,
scan.py ff3717e7f280, todo.py 56be091ebcb3, whose.py 0eceae102467, php2shell's
make_trees.py 50bbcb8d4d12, phase2.py 5ca4e4a1a80e, phase3.py 1328d97cd50f,
phase4.py c8d9315b7a11, score.py 084d0a3a0d7e and score2.py ddf0bde4ff82; this
folder's trees.py 115913787b59, ask.py 41f4b1084fac, score.py 6dc8d70fdc7a,
run.py 50eb674fc551 and flag.py e6c24ea59570. Timings on the real question
count: indexing a unit takes 0.2 to 7.5 s, phase 1's ask 0.3 to 8.3 s a unit,
phase 2's ask 1.3 to 50 s a unit (66 questions on a tree of up to 39,000
passages), `run.py found` 12 s for its 100,000 random orderings, `run.py before`
0.3 s; with a dozen tasks at once on one machine a four-unit task took up to
100 s, inside Kart's limit.

### The gates

| Gate | Verdict | The numbers |
|---|---|---|
| phase 1, rank, bm25, strong | **failed** | 160 pairs; sum of 1/rank 117.27, random orderings give 119.94; p = 0.787 |
| phase 1, rank, bm25, weaker | **failed** | 64 pairs; 45.35 against 50.70 expected; p = 0.997 |
| phase 2, line level, bm25, strong | **passed** | 44 of 160 questions have a line hit in the top 10, 5.55 expected; p = 5.6e-30 |
| phase 2, line level, bm25, weaker | **passed** | 3 of 64, 0.16 expected; p = 5.6e-4 |
| phase 2, null questions, bm25 | **passed** | 14 of 700 null pairs hit, 17.84 expected at chance; p(above chance) = 0.859 |

`run.py found` exited 42 (a rule failed) and `run.py before` exited 0.

### Phase 1: find it among the changed passages (failed)

Each question ranks every passage the fix changed; the statistic is the rank
of the first one that hits. A ranker that does no better than a random order
scores about what chance does, and bm25 did:

| Ranker, group | Pairs | Sum of 1/rank | Random orderings | p |
|---|---|---|---|---|
| kernel, strong | 160 | 38.26 | 119.94 | 1.0 |
| kernel, weaker | 64 | 13.79 | 50.70 | 1.0 |
| **bm25, strong** | 160 | 117.27 | 119.94 | **0.787** |
| **bm25, weaker** | 64 | 45.35 | 50.70 | **0.997** |
| grep, strong | 160 | 121.71 | 119.94 | 0.297 |
| grep, weaker | 64 | 48.26 | 50.70 | 0.894 |

The top-3 hit rate, kept beside it, is not a test: a fix changes so few
passages that three drawn at random already hit 90% of the time (strong) and
99% (weaker). bm25 hit 128 of 160 and 51 of 64; grep 126 and 52; the kernel
19 and 1, because its rule serves a passage only if it holds half the
question's words, and for most questions it serves none (counted as last).

Per unit (bm25): the changed set n, the passages that hit h, the chance that
3 drawn at random hit, the questions with a hit in the top 3 of 16, and the
mean rank of the first hit against the random mean (n+1)/(h+1):

| Unit | Changed before limit | n | h | Chance (3) | Top-3 hits | Mean first-hit rank | Random mean |
|---|---|---|---|---|---|---|---|
| KG01 | 3 | 3 | 1 | 1.000 | 10 of 16 | 1.88 | 2.00 |
| KG02 | 16 | 16 | 7 | 0.852 | 12 of 16 | 3.00 | 2.12 |
| KG03-kartikeya | 33 | 33 | 18 | 0.913 | 14 of 16 | 5.31 | 1.79 |
| KG03-willow-mcp | 8 | 8 | 3 | 0.823 | 11 of 16 | 3.88 | 2.25 |
| KG04 | 4 | 4 | 4 | 1.000 | 8 of 16 | 2.50 | 1.00 |
| KG05 | 18 | 4 | 4 | 1.000 | 13 of 16 | 1.56 | 1.00 |
| KG06 | 18 | 4 | 4 | 1.000 | 13 of 16 | 1.56 | 1.00 |
| KG07-kartikeya | 12 | 12 | 5 | 0.845 | 16 of 16 | 1.19 | 2.17 |
| KG07-willow-mcp | 60 | 60 | 20 | 0.708 | 16 of 16 | 1.44 | 2.90 |
| KG08 | 43 | 43 | 22 | 0.890 | 15 of 16 | 1.56 | 1.91 |
| KG09 | 3 | 3 | 1 | 1.000 | 9 of 16 | 2.00 | 2.00 |
| KG10 | 6 | 6 | 3 | 0.946 | 13 of 16 | 2.75 | 1.75 |
| KG11 | 7 | 7 | 6 | 1.000 | 13 of 16 | 2.44 | 1.14 |
| KG12 | 18 | 6 | 5 | 1.000 | 16 of 16 | 1.00 | 1.17 |

What it shows: bm25 ranks the hit early only where the changed passages are
many and share the question's words (KG07 in both repositories, KG08 and
KG12: first hit at 1.0 to 1.6 against a random 1.2 to 2.9). Where the set is
tiny or all of it hits (KG01, KG04, KG05, KG06, KG09), the mean rank above 1
says only that bm25 returned nothing for some questions, which counts as
last, so those rows measure whether any word matched. In KG02, KG03, KG10 and
KG11 the first hit sat later than a random order's. What it does not show: that the
changed code is hard to find, which phase 2 contradicts; phase 1's changed
sets are the passages the fix touched, so it asks only "which of these", and a
set of 3 to 60 with half of it a hit gives a ranker little room. Both the
strong and the weaker set fail, and no gate was changed after the dry run
except as the README records above.

### Phase 2: before the fix, the whole old tree (passed)

Each question asks the whole vulnerable tree (1,072 to 39,143 passages), top
10; a hit is a passage overlapping a line the fix changed or borders.

| Ranker, group | Questions with a line hit | Expected at chance | p | File level (hits, expected, p) |
|---|---|---|---|---|
| kernel, strong | 19 of 160 | 5.55 | 1.7e-6 | 48, 72.4, 1.0 |
| kernel, weaker | 0 of 64 | 0.16 | 1.0 | 6, 6.2, 0.59 |
| **bm25, strong** | **44 of 160** | 5.55 | **5.6e-30** | 105, 72.4, 4.1e-15 |
| **bm25, weaker** | **3 of 64** | 0.16 | **5.6e-4** | 17, 6.2, 6.8e-5 |
| grep, strong | 21 of 160 | 5.55 | 7.8e-8 | 65, 72.4, 0.96 |
| grep, weaker | 2 of 64 | 0.16 | 0.011 | 13, 6.2, 0.0068 |

The null questions (fifty, asked of all 14 units): bm25 14 hits of 700 where
17.84 are expected, p(above chance) 0.859, every question served ten
passages; the kernel 0 of 700 (286 served nothing); grep 3 of 700. Only
bm25's is the gate; the null gate passed.

Per unit (bm25, the 16 questions of the gap): the old tree's passages N, the
passages that hit, the chance that 10 drawn at random hold a hit, the
questions with a hit expected at chance (16 times that), and observed, with
the kernel's and grep's counts, the questions that reached a changed file
(bm25), and the local and Claude writers' split of bm25's hits:

| Unit | N | Hit passages | Chance (10) | Expected | bm25 | kernel | grep | bm25, file level | Local / Claude |
|---|---|---|---|---|---|---|---|---|---|
| KG01 | 1072 | 6 | 0.0548 | 0.88 | 6 | 2 | 5 | 16 | 5 / 1 |
| KG02 | 1158 | 8 | 0.0672 | 1.08 | 12 | 4 | 6 | 16 | 6 / 6 |
| KG03-kartikeya | 2036 | 20 | 0.0942 | 1.51 | 4 | 1 | 3 | 12 | 3 / 1 |
| KG03-willow-mcp | 36734 | 4 | 0.0011 | 0.02 | **0** | 0 | 0 | 7 | 0 / 0 |
| KG04 | 22456 | 6 | 0.0027 | 0.04 | **0** | 0 | 1 | 5 | 0 / 0 |
| KG05 | 39143 | 5 | 0.0013 | 0.02 | 1 | 2 | 0 | 9 | 1 / 0 |
| KG06 | 39143 | 5 | 0.0013 | 0.02 | 3 | 0 | 0 | 7 | 2 / 1 |
| KG07-kartikeya | 1766 | 5 | 0.0280 | 0.45 | 9 | 2 | 5 | 15 | 5 / 4 |
| KG07-willow-mcp | 35090 | 21 | 0.0060 | 0.10 | 8 | 7 | 1 | 11 | 4 / 4 |
| KG08 | 2445 | 23 | 0.0903 | 1.44 | 1 | 1 | 0 | 7 | 1 / 0 |
| KG09 | 15318 | 1 | 0.0007 | 0.01 | **0** | 0 | 0 | **0** | 0 / 0 |
| KG10 | 13191 | 3 | 0.0023 | 0.04 | **0** | 0 | 0 | 9 | 0 / 0 |
| KG11 | 11717 | 6 | 0.0051 | 0.08 | **0** | 0 | 0 | 5 | 0 / 0 |
| KG12 | 26109 | 5 | 0.0019 | 0.03 | 3 | 0 | 2 | 3 | 1 / 2 |

What it shows: asked of the whole old tree in the words of the gap, bm25 puts
a passage that overlaps the fix's lines in the top ten for 44 of 160 strong
questions where 5.5 would be luck, and the strong set's hits come from eight
of its ten units. What it does not show, and the misses:

- **Five units were not found by bm25**: KG03-willow-mcp, KG04, KG09, KG10 and
  KG11 had no line hit in 16 questions; the kernel found none in them either,
  and grep one (KG04). KG09 never reached the changed file; KG03-willow-mcp,
  KG04, KG10 and KG11 reached it in 5 to 9 of 16 questions, but not the
  changed lines. KG08 found 1 against 1.4 expected, and KG03-kartikeya 4
  against 1.5.
- **The weaker set's pass is thin.** Its 3 hits are all KG12's; KG09, KG10 and
  KG11, the other three, have none. The gate passes (p 5.6e-4) on three
  questions in one gap, and a gap's 16 questions are not independent draws.
- **The strong set's p-value assumes independence too**, between a gap's two
  writers and its eight questions each; they ask the same thing in different
  words, so 44 is not 44 separate chances.
- **The harshest bound, not a frozen gate:** counted as if a gap's questions
  were one draw, each unit hit or not against its own chance, the strong set
  is 8 of 10 units, p = 9.2e-14, and the weaker set 1 of 4, p = 0.0099, which
  survives by a hair. The audit computed these after the run, so they are
  reported beside the gates and judge nothing.
- **File level is easier and reported only**: 105 of 160 against 72 expected
  for bm25; the kernel's and grep's strong-set file hits sit below chance
  (48 and 65), while grep's weaker set is above it (13 against 6.2, p 0.0068).
- **The kernel** serves a passage only when it holds half the question's words
  and so served nothing for 286 of 700 null questions and most gap questions;
  its 19 strong hits are real (p 1.7e-6) but few.

### Phase 3: when, and why, was the code written

Every positional hit range from phases 1 and 2, 124 and 55 ranges, was
blamed at its vulnerable commit by `origin.py`; none failed to resolve.
Per unit, the commits that wrote the hit lines, oldest first, with the days
from that commit to the fix (the merge, or the lone commit), and the gap, audit
or pull request ids their messages cite:

| Unit | Commits that wrote the hit lines (date, days to the fix) | Cited ids |
|---|---|---|
| KG01 | ff59d05ee600 stage1(b) lift of the sandbox core (07-08, 63 d); e37735193b9d bind the root read-only (09-01, 8 d); ca1fd845e975 allow_db warning (09-07, 3 d) | none |
| KG02 | e3a9f2fde444 refuse tree-rewriting git verbs under a read-only root (09-10, 0 d) | 52fcbd04dedb, 5fd840cb5000 |
| KG03-kartikeya | ff59d05ee600, c1000eeb9d16 stage1 lifts (07-08, 81 d); 8664271a7f83 gate Postgres behind allow_db (07-21, 68 d); c1e25fb434f6 env_deny by exact name (09-10, 17 d); 920237592a4d and a71a91ad78c3 ruff format and fixes (09-12, 15 d) | 8a236e0e8f55 (KG01's gap) and five more |
| KG03-willow-mcp | b2e5135e1701 worker liveness heartbeat (07-08, 81 d); bde624d8161d caps-on worker (07-21, 68 d); 849594389942 worker liveness told honestly (09-10, 17 d) | 5fd840cb5000 and three more |
| KG04 | afdd675c5b41 envelope accrual PR5 (08-25, 9 d); 8fc1122f060f doc reconcile (08-26, 8 d) | none |
| KG05 | 2f1ac93850fe defer syscall table writes to trust-owner apply (09-28, 0 d) | 7b1fee1f2861 |
| KG06 | bd2c1b2dd868 lint CI pin follows the dispatch project (09-28, 0 d) | 0b5a2aa26001 |
| KG07-willow-mcp | ten commits from 1d10998ef3e1 (07-08, 76 d) through ecad0ed16991 per-task network authorization (07-18, 67 d) to a05de373f20b broker Kart unit enable (09-22, 0 d) | 60CB6361, D8AFF2DA, 5ecb87cfdf56 |
| KG07-kartikeya | ff59d05ee600 and c1000eeb9d16 (07-08, 76 d); 8664271a7f83 (07-21, 63 d); b5313eee61e6 localhost is not egress (09-22, 0 d) | none |
| KG08 | 884f201b924b package steward (09-12, 8 d); a32dcf88d8e0, 5cb6b25396d8 ci step (09-14, 5 d); 3fcd1f4c7b32 catchup step and a merge (09-15, 5 d) | #76, 8d1bcb2b7c02 |
| KG09 | 4b5dc893d565 the one-script kernel (10-22, 0 d) | none |
| KG10 | f8ee4e860f93 merge-check as a non-root user (10-21, 0 d) | none |
| KG11 | 6cdd825373ba move the one-script skeleton in (10-07, 13 d); 3adeefeaa07d functions first (10-07, 12 d) | none |
| KG12 | a600f822eea0 the table's boxes (10-17, 0 d); 426bfa4ab286 the table on the seat's screen (10-17, 0 d) | none |

What it shows: the flawed lines are usually older than the fix by days to
weeks (the sandbox lift of 07-08 stands under KG01, KG03 and KG07; the longest,
81 days). Eight units have a 0-day commit, written the same day as the fix or
the day before. In six of them every commit is 0-day: a feature commit that
the fix then corrected (KG02, KG05, KG06, KG09, KG10, KG12). KG07's two units
add a 0-day commit to much older ones. Only a handful of commits cite a gap or audit
id (the ids are the study's; most fleet commits before the audit habit do not).

KG07, as the study expected: the sealed ruling (9fe5e179, gap 582b1e676fb3)
exempted `allow_localhost` from the lease, and the KB note names commits
e1a5ab03 and ce2d0d96. **Neither commit exists in any local repository**
(willow-mcp, kartikeya, the other repositories beside them, and the willow-bot
fork all lack both), so the study cannot confirm them from git. What git does
say: the lines the KG07 fix rewrote were written by many commits, not one. In
kartikeya the newest is b5313eee61e6 (2026-09-22, "localhost is not egress"),
a day before the fix, whose body states the exemption: "Signed-envelope gate
applies only to # allow_net, not allow_localhost." In willow-mcp, commit
200ce45 (2026-09-22, on the vulnerable side of the fix) names the ruling:
"Localhost is Kart localhost_tier, not the net authorizer path (9fe5e179)."
The flag itself is far older: it is in kartikeya's code from the 07-08 lift
commits (ec3acc0, ff59d05, c1000ee), and 153ac26 (2026-07-17, "gate #
allow_localhost like # allow_net") is the first commit to name it in its
message. So git shows the exemption written into both repositories the day
before the fix, citing the sealed ruling, on top of a flag that had been gated
like the network since July. The KB note's two commits remain unfound.

### Phase 4: the writers compared (reported, not judged)

Questions with a hit, per writer, with every line and with the flagged lines
left out (the local writer wrote 46 flagged lines of 96; Claude and the null
set none, after the `allow_localhost` exception; 48 and 1 before it). A pair is a question asked of one unit: 112 a writer.

| Phase, ranker | Local, all lines | Local, unflagged | Claude, all lines | Claude, unflagged |
|---|---|---|---|---|
| 1 (top 3), bm25 | 98 of 112 | 53 of 60 | 81 of 112 | 81 of 112 |
| 1 (top 3), grep | 97 of 112 | 52 of 60 | 81 of 112 | 81 of 112 |
| 1 (top 3), kernel | 8 of 112 | 3 of 60 | 12 of 112 | 12 of 112 |
| 2 (top 10), bm25 | 28 of 112 | 12 of 60 | 19 of 112 | 19 of 112 |
| 2 (top 10), grep | 16 of 112 | 3 of 60 | 7 of 112 | 7 of 112 |
| 2 (top 10), kernel | 9 of 112 | 3 of 60 | 10 of 112 | 10 of 112 |

What it shows: in phase 2 the local writer's raw lead over Claude's (28 against
19, bm25) shrinks once its flagged lines are set aside (12 of 60 is 20%,
against Claude's 17%): most of its extra hits are on lines that carried an
identifier. Grep's gap (16 against 7) falls to 3 of 60. In phase 1 it does
not: the local writer's lead stays the same with its flagged lines left out
(87.5% with every line, 88.3% unflagged, against Claude's 72.3%), since nearly
every phase-1 question hits whatever it says. What it does not show: which writer
is better, since the two were not asked the same things and unflagged local
lines are a selected 60 of 112.

### Phase 7: same bytes

Phases 1 and 2 were run four times, from a fresh index each time: Python
3.14.4 with hash seed 0 and 4242, and Python 3.12.13 (one of uv's, offline)
with hash seed 0 and 4242. The four answers files, the four scored files and
the four result files are byte-identical; their SHA-256 are the six in the
table at the top of this section, the same for all four runs. The indexes,
whose hashes are in each unit's stats row, are therefore the same too.

`index.rank` against `kernel.rank` over the whole tree, by phase 6's method
(every passage, in order), on the unit's own 16 questions: every question
compared agreed, in all 14 units. The kernel's rank over a tree of 22,000 to
39,000 passages takes several seconds a question, so the larger trees were cut
at a time budget and not every question was compared:

| Unit | Compared | Same |
|---|---|---|
| KG01 | 16 of 16 | 16 |
| KG02 | 16 of 16 | 16 |
| KG03-kartikeya | 16 of 16 | 16 |
| KG03-willow-mcp | 8 of 16 | 8 |
| KG04 | 14 of 16 | 14 |
| KG05 | 6 of 16 | 6 |
| KG06 | 7 of 16 | 7 |
| KG07-kartikeya | 16 of 16 | 16 |
| KG07-willow-mcp | 11 of 16 | 11 |
| KG08 | 16 of 16 | 16 |
| KG09 | 16 of 16 | 16 |
| KG10 | 16 of 16 | 16 |
| KG11 | 16 of 16 | 16 |
| KG12 | 7 of 16 | 7 |

Note that many of these compare two empty lists (the kernel serves a passage
only if it holds half the question's words), which agree trivially; they also
agree where it served some.

### Not run

Phase 5 (spread: the gaps' questions over the other repositories) and phase 6
(the cpython control, which needs an egress lease) have not run. Nothing here
claims a result for either.
