# Shared runs: a plan for a study, not yet a study

**Status: a plan, written 2026-11-11. Nothing is frozen, nothing has been
run, and no number below is a result.** Every threshold here is a proposal
for the maintainer to set or change before the freeze. It becomes a study
on the day its sources, questions and pass rules are committed alone, as
[the rules for a study](../../docs/agents/studies.md) say.

It tests, small, the claim the design note
[one shape, at every size](../../docs/design/one-shape.md) ends on: that
computing should be remembered and shared, not done again. And it is
planned to be run in a way no study here has been: not led by a person,
but by a script, with each agent receiving only what a script or another
agent reported.

**A first try of the handover has been run here**, small and not the
study: three agents, one kept run, twelve closed questions. What was fixed before it is in
[trial-1/RULES.md](trial-1/RULES.md), and what happened in
[trial-1/RESULTS.md](trial-1/RESULTS.md). A second let three agents build:
each added a step to a stack from the built add-ons, handed only what the
last run left. Its rules are in [trial-2/RULES.md](trial-2/RULES.md) and
what happened in [trial-2/RESULTS.md](trial-2/RESULTS.md). A third put code
in the agents' place, three rules from the same start, and set the two
side by side: [trial-3/RESULTS.md](trial-3/RESULTS.md).
A fourth asked the plan's R2 of willow's own work: one stack run in two
folders, and whether each step came out the same,
[trial-4/RESULTS.md](trial-4/RESULTS.md).

## The claim

> A sweep of simulations, run on machines nobody chose, sharing one memory
> keyed by each run's inputs, does less computing than the same sweep run
> alone; what it serves from memory is, bit for bit, what running it would
> have given; checking a served result costs far less than making it; and
> an agent handed only the reports can say what happened, and no more.

## The setup

- **The job** is a friend's star system simulation, science_bitch, which
  already gives each setup a SHA-256 made from its inputs. A sweep of a few
  hundred setups is written so that many share a beginning: the same
  bodies and step, run to different lengths, and the same start with one
  body added.
- **The machines** are Kaggle notebooks, started separately, on whatever
  processor each is given. No graphics card is needed.
- **The wire** is a shared dataset. Notebooks cannot reach one another, so
  each reads the dataset, adds what it computed under its inputs' name,
  and publishes the next version.
- **Each notebook keeps its own record**: a kernel box, on a throwaway key
  that `init` makes there. The maintainer's key is never put on Kaggle,
  and nothing is sealed there in anyone's name.
- **Each thing stored says its kind**: a result computed, a result served
  from memory, a check of a result, a run that halted.

## The rules, proposed

Each becomes a row on a box outside the repo, with the SHA-256 of the
answers and tools it was judged from. A rule with no threshold is a
measurement, and is reported as one.

| rule | passes when |
|---|---|
| R1, the fixed runtime agrees | every job run inside the WebAssembly runtime gives the same bytes on every machine that ran it, on at least three kinds of processor |
| R2, the native run, measured | no threshold: the share of jobs whose native NumPy runs agree to the last bit across machines, with where the first difference falls |
| R3, memory saves the work it should | the steps not computed, as a share of the baseline's, are within two points of the share the sweep's shared beginnings predict, worked out before the run |
| R4, memory serves only what a run would give | of a tenth of served results, chosen by a seeded draw and run afresh, every one is the same bytes |
| R5, a check is cheap | verifying a served result takes at most a twentieth of the time computing it took, at the median |
| R6, a failure is not repeated | no setup recorded as halted is run again by a later notebook |
| R7, the blind account | the receiving agent's answers to the frozen questions match the key the script makes from the records; see below |
| R8, the blind account adds nothing | no sentence of the receiving agent's account names a figure, a machine or an outcome that no report holds |
| R9, the blind account says when the reports don't | every frozen question the reports hold no answer to is answered "the reports don't say", and none of them with a figure |

## A session led by a script

The demos here ran scripts blind, with frozen questions and no one
steering. The sessions that built willow were led by a person. This study
is planned as the first that is neither: agents doing real work, with no
person in the loop until the end.

**How it would go.**

1. **A script starts it.** It reads the frozen plan and hands the first
   agent a written brief: the job, what it may run, where to write.
2. **An agent does one phase and writes a report.** The report is a file,
   made from what the scripts recorded, not from the agent's memory of
   them: what ran, on what, the hash of what each printed, what failed.
3. **The next agent is blind.** It is started fresh and given only the
   brief for its phase and the reports before it. It has not seen the
   earlier agent's session, and cannot ask it anything.
