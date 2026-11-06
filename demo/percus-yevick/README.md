# Percus–Yevick: found, not generated

**Frozen 2026-11-06**, in commit d9d46e9, alone: [FROZEN.json](FROZEN.json)
holds the SHA-256 of every source pin, step, question, rule, model card and
tool, and the tests fail if one changes. Nothing had been asked of the stack
or of a model before it but nonsense (the dry runs below). A change is a new
freeze, with its reason.

An ML specialist is asking a local model for a derivation of the
hard-sphere equation of state in the Percus–Yevick approximation, starting
from scattering and avoiding Wertheim's method ([prompt.md](prompt.md)). A
physics student who is learning this derivation themselves read the problem
and said what a good answer needs. A model asked that must recall a field 120 years
deep all at once. This study asks whether the derivation can instead be
*found*: each step served by the kernel from a stack of open sources, with
the place it came from, and a step the stack doesn't hold said to be
missing rather than made up.

## The claim

> Asked in plain words, step by step, the kernel serves from the frozen
> stack a passage holding each step of the chain in [steps.json](steps.json),
> from the scattering amplitude to βP/ρ = (1+η+η²)/(1−η)³, through Baxter's
> factorization, with no step reached only through Wertheim's method; and
> the found chain explains its steps at least as well as the local models'
> derivations do, judged blind ([rubric.md](rubric.md)).

## How it could be wrong

| Threat | What answers it |
|---|---|
| The questions knew too much | Blind questions from someone who hasn't seen the stack; the author's are labelled as his |
| Anything would have hit | The null questions, physics off the chain, asked of the same stack |
| "Hit" was defined after looking | The anchors in steps.json are frozen before any question is asked; see "Said plainly" |
| The stack was picked to fit | sources.json lists every source with its role, distractors and the forbidden route included |
| It found formulas, not understanding | The rubric: a second score, for how well each step is explained |

## The chain

| Step | What it is |
|---|---|
| s0 | Warm-up: the low-density limit 1 + 4η + 10η², which every route must reproduce |
| s1a, s1b, s1c | The amplitude from the electronic density; a uniform sphere's form factor; intensity as form factor times structure factor |
| s2 | S(q) from g(r) − 1 |
| s3 | Ornstein–Zernike, and S = 1/(1 − ρĉ) |
| s4 | The Percus–Yevick closure for hard spheres |
| s5a, s5b | Baxter's factorization, and Q(r)'s coefficients |
| s6 | S(0) = (1−η)⁴/(1+2η)², the compressibility |
| s7 | The compressibility equation of state |

Two traps are scored apart from the chain: Carnahan–Starling, which is not
PY, and PY's virial route, which is right for its own route but not the one
a scattering start leads to. A step counts as reached through Wertheim when
every passage holding it says "Laplace", and through Baxter's sticky spheres
when every passage holding it names them (sticky, adhesive, adhesion).

**The extended chain.** The physics student asked for more than the equation
of state: the functions along the way, and the scattering quantities a
measurement gives. These are steps too, each with its anchor in
[steps.json](steps.json), asked and reported beside the pass rules but
never counted in them:

| Step | What it is |
|---|---|
| e1 | The direct correlation function inside the core, a cubic |
| e2 | The contact value of g(r), (1 + η/2)/(1 − η)² |
| e3 | The total correlation function, h = g − 1 |
| e4 | The cavity function y(r), an auxiliary PY function |
| e5 | The form factor P(q) |
| e6 | The intensity I(q) as P(q) times S(q), at a given concentration |
| e7 | A graph of g(r) or S(q) at a stated packing fraction, found by its caption |

They also asked for graphs and for how the functions relate. The kernel
serves text, so a graph is found only through what its caption says (e7),
and how the functions relate is for the found chain's reader, and the
rubric, to judge.

## The physics student's notes, folded in

From the physics student:

- **One radius, uniform electronic density, in vacuum.** In the prompt, and
  as step s1b: the uniform sphere's form factor.
- **Theory only.** No experimental data; comparing with experiment is a
  later project, and an active field.
- **A clear path, not just the answer.** The rubric scores each step 0 to 3,
  from missing to walked through.
- **Start simpler.** Step s0, the low-density limit, is the warm-up rung.

## The stack

[sources.json](sources.json): 13 arXiv papers (their LaTeX source), 11
Wikipedia revisions and one scanned paper, each by address, version, time
fetched and SHA-256, never their text. [fetch.py](fetch.py) fetches them again and checks the
hashes offline (`--check`). Each source has a role:

