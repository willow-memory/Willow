# Strangers at the door, and one who lies

**Status: built and dry-run with a made-up stepper; not yet frozen,
and nothing of it pushed or stepped.** The second of the runs the maintainer asked for
("come up with the next few and run them"). The
[first](../kaggle/README.md) had every signer enrolled and honest. This
one is the first study's sweep again, with two places that are neither.

## What is run

Thirteen notebooks, made by
[strangers_notebooks.py](strangers_notebooks.py):

| notebooks | what each does |
|---|---|
| `round-1-machine-K`, five | the first round. Places 0, 2 and 4 sign with identities the ring holds; places 1 and 3 with identities it does not. Place 3 then lies |
| `round-2-machine-K-before`, five | the second round, by a taker the ring knows, given its own place's first round |
| `check` | every kept state and every halt of the five first rounds stepped again, by a checker the ring knows |
| `round-2-machine-K-after`, for places 1 and 3 | the second round again, given the check as well |

**The lie** ([lie.py](lie.py)) is two changes to place 3's sealed
memory, each chosen so the next round would lean on it: the first byte
of the kept state its longest later job would go on from is turned
over, and on another trajectory a halt is written where nothing halts.
Place 3 then makes its seal again over the changed files and signs it
with its own key. The seal holds. A seal says who left a folder and
that it is as they left it; it does not say the folder is right.

## The rules

[told.py](told.py) holds what comes back to them, and to the first
study's kept runs:

| | passes when |
|---|---|
| T1 | every folder is whole and its signature holds; the two strangers' first rounds are signed by keys the ring does not hold, and everything else by keys it does |
| T2 | before the check, the takers of places 1 and 3 hold what they are given and step more than the first study did there; the other three take theirs and step what the first study did |
| T3 | the check finds places 0, 1, 2 and 4 the same throughout, and finds both of place 3's changes |
| T4 | after the check, place 1 is taken on the checker's word and its second round is the first study's, byte for byte; place 3 is still held |
| T5 | no job of any second round comes to a byte the first study's did not |

Measured, with no threshold: what being held costs a place in steps,
what the check steps, the kinds of processor drawn.

## The dry runs

With a made-up stepper, in [test_strangers.py](test_strangers.py): the
thirteen run in order and every rule passes; the same liar's folder
given to a door with no ring spoils at least two jobs, so the lie is
one that bites; and a run where the cleared stranger was not taken, or
the check did not come back, fails or is not tested.

With the project's stepper, on the cloud session, all thirteen as
processes given only folders: running as this is written. One kind of
processor. A dry run of the wiring, not a result.

## What it cannot show

An enrolled signer who lies: the door takes an enrolled signer's
folder without a check, and this run has none. That is the
[lies study](../../lies/README.md)'s question. And size: this is the
first study's sweep.