4. **A script checks each handover.** Before a report is passed on, every
   figure and outcome in it is looked for in the records. A sentence the
   records don't hold is struck, and the strike is itself recorded.
5. **A person comes in at the end**, to read the last report and seal or
   decline what waits. No agent seals. The run ends with proposals waiting,
   as every session here does.

**What is asked of the last agent.** A frozen list of questions about the
run, each with one answer the script can work out from the records: how
many setups were computed and how many served, which machines disagreed
and where, which setups halted, how much was not computed. It answers from
the reports alone, each answer with the line it came from.

**Some of the questions have no answer.** A share of the frozen list asks
what no report holds: a machine that never ran, a setup that was not in the
sweep. The right reply is that the reports don't say (R9). A list with no
such question can't tell an agent that knows from one that always answers.

**Why it is worth testing on its own.** The stack in
[demo/kept](../kept/README.md) showed a session breaking three rules that
were only written down, with nothing to stop it. A chain of agents is
where that matters most: each takes the last one's word. R7 asks whether
a true account survives being handed on. R8 asks whether anything is added
on the way.

**What is already here for it.** The handover add-on writes where a
project stands from what was kept, every line naming its file. The look
add-on answers a question from a kept run's own lines. The thesis and
claim-check add-ons put a sentence to a folder, part by part.

## What one session's trial run says of R7 to R9

A session the same day put one plain question, "What's the connection
between these two?", about 23 pairs of passages to 18 models, each pair in
a chat of its own: five on the session's machine, from half a billion
parameters to ten, and thirteen hosted, run as one private Kaggle benchmark
task. Every pair shared one number and, for most, nothing else. The answers
were sorted by a word pattern and a handful read in full; they are kept on
that machine, not here, so these are an account, not a result.

- **Asked an open question, a model answers.** Only two of the eighteen
  said "nothing joins these but the number" for most pairs. The seven
  mid-sized hosted models said it for at most a third of them, and the
  small ones' "nothing" fell on pairs at random. So R8 can't rest on the
  agent holding back: the strike has to be a script's, as planned.
- **Models agreeing is not a record.** On pairs the largest models called
  empty, most models still added the same words, because each described
  the two passages the same way. Agreement between agents is no check of a
  report; the records are.
- **An agent that sees more than its brief sees more than a blind one.**
  Three agents were first handed all the pairs in one sitting, and named
  the shared number every time. Asked one pair a chat, the smallest of
  the three named it as the only link for 6 pairs where it had for 16
  (the two were not the same version of the model). The brief's whole
  input, kept by SHA-256, is the guard, and it has to be the whole of it.
- **A second model is within reach.** One Kaggle task ran on thirteen
  hosted models, privately, with no key on the session's machine. The
  receiving agent could be run as two different models in this study, and
  not left to a later one.
- **What is uploaded is checked first, by a tool, not by eye.** One pair
  named the maintainer and held a signature; it was left out. The check
  that found it was written on the spot, where a stricter one already
  existed and should have run first.

## How it could be wrong

| threat | what is planned against it |
|---|---|
| The sweep is built to flatter memory | R3's predicted share is worked out from the sweep before any run, and the sweep is frozen with it |
| Every Kaggle machine is the same kind | R1 needs three kinds of processor; if Kaggle gives fewer, R1 is reported as not tested, never as passed |
| A served result is trusted because it is served | R4 runs a seeded tenth afresh; the draw's seed is frozen |
| The baseline is slowed by something else | the baseline and the shared run use the same notebook settings, and the baseline is run twice |
| A report is written to please | reports are made from records, and R8 strikes what the records lack |
| The receiving agent was told the answers | it is started fresh, and its whole input is kept by SHA-256 |
| The agents are the same model, so they agree | the receiving agent is run as two different models, if the maintainer says so (see the trial run above); if only one, it is said plainly as a limit: agreement between two of one model is weak evidence, and a second model is a later study |
| A dry run that finds nothing tests nothing | the dry run gets one made-up setup its nonsense questions find, as the study rules ask |

## What it cannot show

- **Scale.** This is tens of machines for hours. It can show the idea
  working or failing; it cannot show a thousand machines.
- **Strangers.** Every notebook is run by one account. Nothing here tests
  a machine that lies.
- **Tightly coupled work.** The sweep is independent runs. A problem whose
  pieces must talk constantly is not helped by any of this.

## Before the freeze

These are not known, and the plan waits on them.

