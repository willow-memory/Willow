# Shared runs: a study, frozen and not yet run

**Status: frozen 2026-11-11, and not run. No number below is a result.**
The sweep, the scripts, the rules and the questions were committed alone,
as [the rules for a study](../../docs/agents/studies.md) say; what was
frozen is in [study/FROZEN.json](study/FROZEN.json). The trials and the
dry run told of below came before it, and are accounts. Where a section
says "proposed", the section called "The study as written" says what
was settled.

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
| R1, the machines agree | every job gives the same bytes on every machine that ran it, and every kept state stepped again comes out the same, on at least three kinds of processor, however that is got |
| R2, the project as it is written, measured | no threshold: the share of jobs whose bytes agree across machines with the project's gravity left as its author wrote it, with where the first difference falls |
| R3, memory saves the work it should | the steps not stepped, as a share of the baseline's, are within two points of the share the sweep's shared beginnings predict: worked out before the run, and then cut at each halt the baseline, which has no memory, finds |
| R4, memory serves only what a run would give | of a tenth of served results, chosen by a seeded draw and run afresh, every one is the same bytes |
| R5, what a check costs, measured | no threshold: the steps it takes to step one kept state again from the one before it, at the median |
| R6, a halt is not repeated | no trajectory that began and then halted is stepped into its halt a second time; a setup refused before a first step never ran, and is counted apart |
| R7, the blind account | the receiving agent's answers to the frozen questions match the key the script makes from the records; see below |
| R8, the blind account adds nothing | no sentence of the receiving agent's account names a figure, a machine or an outcome that no report holds |
| R9, the blind account says when the reports don't | every frozen question the reports hold no answer to is answered "the reports don't say", and none of them with a figure |

R1, R5 and R6 are as the maintainer reworded them on 2026-11-11, after
the trials below; R2 now measures the project unchanged, beside R1's run
with one power written another way. The first wording is in this file's
history.

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

### What Kaggle's own pages say

Read on 2026-11-11, from the maintainer's copy of three pages as their
browser showed them: the Terms of Use (effective June 22, 2025), and the
Notebooks and Datasets pages of the documentation, at `kaggle.com` under
terms, docs/notebooks and docs/datasets. Their text is not kept here; the
copy read has the SHA-256
`ff1ff6d58b46ae8d0d12b5ffe6fc637a28f51651ba1aee26a15a2640e7274739`.
What follows is a reading for this plan, not advice on the law.

| asked | what the pages say |
|---|---|
| how long a session runs | 12 hours for a CPU notebook, and a saved version must run top to bottom within that |
| the machine | 4 cores, 30 GB of memory, 20 GB of kept output |
| which processors | "CPU Platforms (ex. Intel Skylake, Broadwell, AMD) may be variable during regular notebook runs": the machine is not the user's to choose, in Kaggle's own words |
| the wire | one notebook's output files can be added as another's input, and the page calls chaining them this way building a pipeline |
| a dataset written from inside a run | no way is described; a dataset is made from a notebook's output afterwards, by hand. Not needed, with the wire above |
| the internet | on by default in a new notebook, and packages may be installed from it |
| how many at once | not said. Five was found by trying, above |
| a private notebook or dataset | private by default, seen by its owner and by Kaggle to run the service |

What the Terms ask, that bears on this study:

- **One account a person.** Nobody may hold or run more than one. So
  "every notebook is run by one account" is not a shortcut taken here:
  a second account to play a stranger is not allowed, and a machine that
  lies stays outside what this study can show.
- **Use is to be one's own, personal and non-commercial**, "and not on
  behalf of or for the benefit of any third party". The study is the
  maintainer's own and nothing is sold. It runs a friend's public code;
  whether that is within those words is the maintainer's to judge, and
  it is the one line here worth their reading themselves.
- **What is forbidden by name** is scraping the service, copying its
  content in bulk, cryptomining, and data under arms-export rules. A
  sweep of simulations is none of these.
- **Limits can change** without these pages changing.

