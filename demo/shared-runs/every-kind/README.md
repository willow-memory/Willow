# Every job on every kind: an addition to the first study

**Status: written and dry-run 2026-11-12, then frozen; see the end.**
An addition made after [the first study](../README.md) was judged. It
changes none of that study's verdicts and none of its files.

## Why

R1 passed: nothing disagreed anywhere it was tried, on three kinds of
processor. But one kind did the work and the others checked it. Counted
strictly, as a job run from its start to its end on a kind:

| kind | jobs of the 220 it ran in full |
|---|---|
| Intel, AVX2 (Kaggle) | 220 |
| Intel, AVX-512 (the laptop, the cloud session) | 20, the ones the draw picked to run afresh |
| AMD, AVX2 (Kaggle) | 0: every job dealt to it went on from the memory |

So the sentence "the same bytes on three kinds" rests, for most jobs, on
kept states stepped again and not on the job itself. This runs the job
itself.

## What is done

A machine runs the whole sweep alone, with the first study's own
runner.py, plan and starts, on the project at its commit and under
NumPy 2.1.3:

    python demo/shared-runs/study/runner.py alone --plan demo/shared-runs/study/plan.json --starts demo/shared-runs/study/starts.json --repo PROJECT --to OUT/NAME

Its folder, `OUT/NAME`, goes in `runs/` here under its name. Then
[every_kind.py](every_kind.py) holds it to what Kaggle's first baseline
came to.

Three machines are named, and no other is added without saying so here
first:

| name | what | what is known of it beforehand |
|---|---|---|
| `cloud-session` | the cloud session this was written in | Intel, AVX-512. In the first study it ran 20 of these jobs afresh and all 20 were the same |
| `laptop` | the maintainer's laptop | Intel, AVX-512. The same 20 jobs, the same |
| `phone` | the maintainer's phone, if its NumPy builds | ARM with NEON. Its NumPy is built there against another linear-algebra library than every other machine's, so it differs in two things at once: whatever it shows cannot be put down to the processor alone |

The AMD machine cannot be asked: Kaggle chose it, once, for one notebook.

## The rules

| rule | passes when |
|---|---|
| E1, the job itself | every added machine ran every job of the plan alone, and each came to the same outcome, the same step and the same bytes as the first baseline. A machine that ran fewer is not tested; one job otherwise fails it |
| E2, how far it reaches, measured | no threshold: the jobs run in full on each kind, and on how many kinds each job was, counting what the first study's machines ran from a start |

What is expected, said now: E1 passes for the two AVX-512 machines,
since the 20 jobs each already ran were the same and 1,305 kept states
were. That is two kinds in full, not three. A third comes only from the
phone, and of the phone nothing is known.

## The dry run

On the first study's made-up sweep and this cloud machine: the 30 jobs
run alone again and held to the dry run's own baseline, 30 of 30 the
same. What that could see is that the judge reads a run and a truth and
says so; a test with a changed byte and a test with a run cut short hold
the other two verdicts. It could not see a second kind, being one
machine.

## What it cannot show

- The AMD kind in full.
- Anything about the project as it is written. This is the rewritten
  power only; the first study's R2 measured the other.
- That the phone's difference, if there is one, is the processor's.