- **chain:** where a step is expected, such as Wu's thesis (2604.03963,
  Baxter's factorization in full) and Coquand and Sperl (1912.06574, JCP
  2020, Baxter's coefficients), the second Baxter source;
- **forbidden route present:** Wertheim's Laplace method, in Santos's
  lecture notes (1310.5578) and three others, so that avoiding it is
  something the chain does, not something the stack makes trivial;
- **trap present:** Wikipedia's "Hard spheres", which gives only
  Carnahan–Starling;
- **distractor:** Baxter's sticky spheres (cond-mat/0406603), the
  hypernetted-chain closure;
- **motivation:** Ornstein and Zernike's own 1914 paper, "Accidental
  deviations of density and opalescence at the critical point of a single
  substance" (KNAW Proceedings 17 II, 793–806), from the KNAW Digital
  Library's scan. Its text is the scan's OCR: readable as prose, with
  errors ("deviatiuns"), and its math not to be relied on.

Left out: further sticky-sphere papers, at the physics student's warning that
Baxter's attractive shell is a complication of its own; Henderson 2009
(Condensed Matter Physics), which holds the factorization but has a sign
slip in a; and a scanned 1993 Rev. Mex. Fís. paper whose text can't be read
reliably. The books the physics student recommends are under copyright and are not in the
stack. In their words (2026-11-05): Hansen and McDonald, *Theory of Simple
Liquids*, "the bible for liquid theory"; four general statistical-mechanics
books for background: McQuarrie, *Statistical Mechanics*; Hill's two
(presumably *Statistical Mechanics: Principles and Selected Applications* and
*An Introduction to Statistical Thermodynamics*); and Goodstein, *States of
Matter*; Guinier and Fournet, "the OG for SAXS" though its nomenclature is
dated,
*Small-Angle Scattering of X-Rays* (1955; HathiTrust gives it as search-only,
so in copyright); and the monograph he names as Oberdisse and Lindner's,
which is *Neutrons, X-rays, and Light: Scattering Methods Applied to Soft
Condensed Matter*, edited by Lindner and Oberdisse (Elsevier, second edition
2024; the first, 2002, was edited by Lindner and Zemb): "much more
experimental and modern, good for comparison with experiment".

The pile is built by the repo's own readers: [latex](../../adapters/stdlib/latex/)
for each paper's prose, [equations](../../adapters/stdlib/equations/) for its
math, [mediawiki](../../adapters/stdlib/mediawiki/) for each Wikipedia
revision. [pdf](../../adapters/deps/pdf/), which needs pypdf, reads the scanned paper.
The pile holds 37 files and 4,431 passages.

## The models

Two local models, run by Ollama 0.40.14 on this machine (127.0.0.1 only),
are given the prompt for the side that generates: [gemma3-4b](models/gemma3-4b.md)
and [qwen3-8b](models/qwen3-8b.md), each card read from the weights file's own
header by weights-card, with its SHA-256. weights-pin holds the file to its
card before each run. The ML specialist's own model can't be one of these. They report
Qwen3.8-Flash-Next at IQ3_S, run by Strata. Strata is said to be an MIT-licensed
local runtime, and the model has 125 billion parameters with a download of about
70 GB, too large for a 15 GB machine with no GPU. So its derivations come from the ML specialist's machine.

What they reported (2026-11-05) for the run behind their interim report and
transcript: Strata 0.1.56 (from its install path), the weights in two GGUF
files, `Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-0000{1,2}-of-00002.gguf`, a Strata
pack of their own naming (so an IQ3_S build does exist, as Strata's; the
public lists name IQ3_XXS); speculative decoding with DFlash2 drafts and MTP;
a 256k context, int8 KV cache, a 157.5k reasoning budget, compaction keeping
30k; and opencode's default temperature, which they took to be 0.8. No seed
is set, so the run can't be repeated token for token. The weights files' SHA-256,
as they sent them: `4c1eb2ce…7d2aca3` (00001-of-00002) and `316b46f3…c161e113`
(00002-of-00002), in full:
`4c1eb2ceb4915e1192f4f386021897bde56a97f40a0bb78bb86465e0f7d2aca3` and
`316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113`. The temperature
is not known: they took opencode's default to be 0.8 and did not confirm it.
That is as far as the record of this run goes; it is closed as it stands.

