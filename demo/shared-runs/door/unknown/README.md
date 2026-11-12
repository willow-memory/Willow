# The grown sweep where nobody is known

**Status: frozen 2026-11-12, before any job of it was stepped.** The
fifth of the runs the maintainer asked for, and the one their question
was about: what falls at a larger size. [The grown sweep](../grown/README.md)
said size alone changes nothing when every signer is enrolled. This is
the same 2,200 jobs with the other end of the door: every signer a
stranger, and nobody ever cleared.

## What is run

[unknown_notebooks.py](unknown_notebooks.py) makes the grown sweep's
55 notebooks again, with one thing changed. Every round signs with an
identity made for that round alone, and the ring holds none of them. So
each round's folder is whole and signed, and its signer is nobody the
door knows: a later round holds every folder it is given, and steps
from what it kept itself. The memory is kept and carried and never
trusted. Nobody checks until the end, when a check a place looks at
every folder, to see that what was held was in fact right.

## What was counted beforehand

`python demo/shared-runs/door/unknown/fell.py foretell --against RUNS`,
from the plan and the halts the enrolled sweep found, stepping nothing:

| | steps | saved |
|---|---|---|
| alone | 13,319,565 | |
| every signer enrolled, as it ran | 1,726,780 | 87.0% |
| nobody known, counted | 8,683,650 | 34.8% |

A place still remembers within a round, so a third is saved; what is
lost is everything one round could have had from another. That is five
times the stepping for the same answers.

## The rules, frozen in [FROZEN.json](FROZEN.json)

[fell.py](fell.py) holds what comes back to them, and to the enrolled
sweep's kept run:

| | passes when |
|---|---|
| U1 | every folder is whole and its signature holds, and no round's signer is in the ring |
| U2 | every round held every folder it was given |
| U3 | the share of steps saved is within 2 points of the 34.8% counted |
| U4 | every one of the 2,200 jobs ends as it did where every signer was enrolled: the same end, outcome and SHA-256 |
| U5 | the checks find every kept state of every round the same, and every halt a halt |

Measured, with no threshold: steps beside the enrolled sweep's, states
kept, bytes that came back, the kinds of processor drawn.

## The dry run

With a made-up stepper and a small made-up plan, in
[test_unknown.py](test_unknown.py): an enrolled run and this one, side
by side; every round holds what it is given, the steps are what was
counted to the step, and every job ends as the enrolled run's did. The
enrolled run passed off as this one fails U2 and U3; a changed job
fails U4. The grown sweep itself has not been stepped this way
anywhere.

## What it cannot show

The middle. Between everyone enrolled and nobody known are the doors a
person would really keep: some places known, a check that clears a
stranger after a round. The [strangers run](../strangers/README.md)
showed one such clearing at the first study's size; a sweep of this
size with a check every round is the next thing to build.
