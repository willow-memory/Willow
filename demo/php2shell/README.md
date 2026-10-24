# PHP2Shell: proving the result

In October 2026, Willow's kernel was asked about PHP2Shell
(CVE-2026-109618 and CVE-2026-109619) in the advisories' own words, through
the [scan](../../adapters/stdlib/scan/) add-on. Given the fixed release, it
pointed at the code the fix replaced; without it, at the two files that held
the bugs. This folder tests that result seven ways, so that it stands or
falls on what anyone can rerun. The plan, phase by phase, is published as
*PHP2Shell: proving the result*; its summary is here.

## The claim

Asked of 16 PHP releases (5.6 to 8.5), eight questions in the advisories'
words served `main/rfc1867.c` and `ext/session/session.c` in every
release. Asked `--changed-from` each fix, of only the passages the release
lost to it, they served the allocator's out-of-memory raise, `add_post_var`'s
loop, the multipart parser's registration and the session's upload-progress
handler, on 8.2, 8.3, 8.4 and 8.5 alike.

## How it could be wrong, and the phase that answers each

| Threat | Phase |
|---|---|
| The questions knew too much | 1, blind questions; 5, rewording |
| Anything would have hit: the changed set is small | 2, null tests and baselines |
| "Hit" was defined after the fact | 0, this freeze; 6, independent scoring |
| It worked once | 3, other CVEs; 6, same bytes from four kernels |

## Phase 0: what is frozen

[FROZEN.json](FROZEN.json) holds the SHA-256 of each frozen file, and
`test_php2shell.py` fails if one changes. A change is a new freeze, made
in its own commit with its reason, before the phase that needs it runs. The
commit that froze a file is its pre-registration.

- [releases.json](releases.json): 18 PHP releases by commit and git tree
  hash (the 16 already asked, and 8.5.10 and 8.4.25 for the wrong-pair null
  test), and the security commit on each of 8.2 to 8.5 with the SHA-256 of
  its diff against its parent. Other commits in a release never count.
- [make_trees.py](make_trees.py): fetches them from php-src (online, with
  git) and checks them without git, by hashing each tree the way git does.
- [score.py](score.py): the hit rule. A passage scores `core` when it holds
  a line the security commit removed (asking the old code) or added (asking
  the new) in one of seven files, `any` for such a line elsewhere, `file`
  when only its file was changed, and `miss`. Context lines, test files and
  NEWS never count. This is stricter than the first look, which counted
  context lines.
- [questions/author.txt](questions/author.txt): the eight questions of the
  first look, labelled as the author's: written before any run, but by
  someone who has since seen the results and the fix.
- [questions/null.txt](questions/null.txt): fifty questions about PHP with
  nothing to do with the bug, for phase 2.

**Said plainly:** the seven `core` files (the advisories' mechanisms, and the
request startup the commit message names) were chosen after the first look.
The security commit changed more than 400 files, hardening out-of-memory
handling everywhere, so `any` alone would score a question about JSON as a
hit. Both levels are reported; the blind and null phases are what make
`core` mean anything.

FROZEN.json also records the SHA-256 of `kernel.py`, `scan.py` and
`todo.py` when the freeze was made, so every result says which tools gave it.

## Reproduce

    python demo/php2shell/make_trees.py --to /tmp/php2shell       # about 3 GB
    python demo/php2shell/make_trees.py --to /tmp/php2shell --check
    python adapters/stdlib/scan/scan.py index --from /tmp/php2shell/trees/8.5.11 --to /tmp/ix/8.5.11
    python adapters/stdlib/scan/scan.py index --from /tmp/php2shell/trees/8.5.12 --to /tmp/ix/8.5.12
    python adapters/stdlib/scan/scan.py scan --index /tmp/ix/8.5.11 --changed-from /tmp/ix/8.5.12 \
        --questions demo/php2shell/questions/author.txt > answers.jsonl
    python demo/php2shell/score.py --fixes /tmp/php2shell answers.jsonl

A tree from `git archive` has `$Id$` filled in, in the six files PHP marks
`ident`; the check puts it back before hashing, as git does.

## Phase 2: the null tests, 2026-10-24

Run by [phase2.py](phase2.py), frozen before it ran. Four tests passed and two
failed. The result survives in part: the kernel lands on the fix's core
well above chance, but not by the frozen margin, and BM25 does better.

Each fix's pair, the vulnerable release asked `--changed-from` the fixed
one, eight questions each, 32 answers:

| Test | core | any | file | miss | Passes when | Result |
|---|---|---|---|---|---|---|
| kernel, top 3 | 12 | 0 | 12 | 8 | (the result under test) | |
| random, 3 of the changed passages, 40,000 draws | 20.8% | 66.7% | 11.4% | 1.2% | kernel's core above it, p < 0.01 | **fails**: p = 0.022 |
| null questions, 200 answers | 0 | 59 | 29 | 112 | core rate below the kernel's | passes |
| wrong pair, 16 answers | 0 | 0 | 0 | 16 | no core answer | passes |
| diff size | 0 | 24 | 8 | 0 | kernel's core at least as many | passes |
| grep | 12 | 0 | 8 | 12 | kernel's core at least as many | passes (a tie) |
| BM25 | 17 | 3 | 10 | 2 | kernel's core at least as many | **fails**: 17 against 12 |
| kernel, the fix's side (not judged) | 17 | 11 | 0 | 4 | | |

**What it says:**

- **Most of the work is the narrowing.** The changed set is 876 to 1,305
  passages a fix, and nearly nine in ten random draws of three (87.5%) land on a line the
  security commit changed somewhere (core or any). Asking only what changed
  between two releases is most of the result.
- **The questions do matter.** On a pair the fix isn't in, the same
  questions find nothing at all. The fifty null questions never reach a core
  hunk, though 59 of 200 reach another file the commit hardened, as the
  freeze expected.
- **The kernel's ranking is not the best one.** It needs half a question's
  rarer words in one passage, so it serves nothing for 618a and 619c, where
  BM25 still finds the right file or a changed line. Which ranking a person
  should use on code is open.
- **The frozen rule has a blind spot, kept as frozen.** Asking the old code,
  only removed lines count, so a passage the fix only added lines to scores
  `file`. That is why 619b, the upload-progress handler, scores `file` on the
  old side and `core` on the fix's side. Changing the rule now would be
  changing it after seeing results; a later freeze can add a rule that
  counts such passages, run on new questions.

The verdicts are rows on a kernel record (`verify`: the chain holds, 7 rows,
0 sealed), each with the SHA-256 of the scored answers (93bb155f) and of the tools:
`kernel.py` 2d7fd0f6, `scan.py` ead27057, `score.py` 084d0a3a, `phase2.py`
5ca4e4a1.

## Where each phase stands

| Phase | Status |
|---|---|
| 0, freeze | done: 18 releases and 4 fix diffs fetched and matching their pins |
| 2, null tests | done: 4 of 6 pass; random (p = 0.022) and BM25 fail |
| 1, blind questions | not started |
| 6, reproducibility | not started |
| 3, out of sample | not started; its CVEs and releases are frozen when it starts |
| 4, before the fix | not started |
| 5, robustness | not started |

Results go here, each with the tools' hashes it ran on, misses included.
