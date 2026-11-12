# The door on Kaggle: the first study's sweep, cut, carried on and sealed

**Status: frozen 2026-11-12, before any of it was pushed to Kaggle.
Dry-run here only.** The maintainer's word for it, going to bed: "come
up with the next few and run them". This is the first of them, and the
smallest: nothing new is stepped. It asks whether
[machine.py](../machine.py) does on Kaggle what it did on two machines
at home, in the one place where three things can go wrong that cannot
at home: a part carried from one notebook to the next, a part that
comes back on another kind of processor, and a seal made on a machine
nobody here can see.

## What is run

The first study's plan and starts, unchanged: 220 jobs, five machines,
two rounds. [door_notebooks.py](door_notebooks.py) makes sixteen
notebooks, each private, CPU only, carrying its files inside itself:

| notebooks | what each does |
|---|---|
| `round-1-machine-K-a`, five | the first round, stopped by a budget of ten seconds |
| `round-1-machine-K`, five | the same round, carried on from what `-a` left |
| `round-2-machine-K`, five | the second round, given its own place's first round and nothing else |
| `check` | every kept state of the ten stepped again, and every halt |

Each place signs with an identity made for this run and no other, and
every notebook carries the ring. If a part comes back on another kind
of processor, machine.py refuses to go on, and the notebook begins that
part over and says so.

## The rules

[held.py](held.py) holds what comes back to them, and to the first
study's kept runs:

| | passes when |
|---|---|
| K1 | every folder that ended is whole by its seal, its log holds, and its signer is in the ring |
| K2 | each machine's part is the first study's, byte for byte, on whatever kind it drew |
| K3 | every first-round part was carried on, at least one cut inside a job, and none began over without saying so |
| K4 | the ten shared runs step 336,379 steps |
| K5 | the check finds every kept state the same and every halt a halt |
| K6 | each second round took in its own place's first round, as enrolled, and nothing else |

Measured, with no threshold: the kinds of processor drawn, the parts
begun over, the seconds, the bytes that came back.

## The dry runs

With a made-up stepper, in [test_kaggle.py](test_kaggle.py): the
notebooks run in order and pass; a part made to look as if it came back
on another kind is begun over, says so, and still passes K2; a state
changed after it came back fails K1 and K2; a folder that did not come
back leaves the rules not tested and never passed.

With the project's stepper, on the cloud session, all sixteen as
processes given only folders: every rule passed. Five parts were cut
inside a job and carried on; 336,379 steps; 3,473 of 3,473 states and
four halts of four; 2.3 MB came back in all. One kind of processor, so
the refusal across kinds was tried only in the made-up dry run. That is
a dry run of the wiring and not a result.

## What it cannot show

Strangers and liars: every signer here is enrolled and honest. Size:
it is the first study's sweep. Those are the next two.
