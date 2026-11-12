# A liar the ring trusts

**Status: built and dry-run with a made-up stepper; not yet frozen,
and nothing of it pushed.** The fourth of the runs the maintainer asked
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

## The rules

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
