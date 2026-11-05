# Percus–Yevick: found, not generated

**DRAFT: not frozen.** Nothing here has been asked of the stack or of a
model except nonsense (the dry run below). The freeze is a later commit of
its own, made before any real question is asked; until then every file may
change.

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

## The dry run

`pipeline.py --dry` asked all 24 questions as nonsense ("qqqq zzzz" and a
number). What it could see, and what it found:

- **Every question served nothing**, as it should.
- **A wiring break.** Santos's lecture notes came out empty: their 196 KB
  main file is ASCII but for one Windows-1252 en dash, and both readers
  skipped any file that wasn't UTF-8. The equations reader now falls back
  to Windows-1252, then Latin-1 (pull request #248). The latex reader still
  skips the file, so the notes' math is in the pile and their prose is not
  until it gets the same fix.

What it can't see: whether any real question is held, which is the result.

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
| R4 | Random baseline | three passages drawn at random from the index for each author question, by a seed fixed at the freeze, find at most 2 of 11 steps |
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
  the rows, R4's random passages drawn by `--seed`, R6 left to the rubric.
  With `--box`, each verdict is a kernel row on a box outside the repo; a dry
  run's are named `percus-yevick:dry:R1` and so on, so they are never read as
  the study's. Its tests use rows and formulas made by hand.
- **Dry run of the tallies** (`--dry --seed 0 --box`): every question served
  nothing, so R1 failing at 0 of 11 and R3 satisfied at 0 of 10; R2 not asked,
  with no blind questions yet; R4's draw ran with its passages made to hold
  nothing, since its true count is a result; R5 satisfied; R6 judged by hand.
  Seven rows, and `kernel.py verify` on the box: "the chain holds: 7 rows, 0
  sealed". R4's seed for the study is fixed at the freeze.

## Open, before the freeze

- **Who judges the rubric**: settled: the physics student, blind, after
  working through the derivation with their advisor.
- **Blind questions**: settled: written by qwen3:8b through
  [blind.py](blind.py), from [questions/blind-prompt.txt](questions/blind-prompt.txt)
  alone (the steps by name, no formula, no source, none of the author's
  questions), at temperature 0 and seed 0. The physics student couldn't
  write them. A model has seen none of this stack, but its physics
  vocabulary was learned from the same literature, so its questions may
  share the sources' words more than a student's would.
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
        --seed N --box BOX [--dry]
    python kernel.py verify --box BOX

STACK, WORK and OUT.json are outside the repo. The pipeline records the
SHA-256 of the kernel, scan, the three readers, score.py and steps.json with
its rows.