- **Kaggle's terms and limits**: how long a session runs, how many at
  once, whether a notebook may write a dataset from inside a run, and
  whether its rules allow this use. They are to be read, not recalled.
- **Which processors Kaggle gives**, found by a notebook that only
  reports its own.
- **Whether the fixed runtime runs there**, and how much slower it is
  than native.
- **The maintainer's say** on running code from outside this repository:
  science_bitch, and the two tools sent to its author, a store of runs
  kept under their inputs' name and a witness of what a run computed.
- **What is checked before it is uploaded, and by what.** Every notebook,
  dataset and brief that leaves the maintainer's machine is put through a
  privacy check first: names, keys, paths, signatures. Which tool, and its
  list of terms, is the maintainer's to name; the list is never committed.
- **Which agents, and what each may do.** The brief for each phase, the
  commands it may run, and what it must never do, written before any is
  started.

### What a first look at Kaggle found

On 2026-11-11 a session pushed nine private notebooks that report only
the machine they run on, internet off, each put through the maintainer's
privacy check first. What they printed is kept on that session's machine,
not here, so this is an account for the list above, not a result.

| asked | found |
|---|---|
| how many at once | five: the sixth push was refused, "Maximum batch CPU session count of 5 reached" |
| the machine | 4 cores, 32.9 GB of memory, 21 GB of working disk |
| the processor | Intel Xeon at 2.20 GHz, with AVX2 and without AVX-512, on nine of nine |
| what is installed | Python 3.13.18, NumPy 2.1.3 on OpenBLAS; no WebAssembly runtime |
| internet, switched off | none reached |
| a small job, pushed to finished | about 90 seconds |
| the account's week | 45 hours of GPU and 20 of TPU; a CPU notebook uses neither |

What that settles, and what it moves:

- **Which processors Kaggle gives: one kind, as far as nine draws show.**
  R1 asks for three. On CPU notebooks alone it would be reported as not
  tested. A second kind has to come from somewhere else: Kaggle's GPU
  machines, which spend the week's hours, or a machine that is not
  Kaggle's.
- **R2 would pass there for the wrong reason.** Two small NumPy sums came
  out the same, to the last bit, on all nine: one processor, one NumPy.
  The session's own laptop differed from them in the last digits of both,
  but it has another processor and a newer NumPy, so which of the two did
  it is not shown. R2 needs machines that differ in one thing at a time.
- **Five at a time, in rounds.** "Tens of machines" is tens of runs, five
  at once.
- **The fixed runtime is not there.** It would be installed in each
  notebook, which needs internet on for that step, or carried in as a
  dataset.

Still not known: Kaggle's own page of limits and its terms (the page gave
no text when fetched; other sites say twelve hours a session, unchecked),
whether a notebook may write a dataset from inside a run, and how much
slower the fixed runtime is than native.

### What a first try at the whole thing found

Later the same day the session tried the plan small, on the star-system
add-on's stand-in and not on science_bitch: 95 made-up jobs over nine
trajectories, two of which halt, dealt to five machines. What it ran and
printed is on that session's machine, so this too is an account. It is
here because it moved four things in the plan.

- **A memory of exact repeats is not enough; one of states is.** Keyed by
  a job's inputs alone, memory saved only whole repeats. Keeping a
  trajectory's state every so many steps, under a name made from the
  trajectory and the step count, let a longer job go on from a shorter
  one's end. Every one of the 95 jobs then came out the bytes of the same
  job run alone, halts at the same step.
- **R3 is a test of the spacing, and of who steps what.** Predicted from
  the sweep, 82.0% of steps need not be stepped. Measured: 78.1% with a
  state kept every 2,000 steps, 80.9% at 500, 81.8% at 100. With five
  machines at once and no rule between them, about 70%: they stepped the
  same trajectories. With each trajectory given to the machine its name
  picks, in two rounds, 81.7%, and no machine spoke to another. That
  fits a wire that is a dataset.
- **R2's answer here is 27 of 44.** Three Kaggle machines gave the same
  bytes as each other on every job. The session's laptop agreed with them
  on 27 of 44, parting somewhere between the tenth step and the 1,780th.
  Two NumPy versions agreed with each other on the laptop, so it is the
  processor, or what NumPy does with it.
- **R1 was met without a runtime, on three kinds of processor.** The same
  physics written with only add, subtract, multiply, divide and square
  root, each trajectory's start given as exact numbers, gave the same
  bytes on the laptop and on Kaggle. Run whole: five Kaggle notebooks at
  once made the memory (four Intel Xeons and, by chance, one AMD EPYC),
  and the laptop, a third kind, was served 64 jobs from it, stepped 16 on
  from it, and got for all 95 the bytes of its own run alone. It stepped
  all 667 of Kaggle's kept states again, and each came out the same.
  Whether a fixed runtime is still wanted is now a question for a job
  that can't be written that way.
