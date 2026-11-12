# The sweep grown ten times

**Status: built and dry-run with a made-up stepper; not yet frozen,
and nothing of it pushed or stepped.** The
third of the runs the maintainer asked for. The first two were the
first study's sweep; counting ([the door's page](../README.md)) said
size alone would change nothing. This runs it.

## What is run

[plan.json](plan.json): the first study's 22 setups, each as it was and
at four other distances (0.94, 0.97, 1.03 and 1.06 of its own), each
run to twenty lengths: 2,200 jobs where the first study had 220, dealt
over ten rounds and five machines. The 22 setups at their own distances
are the first study's, start for start, and its ten lengths are among
the twenty, so 220 of the jobs are jobs the first study ran.
[starts.json](starts.json) is every start as exact numbers, made once
with the project's own `make_system`.

[grown_notebooks.py](grown_notebooks.py) makes 55 notebooks: fifty
rounds, each given only its own place's earlier rounds, and a check for
each place over that place's ten rounds. No notebook is given more than
ten inputs. Every folder is signed and every signer enrolled.

**No baseline is run.** Alone, every job would step its own length, or
to where its trajectory halts: 15,721,750 steps if nothing halts. The
shared run finds each halt itself, and the check steps up to each one
to see it halt, so what alone would cost is counted from the plan and
the halts found. Running it would be the dearest thing here and would
show nothing the first study's baseline did not.

## The rules

[grew.py](grew.py) holds what comes back to them:

| | passes when |
|---|---|
| G1 | every folder is whole by its seal and signed by the ring |
| G2 | the share of steps saved is within 2 points of what stepping each trajectory once would save (87.4% if nothing halts; recounted with the halts found) |
| G3 | the checks step every kept state of all fifty folders again, find every one the same, and every halt a halt |
| G4 | each round took in its own place's earlier rounds and nothing else, as enrolled |
| G5 | no trajectory is stepped into its halt twice |
| G6 | each of the 220 jobs the first study also ran comes to the first study's SHA-256 |

Measured, with no threshold: bytes that came back by round, states
kept, seconds, what the checks cost as a share of the sweep alone, the
kinds of processor drawn.

## The dry run

With a made-up stepper and a small made-up plan of three rounds, in
[test_grown.py](test_grown.py): the notebooks run in order and pass;
steps counted twice, a job's bytes changed, or a check that did not
come back fail or are not tested. The grown sweep itself has not been
stepped anywhere, here included.

## What it cannot show

Strangers and liars at this size: every signer is enrolled. A hundred
times: this is ten.
