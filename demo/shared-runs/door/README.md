# A door on the shared memory, counted at larger sizes

**Status: counted 2026-11-12, not run. Nothing is frozen, and nothing
here is a result of running anything.** It ties two things together: the
[first study](../README.md), which shared a memory between machines that
were all honest and all known, and the rule worked out for health records
on the branch `health/minors-boxes`, where what a signer sends is taken
by how the signer stands at the door.

## Counting is the run, to the step

[door.py](door.py) steps nothing. It counts what a sweep would step, by
the rules the study's runner runs by. Held to what the study's machines
actually did on Kaggle:

| | counted | what the machines kept |
|---|---|---|
| steps of the shared run | 336,379 | 336,379 |
| each of the ten machine runs | the same ten numbers | 54,752, 46,377, 50,985, 87,310, 39,095, 735, 14,765, 4,030, 4,530, 33,800 |
| states kept | 3,473 | 3,473 |
| steps the check stepped kept states again | 41,410 | 41,410 |
| steps the check ran served jobs afresh | 121,940 | 121,940 |

A test holds every one of those. So what is counted below at other
sizes is the same arithmetic the real run obeyed, and not a guess. What
arithmetic cannot show is said at the end.

**Something the first study did not say.** Its 73.2% is the stepping
saved. Its own check then stepped another 163,350 steps, three quarters
of them re-running served jobs from their start. With the check counted
in, the saving is 60.2%. That is not a correction to a verdict: R3 was
about the stepping. It is what the sharing cost once someone looked.

## The door

As the wards scenes and the phone-keys proposal have it, put on a memory
of kept states:

| what a machine sends | what kind of thing it is | how it is taken |
|---|---|---|
| a kept state: "this trajectory, at this step, is these bytes" | an all-clear: it lets the next machine do less | gone on from at once from an enrolled signer; held, from one nobody enrolled, until an enrolled machine has stepped it again |
| "this state did not step the same" | a caution: it costs only doing the work again | honoured from anyone |
| "this trajectory halts here" | a stop | from an unknown signer, weighed: stepped up to, not taken on its word |

A signer nobody enrolled earns standing as the share add-on's rungs do,
on the door's own record: when everything it kept in a round has been
stepped again and found the same, it is treated as enrolled from the
next round. A signer whose state is found wrong loses it.

## What falls, and what does not

All of it at ten times the first study's sweep unless said: 2,200 jobs,
220 trajectories, ten rounds of five machines.

### Size alone: nothing

| | jobs | steps alone | saving | saving after the door |
|---|---|---|---|---|
| as run | 220 | 1,256,518 | 73.2% | 63.5% |
| ten times, two rounds | 2,200 | 12,565,180 | 73.2% | 62.0% |
| ten times, ten rounds | 2,200 | 12,565,180 | 73.2% | 60.9% |
| a hundred times, ten rounds | 22,000 | 125,651,800 | 73.2% | 61.0% |

The saving is the same at every size, and the checking stays about an
eighth of the work alone. The jobs do not depend on one another, so more
of them is more of the same. If something breaks at size it is not in
the arithmetic.

### Strangers: the saving falls, and does not fall away

| signers, taking turns | saving after the door | checking, as a share of the work alone |
|---|---|---|
| 25, all enrolled | 60.9% | 12.4% |
| 25, 20 enrolled | 58.7% | 14.5% |
| 25, 10 enrolled | 52.8% | 20.4% |
| 25, none enrolled | 41.4% | 31.8% |
| 50, none enrolled: no signer is ever seen twice | 37.5% | 35.7% |
| 5, none enrolled, the same five held open for all ten rounds | 54.6% | 18.6% |

- **A stranger costs one round of its own work.** Everything it keeps
  the first time is stepped again; after that it has earned its place.
- **Even when nobody is ever known, more than a third is still saved.**
  This is the thing worth having found. Stepping a stranger's kept
  states again costs what the stranger stepped, not what the jobs would
  cost alone: the beginnings they share are still shared. Trusting no one
  halves the saving. It does not end it.
- **A machine that never comes back never earns anything**, and one
  that stays earns it once. If every round is run by a signer never
  seen before, every round is a stranger's: 37.5%. If the same five
  machines stay for all ten rounds, they are strangers for the first
  round only: 54.6%, most of the way back to 60.9%.
- **Kaggle can hold a machine open**, as the maintainer points out: its
  own pages give a session twelve hours. The first study started a new
  notebook for every round, and that was this study's habit, not
  Kaggle's rule. A session held open is one machine across rounds, and
  its key can be made there and never leave it, which is what the
  phone-keys proposal asks of a key. Since a place needs only its own
  earlier work, a session held open needs no one else's output to go
  from one round to the next.