They also sent the solver the session wrote (`alt3.py`, 69 lines, SHA-256
`b7ac94de…7122d6`, kept outside the repo). It is numerics only (numpy and
scipy): the bilinear real-space system solved by alternating linear solves,
c given h then h given c, with an Aitken-style step and η stepped up by 0.02;
it saves its arrays under /tmp. Read, it matches the report's description, and one line of it is dead (line
13's value is overwritten on line 14). Run here with the person's leave
(numpy 2.5.4, scipy 1.18.1), on the report's finer grid (`alt3.py ETA 321
0.025`), it gives the report's S(0) column to every digit: 0.6731437,
0.1406129, 0.0253955 at η = 0.05, 0.25, 0.45. The contact values the report lists (1.135747, 2.00035, 4.0493) come from an
extrapolation to r = 1 that this script doesn't do; it prints g at the first
node (3.83 at η = 0.45). The transcript logs that step's output but not its
code; done here as it describes, a quadratic through the six nodes of
(1, 1.15] evaluated at r = 1, it gives 1.135742, 2.00030 and 4.04994, within
5×10⁻⁴ of the report. Its own residual, the largest
miss in the equations it solves, is 6×10⁻⁶, 7×10⁻⁴ and 0.034 at the three
η, so at η = 0.45 the solve is not converged tightly, which fits its S(0)
being 0.2% off the closed form there.

**Reasoning, on and off.** Through Ollama's OpenAI-compatible endpoint, which
local-model and same-way use, qwen3:8b reasons before it answers; gemma3:4b
doesn't reason at all. Measured here on 2026-11-05 (Ollama 0.40.14): `/no_think`
at the top of the system message and `"think": false` in the request both
left it reasoning (233 and 237 tokens for a one-sentence answer);
`"reasoning_effort": "none"` stopped it (10 tokens). **Both, side by side** (decided 2026-11-05): the found-then-arranged arm asks
qwen3:8b twice, once with its reasoning and once with `reasoning_effort` set
to none, and gemma3:4b once, having none. The option that sends it,
`--reasoning` on local-model and same-way, is pull request #259; this study
is built on that branch, and its tools are hashed as they are there.

**Expected, before anything is run:** reasoning isn't needed to arrange found
passages. The person running this study found so in other studies, and this
arm is more data on it. Whether it held is reported, with each version's
claim-check and misquote counts and the rubric's scores, not argued.

## The dry run

`pipeline.py --dry` asked all 24 questions as nonsense ("qqqq zzzz" and a
number). What it could see, and what it found:

- **Every question served nothing**, as it should.
- **A wiring break.** Santos's lecture notes came out empty: their 196 KB
  main file is ASCII but for one Windows-1252 en dash, and both readers
  skipped any file that wasn't UTF-8. The equations reader now falls back
  to Windows-1252, then Latin-1 (pull request #248), and the latex reader
  now does the same (#249).

A second dry run, on 2026-11-06, rebuilt the pile with both fixes and ran
the pipeline (`--seed 0`, verdicts to a scratch box) and every arm in
[arms.py](arms.py), with qwen3:8b, qwen3:8b with no reasoning, and gemma3:4b:

- **Santos's notes are in**: 114 KB of prose and 132 KB of math. The one
  file still skipped, `diagrams_LN.tex`, is picture macros and no text.
- **Every rule tallied and every verdict was written**: 0 of 11 steps, 0 of
  7 extended, 0 of 10 nulls serving a step, R4's draw at 0, R5 satisfied,
  R6 left to the judge; `kernel.py verify` held on the box.
- **Every ranker served nothing a step counts**, bm25 included, which
  always serves its top passages: the hit rule, not the ranker, is what
  keeps nonsense from counting.
- **why-not, predict, claim-check and misquote ran** and said what each
  should on nonsense.
- **contradictions found only LaTeX**: five "disagreements", every one
  between macro names read as words (`frac`, `left`, `right`, `boxed`). On
  this pile it measures nothing, so it was dropped before the freeze.
- **The arranged arm asked each model on a plumbing box** that holds one
  nonsense passage, so a model has something to answer. Reasoning off
  really was asked differently: qwen3:8b with its reasoning declined one of
  the two questions and answered the other; with none it answered both.
  gemma3:4b declined both. same-way: 0 flipped for all three, with Ollama
  alone on the machine. (The first dry run, sharing the machine, flipped
  gemma at temperature 0: the real run gets the machine to itself.)
- **A wiring break**: the arm kept only the last 400 characters of an
  answer, so a long one lost its start. It now keeps the whole answer.
- **Time**: the pipeline 7 seconds; the arms 42 minutes, 39 of them the
  three model variants on this machine's CPU, for two questions each. The
  real run asks many more, so it is a run of hours, not minutes.

- **A gap neither dry run showed**: the pipeline asked the author and null
  sets unless told otherwise, so the blind questions were never asked and R2
  came out "not asked". It now asks every blind set too. A pipeline-only dry
  run after the fix asked all 49 (21 author, 18 blind, 10 null): R2 failing
  at 0 of 11, as nonsense should, and eight rows on the box, which verify.

What it can't see: whether any real question is held, which is the result.

## The run

Run once, on 2026-11-06 from 01:53 UTC, at commit d758030 (the freeze is
d9d46e9), on the stack as `fetch.py --check` found it: all 25 sources the
same as their pins. Every question asked as written; the pipeline took 7
seconds.

| Rule | Verdict | Frozen number |
|---|---|---|
| R1 | **failing** | 1 of 11 steps found (s3); needed 9, with s5a, s5b and s7 |
| R2 | **failing** | 1 of 11 found (s5a); needed 7, with s5b and s7 |
| R3 | satisfied | 0 of 10 null questions served a chain step; at most 2 |
| R4 | satisfied | 1 of 11 steps found by random passages, seed 0; at most 2 |
| R5 | satisfied | no found step only through Wertheim or sticky spheres |
| extended | reported | 3 of 7: e2, e3, e6 |
| R6 | not yet judged | the physics student, with [rubric.md](rubric.md) |

**Freeze 1's claim failed: the kernel alone did not find the chain.** That
is narrower than the claim of the person running this study, which is that
the stack *and the add-ons* find it; freeze 2, below, tests that. The
author's questions found one step of eleven,
Ornstein–Zernike (s3, from Wikipedia's article); the blind questions found
one, a different one, Baxter's factorization (s5a, from Coquand and
Sperl's square-shoulder paper). The
random baseline found as many as either. The answer itself, s7, was found by
no question. R6 is still to be judged, but with one step found there is
little chain for it to judge.

The rows: `found.json`, SHA-256 `db31eb39d0df8908609f996c17961d58c9316f246a28c0a73025e4888a752d3e`,
and eight verdict rows on a box outside the repo, the last row's hash
`c4fe510d18b3ea858ae25b5d01bd3ff14cbe6cf575d72c47670d580c6aec5ecc`;
`kernel.py verify` on it: "the chain holds: 8 rows, 0 sealed".

**Looked at after the result, not part of it.** How many of the pile's
5,533 passages meet the hit rule, step by step, whatever any question asked:

| Step | Passages that hold it | Step | Passages that hold it |
|---|---|---|---|
| s0 | 0 | s5a | 10 (all math) |
| s1a | 0 | s5b | 12 (all math) |
| s1b | 8 (all math) | s6 | 2 (math) |
| s1c | 2 | s7 | 4 (all math) |
| s2 | 3 | e1, e5, e7 | 0 |
| s3 | 6 | e2, e3, e4, e6 | 4, 5, 3, 1 |
| s4 | 2 | | |

So the stack holds 9 of the 11 steps, which is exactly R1's bar and no
more, and it lacks s0 and s1a under their anchors outright. The other eight
the kernel didn't find. Most of the passages that hold a step are from
the equations reader: an equation and a line or two around it, few of the
words a question asks in. A passage must hold half a question's content
words to be served, and these mostly don't. This reading is a guess at the
cause, made after seeing the result; testing it is a new study with a new
freeze, not a change to this one.

The arms (rankers, why-not, predict, claims on the ML specialist's interim
report, and the models arranging what was found) were still running when this
was written; they are reported below when done, and none of them changes a
verdict.

## Freeze 2: the stack and the add-ons

Freeze 1 was written as "the kernel serves", and R1 to R4 count the kernel
alone; every other add-on was an arm, reported and never counted. After the
run, the person running this study said that was never the claim: "my claim
isn't that the kernel alone could find it." It is that a stack of data and a
pile of add-ons can find the derivation, and the frozen rules didn't test
that. So a second freeze, before anyone read the arms' output, tests it
with the same questions, steps, hit rule and stack:

| Rule | What | Needed |
|---|---|---|
| R7 | The author's questions, asked of all five rankers (the kernel, the kernel with words.txt, scan's BM25, pile-rungs, latent), three passages each; a step counts when any ranker serves its own question a passage holding it | at least 9 of 11, with s5a, s5b and s7 |
| R8 | The blind questions, the same way | at least 7 of 11, with s5b and s7 |
| R9 | The null questions: served a chain step by any of the five | at most 2 of 10 |
| R10 | Random baseline: fifteen passages a question (five rankers, three each), seed 0 | at most 2 of 11 |

Reported beside them, never counted: each ranker's own finds, and the steps
found only through Wertheim's Laplace method or sticky spheres.

- **Why R9 and R10 matter here.** BM25 and latent always serve their top
  passages, whatever is asked, and five rankers serve fifteen passages to a
  question where the kernel serves three. Without them, volume could pass
  for finding.
- **What was known when it was written**: freeze 1's result, including
  which steps the stack holds at all (above). Not known: anything any other
  ranker served. The arms were running, and their output wasn't read until
  freeze 2 was committed. The ceiling is the same: no ranker can find s0 or
  s1a, so R7 needs every other step.
- **Counted by [union.py](union.py)**, which uses arms.py's rankers unchanged
  and every question set. Its verdicts are kernel rows named
  `percus-yevick:R7` and on. Its tests use rows made by hand.
- **Dry run** (2026-11-06, 02:09 to 02:14 UTC): all 49 questions asked as
  nonsense, of all five rankers: R7 and R8 failing at 0, R9 and R10
  satisfied at 0, nothing found through Wertheim; five rows on the box,
  which verify. It shared the machine with the arms' model arm for those
  minutes.
- **Frozen in [FROZEN-2.json](FROZEN-2.json)**, in commit 2a53628, alone: the hashes of
  union.py, its rules, and every file and tool it uses. Freeze 1 is
  unchanged and its verdicts stand.

## Said plainly

- **The anchors were written after the source search had grepped each
  source for these formulas.** The search's report named which sources hold
  which step. The anchors are the textbook forms of each formula, and their
  tests use formulas written by hand, not lines from the stack, but they were
  not written blind.
- **The author's questions** ([questions/author.txt](questions/author.txt))
  were written by someone who has seen the source list and that report.
  Blind questions are still to be written by someone who hasn't.
- **A model's interim report was read before the freeze.** On 2026-11-05 the
  ML specialist shared an interim report from an opencode session (a PDF,
  SHA-256 `befd4060…63f9ac`, kept outside the repo). steps.json, score.py and
  the questions were not changed after reading it; a later change to them
  will say whether it was.
- **The same session's full transcript was read too** (Markdown, SHA-256
  `bb472654…41dea1`, kept outside the repo). It fetched three of this
  stack's Wikipedia revisions itself (Ornstein–Zernike, Percus–Yevick, Hard
  spheres), so its answer was partly found as well. It judged the C code on
  the Percus–Yevick page wrong; run here, that code matches a structure
  factor computed from the PY c(r) to six digits at every q tried, and fails
  only for qr below about 10⁻², where its last term loses its digits to
  cancellation. The page stays in the stack. Nothing frozen-to-be was changed
  after reading it.
- **The rule is strict.** A formula in another form (expanded, or with the
  diameter set to 1) is not held. That makes misses likelier, not hits.

## Pass rules

Approved 2026-11-05, before any real question was asked; they go into
FROZEN.json with the freeze. A step is **found** when, for any of its
questions, one of the kernel's top three passages holds that step's anchor
in [steps.json](steps.json). There are 11 steps.

| # | Rule | Passes when |
|---|---|---|
| R1 | Found, with the author's questions | at least 9 of 11 steps found, and s5a, s5b and s7 among them |
| R2 | Found, with the blind questions | at least 7 of 11 steps found, and s5b and s7 among them |
| R3 | Off-topic questions | at most 2 of the 10 null questions are served a passage holding any chain step |
| R4 | Random baseline | three passages drawn at random from the index for each author question, by seed 0 (`tally.SEED`), fixed at the freeze, find at most 2 of 11 steps |
| R5 | Avoiding Wertheim, and hard spheres done directly | no found step is reached only through passages that say "Laplace", or only through passages that name sticky spheres |
| R6 | A clear path, judged blind ([rubric.md](rubric.md)) | the found chain's mean score is at least the model's, and the found chain scores at least 2 on s5 (Baxter) |

Why these numbers:

- **R1** allows two misses where the stack is thinnest (the scattering
  start), but none on Baxter's step or the answer, which are the point.
- **R2** is lower because blind questions won't share the sources' words;
  it is the stronger test.
- **R3** isn't 0 because two null questions (the hypernetted-chain and mean
  spherical closures) are close cousins of the chain by design.
- **R4** rules out a stack so full of these formulas that anything lands.
- **R5** has no tolerance: avoiding Wertheim is a hard constraint of the
  prompt. The sticky-sphere half was added on 2026-11-05, before any real
  question was asked, at the physics student's wish to see hard spheres
  done directly, not as the limit of no attraction.
- **R6** is the physics student's own measure, and the physics student
  scores it, blind, once they have worked through the derivation with their
  advisor's help (their advisor won't judge, but will help them learn it). The model's text is the ML
  specialist's final derivation if one comes, else their interim report; the
  local models' derivations are scored the same way, each beside the found
  chain.

How they are reported:

- **Each rule gets its own verdict**, a kernel row, with its number. There is
  no overall verdict that could hide a failure: R1 can hold while R2 fails,
  and both are written down.
- **Traps are reported, not scored.** Carnahan–Starling or the virial route
  served beside the s7 anchor is no fault; served without it, s7 is not found,
  which R1 and R2 already count.
- **Counted by [tally.py](tally.py)**, which pipeline.py calls: R1 to R5 from
  the rows, R4's random passages drawn by `tally.SEED` (0; `--seed` takes
  another only with `--dry`), R6 left to the rubric.
  With `--box`, each verdict is a kernel row on a box outside the repo; a dry
  run's are named `percus-yevick:dry:R1` and so on, so they are never read as
  the study's. Its tests use rows and formulas made by hand.
- **Dry run of the tallies** (`--dry --seed 0 --box`): every question served
  nothing, so R1 failing at 0 of 11 and R3 satisfied at 0 of 10; R2 not asked,
  with no blind questions yet; R4's draw ran with its passages made to hold
  nothing, since its true count is a result; R5 satisfied; R6 judged by hand.
  Seven rows, and `kernel.py verify` on the box: "the chain holds: 7 rows, 0
  sealed". R4's seed is 0, the one both dry runs used.

## Settled before the freeze

- **R4's seed**: 0, `tally.SEED`, the one both dry runs used.
- **The rubric's A/B order**: by `random.Random(0)`, step by step, as
  [rubric.md](rubric.md) says.
- **The contradictions arm**: dropped. On this pile it compares LaTeX macro
  names, not physics (the second dry run).

- **Who judges the rubric**: settled: the physics student, blind, after
  working through the derivation with their advisor.
- **Blind questions**: settled: written by qwen3:8b through
  [blind.py](blind.py), from [questions/blind-prompt.txt](questions/blind-prompt.txt)
  alone (the steps by name, no formula, no source, none of the author's
  questions), at temperature 0 and seed 0. The physics student couldn't
  write them. A model has seen none of this stack, but its physics
  vocabulary was learned from the same literature, so its questions may
  share the sources' words more than a student's would. Written 2026-11-05,
  18 questions, one a step, in [questions/blind-a.txt](questions/blind-a.txt)
  with the reply word for word beside it. They stay close to the prompt's
  names for the steps, and those names were written by the author, who had
  seen the source search: blind to the sources and to the author's
  questions, not to the author's names for the steps.
- **The ML specialist's run is in, as far as it goes**: the interim report,
  the full transcript, the solver, the weights' hashes and Strata's settings.
  Its final long-form derivation, if one comes, is the text to score; until
  then the interim report is.
- **Baxter, which paper.** Baxter published two papers in 1968. "Ornstein–Zernike
  Relation for a Disordered Fluid" (Aust. J. Phys. 21, 563) is the
  factorization, and its abstract says the PY hard-sphere solution follows
  from it, with no attraction. "Percus–Yevick Equation for Hard Spheres with
  Surface Adhesion" (J. Chem. Phys. 49, 2770) is the one with the
  infinitesimal attractive shell. This study's step s5 is the first. The
  physics student's answer (2026-11-05): the warning was about the second,
  the sticky-sphere model, and they would like to see the method applied to
  hard spheres directly, "without it just being the limit that the
  attractive potential goes to 0". The factorization on plain hard spheres,
  as Wu and as Coquand and Sperl give it, is that.

## Running it

    python demo/percus-yevick/fetch.py --to STACK            # online
    python demo/percus-yevick/fetch.py --to STACK --check    # offline
    python demo/percus-yevick/pipeline.py --stack STACK --work WORK --out OUT.json \
        --box BOX [--dry]
    python kernel.py verify --box BOX

STACK, WORK and OUT.json are outside the repo. The pipeline records the
SHA-256 of the kernel, scan, the three readers, score.py and steps.json with
its rows.
