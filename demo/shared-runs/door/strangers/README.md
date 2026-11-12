# Strangers at the door, and one who lies

**Status: frozen 2026-11-12, before any of it was pushed to Kaggle;
run there the same day, and every rule passed.** The second of the runs the maintainer asked for
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

## The rules, frozen in [FROZEN.json](FROZEN.json)

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
processes given only folders: every rule passed. Held, the takers of
places 1 and 3 stepped 53,562 and 56,635 steps where the first study's
second round stepped 14,765 and 4,530. The check found both changes
(three of the liar's 891 states and halts not the same, since the state
after a changed one is wrong too) and the other four places clean.
After it, place 1 was taken and stepped the first study's 14,765; place
3 stayed held. One kind of processor. A dry run of the wiring, not a
result; the figures are kept in [FROZEN.json](FROZEN.json).

## What came back

Pushed by the maintainer's laptop session on 2026-11-12, through the
privacy gate, in four waves, from the freeze commit. All thirteen ended
clean the first time; eleven minutes by the clock. The folders, the
liar's own account of its lie, Kaggle's logs and the timeline are on
the branch `shared-runs/door-kaggle-runs-k2`; the identities and the
ring stay on the laptop.

| | |
|---|---|
| T1 | passed: 13 folders whole; two first rounds signed by keys the ring does not hold |
| T2 | passed: held, the takers of places 1 and 3 stepped 53,562 and 56,635 steps where the first study stepped 14,765 and 4,530 |
| T3 | passed: the changed state found, the halt that is no halt found; the other four places clean |
| T4 | passed: place 1 taken on the checker's word, 14,765 steps, the first study's bytes; place 3 still held |
| T5 | passed: every job of the seven second rounds ends as the first study's did |

Judged on the laptop with the run's ring, and again by the cloud
session from the bytes on that branch.

**What it cost.** Not being known cost place 1 38,797 steps, once: its
second round stepped 3.6 times what it would have, and after one check
it cost nothing more. Lying cost place 3 its whole memory for good:
52,105 steps more in every round that follows, until someone steps
those trajectories again honestly. The check that told the two apart
stepped 276,269 steps for all five places. Nobody was handed a wrong
byte at any point, before the check or after.

Measured: twelve notebooks drew an Intel Xeon with AVX2 and one an AMD
EPYC. Place 2's first round ran on the AMD and its taker on the Intel:
a folder kept on one kind was gone on from on another, and the second
round came to the first study's bytes. That is a memory crossing kinds
between two runs, which the door allows; it is not a run taken up
again part way on another kind, which machine.py refuses and which has
still not been met. The figures are the dry run's to the step, on other
processors.

## What it cannot show

An enrolled signer who lies: the door takes an enrolled signer's
folder without a check, and this run has none. That is the
[lies study](../../lies/README.md)'s question. And size: this is the
first study's sweep.