**The three pages the Terms fold in**, read the same day from a second
copy (SHA-256 `05d787be92f428332b28e1bcc4335ae7c9b824c0530976a8b6f23804250a936d`): the Acceptable Use Policy (effective
June 22, 2025), the Community Guidelines (updated March 4, 2026) and the
Privacy Policy (effective February 5, 2024).

- **The one line that bears on whether this may be run there at all.**
  The Acceptable Use Policy forbids abusing the resources, and lists
  under that "server farming" and "activity unrelated to ML data
  science". This study is a sweep of gravity simulations: numerical
  computing, in NumPy, asking whether machines agree and whether a memory
  saves work. It trains nothing and analyses no dataset. Whether that is
  related to data science is not this plan's to decide, and it is not
  plain either way. The Guidelines name abusing notebook resources as
  grounds for a ban without warning.
- **How large it is**, for whoever judges: about fifteen notebook runs,
  five at a time, on CPU only, each a few minutes; near an hour of
  machine time in all, a few megabytes kept.
- **Attaching an input a notebook doesn't use is not allowed.** A
  second-round notebook is given the first round's outputs and reads
  every one, so the wire is within that; a notebook given a round it
  does not read would not be.
- **The rules on what a shared notebook should be for** are about ones
  shared publicly. These stay private. The general rules hold for
  private ones too, and nothing here touches them.
- **Kaggle sees what is uploaded, private or not**, to run the service
  and to look for abuse, and keeps deleted things for up to about two
  months, and backups up to six. So the privacy check before upload is
  not a courtesy: what goes up is read.

So, before step 5: the maintainer either takes the study to be within
those words, asks Kaggle whether it is, or takes the machines from
somewhere else. The scripts don't care which: a machine is anything
that runs runner.py and hands back a folder. Earlier trial runs on
Kaggle, above, were made before these pages were read.

**Settled 2026-11-11, by the maintainer:** the study runs on Kaggle. It
is their account and their judgment that a run this small, on CPU and
well inside the week's free allowance, is no abuse of the resources.
The policy's words are as quoted above, and the question was not put to
Kaggle.

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

## The study as written, and its dry run

Written 2026-11-11, on the maintainer's word for each choice. Nothing here
is frozen, and nothing below is a result.

**What was settled.**

- The project is run both ways. R1's jobs run it with `d2**1.5` written
  as `d2*np.sqrt(d2)`, changed in memory and never in its files; R2's run
  it as its author wrote it. The change is still theirs to make.
- R1, R5 and R6 as reworded above; R5 is a measurement, in steps.
- R3's two points and R4's tenth stand as first proposed.
- For the blind half a script makes the reports and the key and holds the
  account to them. One agent answers, run as two models, named in the
  plan: the smallest and the mid-size Claude model the judging session
  offers, each given the brief as its whole prompt.

**The scripts**, in [study/](study/):

| | |
|---|---|
| [sweep.py](study/sweep.py) | a plan's jobs, the order they are dealt in, the machine each trajectory belongs to, the predicted saving, and the seeded draw; and each start as exact numbers, so no machine builds one |
| [runner.py](study/runner.py) | what one machine does: every job alone, its share with the memory, a check of the memory, or the project as it is written |
| [judge.py](study/judge.py) | the nine rules, counted from what the machines kept, and each verdict as a row on a record |
| [account.py](study/account.py) | the reports, an agent's whole input, the 21 questions and their key, and an agent's answers held to it |
| [dry.py](study/dry.py) | all of it on one machine, and only for a plan that says it is a dry one |

