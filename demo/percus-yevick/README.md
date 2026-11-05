# Percus–Yevick: found, not generated

**DRAFT: not frozen.** Nothing here has been asked of the stack or of a
model except nonsense (the dry run below). The freeze is a later commit of
its own, made before any real question is asked; until then every file may
change.

A physicist learning liquid theory asked a local model for a derivation of
the hard-sphere equation of state in the Percus–Yevick approximation,
starting from scattering and avoiding Wertheim's method
([prompt.md](prompt.md)). A model asked that must recall a field 120 years
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
every passage holding it says "Laplace".

## The physicist's notes, folded in

From the physicist who set the problem:

- **One radius, uniform electronic density, in vacuum.** In the prompt, and
  as step s1b: the uniform sphere's form factor.
- **Theory only.** No experimental data; comparing with experiment is a
  later project, and an active field.
- **A clear path, not just the answer.** The rubric scores each step 0 to 3,
  from missing to walked through.
- **Start simpler.** Step s0, the low-density limit, is the warm-up rung.

## The stack

[sources.json](sources.json): 13 arXiv papers (their LaTeX source) and 11
Wikipedia revisions, each by address, version, time fetched and SHA-256,
never their text. [fetch.py](fetch.py) fetches them again and checks the
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
  hypernetted-chain closure.

Left out: further sticky-sphere papers, at the physicist's warning that
Baxter's attractive shell is a complication of its own; Henderson 2009
(Condensed Matter Physics), which holds the factorization but has a sign
slip in a; and a scanned 1993 Rev. Mex. Fís. paper whose text can't be read
reliably. The books the physicist recommends (Hansen and McDonald, McQuarrie,
Goodstein, Guinier and Fournet, Oberdisse and Lindner) are under copyright
and are not in the stack.

The pile is built by the repo's own readers: [latex](../../adapters/stdlib/latex/)
for each paper's prose, [equations](../../adapters/stdlib/equations/) for its
math, [mediawiki](../../adapters/stdlib/mediawiki/) for each Wikipedia
revision. It holds 36 files and 4,368 passages.

## The models

Two local models, run by Ollama 0.40.14 on this machine (127.0.0.1 only),
are given the prompt for the side that generates: [gemma3-4b](models/gemma3-4b.md)
and [qwen3-8b](models/qwen3-8b.md), each card read from the weights file's own
header by weights-card, with its SHA-256. weights-pin holds the file to its
card before each run. The physicist's friend's own model is not one of
these; which model that is, and whether to add it, is open.

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
- **The rule is strict.** A formula in another form (expanded, or with the
  diameter set to 1) is not held. That makes misses likelier, not hits.

## Open, before the freeze

- **Pass rules**: what share of steps must be held, and what null hit rate
  makes a hit mean nothing. To be written down here, with numbers.
- **Who judges the rubric**: someone who knows the field, blind; the
  physicist suggests it's beyond them.
- **Blind questions**: from whom.
- **For the physicist**: whether "Baxter includes the infinitesimal
  attractive region" means the method itself, or Baxter's other 1968 paper
  on sticky spheres; which four books he meant; and the exact title of the
  Oberdisse and Lindner monograph.
- **Ornstein and Zernike's 1914 paper**, likely open in the Dutch academy's
  (KNAW) digital library, to be checked and perhaps added.

## Running it

    python demo/percus-yevick/fetch.py --to STACK            # online
    python demo/percus-yevick/fetch.py --to STACK --check    # offline
    python demo/percus-yevick/pipeline.py --stack STACK --work WORK --out OUT.json --dry

STACK, WORK and OUT.json are outside the repo. The pipeline records the
SHA-256 of the kernel, scan, the three readers, score.py and steps.json with
its rows.