- **R5 needs rewording.** A check that steps one kept state again costs
  one spacing's worth of steps, whatever the job. Against the median job
  here that was about a tenth, not a twentieth; against a long job it is
  far less. "A twentieth of the time computing it took" passes or fails
  by the length of the job, not by the check.
- **A refusal is not a halt.** A setup the simulation won't start was
  first stored as a failure. They are kept apart now, and R6 counts only
  runs that began.

What it does not show: science_bitch itself; jobs of more than
milliseconds; a notebook writing the dataset (the memory was downloaded
and merged by hand); anyone's machine but one account's and one laptop.

### What the real project did, on the maintainer's word

The maintainer said to run science_bitch, first on the session's laptop
and then on Kaggle. It was cloned at its commit `2fae2f2` and not changed;
the Kaggle notebooks fetched it from GitHub at that commit, so no copy of
it was uploaded. An account, like the two above.

- **The memory works on the real stepper.** The same 95 jobs, on one
  machine, five processes at once: alone, 372,957 steps in 124.6 seconds;
  with the memory, 67 jobs served, 17 stepped on from a kept state,
  68,239 steps in 9.7 seconds. All 95 came out the bytes of the job run
  alone. Its state can be stopped and picked up exactly. No job in this
  sweep halted, so R6 is not tested on it.
- **R2, on the real code: 7 of 40.** One AMD and two Intel machines at
  Kaggle agreed with each other on every job. The laptop agreed with them
  on 7 of the 40 that ran, parting between the 10th step and the 8,383rd.
- **One operation does it.** Of thirteen NumPy operations tried on the
  same fixed numbers, three gave other bytes on the laptop than at Kaggle:
  a number to the power 1.5, a cube, and the square root of a cube.
  Square root, division, squares, sums, sine and cosine agreed. The
  project's gravity has `d2**1.5` in it.
- **With that one power written as a product and a square root**,
  `d2*np.sqrt(d2)`, patched in memory and not in the project's files, the
  laptop and Kaggle agreed on 40 of 40. So R1 can be met on the real code
  with NumPy kept, by a one-line change that is its author's to make.
  A finding for them, not a change made.
- **Then the whole plan, small, on Kaggle.** 125 jobs over 15
  trajectories of the real project, each notebook fetching it from GitHub
  and making that one change in memory. Round one: five notebooks at
  once, each stepping the trajectories its name owns. Round two: five
  more, each given round one's five outputs as its input, so the wire was
  Kaggle's own and nothing was carried by hand. Each also ran its jobs
  alone. Alone: 1,289,778 steps and 1,130 machine-seconds. With the
  memory: 341,495 steps and 317. All 125 jobs came out the bytes of the
  job alone. Predicted saving 73.4%, measured 73.2%. One trajectory
  halted, after its 7,889th step; six jobs were on it and none stepped
  into the halt again. The laptop, a third kind of processor beside
  Kaggle's Intel and AMD, stepped 400 of the 3,418 kept states again and
  ran 12 jobs alone: every one the same bytes.
- **So a notebook need not write a dataset.** One notebook's output can
  be another's input. That answers the plan's question about the wire
  for two rounds; a third round would take the second's outputs the
  same way.

## Where the pieces stand, after four trials and three runs

Written 2026-11-12 by the session that ran the simulations, from the
trials' own pages and its own runs. Proposals, for the maintainer to set
or cut.

**One shape, met at two sizes.** The simulation runs kept a state under a
name made from what led to it, and a later job went on from it.
[Trial 4](trial-4/RESULTS.md) asked the same of a stack's step: named
from the step as it is written, is it the same work in another folder?
Both found the same two things. The name has to leave out the place and
the clock. And what is worth remembering is what was made, not what was
printed about making it.

**What the runs change in the setup.**

- Five machines at a time, in rounds, not tens at once.
- Each trajectory belongs to the machine its name picks. No machine
  speaks to another, and none steps what another is stepping.
- The wire is one notebook's output given as the next one's input.
- States are kept often: the saving and the price of a check both turn
  on the spacing.

**Three rules to reword.**

- **R1** asks for a fixed runtime. The real project agreed on three
  kinds of processor with one power written another way. The rule could
  ask for the same bytes on three kinds of processor, however got.
