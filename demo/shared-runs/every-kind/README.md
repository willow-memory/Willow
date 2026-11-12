# Every job on every kind: an addition to the first study

**Status: frozen 2026-11-12. The cloud session's and the laptop's parts
are run and judged; the phone's is under way. See "What has
come back" at the end.**
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

## What has come back

Frozen in [FROZEN.json](FROZEN.json) before any of the three machines
ran the sweep alone. Each judging is a pair of rows,
`shared-runs:every-kind:E1` and `E2`, on the same record outside the
repository as the first study's verdicts; a copy is
[results/record.jsonl](results/record.jsonl), and the kernel says of it:
"the chain holds: 23 rows, 0 sealed". It is judged again, onto that
record, each time a machine's folder comes back, so the record holds a
pair of rows for each judging.

**The cloud session, 2026-11-12.** An Intel Xeon with AVX-512, NumPy
2.1.3, the project at its commit. It ran all 220 jobs alone.

| rule | verdict | what was counted |
|---|---|---|
| E1 | **passed**, for the one machine back | 220 of 220 jobs the same outcome, step and bytes as Kaggle's baseline |
| E2 | measured | every job now run in full on two kinds: Intel AVX2 220, Intel AVX-512 220. On three kinds: 0 |

So what the first study's R1 rested on for most jobs, kept states
stepped again, is now the job itself for all of them, on a second kind.
A third kind in full waits on the phone.

**The laptop, 2026-11-12.** An Intel Core i7 with AVX-512, NumPy 2.1.3
in an environment of its own, the project at its commit, run by the
maintainer and brought in from the branch
`shared-runs/laptop-every-kind`. It ran all 220 jobs alone.

| rule | verdict | what was counted |
|---|---|---|
| E1 | **passed**, for the two machines back | cloud-session 220 of 220 the same as Kaggle's baseline; laptop 220 of 220 |
| E2 | measured | unchanged: Intel AVX2 220, Intel AVX-512 220; on three kinds 0. The laptop is the cloud session's kind, so it is a second machine and not a third kind |

Two machines of one kind, a laptop's Core i7 and a cloud Xeon, now
agree with each other and with Kaggle's on every job.

**The phone, so far, as the laptop's session tells it.** Its every-kind
run is still going. Before it, the phone did the dry sweep by the
tester's page: it says its kind is `other arm64 neon` (the runner names
Intel, AMD and Apple as makers, and this is none of them), NumPy 2.1.3;
with the power rewritten, 30 of 30 jobs the same bytes as the machine
that wrote the page; as the project is written, 6 of 30. That is a dry
run on made-up setups and no result. It is the first sign from a
processor that is not x86, and from a machine whose NumPy is linked to
another linear-algebra library.

## What it cannot show

- The AMD kind in full.
- Anything about the project as it is written. This is the rewritten
  power only; the first study's R2 measured the other.
- That the phone's difference, if there is one, is the processor's.