- **What holding open does not give.** A run's output can be another
  notebook's input only when the run is done, as far as Kaggle's pages
  say. So a door that looks after every round cannot look into a
  session that is still open, unless what it keeps gets out some other
  way. Either the rounds end and start again, or the checking waits for
  the end, or there is a way out mid-run that those pages do not name.
  That is for a run to find, not for counting.

### How much is checked: this is where it falls

One lie in round three, told where it does most harm: the last kept
state of a trajectory that still has a longer job to come. Sixty
placings each.

| what the door checks after each round | lies found, of 60 | wrong jobs handed out | never found | checking | saving left |
|---|---|---|---|---|---|
| every kept state against the one before it; no job afresh | 60 | 0 | 0 | 26.7% | 46.5% |
| every kept state, and every served job afresh | 60 | 0 | 0 | 116.6% | none: it costs more than working alone |
| as the first study: a state in 8, a served job in 10 | 24 | 175 | 117 | 12.4% | 60.9% |
| a state in 8, no job afresh | 5 | 202 | 202 | 3.4% | 69.9% |
| a state in 64, a served job in 100 | 2 | 217 | 212 | 1.7% | 71.5% |
| nothing | 0 | 219 | 219 | 0 | 73.2% |

- **The first study's rate finds two lies in five**, and lets 117 wrong
  answers stand out of 175 handed out. Every machine in that study was
  honest, so nothing there could show it.
- **Checking every state against the one before it finds every lie
  before a single job goes on from it**, for about a quarter of the work
  alone. Each state is stepped from the state before, all the way back
  to a start that was frozen as exact numbers, so the whole chain is
  proven and no job needs running afresh. The saving left is 46.5%.
- **Running jobs afresh is the dear check and the weak one.** It is
  three quarters of what the first study's check cost, and running every
  job afresh costs more than having no memory at all.
- **So the choice is plain, and it is between two numbers**: 60.9% saved
  with most lies standing, or 46.5% saved with none. Fourteen points is
  the price of being right.

It is the same rule as the emergency card. A kept state is an all-clear,
and an all-clear is what an unknown signer may not be believed on. The
door that checks every state is the door that takes no all-clear on
trust, from anyone.

## What counting cannot show, and a run at size would

1. **Whether Kaggle will carry it.** Ten rounds is fifty notebooks, five
   at a time. A hundred times the sweep keeps about 350,000 states.
   Nothing in its pages says where that stops.
2. **What the memory weighs to a machine that has to read it.** Every
   notebook loads all it is given before it steps anything.
3. **Signing and checking signatures**, which cost time and no steps.
   One signature for all a machine kept in a run, over that file's hash,
   would keep it small; a signature a state would not.
4. **The clock.** Steps are counted; hours are not.
5. **Kinds of processor at size.** The first study had Kaggle's draw
   give one AMD machine in thirteen.

### What Kaggle will and won't do, as far as is known

Asked of the maintainer's laptop session, which has the account, on
2026-11-12. Each answer says how it is known: *tried* is from the
thirteen notebooks of the first study or an earlier probe; *pages* is
Kaggle's own pages as read for the first study; *recalled* is a
session's own knowledge and is not checked.

| asked | answer | how known |
|---|---|---|
| can a run hand something out before it ends | no way is described. With the internet on and the account's credentials given to the notebook, the Kaggle API inside it may be able to write a new version of a dataset mid-run | pages; the second part recalled |
| how long a session is held | twelve hours for a CPU notebook; a saved version runs top to bottom within that. The longest tried was about 25 minutes | pages; tried |
| the idle limit of a session someone is typing into | not found | |
| one machine for the whole of a session | not found; thought to be so | recalled |
| a value that outlasts a run and is not in its output | notebook secrets are thought to exist, and to be kept out of output | recalled |
| how many inputs a notebook may have | 5 were taken, and 10 by the check notebook. The most, and any limit on size: not found | tried |
| what a run may leave | 20 GB. A limit on the number of files: not found | pages |
| a limit on CPU time over a day or a week | none is shown: the account's quota lists hours for GPU and TPU only | tried |
| how many at once | five. The sixth was refused, twice | tried |
| pushed again while it is still running | not tried | |
| how long before a pushed notebook starts | under about 20 seconds, every time | tried |
| the machine | nine draws of nine an Intel Xeon at 2.20 GHz with AVX2; one AMD EPYC in the first study's thirteen | tried |

Three of those can be settled only by pushing a notebook, which is the
maintainer's to allow on their own account: handing out mid-run, a
value that outlasts a run, and a push onto a running notebook.
[probe.py](probe.py) is one small notebook that asks all three. It
writes a numbered line to its output every half minute for four
minutes, so that whoever pushed it can ask for its output while it
runs; it says whether the account gave it a secret of one agreed name,
and never the value; and it says when it began, so a second push
halfway through can be told from the first. It needs no credentials and
reaches no network.