**The sweep**, in [study/plan.json](study/plan.json): 220 jobs,
22 trajectories of the project's own bodies each run to ten lengths, five
machines, two rounds, a state kept every 100 steps. Alone it is 1,481,810
steps; each trajectory stepped once is 396,000; so the predicted saving is
73.3%. In the order the jobs are dealt it is 403,390 steps, 72.8%: a short
job dealt after a longer one steps on from the last kept state before it.
That is counted from the plan, not run. Each start is in
[study/starts.json](study/starts.json) as exact numbers, built by the
project's own code and never stepped: the same file under NumPy 2.1.3 and
2.5.3. No setup has been stepped for this study. One start, the Sun with
Earth and Jupiter, is the one [demo/kept](../kept/README.md) ran three
orbits of through the star-system add-on, with the project as written;
what was read there was how well it kept its energy, and no bytes.
Five are crowded on purpose and whether any halts is not known: if none
does, R6 is not tested. One has a step too coarse to take, and is refused
by arithmetic.

**The dry run** put the whole plan through on one machine, on six made-up
setups under nonsense names ([study/dry-plan.json](study/dry-plan.json)):
30 jobs, one setup tuned until it halted partway and one too coarse to
start. The baseline twice, two rounds of five machines as separate
processes given only folders, a check, and the reports handed to two
agents, a small model and a larger one. What it printed is in
[study/dry/](study/dry/); its verdicts are rows `shared-runs:dry:R1` to
`R9` on a scratch record, which verifies (10 rows, 0 sealed). The kept
files are of its second pass, under NumPy 2.1.3; the two agents were
asked again, since their input's last line had changed.

| rule | in the dry run | what that can and can't say |
|---|---|---|
| R1 | not tested | every job and kept state agreed, on one kind of processor; one machine can't give three |
| R2 | 30 of 30 | one machine agrees with itself |
| R3 | failed: 48.8% against 52.5% | the rule did its job: the made-up lengths are near the spacing, so the order wastes 3.7 points |
| R4 | passed, 7 of 7 | the draw, the fresh runs and the comparison are wired |
| R5 | 100 steps | one spacing, as expected |
| R6 | passed | the made-up halt was stepped into once, and the refusal was counted apart |
| R7 | passed, 16 of 16, both models | |
| R8 | passed, nothing struck | |
| R9 | passed, 5 of 5, both models | |

**What the dry run found and changed.**

- A machine dealt no job kept no list of acts, and the check stopped on
  it. It keeps an empty one now.
- **R3's prediction can't be made from the sweep alone when something
  halts.** A halt shortens the baseline and the shared run both. The plan
  can't say where a trajectory halts, so the judge takes it from the
  baseline, which has no memory, and holds the shared run to the share
  that leaves. That was a change to R3 as it was first agreed; the
  maintainer accepted it on 2026-11-11, and the rule above says it.
- **The first proposed lengths all fell on the spacing**, which would have
  made R3 true by arithmetic. They no longer do, and a test holds that.
- The dry run can't be pointed at the study's sweep: it refuses a plan
  that doesn't say it is a dry one.
- A machine refuses a checkout whose stepper is not the file the plan
  names by SHA-256.

**A kind of processor, and a fourth machine**, added the same day on the
maintainer's word.

- **A kind is the processor's maker, its architecture and its widest
  vector instructions**, as each machine says of itself and as NumPy
  found them: `intel x86_64 avx512`. R1 counted the name a machine gives
  its processor, so two of one make at another clock speed would have
  been two kinds. They are one now.
- **The session that wrote this is a check machine.** Its processor is an
  Intel with AVX-512, which NumPy uses; Kaggle's Intel, in the first look
  above, had none. So it is a kind Kaggle did not give, beside the laptop
  and Kaggle's AMD when the draw gives one. It was chosen, where the
  claim is of machines nobody chose, so it only checks: it steps kept
  states again and runs the project as it is written, and steps no job
  of the shared run. A cloud session's machine is not promised to be the
  same the next time, so its part is run, with what it says of itself,
  in one sitting after the freeze. The plan names the three check
  machines: a fresh Kaggle notebook, the laptop, this.
- **One NumPy on every machine.** The plan names 2.1.3, Kaggle's, and a
  machine with another is refused, so two machines differ by their
  processor and not by their NumPy as well. Here it is a virtual
  environment. The dry run was run again in it, and under 2.5.3 before:
  the same bytes for all 30 jobs.
