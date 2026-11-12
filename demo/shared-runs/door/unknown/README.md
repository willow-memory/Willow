# The grown sweep where nobody is known

**Status: frozen 2026-11-12, before any job of it was stepped; run on
Kaggle the same day, and every rule passed.** The
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

## What came back

Pushed by the maintainer's laptop session on 2026-11-12, through the
privacy gate, in eleven waves, from the freeze's bytes. All 55
notebooks ended clean the first time; an hour and twenty-five minutes
by the clock. The folders (47 MB), Kaggle's logs and the timeline are
on the branch `shared-runs/door-kaggle-runs-k5`.

| | |
|---|---|
| U1 | passed: 50 rounds whole, each signed by a key the ring does not hold |
| U2 | passed: every round held every folder it was given |
| U3 | passed: 8,683,650 steps where alone would be 13,319,565: 34.8% saved, 34.8% foretold; 2,200 of 2,200 jobs |
| U4 | passed: all 2,200 jobs end as they did where every signer was enrolled |
| U5 | passed: 88,027 of 88,027 states the same, 163 of 163 halts halt, over 50 folders |

Judged on the laptop with the run's ring, and again by the cloud
session from the bytes on that branch.

**The count was right to the step**: 8,683,650 counted beforehand,
8,683,650 stepped. What a door costs can be known before anything is
run, from the plan and where things halt.

**What fell, at this size.**

- **The saving: 87.0% to 34.8%.** The same 2,200 jobs to the same
  bytes, for 5.03 times the stepping. A memory that is kept and never
  trusted is worth what one round can remember by itself.
- **The memory grew five times and bought nothing more.** 88,027
  states kept where the enrolled sweep kept 18,290, 36 MB of rounds
  where it had 8.5: every round keeps again what an earlier round
  already had and could not be believed about.
- **Checking it cost five times as well.** The checks at the end
  stepped 8,208,050 steps, where the enrolled sweep's stepped
  1,651,220: there is five times as much to look at, most of it the
  same states again in another round's folder. So the whole of it,
  stepped and checked, cost 16.9 million steps, more than the 13.3
  million the sweep costs alone with no memory at all.
- **Every halt is walked into again.** 163 halts are written where the
  enrolled sweep wrote 20: each round finds for itself that a setup
  falls apart.
- **Nothing was wrong.** Every state checked the same and every job
  ended as the enrolled sweep's did. Distrust cost steps and bytes
  and never a wrong answer; and nor did trust, in the grown sweep.
  What separates them is only who was willing to look.
- **The clock.** A round took 135 to 312 seconds from push to seen
  complete, a check 19 to 37 minutes. 52 notebooks drew an Intel Xeon
  with AVX2 and three an AMD EPYC.

## What it cannot show

The middle. Between everyone enrolled and nobody known are the doors a
person would really keep: some places known, a check that clears a
stranger after a round. The [strangers run](../strangers/README.md)
showed one such clearing at the first study's size; a sweep of this
size with a check every round is the next thing to build.