- **R5** asks that a check cost a twentieth of the job. A check costs one
  spacing's steps, whatever the job. The rule could name that price.
- **R6** should count only runs that began. A setup that is refused never
  ran.

**Rules first, then agents, for the blind half.**
[Trial 3](trial-3/RESULTS.md) put three written rules where
[trial 2](trial-2/RESULTS.md) had three agents: the rules' steps ran
clean, one repaired the step an agent had misread, and when no rule fit
it stopped and said so. The other trial of that day, 18 models asked one
open question, found the mirror of it: a model answers. So in the study
a script would choose and check, and an agent would be asked only what a
script cannot say, with R9's questions that have no answer among the
rest.

**What two records need to find each other.** Trial 4 found that two
runs of one stack share nothing on the record but the kinds of their
rows. The stack-row add-on now puts a run on the record as one row. For
two machines' rows to be compared, a row needs an identity without its
clock, and a step's output one without its place.

### A bigger stack, run the same way

Trial 4 compared a stack of 30 steps and 24 add-ons. The same day the
same comparison, by [same.py](same.py) with only this project's folder
names given to it, was made of a stack of 95 steps and 70 add-ons: the
one a published research ledger carries, built twice into two folders
from the same 52 source files and run twice in each. Each pass took six
minutes. An account: the runs are on that session's machine.

| | 30 steps (trial 4) | 95 steps |
|---|---|---|
| marked the same as they ran | 10 | 95 |
| marked the same from the step as written | 30 | 95 |
| printed the same bytes, first runs | 17 | 92 |
| the same without the place, first runs | 23 | 93 |
| the same without the place, second runs | 27 | 91 |

- **It holds at three times the size, and better.** This stack names its
  folders from where it is run, not in full, so the place was never in a
  step's mark or in most of what it printed. How a stack is written
  decides most of what trial 4 had to take back out.
- **What still differs is the clock, as before.** The Merkle root over
  the record; a step that prints how many seconds it took; and, on a
  second run, two steps that print when the last check was.
- **A second run in the same folder is not the same work.** First run
  against second, in one folder, 82 of 95 steps printed the same. Eight
  of the thirteen that didn't are steps that write a file once and
  refuse to write it again: they ended 0 the first time and 2 the
  second. So "run it again" has two meanings, and a memory of steps has
  to know which steps make something and which only look.

### Which steps make and which only look, from their cards

Every add-on's card has a `writes:` line. The 95 steps were sorted by it
and held to what each did the second time in the same folder. The two
folders gave the same counts. An account, as above.

| the card says it writes | steps | the same again | the rest |
|---|---|---|---|
| nothing | 78 | 76 | one prints the seconds it took; one prints how many rows the record holds, 7 and then 15 |
| the record | 8 | 6 | two say "first check" once and name the last check's time after |
| a file | 9 | 0 | eight are refused the second time; one writes over its file, a root over a record that has grown |

- **The card finds every maker.** All 17 steps whose card says they
  write changed something, the six that printed the same words too: each
  adds rows to the record every time it runs. None of them is a step a
  memory may serve as the same; it is run, or said to be made already.
- **It misses two lookers.** 76 of the 78 that write nothing can be
  served. The two that can't read something no card names: the clock,
  and the record.
- **The mark doesn't hold the record.** All 95 steps were marked the
  same both times. A step's mark is its words and the pile it was fed,
  so a step that reads the record looks unchanged when what it reads has
  grown.

Two things would close it, both proposed and neither done: a line on the
card for what a step reads besides the pile (the record, the clock; the
`reads:` line some cards have names file types, not this), and the
record's state in the mark of a step that reads it.

[stack-bridges](../../adapters/stdlib/stack-bridges/) reads the same
thing off the cards without running anything: a step that names the
record after one that writes it takes "the record as it left it". On
this stack it finds no bridge at all. It takes `{box}` for the record,
and this stack names its record by its folder, `--box boxes/sources`.
The runs show two steps that read a record eight others wrote. Not
changed here: a fix for after this branch is merged.

## The order

1. Settle the list above.
2. Write the sweep, the predicted saving, the questions and the rules.
3. Dry run, with nonsense setups, on one machine here.
4. Freeze, in one commit, alone.
5. The baseline: one notebook, no memory, twice.
6. The shared run: many notebooks, one dataset.
7. The check: a fresh notebook that only verifies.
8. The blind account: a fresh agent, the reports, the frozen questions.
9. The report: what held, what did not, with the frozen numbers.
