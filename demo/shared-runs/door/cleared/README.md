# Strangers cleared every round

**Status: frozen 2026-11-12, before any job of it was stepped; run on
Kaggle the same day, and every rule passed.** The
sixth of the runs the maintainer asked for: the middle of the door.
[Every signer enrolled](../grown/README.md) saved 87.0% of the grown
sweep. [Nobody known](../unknown/README.md) was counted to save 34.8%.
A door a person would really keep is between: some places known, some
not, and someone who looks.

## What is run

The grown sweep's 2,200 jobs again. Places 0, 2 and 4 are in the ring.
Places 1 and 3 sign every round with an identity made for that round
alone, which the ring does not hold. After each round but the last, a
checker the ring knows clears each of those two places: it steps again
every state that place has kept which no clearing has yet looked at.
The next round is given the clearing, and takes every earlier round of
its place on the checker's word.

[cleared_notebooks.py](cleared_notebooks.py) makes 73 notebooks: the
fifty rounds, eighteen clearings, and a check a place at the end. No
notebook is given more than ten inputs. A clearing is carried on from
the one before it, so it steps only what is new; machine.py learned to
do that for this run.

## What was counted beforehand

`python demo/shared-runs/door/cleared/bought.py foretell --against RUNS`,
from the enrolled sweep's own folders, stepping nothing:

| | steps | saved |
|---|---|---|
| alone | 13,319,565 | |
| every signer enrolled, as it ran | 1,726,780 | 87.0% |
| two places of five strangers, cleared every round: the sweep | 1,726,780 | 87.0% |
| and the eighteen clearings | 714,369 more | 81.7% with them paid for |
| nobody known, counted | 8,683,650 | 34.8% |

A clearing a round costs 5.4% of the sweep alone and buys back
everything two strangers remember. The clearings look at 7,542 states.

## The rules, frozen in [FROZEN.json](FROZEN.json)

[bought.py](bought.py) holds what comes back to them, and to the
enrolled sweep's kept run:

| | passes when |
|---|---|
| C1 | every folder is whole; the strangers' rounds are signed by keys the ring does not hold, and every other folder by keys it does |
| C2 | every round took in every earlier round of its place and held none: the strangers' on the checker's word, the others as enrolled |
| C3 | every round is the enrolled sweep's, byte for byte, so the strangers cost no step of the sweep itself |
| C4 | the clearings looked at every state and halt places 1 and 3 kept in rounds one to nine, each once, found every one the same, and stepped the 714,369 counted |
| C5 | the checks at the end find every kept state of all fifty rounds the same, and every halt a halt |

Measured, with no threshold: what the clearings cost as a share of the
sweep alone, the saving with them paid for, how many clearings were
carried on on another kind of processor, the kinds drawn.

## The dry run

With a made-up stepper and a small made-up plan of four rounds, in
[test_cleared.py](test_cleared.py): an enrolled run and this one, side
by side. Every rule passes; the clearings step what was counted to the
step and look at nothing twice; a stranger's round that took its
earlier round as enrolled fails C2. The grown sweep has not been
stepped this way anywhere.

## What came back

Pushed by the maintainer's laptop session on 2026-11-12, through the
privacy gate, in twenty waves, from the freeze's bytes. All 73
notebooks ended clean the first time; forty-two minutes by the clock.
The folders (28 MB), Kaggle's logs and the timeline are on the branch
`shared-runs/door-kaggle-runs-k6`.

| | |
|---|---|
| C1 | passed: 73 folders whole; the strangers' rounds signed by keys the ring does not hold |
| C2 | passed: every round took in every earlier round of its place, the strangers' on the checker's word |
| C3 | passed: all 50 rounds are the enrolled sweep's, byte for byte: 1,726,780 steps |
| C4 | passed: 7,542 of 7,542 states looked at, none twice, none not the same; 714,369 steps, 714,369 foretold |
| C5 | passed: 18,290 of 18,290 states the same, 20 of 20 halts halt, over 50 folders |

Judged on the laptop with the run's ring, and again by the cloud
session from the bytes on that branch.

**The three doors, at one size, all run.**

| | steps | saved | wrong bytes out |
|---|---|---|---|
| every signer enrolled | 1,726,780 | 87.0% | none |
| two of five strangers, cleared every round | 1,726,780 and 714,369 for the clearings | 81.7% | none |
| nobody known, nobody cleared | 8,683,650 | 34.8% | none |

Each of the two lower rows was counted before it was run and came to
the count to the step. Looking is cheap and not looking is dear: a
check a round cost 5.4% of the sweep alone and kept 81.7 of the 87.0
points; never trusting cost 52 of them.

**A check carried on from one notebook to the next works on Kaggle.**
Sixteen of the eighteen clearings were carried on from the one before,
and between them looked at each state once. Place 1's clearings drew
an Intel, an Intel, an Intel, an AMD, an Intel, an AMD, an Intel, an
AMD, an Intel: six of its eight carryings-on were onto another kind of
processor, and each says so in its log. Every state was the same. That
is the first work carried on across kinds on Kaggle, and it is a check
and not a job: machine.py still refuses the second.

**One figure was wrong when it first came back, and is put right.**
The judge's count of clearings carried on on another kind said 1 of
18; the logs say 6. It looked only at the last twelve lines of each
log. No rule reads that figure and no verdict changed. The second
freeze in [FROZEN.json](FROZEN.json) says what was changed and why.

**The clock.** A round took 33 to 209 seconds from push to seen
complete, a clearing 31 to 222 (the first of them the longest), a
final check 305 to 446. 63 notebooks drew an Intel Xeon with AVX2 and
ten an AMD EPYC.

## What it cannot show

A stranger who lies, at this size: both strangers here are honest. And
a checker who looks at less than everything.
