# The sweep grown ten times

**Status: frozen 2026-11-12, before any job of it was stepped; run on
Kaggle the same day, and every rule passed.** The
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

## The rules, frozen in [FROZEN.json](FROZEN.json)

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

## What came back

Pushed by the maintainer's laptop session on 2026-11-12, through the
privacy gate, in eleven waves, from the first freeze's bytes. All 55
notebooks ended clean the first time; twenty-nine minutes by the clock.
The folders, Kaggle's logs and the timeline are on the branch
`shared-runs/door-kaggle-runs-k3`; the identities and the ring stay on
the laptop.

| | |
|---|---|
| G1 | passed: 55 folders whole and signed by the ring |
| G2 | passed: 1,726,780 steps where alone would be 13,319,565: 87.0% saved, 87.6% foretold; 2,200 of 2,200 jobs |
| G3 | passed: 18,290 of 18,290 states the same, 20 of 20 halts halt, over 50 folders |
| G4 | passed: each round took in its own place's earlier rounds, as enrolled |
| G5 | passed: 20 trajectories halt, none stepped into its halt twice |
| G6 | passed: 220 of the first study's 220 jobs come to its SHA-256 |

Judged on the laptop with the run's ring, and again by the cloud
session from the bytes on that branch.

**What it says about size.**

- **The saving held, and is set by the shape of the sweep, not its
  size.** 87.0% here against the first study's 73.2% is not ten times
  the jobs doing better: it is twenty lengths a trajectory where the
  first study had ten. Each trajectory is still stepped about once,
  and the more jobs lean on that one stepping the more is saved. The
  order the jobs were dealt in cost 4.6% over stepping each exactly
  once (1,726,780 against 1,651,220), where it cost the first study
  about as much.
- **Checking everything costs one more pass, and no more.** The checks
  stepped 1,651,220 steps: to the step, what stepping every trajectory
  once to its end costs. So a sweep shared and then checked in full
  cost 3,378,000 steps, a quarter of the 13.3 million it would cost
  alone: 74.6% saved with every kept state stepped twice by two
  different notebooks. Counting had said a full check would cost about
  a quarter of the first study's sweep alone; here, with more jobs to
  a trajectory, it is an eighth.
- **What comes back shrinks by the round.** 3.4 MB in the first round,
  1.6 in the second, 0.2 by the ninth: most states are kept the first
  time a trajectory is stepped far, and later rounds mostly remember.
  8.5 MB for all fifty rounds, 13 MB with the checks and Kaggle's logs.
- **More of it halts.** 20 of 110 trajectories, five of them refusing
  their first step: moving a setup's planets a few parts in a hundred
  nearer or farther makes some of them fall apart sooner. Alone, the
  sweep would have stepped 13.3 million steps, not the 15.7 million it
  would if nothing halted.
- **Kinds.** 43 notebooks drew an Intel Xeon with AVX2 and 12 an AMD
  EPYC. Places 2 and 4 changed kind between rounds five times each, so
  a place's memory crossed kinds again and again, and every state
  checked the same and the 220 jobs shared with the first study came to
  its bytes. No job here was cut, so none was carried on across kinds.
- **The clock.** A round's notebook took 33 to about 100 seconds from
  push to seen complete, a check 342 to 515. Stepping took 1,593
  seconds in all across the fifty rounds; most of the twenty-nine
  minutes was waiting to see each wave complete.

## What it cannot show

Strangers and liars at this size: every signer is enrolled. A hundred
times: this is ten.