- **An answer with no account under it was passing R8**, with nothing to
  strike. Found when the kept answers were rebuilt without that line. It
  is not tested now, and said.

**What it could not see.** A second processor, so nothing of R1 or R2. A
wrong answer, an added figure or a guess from an agent: both models got
every one right, so those paths are held only by tests with made-up
answers. Kaggle: a notebook's limits, and one notebook's output given as
the next one's input. And the two agents were this session's own, started
with the brief as their whole prompt but not sealed off from the
repository; neither opened a file.

## Running it

Written after the freeze; the notebook is not among the frozen files,
and decides nothing the rules read.

[study/notebooks.py](study/notebooks.py) makes thirteen notebooks from
the frozen files, one a machine run: the baseline twice, five machines
for each of two rounds, and the check. Each is one script that carries
the plan, the starts and the two scripts it needs inside itself, held to
their SHA-256 when unpacked, so nothing else is uploaded. It fetches the
project at the plan's commit, installs the plan's NumPy beside the
machine's own if that is another, and calls runner.py for its part. A
round's notebooks name the rounds before as their inputs, and stop if
one is missing.

It was rehearsed here on the dry run's made-up sweep: all thirteen run
one after another as Kaggle would run them, each given only a folder of
the earlier ones' output, came to the same reports as the dry run, byte
for byte. What the rehearsal could not try is the fetch from GitHub,
which this session's network refuses, and Kaggle itself.

The steps, for the maintainer. The three `kaggle` commands are as
recalled from Kaggle's command line, not read from its pages:

1. Make them, outside the repository, with the account's name:
   `python demo/shared-runs/study/notebooks.py make --user NAME --to DIR`.
2. Put DIR through the privacy check.
3. Push the two baselines and the five of round one, each with
   `kaggle kernels push -p DIR/NAME-OF-RUN`. Kaggle ran five at once
   when it was tried, so the baselines go first or after.
4. When round one's five have finished, push round two's five. Their
   inputs are round one's outputs, so they can't go sooner.
5. When round two has finished, push the check.
6. Fetch each one's output into one folder, a folder a run:
   `kaggle kernels output NAME/shared-runs-NAME-OF-RUN -p RUNS`.
7. The two other check machines, the laptop and the cloud session, run
   runner.py themselves, given the ten rounds' folders: first `check`
   and then `native`, each with `--to RUNS/laptop` or
   `RUNS/cloud-session`, under NumPy 2.1.3, on a checkout of the project
   at its commit.
8. Then the reports, the two agents, and judge.py with a record outside
   the repository, as the dry run did.

**A fourth check machine, said before anything is run.** A person the
maintainer knows has offered a machine of their own. The frozen plan
names three check machines, and is not changed. If theirs takes part it
does what a check machine does and no more, its folder is judged with
the rest, and its kind counts toward R1's three like any other. First it
is asked to try the dry sweep, by [study/TESTER.md](study/TESTER.md)
alone: a page written for someone who was not here.

## The order

1. Settle the list above. Kaggle's pages are read. The maintainer has
   settled that it runs there. One thing waits on them: the privacy
   check, before anything is uploaded. It is not needed before step 4.
2. Write the sweep, the predicted saving, the questions and the rules.
   Done, above.
3. Dry run, with nonsense setups, on one machine here. Done, above.
4. Freeze, in one commit, alone. Done 2026-11-11, in commit `92db883`:
   [study/FROZEN.json](study/FROZEN.json) holds the sweep, its starts,
   the scripts, the rules and the questions by SHA-256, and a test holds
   them to it. With it in that commit are only that test and their two
   lines in the file tree. From here a change to any of them is a new
   freeze, with its reason.
5. The baseline: one notebook, no memory, twice. The notebooks for this
   and the next two steps are written and rehearsed; see "Running it".
6. The shared run: many notebooks, one dataset.
7. The check: a fresh notebook that only verifies.
8. The blind account: a fresh agent, the reports, the frozen questions.
9. The report: what held, what did not, with the frozen numbers.
