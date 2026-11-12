# The same brief, given to models that run on a laptop

**Status: asked and answered 2026-11-12; scored below.** A
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
   `answers/<NAME>/answers.txt` in this folder, NAME being the model's name
   with its colon made a dash.
3. Beside it, as `answers/<NAME>/model.txt`, the line `ollama list` gives
   for it: its name, its id and its size.

Then, for each:

    python demo/shared-runs/study/account.py score --plan demo/shared-runs/study/plan.json --runs demo/shared-runs/study/runs demo/shared-runs/local-models/answers/<NAME>/answers.txt

What comes back to the branch is the `answers` folder. The counting and
the writing up are done after, from those files.

## What came back

Fourteen models were on the laptop. The maintainer's session there gave
each the input whole, once, at its own settings, and checked the input's
SHA-256 against the one above first. Thirteen answered; one is a model
for embeddings and cannot answer at all, and its refusal is kept. Every
answer is in [answers/](answers/), word for word, with the line that
names the model. Scored here by the first study's account.py as its
second freeze left it; the counts are in [results.json](results.json).

| model | size on disk | right, of 16 | left unsaid, of 5 | guessed, of 5 | wrote an account |
|---|---|---|---|---|---|
| qwen3:4b | 2.5 GB | 16 | 5 | 0 | yes |
| qwen3-4b-32k | 2.5 GB | 16 | 5 | 0 | yes |
| llama3.2:3b | 2.0 GB | 16 | 5 | 0 | no |
| gemma4:e2b | 4.6 GB | 16 | 5 | 0 | yes |
| qwen2.5vl:7b | 6.0 GB | 16 | 5 | 0 | yes |
| mistral:7b | 4.4 GB | 15 | 5 | 0 | no |
| gemma3:4b | 3.3 GB | 14 | 5 | 0 | no |
| phi4-mini | 2.5 GB | 13 | 3 | 1 | yes |
| willow-lane4-3b | 2.0 GB | 15 | 0 | 5 | yes |
| qwen2.5:0.5b | 397 MB | 0 | 0 | 5 | no |
| llama3.1:8b | 4.9 GB | 0: not in the form | 0 | 0 | yes |
| llama3.2:1b | 1.3 GB | 0: not in the form | 0 | 0 | no |
| qwen3.5 | 6.6 GB | nothing: an empty answer after 1,250 seconds | | | |
| nomic-embed-text | 274 MB | cannot answer: an embedding model | | | |

No sentence of any account was struck: of the seven that wrote one, none
said a figure the reports lack.

What that says:

- **Five models that fit on a laptop did what the two hosted ones did**:
  every question right and every unanswerable one left unsaid. Two of
  them are 2 to 2.5 GB on disk.
- **Saying "the reports don't say" does not go by size.** A 2 GB model
  left all five unsaid and another 2 GB model guessed all five. The
  one that guessed got 15 of the 16 real answers right: it can read the
  report, and it will not leave a blank.
- **Two took the steps for the seconds.** Asked how many seconds the
  shared run took, phi4-mini and willow-lane4-3b both gave 336379, which
  is the shared run's steps. The nearest figure was put where there was
  none.
- **One said "not specified" to a question the reports answer.**
  mistral:7b, on the baseline's steps. The wall can be wrong in that
  direction too.
- **The smallest gave the reports back.** qwen2.5:0.5b copied the input
  out under headings and answered nothing.
- **The form is a test of its own, and a stricter one than it should
  be.** llama3.1:8b wrote its answers in bold, each name between
  asterisks, and the scorer found none of them. With the asterisks taken
  out, by hand and not by the frozen scorer, it is right on 16 of 16 and
  leaves all 5 unsaid. So one of the two "not in the form" rows is the
  scorer's strictness and not the model. llama3.2:1b's answer is not in
  any form.
- **Six of the thirteen wrote no account**, so for them R8 has nothing
  to hold. The first study's two agents both wrote one.

What it does not say: anything about these models beyond this one brief,
asked once. A second ask could come out otherwise, and none was made.
