# How clear the path is

The second score, beside the hit rule in [score.py](score.py): not whether a
step was reached, but whether what reached it explains it. The physicist's
measure of a good answer is one that "holds my hand through the complex
analysis". DRAFT: not frozen; who judges is not yet settled.

## Each step, scored 0 to 3

| Score | The step's passages, or the model's text for it |
|---|---|
| 0 | Missing, or wrong. |
| 1 | States the result: the formula is there, with no reason given. |
| 2 | States it and says why: names the move (a Fourier transform, a closure, a factorization) and what it rests on. |
| 3 | Walks through it: each non-obvious move has its reason, so a reader who knows calculus but not this field could redo it. |

For s5 (Baxter) a 3 means: why the factor is analytic in a half-plane, why
Q(r) vanishes outside 0 < r < sigma, and how the closure fixes the quadratic
and its two coefficients.

## How it is judged

- **Blind.** The judge sees, for each step, two texts labelled A and B: the
  found chain's passages and the model's derivation, in an order set by a
  seed frozen in advance. Neither the labels nor the order say which is
  which.
- **By someone who knows the field.** The physicist says this is beyond
  them; their advisor is the obvious candidate. To be settled before the
  freeze.
- **Recorded as kernel rows**, one per step and text, appended to a box
  outside the repo, as php2shell's verdicts are.

## What it can't tell

A found chain is made of passages written for other purposes, in several
notations; a model writes one text in one notation. The rubric scores what
each step says, not how well the whole reads, so a chain that changes
notation between steps isn't marked down for it here. That is a choice,
stated.
