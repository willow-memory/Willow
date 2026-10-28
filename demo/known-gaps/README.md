# known-gaps: the fleet's own security gaps, asked of the code their fixes changed

This is [php2shell](../php2shell/README.md)'s method pointed at the fleet's
own twelve known security gaps. php2shell asked questions in the words of a
PHP advisory and checked whether the code a fix changed came back. Here the
"advisory" is the gap as its finder wrote it (a gap record, an audit finding)
or, for four of them, as the fixer wrote it (a commit message).

**This page is the state at the first freeze.** It holds the claim, the
threats, what is frozen and the dry run. There are no results yet: no real
question has been written, and no scored phase has run. They come in later
bites, each frozen before it runs.

## The claim

For each of twelve security gaps the fleet found, fixed and recorded, a
question written from the gap's own text, asked of the code as it was just
before the fix, finds the lines the fix changed more often than chance.

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
other ten by their gap id). KG05 and KG06 share one fix commit and are
scored on the same diff. KG12's commit also carries two changes that are not
security, so only the two files of its security findings are scored
(`files_scored`, chosen before any run).

## The threats

| Threat | What answers it |
|---|---|
| The questions are written with the fix in hand | The strong set's text predates its fix; the weaker set is reported apart. Questions are written from the redacted gap text only, by writers who never see the fix, and frozen before any run (a later bite). |
| The hit rule is chosen after seeing results | The rule is php2shell's rule 2, unchanged, plus a short list of files that never count. `score.py` is frozen before any scored phase, and `test_known_gaps.py` holds its hash. |
| The fix is a different diff on another machine | `resolve.py` pins the vulnerable and fixed commit, each side's git tree hash and the SHA-256 of the diff (php2shell's flags). `trees.py check` re-hashes all of it without git. |
| A tree is not what git stored | `trees.py` writes each tree as git stores it (php2shell's `write_tree`), then compares its hash to the pin. |
| Few changed passages make chance high | Each unit's random rate is measured, not assumed: 10,000 draws of 3 changed passages, seeded. See the dry run: it is already high for these small fixes. |
| The apparatus finds things by accident | A null set is asked of every unit, and a phase fails if any null question hits. |
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
| `resolve.py` | gaps.json to pins.json, from the fleet's own local repositories (`--repos`). Refuses a merge that does not name its pull request. |
| `trees.py` | `fetch` writes each unit's vulnerable (old) and fixed (new) tree and the fix diff; `check` holds them to the pins. No network. |
| `ask.py` | per unit, indexes both trees with `scan.py` (cached by tree hash), asks the unit's questions of the passages the fix changed (top 3) three ways: the kernel's rank, BM25, a grep baseline. `--mode before` asks the whole old tree, top 10. Also writes the unit's changed-passage count and random rate. |
| `score.py` | the hit rule below, per answer, with the `path:first-last` ranges that hit. |
| `origin.py` | for every hit range, `whose.py` at the vulnerable commit: the commit that wrote it, its date, the gap, audit and pull request ids its message cites, and the days before the fix. |
| `run.py` | phase 1 (`found`): scores the answers, applies the pass rules per kind, writes each rule as a kernel verdict row. |
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
here.

### Phase 1 pass rules

| Rule | Passes when |
|---|---|
| above chance, bm25, strong | the strong set's pooled hits beat its pooled random rate, one-sided binomial p < 0.01 |
| above chance, bm25, weaker | the same for the weaker set |
| null questions hit nothing | at least one null question was asked, and none of its answers hit |

The kernel's and grep's rates are reported beside, never gates.

## Reproduce

Needs git and the fleet's repositories checked out side by side (they are
read, never written). Python 3.9 or newer.

    python demo/known-gaps/resolve.py --repos REPOS --out pins.json
    python demo/known-gaps/trees.py fetch --to WORK --repos REPOS
    python demo/known-gaps/trees.py check --to WORK
    python demo/known-gaps/ask.py --to WORK --ix WORK/ix/UNIT --questions QUESTIONS --out WORK/ans/UNIT.jsonl --unit UNIT
    python demo/known-gaps/run.py found --to WORK --answers ANSWERS --box BOX --out SCORED
    python demo/known-gaps/origin.py --repos REPOS --scored SCORED --out ORIGINS
    python -m pytest demo/known-gaps

Run `ask.py` once a unit: Kart kills a task at 300 seconds, and the largest
unit took about 25 seconds (below).

## The dry run

Run on Kart on 2026-10-28 over the fourteen pins, with one meaningless
question for every gap and one for the null set (`qqqq zzzz`). Its purpose is
plumbing: every tree fetched and checked, every index built, every answer
scored, the verdict rows written and the record verified.

| Step | Result |
|---|---|
| `trees.py fetch` (14 units, 28 trees) | 4 s; all 14 old, new and fix lines `matches`, exit 0 |
| `ask.py` (14 tasks) | all exit 0; timings below |
| `run.py found` | 0.23 s; exit 42, as it must be: 0 hits of 10 strong, 0 of 4 weaker, 42 null answers, none a hit |
| verdict rows | 3 written; the record's chain holds |
| `origin.py` | 0 ranges to look up, so 0 rows (nothing hit) |

Per-unit timings (index and ask are `ask.py`'s own; the 14 tasks ran at once on
one machine, so each is slower than it would be alone):

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
  is empty and every score is `miss`. No number above says anything about the
  method. It shows that a fresh checkout can fetch, index, ask, score and
  record, and that each unit fits well inside Kart's limit.
- **The shape of chance.** The fix changes few passages (3 to 60 a unit), so a
  random draw of three passages hits the fix's lines often: 0.71 to 1.00 a
  unit, 0.90 pooled for the strong set and 0.92 for the weaker. The pass rule
  "above chance, p < 0.01" asks a question to beat a rate that high, and with
  a unit at 1.00 (KG01, KG04, KG09 and KG11: every draw hits) it cannot be
  beaten there. The rule is frozen as written; this is the thing the real
  runs will show, or the next freeze will have to answer.

| Unit | Passages the fix changed | Of them, hit | Random rate |
|---|---|---|---|
| KG01 | 3 | 1 | 1.000 |
| KG02 | 16 | 7 | 0.852 |
| KG03-kartikeya | 33 | 19 | 0.929 |
| KG03-willow-mcp | 8 | 3 | 0.823 |
| KG04 | 4 | 4 | 1.000 |
| KG05 | 18 | 11 | 0.959 |
| KG06 | 18 | 11 | 0.957 |
| KG07-kartikeya | 12 | 5 | 0.845 |
| KG07-willow-mcp | 60 | 20 | 0.708 |
| KG08 | 43 | 23 | 0.905 |
| KG09 | 3 | 1 | 1.000 |
| KG10 | 6 | 3 | 0.946 |
| KG11 | 7 | 6 | 1.000 |
| KG12 | 18 | 6 | 0.736 |

- **KG05 and KG06 are scored on the same diff.** They share one fix commit
  and gaps.json names no `files_scored` for either, so both count all 23 KB
  of the diff. Their different gap text is what tells them apart.
- **The nulls.** A null question hit nothing, in this run, because no question
  meant anything. That is not yet a test of the null rule.

## What the first real run still owes

Questions (a later freeze), phases 1 to 4 and 7, the spread and the outside
control. None is run, and nothing here claims a result.
