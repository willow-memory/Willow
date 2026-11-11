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
