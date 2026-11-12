# Strangers cleared every round

**Status: frozen 2026-11-12, before any job of it was stepped.** The
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

## What it cannot show

A stranger who lies, at this size: both strangers here are honest. And
a checker who looks at less than everything.
