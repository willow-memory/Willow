# The same brief, given to models that run on a laptop

**Status: asked 2026-11-12, on the maintainer's word; not yet run.** A
measurement made after [the first study](../README.md) was judged. It is
entry C4 of [NEXT.md](../NEXT.md), and changes none of that study's
verdicts.

The first study's two agents were hosted models, and both got every
question right once the scorer was mended. That says little about where
it stops working. This gives the same input to the models the
maintainer's laptop runs itself, from half a billion parameters up.
Nothing leaves that machine.

## What is fixed before any model is asked

- **The input** is [the two agents' own](../study/results/agent-input.txt),
  whole and unchanged, as the only thing a model is given: no system
  prompt, nothing before it, nothing after. Its SHA-256 is
  `7745af1d72a29d84177a6c0525970830a61ae89b0585c2d9e850645f5d3e6346`.
- **One ask a model**, at the model's own default settings, with nothing
  kept from an earlier ask.
- **The scorer** is the first study's account.py as its second freeze
  left it, and the key is the one it makes from the kept run.
- **What is counted for each model**, as R7, R8 and R9 were: how many of
  the 16 questions the reports answer it got right; how many sentences
  of its account say a figure no report holds; how many of the 5
  questions the reports don't answer it left unsaid. And, where there is
  no line `## account` or no answers at all, that.
- **No threshold.** These are measurements. What is expected, said now:
  the smallest will guess at the questions that have no answer, and some
  will not keep to the form.

## What to do, on the laptop

For each model that ollama lists:

1. Give it the input file's text as the whole prompt, once.
2. Save what it sends back, word for word, as
   `answers/NAME/answers.txt` in this folder, NAME being the model's name
   with its colon made a dash.
3. Beside it, as `answers/NAME/model.txt`, the line `ollama list` gives
   for it: its name, its id and its size.

Then, for each:

    python demo/shared-runs/study/account.py score --plan demo/shared-runs/study/plan.json --runs demo/shared-runs/study/runs demo/shared-runs/local-models/answers/NAME/answers.txt

What comes back to the branch is the `answers` folder. The counting and
the writing up are done after, from those files.
