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
| The hit rule is chosen after seeing results | The rule is php2shell's rule 2, unchanged, plus a short list of files that never count. `score.py` is frozen before any scored phase, and `test_known_gaps.py` holds its hash. |
| The pass rule is chosen after seeing results | It was changed once, after the dry run and before any real question: see "Why phase 1 is judged by rank". The change is recorded here, and the dry run that prompted it is kept below. |
| The fix is a different diff on another machine | `resolve.py` pins the vulnerable and fixed commit, each side's git tree hash and the SHA-256 of the diff (php2shell's flags). `trees.py check` re-hashes all of it without git. |
| A tree is not what git stored | `trees.py` writes each tree as git stores it (php2shell's `write_tree`), then compares its hash to the pin. |
| Few changed passages make chance high | Phase 1 no longer asks for a hit in the top 3 of 3 to 60 passages. It judges the rank of the first hit against random orderings, and phase 2 asks the whole tree, where chance is small. |
| The apparatus finds things by accident | A null set is asked of every unit, and phase 1 fails if any null question's top 3 hits. |
| An open gap leaks into a public branch | Only fixed gaps are in `gaps.json`. Candidates and unfixed gaps live in a private place and never enter this folder. |
| A model has seen the code | The fleet's repositories are newer than any model's training and were written largely by models; this is a different threat from php2shell's old CVEs and is named, not solved. |

## What is frozen

At freeze 1, FROZEN.json holds the SHA-256 of `gaps.json`, `pins.json`,
`resolve.py`, `trees.py`, `ask.py`, `score.py`, `origin.py` and `run.py`, and
of the tools they lean on (`kernel.py`, `adapters/stdlib/scan/scan.py`,
`adapters/stdlib/ci/whose.py`). `test_known_gaps.py` re-hashes every one; a
change is a new freeze, in its own commit, before the phase that needs it
runs. The freeze file is the operator's commit: until it lands, the freeze
test skips and says so.

`spread.py` and `outside.py` are stubs that exit 2. They are not frozen, and
are written in their own bites.

## The scripts

All stdlib, each takes its paths as arguments, writes only what it is told,
and exits 0, 42 or 2 as the kernel does.

| Script | Does |
|---|---|
| `resolve.py` | gaps.json to pins.json, from the fleet's own local repositories (`--repos`). Refuses a merge that does not name its pull request, and a scored file that is not in the diff. |
| `trees.py` | `fetch` writes each unit's vulnerable (old) and fixed (new) tree and the fix diff; `check` holds them to the pins. No network. |
| `ask.py` | per unit, indexes both trees with `scan.py` (cached by tree hash) and asks the unit's questions three ways: the kernel's rank, BM25, a grep baseline. `found` ranks every passage the fix changed; `--mode before` asks the whole old tree, top 10. Also writes the unit's counts and its chance. |
| `score.py` | the hit rule below, per answer, with the rank of the first hit and the `path:first-last` ranges that hit. |
| `origin.py` | for every hit range, `whose.py` at the vulnerable commit: the commit that wrote it, its date, the gap, audit and pull request ids its message cites, and the days before the fix. |
| `run.py` | `found` (phase 1) and `before` (phase 2): scores the answers, applies the pass rules per kind, writes each rule as a kernel verdict row. |
| `spread.py`, `outside.py` | not in this bite. |

### The hit rule

`demo/php2shell/phase3.py`'s `changed` and `hit`, which are rule 2 of
php2shell: a passage hits when it holds a line the fix removed, or the one
unchanged line just before or after a run of added lines. A line counts when
it is at least 8 characters and 2 of the kernel's words long.

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
| null questions hit nothing | at least one null question was asked, and none of its top 3 hit |

The kernel's and grep's results are reported beside, never gates.

### Phase 2: before the fix (the main judged test)

Each question is asked of the whole vulnerable tree, top 10, and scored at the
line level (a passage holding a counted line) and the file level (any passage
of a scored file). The chance is exact: php2shell's phase4 `chance_one` for a
pair, `poisson_binomial_tail` for a group, and `recall_at` for the hits.

| Rule | Passes when |
|---|---|
| line level above chance, bm25, strong | questions with a line hit in the top 10 beat chance, one-sided p < 0.01 |
| line level above chance, bm25, weaker | the same for the weaker set |

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
chance is 0.1% to 19% a question (the table below).

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
largest unit took about 25 seconds to index (below).

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
| `run.py found` | exit 42, as it must be: no hits, so the rank statistic sits far below random (strong 1.42 against 7.54 expected, p 1.0; weaker 0.81 against 3.25, p 1.0). Run after amendment 2, with the `files_scored` limit. |
| `run.py before` | exit 42, as it must be: 0 line hits against 0.57 expected (strong) and 0.016 (weaker); file level 0 against 4.52 and 0.39, reported |
| verdict rows | 5 written (3 for phase 1, 2 for phase 2); the record's chain holds |
| `origin.py` | 0 ranges to look up, so 0 rows (nothing hit) |

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
- **The shape of chance, which is why the rule changed.** For each unit, the
  passages the fix changed and the chance of a random hit, in phase 1
  (3 drawn from the changed set) and in phase 2 (10 drawn from the whole old
  tree; the file level counts any passage of a scored file):

| Unit | Changed passages before the limit | After the limit | Hit | Chance, 3 of them | Old tree passages | Hit | In a scored file | Chance, 10 of the tree (line) |
|---|---|---|---|---|---|---|---|---|
| KG01 | 3 | 3 | 1 | 1.000 | 1072 | 5 | 193 | 0.046 |
| KG02 | 16 | 16 | 7 | 0.852 | 1158 | 15 | 235 | 0.123 |
| KG03-kartikeya | 33 | 33 | 19 | 0.929 | 2036 | 30 | 294 | 0.138 |
| KG03-willow-mcp | 8 | 8 | 3 | 0.823 | 36734 | 7 | 75 | 0.002 |
| KG04 | 4 | 4 | 4 | 1.000 | 22456 | 6 | 140 | 0.003 |
| KG05 | 18 | 4 | 4 | 1.000 | 39143 | 15 | 276 | 0.004 |
| KG06 | 18 | 4 | 4 | 1.000 | 39143 | 5 | 76 | 0.001 |
| KG07-kartikeya | 12 | 12 | 5 | 0.845 | 1766 | 6 | 266 | 0.034 |
| KG07-willow-mcp | 60 | 60 | 20 | 0.708 | 35090 | 79 | 2497 | 0.022 |
| KG08 | 43 | 43 | 23 | 0.905 | 2445 | 52 | 153 | 0.194 |
| KG09 | 3 | 3 | 1 | 1.000 | 15318 | 1 | 89 | 0.001 |
| KG10 | 6 | 6 | 3 | 0.946 | 13191 | 3 | 214 | 0.002 |
| KG11 | 7 | 7 | 6 | 1.000 | 11717 | 11 | 169 | 0.009 |
| KG12 | 18 | 6 | 6 | 1.000 | 26109 | 10 | 116 | 0.004 |

  The limit (amendment 2) changes three rows: KG05 and KG06 from 18 to 4
  changed passages and KG12 from 18 to 6, each the passages of its own scored
  file or files. Every one of those passages is a hit, so in phase 1 a pair on
  those units has its first hit at rank 1 under every ordering: it adds
  nothing to the statistic that chance does not already give. KG04 has the
  same shape (4 of 4) without a limit. Phase 2, which asks the whole tree, is
  where those units are tested.
- **The file level's chance is large in places.** Phase 2's file level counts
  any passage of a scored file: 75 to 2,497 passages of a tree. Its chance
  for 10 passages, summed over the dry run's pairs, is 4.52 file hits expected
  from the 10 strong pairs and 0.39 from the 4 weaker ones, against 0.57 and
  0.02 for the line level. The file level can be won, but is a weaker claim
  than the line level; both are reported.
- **The nulls.** A null question hit nothing, in this run, because no question
  meant anything. That is not yet a test of the null rule.

## What the first real run still owes

Questions (a later freeze), the real runs of phases 1 and 2, phases 3, 4 and 7,
the spread and the outside control. None is run, and nothing here claims a
result.
