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

## Phase 1: blind questions, a second rule, and BM25, 2026-10-24

Run by [phase1.py](phase1.py), frozen with what it used before it ran:
three blind question sets, [score2.py](score2.py) and scan's `--rank bm25`.
Four of five pass rules pass.

**The blind sets.** Three agents each wrote eight questions without seeing
PHP's code, the fix, the author's questions or any result:
[blind-a.txt](questions/blind-a.txt) as a security engineer and
[blind-c.txt](questions/blind-c.txt) in terse keywords, both from the
advisories, and [blind-b.txt](questions/blind-b.txt) as a sysadmin from one
news article. None could open a web page (each fetch failed), so all three
worked from search summaries, which describe the bugs' mechanisms in plain
words but show no code. Each file's header lists its sources.

**The second rule.** Phase 2 showed rule 1 blind where the fix only added
code. Rule 2 also counts the unchanged line just before and just after each
run of added lines. It was written after phase 2's results, so it is judged
only on the blind questions, which nobody had asked yet, and against random
draws scored the same way, since it is looser.

Pooled over the three blind sets, each asked of the four fixes' pairs, top
3, 96 answers a row:

| Ranked by | Rule | Core answers | Random | p | Passes when | Result |
|---|---|---|---|---|---|---|
| the kernel | 1 | 28 (29%) | 20.1% | 0.022 | p < 0.01 | **fails** |
| the kernel | 2 | 48 (50%) | 27.7% | 0.000003 | p < 0.01 | passes |
| BM25 | 1 | 31 (32%) | 20.1% | 0.0034 | p < 0.01 | passes |
| BM25 | 2 | 75 (78%) | 27.7% | 10^-24 | p < 0.01 | passes |

The blind sets reach 29% under rule 1 with the kernel, against the author's
37.5%: at least half, as the rule asks, so it passes. By set, out of 32:

| Set | kernel, rule 1 | kernel, rule 2 | BM25, rule 1 | BM25, rule 2 |
|---|---|---|---|---|
| blind-a, security engineer | 6 | 12 | 9 | 27 |
| blind-b, one news article | 14 | 16 | 14 | 20 |
| blind-c, terse keywords | 8 | 20 | 8 | 28 |
| author's (not blind) | 12 | 24 | 17 | 27 |

**What it says:**

- **The result holds for questions its author didn't write.** Blind
  questions land on the fix far above chance once the rule counts where the
  fix added code. The sysadmin's set, from one news article, did as well as
  any.
- **BM25 is the better ranking for this.** Under rule 2 it lands three
  answers in four on the fix's core, against half for the kernel's rank.
  The kernel's need for half a question's rarer words in one passage costs
  it most on long, descriptive questions (set A).
- **Under the strict rule, the kernel still misses the frozen margin**, as
  in phase 2 (p = 0.022 both times). Its result rests on rule 2, which was
  written after phase 2; BM25's does not.

The verdicts are rows on a kernel record (the chain holds, 6 rows, 0
sealed), with the SHA-256 of the scored answers (868f771a) and of the
tools: `kernel.py` 2d7fd0f6, `scan.py` d93536eb.

## Phase 3: seven other CVEs, 2026-10-24

Run by [phase3.py](phase3.py), frozen with [its pins](phase3.json) and
[its questions](questions/phase3.txt) before it ran. Four of six pass rules
pass. **BM25 found all seven; the kernel's rank found one.**

