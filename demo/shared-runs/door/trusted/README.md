# A liar the ring trusts

**Status: frozen 2026-11-12, before any of it was pushed to Kaggle;
run there the same day, and every rule passed.** The fourth of the runs the maintainer asked
for. Among [the strangers](../strangers/README.md) the liar was not
enrolled, so the door held it before anyone looked and no wrong byte
went out. Here the liar's key is in the ring.

## Why it is run

The door's rule takes an enrolled signer without a check: that is what
being enrolled is for. So an enrolled signer who lies is taken, and
wrong bytes go out until someone looks. That is the cost of the rule,
and this run measures it on the first study's sweep.

What happens after someone looks is the part that was wrong. As the
door stood for the first three runs, it went on taking an enrolled
signer's folder even when an enrolled checker had stepped it again and
found it not the same. No rule of those runs turned on it, since their
enrolled signers were honest; their freezes say so. The door now holds
such a folder, and any folder that went on from it, whoever signed
them. This run is what holds the door to that.

## What is run

Twelve notebooks, made by [trusted_notebooks.py](trusted_notebooks.py):

| notebooks | what each does |
|---|---|
| `round-1-machine-K`, five | the first round, every place enrolled. Place 3 then lies, as among the strangers: one kept state changed, one halt written where nothing halts, sealed again with its own key |
| `round-2-machine-K-before`, five | the second round, by a taker the ring knows, given its own place's first round |
| `check` | every kept state and halt of the five first rounds, and of place 3's second round, stepped again |
| `round-2-machine-3-after` | place 3's second round again, given its first round, the second round that went on from it, and the check |

## The rules, frozen in [FROZEN.json](FROZEN.json)

[seen.py](seen.py) holds what comes back to them, and to the first
study's kept runs:

| | passes when |
|---|---|
| N1 | every folder is whole and signed by the ring, the liar's among them |
| N2 | before the check, the liar's folder is taken as enrolled and the harm goes out: a job stops at the halt that is no halt, and a job from the changed state comes to a wrong SHA-256 |
| N3 | the check finds both changes, and the other four first rounds clean |
| N4 | after the check, the liar's first round and the round that went on from it are both held, whoever signed them, and every job done again ends as the first study's did |
| N5 | the other four places take their own and are the first study's, byte for byte |

N2 is a rule that passes when harm is seen. That is on purpose: a run
in which the lie did not bite would show nothing about what follows.

Measured, with no threshold: how many jobs go out wrong before the
check; what the check finds of the round that went on from the lie;
steps; the kinds of processor drawn.

## The dry runs

With a made-up stepper, in [test_trusted.py](test_trusted.py): the
twelve run in order and every rule passes; a run in which the door went
on taking the liar after the check fails N4.

With the project's stepper, on the cloud session, all twelve as
processes given only folders: every rule passed. Before the check the
liar was taken and two jobs of 20 went out wrong, one stopped at the
halt that is no halt and one from the changed state. The check found
both changes. Of the round that went on from the lie it found 19 of 19
states the same. After it, both were held and the round done again
came to the first study's bytes, for 56,635 steps. One kind of
processor; a dry run of the wiring, not a result.

## What came back

Pushed by the maintainer's laptop session on 2026-11-12, through the
privacy gate, in four waves, from the freeze commit. All twelve ended
clean the first time; ten minutes by the clock. The folders, the liar's
own account of its lie, Kaggle's logs and the timeline are on the
branch `shared-runs/door-kaggle-runs-k4`; the identities and the ring
stay on the laptop.

| | |
|---|---|
| N1 | passed: 12 folders whole and signed by the ring, the liar's among them |
| N2 | passed: the liar's folder was taken; 2 jobs went out wrong, one stopped at the halt that is no halt and one from the changed state |
| N3 | passed: both changes found; the other four places clean |
| N4 | passed: the liar's first round held, the round that went on from it held; no job wrong after, 56,635 steps |
| N5 | passed: the other four places took their own and are the first study's, byte for byte |

Judged on the laptop with the run's ring, and again by the cloud
session from the bytes on that branch. Nine notebooks drew an Intel
Xeon with AVX2 and three an AMD EPYC. The figures are the dry run's to
the step.

**What it cost, beside the strangers.** A liar nobody knew cost nobody
a wrong byte and cost its own place 52,105 steps a round. A liar the
ring trusted put two wrong jobs out of twenty into the world before
anyone looked, and then cost the same 52,105 steps once someone had.
Being enrolled is worth what was seen in the [strangers
run](../strangers/README.md): 38,797 steps saved for an honest place.
What it risks is what was seen here: whatever a trusted signer gets
wrong goes out until a check looks. The check is the same check either
way, 276,269 steps for the five places.

**The round that went on from the lie: 19 of 19 states "the same".**
On Kaggle as in the dry run. See the next section; it is the reason the
door holds a folder for what it took in.

## What the check cannot see by itself

A state stepped rightly from a wrong state is the right step from the
wrong place. A check that steps each kept state again from the one
before finds the first wrong state and the one after it, and then
finds the rest of that run's states "the same". So the round that went
on from the lie can look clean to the check of its own steps. The door
does not lean on that: it holds a folder because of what it took in,
which its seal names, not because of how its own steps check.

## What it cannot show

How often to look. Here one check looks at everything once. A liar who
is right most of the time, and a checker who looks at one state in
several, is the [lies study](../../lies/README.md)'s question, and it
is still drafted and not run.