**The probe was pushed**, on the maintainer's word to the laptop
session, on 2026-11-12, unchanged, private, through the privacy gate.
What it found, as that session reported it:

| asked | found |
|---|---|
| can its output be read while it runs | not from outside, by Kaggle's command line (2.2.4): at one minute and at two and a half, asking for the output and for the log both gave nothing |
| pushed again while it is still running | the push is taken, and the new version begins about 4 seconds later. Only the second version's output exists afterwards: asking for the first's gives the second's. What the first had done is gone, or cannot be reached |
| a value that outlasts a run | not settled. The account had no secret of the agreed name, and the secrets client answered with a connection error, so "no such secret" cannot be told from "could not ask" |
| one machine for the whole of a run | the same processor at the start and at the end of one run of four minutes, an AMD EPYC 7B12 |

Two things follow for a run at size. A notebook's output is all or
nothing: one that is cut off, or pushed over, leaves nothing, so a
long machine run is better as several short ones, each ending clean
and given the one before as an input. And the processor drawn can
differ from one push to the next (this draw was AMD, where nine of
nine before were Intel), so a run taken up again may come back on
another kind.

### What a run at size would take, by the first study's clock

From what was tried: a baseline notebook stepped about 1.59 million
steps in about 25 minutes, near a thousand steps a second with its
starting and stopping.

| | ten times the sweep | a hundred times |
|---|---|---|
| the baseline, every job alone | about 3.3 hours in one notebook | about 33 hours: more than one session holds, so five notebooks of about 6.6 hours |
| the shared run, over five machines | about 11 minutes each, all rounds together | about 1.8 hours each |
| checking every kept state against the one before | about 53 minutes for one checker | about 8.8 hours for one checker |

So ten times fits easily, and a hundred times fits only if the baseline
is split. The baseline is the dearest thing in the study at any size:
it is the work the memory exists to avoid. These are estimates from one
evening's timings, and nothing more.

**One thing to put right before any such run.** Each second-round
notebook of the first study was given all five first-round outputs. By
the rule of who steps what, it needed only the one from its own place:
no other machine had stepped its trajectories. Kaggle's guidelines say
not to attach what a notebook does not use. A run of ten rounds should
give each notebook only its own place's earlier outputs, which is also
one input a round and not five.

## The machine a run at size would use

[machine.py](machine.py) is what one machine would do: the first
study's stepping (it calls that study's own steppers and keeps its rule
for a job, and those files are not changed), with what a longer run
among less-known machines needs built in. Tried here with the made-up
stepper in its tests, and once with the project's: machine 3's first
round of the first study, stopped by a budget after eight jobs and
taken up again, came to the same 30 acts and the same 891 kept states,
byte for byte, as Kaggle's run of it.

| built in | what it does |
|---|---|
| checks before it starts | the starts are the plan's; the machine and round are in the plan; the stepper is the file the plan names, under the NumPy it names; there is room on the disk; and what is already in its folder is the same run, of the same plan and starts, by the same code, on the same kind of processor. Each is a line in its log, held or not. One that does not hold stops it, exit 2 |
| a log | `log.jsonl`, one line a thing done (each check, each folder at the door, each stop, each canary, how far it is), every line holding the hash of the one before, so a line changed or taken out shows |
| going on | the same command again goes on. A job done is not done again. A job cut off goes on from the states it had kept, and its act says the whole of what it stepped and how often it was taken up again. A last line torn by the cut is dropped, and the log says so. `--from DIR` is for a machine that comes back with an empty disk: the folder the run before left |
| a budget | `--budget SECONDS`: it stops clean, between jobs or inside one at a state it has just kept, and exits 42 |
| a canary | every 25 jobs it steps one of its own kept states again from the one before; a machine that does not agree with itself stops |
| a seal | when it ends clean, `manifest.json`: the SHA-256 of every file it leaves, of the plan, the starts and the code, the tip of its log, and what it took in and held, signed with an identity of the share add-on's kind when it is given one. `verify` holds a folder to its seal, and to a ring |
| the door | another run's folder is taken in only if it is whole by its seal, is this plan's by this code, and its signer is enrolled or an enrolled checker stepped every state of it again and found it the same. Whole and unknown, it is held: logged, and not gone on from. Not whole, it is refused and the run stops |
| a check that takes no one's word | `check` steps kept states again from the state before, and steps up to every halt the memory names to see it halt. Its seal says, for each folder, how many states it stepped and whether all were the same; that is the vouching the door reads. A run that went on from another's states is vouched for only if that other is enrolled or vouched for too |

