# The problem

The prompt the local models are given, word for word, and the one the
found chain answers. DRAFT: not frozen.

## As asked

> Give a derivation in great gory detail of the equation of state for a
> monodisperse hard sphere fluid using the Percus-Yevick approximation.
> Start from the general expression for the amplitude of a wave scattered
> from the electronic density. In your derivation, you *must* avoid
> Wertheim's method.

## What the physicist added

From the physicist who set the problem (Discord, 2026-11-05), folded in:

- **The spheres are all the same radius and have uniform electronic
  density.** Anything else is too hard to start with, and can't be compared
  with until the simpler case is done. This makes the form factor that of a
  uniform sphere (step s1b).
- **They are in a vacuum.** There's no solvent to subtract, which makes the
  equations a little neater: the contrast is the electronic density itself.
- **Theory only.** The study derives the result; it doesn't fit experimental
  data. Comparing a model with experiment means getting the prefactors and
  assumptions right, which is why that is still an active field, and is a
  later project.
- **A clear path counts, not only the right answer.** "The LLM should hold my
  hand through the complex analysis and/or functional calculus." A
  derivation that reaches the answer without explaining its steps is
  scored lower than one that does; see [rubric.md](rubric.md).

## The prompt as asked of the models

> Give a derivation in great gory detail of the equation of state for a
> monodisperse hard sphere fluid using the Percus-Yevick approximation.
> The spheres all have the same radius and a uniform electronic density,
> and are in a vacuum. Start from the general expression for the amplitude
> of a wave scattered from the electronic density. In your derivation, you
> *must* avoid Wertheim's method. Explain each step, especially the complex
> analysis, so that someone learning it could follow.