Five are older CVEs a model may remember, and two were disclosed after
mid-2026: Brotli's CVE-2026-111497 (the Node.js bug) and Onigmo's
CVE-2026-110264 (the GitLab bug, in Ruby's regex engine). Two agents wrote
eight questions a CVE from the advisories, without seeing any project's
code or any fix. Each vulnerable release was asked `--changed-from` its
fixed one, top 3. A hit is a passage holding a line a fix commit removed,
or one next to code it added (rule 2), anywhere but tests, changelogs and
version files. Each tree is every file of its commit as git stores it, since
`git archive` drops most of Brotli's files and rewrites one of Log4j's.

| CVE | Changed passages | Random | Kernel | BM25 |
|---|---|---|---|---|
| CVE-2024-4577, PHP CGI | 138 | 2.2% | 2 of 8 | 5 of 8 |
| CVE-2019-11043, PHP-FPM | 354 | 0.9% | 2 | 7 |
| CVE-2012-1823, PHP CGI | 5 | 60.5% | 3 | 6 |
| CVE-2014-0160, Heartbleed | 217 | 5.6% | 3 | 8 |
| CVE-2021-44228, Log4Shell | 1,543 | 7.3% | 3 | 4 |
| CVE-2026-111497, Brotli (new) | 46 | 86.8% | 4 | 7 |
| CVE-2026-110264, Onigmo (new) | 72 | 23.4% | 0 | 7 |

| Rule | Kernel | BM25 |
|---|---|---|
| found: half a CVE's questions hit, for 4 of 7 | **fails**: 1 of 7 | passes: 7 of 7 |
| above chance, the two new CVEs | **fails**: 4 of 16 against 55%, p = 1.0 | passes: 14 of 16, p = 0.0068 |
| above chance, the five older | passes: 13 of 40 against 15%, p = 0.0051 | passes: 30 of 40, p = 10^-17 |

**What it says:**

- **The method travels.** Asking only what changed between a release and
  its fix, with BM25, found the fixed code for every CVE tried, in four
  projects and three languages, and for the two a model can't remember.
- **The kernel's rank is the wrong tool for this.** It serves a passage
  only when it holds half a question's rarer words; on code, few passages
  do. On Onigmo it served nothing that hit, for all eight questions.
- **Two tests are weak, and say so.** Brotli's fix changed 46 passages,
  most of the changed set, so random draws hit 87% of the time; PHP 5.4.2
  changed only 5. They count, but they show little either way.
- **The older five can't rule out memory.** Their writer was told to use no
  remembered identifier, and says it used none, but a model knows these
  bugs. The two new CVEs are the clean test, and BM25 passes it.

The verdicts are rows on a kernel record (the chain holds, 7 rows, 0
sealed), with the SHA-256 of the scored answers (3b8fd0d7).

## Phase 6: reproducibility, 2026-10-24

Run by [phase6.py](phase6.py), frozen before any part ran. Every check
passes: anyone gets the same answers, byte for byte, from the same files.

| Check | What was compared | Result |
|---|---|---|
| exact | the index's full ranking against the kernel's own `rank` over the whole tree, 8 questions on each of 16 releases | the same, passage for passage, all 128 |
| bytes | scan's answers for 8.5.11, whole and `--changed-from` 8.5.12, on Python 3.9, 3.11, 3.12, 3.13 and 3.14, hash seeds 0, 1 and 4242 (30 runs); the index of 8.5.11 made on 3.9, 3.13 and 3.14 | every run byte-identical; the index file for file |
| ports | the Java, TypeScript and C# kernels' `bite` on the whole 8.5.11 tree, no index, against kernel.py's | each serves the same passages in the same order, 8 of 8 |
| agree | four independent labellers, each given only the criterion and one fix's diff, never the scorer or any result, said yes or no for 180 passages; [their labels](results/phase6-labels.json) | rule 2: 170 of 180 agree, kappa 0.707 (passes, at least 0.6); rule 1, reported: 92 of 180, kappa 0.104 |

**What it says:**

- **The speed costs nothing.** The index ranks exactly as the kernel does on
  every release asked, so its answers can be checked against the kernel's.
- **Four implementations agree** on a 26,582-file tree, so the answers are
  the method's, not one program's.
- **An independent reader agrees with rule 2, not rule 1.** Rule 1 counted
  only removed lines; a reader judging "did the fix change this passage"
  sides with rule 2 nine times in ten.

Python 3.9 and 3.14 came from `uv`, and .NET 8 from Ubuntu's packages, for
this run. The verdicts are rows on a kernel record (the chain holds, 25 rows,
0 sealed).

## Phase 4: before the fix, 2026-10-24

Run by [phase4.py](phase4.py), frozen before it ran. The question October 20
posed: with no fixed release to compare against, does asking the whole
vulnerable release point at the code? Each question is ranked over the whole
release, top 50, three ways, and scored at two levels: a *line* hit (a
passage the fix changed, rule 2) and a *file* hit (any passage of a file the
fix changed). The pass rule judges the line level in the top 10, against an
exact random baseline, for the kernel and BM25 on the blind, new-CVE and
older-CVE groups.

**Line level**, questions with a hit in the top k, of the group's total:

| Group | Ranker | @3 | @10 | @50 | random expects @10 | p |
|---|---|---|---|---|---|---|
| blind (96) | kernel | 3 | 11 | 42 | 0.7 | 10^-10 |
| blind (96) | BM25 | 8 | 9 | 52 | 0.7 | 10^-8 |
| blind (96) | grep | 2 | 19 | 40 | 0.7 | 10^-22 |
| p3 new (16) | kernel | 0 | 2 | 7 | 0.25 | 0.024 |
| p3 new (16) | BM25 | 2 | 2 | 8 | 0.25 | 0.024 |
| p3 new (16) | grep | 2 | 5 | 8 | 0.25 | 10^-6 |
| p3 old (40) | BM25 | 7 | 11 | 21 | 0.1 | 10^-23 |

**File level**, the same, for the blind set of 96: kernel 31 / 50 / 68,
BM25 26 / 51 / 80, grep 24 / 48 / 69.

**What it says:**

- **Far above chance, at both levels.** Every group beats its random
  baseline (p well below 0.01 for the blind and older sets); where random
  expects under one hit in the top 10, the search returns 9 to 19.
- **Good at the file, weak at the line, as expected.** Over a whole release
  the top 10 holds a changed *file* about half the time (50 of 96 blind), a
  changed *line* about one time in five to ten. Without the fix to narrow
  to, a person gets pointed at the right file and reads it, not handed the
  line.
- **The two new CVEs are the weak spot here.** Only the frozen pass rule
  counts, and both the kernel and BM25 miss it (p = 0.024, just over 0.01);
  grep passes (p = 10^-6). The group is 16 questions on two bugs, so one or
  two hits move it; at the file level it is 9 to 11 of 16.
- **Four of six pass rules pass.** Both failures are the two-new-CVE line
  level at the strict margin, where grep, not judged, does clear it.

So the honest answer to the pre-disclosure question: on October 20, this
would have pointed a reader at the handful of files to read, well above
chance, but rarely at the exact line. The line comes once the fix exists to
compare against (phases 1 and 3). The verdicts are rows on a kernel record
(the chain holds, 7 rows, 0 sealed), answers SHA-256 a4340fab.

## Phase 5: robustness, 2026-10-24

Run by [phase5.py](phase5.py), frozen before it ran. Three checks, all asking
the PHP2Shell pairs (vulnerable `--changed-from` fixed, the kernel's rank,
rule 2 on a core file). The headline rule, that rewording keeps most hits,
**fails**, narrowly, and on the kernel's known weakness.

**Rewording.** A blind agent rephrased the author's eight questions five ways
each (40 variants). Of the originals, 24 of 32 hit; of the variants, 80 of
160 (50%), just under the 70%-of-original bar (52%). By kind, of 32:

| Rewording | Hits | Kept, where the original hit |
|---|---|---|
| v5 reordered | 24 | 24 of 24 |
| v2 shorter | 24 | 20 of 24 |
| v4 misspelled | 16 | 16 of 24 |
| v1 synonyms | 8 | 8 of 24 |
| v3 longer | 8 | 8 of 24 |

Word order costs nothing, as a word-matcher should. Synonyms and a longer,
chattier phrasing cost the most: the kernel matches words, not meanings, and
needs half a question's words in one passage, so swapping words for synonyms
or padding the question with common ones drops the hit. This is the limit
[LIMITS.md](../../LIMITS.md) already names, measured.

**Settings.** The author's eight, ranked by the kernel: 24 hits at top 1, 24
at top 3, 24 at top 10. When the kernel hits here, it hits at rank 1; more
room adds nothing. The advisory words list (oom/rce/uaf, acronyms the
advisories expand) changed no result: those words aren't what the questions
turn on. Only the kernel's rank was reworded and re-ranked here, not BM25.

**Leakage.** All 35 old-side hits rest on a line the fix removed, which is
old-release code, so a comment the fix added can never be a hit on the side
the headline results use. (A separate count: 12 served passages also contain
text the fix adds somewhere, common lines that coincide; the docstring's
guess that this would be zero was wrong, and it doesn't bear on the hits,
which are removed lines.)

**Source.** The plan's fourth check, php.net's release tarball against the
git tree, is not run: php.net is unreachable from here (the proxy returns
403). It stands for anyone to run where php.net is reachable.

The verdict is a row on a kernel record (the chain holds, 2 rows, 0 sealed),
answers SHA-256 ac3c4902. The rewording rule failing is a true finding about
the kernel's ranking, not a flaw in the run; BM25, which the other phases
show is stronger, was not put through rewording.

## Where each phase stands

| Phase | Status |
|---|---|
| 0, freeze | done: 18 releases and 4 fix diffs fetched and matching their pins |
| 2, null tests | done: 4 of 6 pass; random (p = 0.022) and BM25 fail |
| 1, blind questions | done: 4 of 5 pass; the kernel under rule 1 fails (p = 0.022) |
| 6, reproducibility | done: every check passes |
| 3, out of sample | done: 4 of 6 pass; BM25 finds all 7 CVEs, the kernel 1 |
| 4, before the fix | done: 4 of 6 pass; above chance everywhere, strong at the file level |
| 5, robustness | done: rewording rule fails (50% vs 52%); word order free, synonyms costly |

Results go here, each with the tools' hashes it ran on, misses included.

## What the seven phases found, together

All seven have run. The result survives, narrowed and qualified:

- **The method is real, not the author's wording.** Blind questions, from
  people and models that never saw the code, find the fixed code far above
  chance (phases 1, 3, 4), in four projects and three languages, on two CVEs
  disclosed after any model's training (phase 3).
- **Most of the power is the narrowing.** Asking only what changed between a
  release and its fix does most of the work; on the whole release, with no
  fix to compare, it points at the right file but rarely the right line
  (phases 2, 4).
- **BM25 is the ranking that carries it; the kernel's own rank is the weak
  link.** BM25 found all seven phase-3 CVEs and passed every null test; the
  kernel's rank found one, missed the strict margins (phases 1, 2, 3), and
  is the thing rewording breaks (phase 5). Its half-the-words rule and its
  blindness to synonyms are the documented limits, now measured.
- **The pipeline is sound where it can be checked cold.** The index matches
  the kernel exactly, four implementations agree, the bytes are stable
  across Pythons, and an independent reader backs the scoring rule
  (phase 6).

The honest one line: *given a vulnerability's public advisory and the fixed
release, a word-ranker over only the changed code points at the fix well
above chance, across projects and for bugs no model had seen; Willow's own
ranking is weaker at this than plain BM25.*