**The whole first-study sweep through it, with the door on**, on
2026-11-12, on two machines of one kind (intel x86_64 avx512): the
cloud session, and the maintainer's laptop on their word, as the
laptop session reported it. Every machine signed, each second-round
machine was given only its own place's first-round folder, and each
took it as enrolled. Both came to 336,379 steps over the ten shared
runs, the first study's number, with each machine's count the first
study's own. A check of every kept state found 3,473 of 3,473 the same
and four halts of four (three part way and one refusal, kept as a halt
at nothing), for 330,244 steps here. The eleven folders are under
2 MB together, and `verify` took about a tenth of a second a folder.
The ten shared runs took 79 seconds here with a round's machines at
once, and 242 on the laptop under another job's load; the check 213
and 242. What signing costs was not told apart from that load. These
are trials of the machine, not a study's results, and the folders are
kept outside this repository.

A seal says who left a folder and that it is as they left it. It does
not say the folder is right: in the tests a liar seals its own lie, the
seal holds, and only the check finds it.

**Not built, and why.** It does not hold a run taken up again on
another kind of processor to anything gentler than a refusal: the
first study found three kinds agreeing to the byte, but an act is
written under one kind, so mixing two in one folder would blur which
kind stepped what. On Kaggle that means a run taken up again can be
refused by the draw; a notebook would then start that machine's part
over. There is no maker of notebooks for it yet, and it has never run
on Kaggle. The first study's judge reads its acts as they are (the same
fields, and two more), but has not been pointed at them.

## Willow's add-ons, by what use they would be

Read from every card's own line on 2026-11-12. Only the first row is
used by anything here; the rest is a reading, to choose from.

| | add-on | for what |
|---|---|---|
| **is used** | share | its Ed25519, for the seal on a machine's folder; the same kind of identity, so a place's key here is one it could send packages with |
| **will be** | tip-pin | a log's tip written where the run cannot reach. The seal holds the tip, but a folder and its seal can be replaced together; a tip kept elsewhere is what catches that |
| | merkle | one kept state proven from a folder with a handful of hashes. At a hundred times the sweep the memory holds some hundreds of thousands of states, and a door that wants one should not need them all |
| | stack, stack-row | the maintainer's side of a run (make, push, fetch, verify, judge) as one stack, each run of it a row on the record with the hash of what each step printed |
| | diverge | two copies of a run's folder, or a run and its copy on the laptop, down to the first line that differs |
| **should be** | backup, restore-drill, three-two-one | the verdict box and the kept runs are the study. Kaggle keeps one copy and, pushed over, none |
| | fixity | the kept runs under `study/runs` hashed again now and then, so rot is told from a change |
| | ci-memo | its idea, more than its code: a job whose inputs' bytes are unchanged keeps its recorded result. That is the shared memory's own rule, already written and tested for CI's gates |
| | hook-replay | the same again for a check: the hashes of what went in and came out, and a run again to prove the same answer. `check` here is that, for states |
| | in-toto, prov | a machine's seal written in the envelope others already read, and what came from what across rounds. The seal's own shape is this demo's and no one else's |
| | weights-pin | for the local-models runs: a model's file held to its hash before it answers |
| | predict, forecasts | each rule's number written before the run and graded after. The first study did this by hand in its freeze |
| **might be** | parallel | every core of one machine. The first study used one |
| | bench, slow-tests | steps a second by kind of processor, kept per run, so a slow draw is seen |
| | ci-logs, ci-why | Kaggle's own log of a run that failed, as passages, and the block that says why |
| | handover | where a run of fifty notebooks stands, for whoever takes it up: the laptop, the phone, this session |
| | box-health, changed, stale | whether the verdict box can still be read, what changed under it, and answers whose passage has gone |
| | ids, ro-crate | the kept runs as something an archive takes, with names others use |
| | record-sql | questions of the verdict box straight in SQL |
| | decisions | each "not built, and why" here as a kept no with what would reopen it |
| **can be, with care** | night-batch | the pattern of a long local run stopped when its owner is back. It is for model suggestions; a stepper's run is another thing |
| | snapshot | the project fetched once at its commit and cited as a copy. The runner already holds the stepper to a SHA-256, which is the stronger hold |
| | claim-check, pair-drift | the write-ups held to the kept figures. The first study's own scorer does this for its accounts |

Three things a run needs that no add-on is: a job taken up again
after a cut, a budget, and a door that reads a signer's standing. The
first two are in machine.py. The third is the planned idea `received`
on the health branch, and the rule here is that one's.

## What would be run

Not frozen; a sketch for the maintainer.

- The same project, runner and rules, at ten times the sweep, ten
  rounds.
- One arm as the first study checked, and one checking every state
  against the one before and no job afresh, since counting says that is
  where the difference lies.
- The lies of [the lies study](../lies/README.md) told in both.
- A key for each place that lasts across rounds, enrolled once.
- What is measured that counting cannot give: hours, the weight of the
  memory, what signing costs, and whether Kaggle carries fifty
  notebooks.
