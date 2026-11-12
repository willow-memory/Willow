# What could be tried next

Started 2026-11-12, after the study in [README.md](README.md) was run and
judged. A list, not a plan: nothing here is frozen, promised or in order
of doing. Each entry says what it would show and what it needs. Any that
is taken up becomes a study of its own, with its own freeze.

**The last column is the maintainer's.** A good deal of work that bears
on these is already on their own machine and not in this repository.
Where an entry is already answered there, in part or whole, say so in
that column: what it is, and where. An entry answered there needs
writing up, not running.

Filled 2026-11-12 from the maintainer's machine, from the maintainer's notes (`~/willow-stacks/dashboards/notes.md`) and the
folders they name, which stay there. A blank is nothing found, not
nothing there.

How to read "from where": *here* is a cloud session like the one that
wrote this; *laptop* is the maintainer's machine; *Kaggle* is their
account there; *someone* is a person with a machine of their own.

## What could be asked of the laptop and the phone

Proposed 2026-11-12, after the laptop's session said what it can run.
**None of these is asked until the maintainer says so**, and each says
what it would belong to. A thing run for a study that is already judged
is an addition after the fact, and is written up as one.

| | what | on what | belongs to | what comes back |
|---|---|---|---|---|
| P1 | the dry sweep, by [study/TESTER.md](study/TESTER.md) alone | the phone (ARM, NEON, NumPy built on Termux's OpenBLAS) | nothing frozen: it is a dry run, and no result | its last three lines and its runs folder. The first ARM machine, and the first with another linear-algebra library; both differences are to be said beside whatever it shows |
| P2 | every job of the frozen sweep alone: `runner.py alone` with the study's plan and starts | the laptop, and a cloud session beside it | an addition to the first study, B1 below: every job in full on a third kind. It needs a line frozen first, saying what is held to what | one folder a machine, as the study's machines left theirs |
| P3 | the two agents' input, [study/results/agent-input.txt](study/results/agent-input.txt), given whole to each local model | the laptop's thirteen models under ollama | C4 below: a measurement after the fact, scored by the second freeze's account.py as the two agents were | each model's answer, word for word, in a folder of its own |
| P4 | the lies study, both arms | one machine: the laptop or a cloud session | [lies/](lies/README.md), once it is frozen | its trials, as lies.py keeps them |

## The gaps the study left

From "What it cannot show" and "What the passes do and don't say".

| | the gap | entries that would close it |
|---|---|---|
| G1 | every machine was honest | A1 to A8 |
| G2 | only 3 jobs were run in full on all three kinds of processor | B1 |
| G3 | every processor was x86 | B2, B3 |
| G4 | both agents got everything right, so the blind half was never strained | C1 to C6 |
| G5 | one workload, one author's code | W1 to W5 |
| G6 | fifteen machine runs of minutes each | S1, S2 |
| G7 | every machine was one person's | E1, E2 |
| G8 | the project as written agrees on 14 of 220 | H1 |

## A. Trust: what the memory does when it is wrong

| | what is tried | what it would show | needs | from where | already on the maintainer's machine? |
|---|---|---|---|---|---|
| A1 | **A machine that lies.** Drafted and dry-run, not frozen: [lies/](lies/README.md). One kept state is changed by a bit, or one notebook hands back other bytes. | whether the check catches it, how many jobs were served from it first, and how that moves with the size of the draw | the frozen scripts, and a rule for what counts as caught | here | |
| A2 | **Two machines disagree.** One is wrong and nothing says which. | whether a third settles it, and what it costs | A1's set-up, three machines | here | |
| A3 | **A stale memory.** States kept by an older version of the code are offered to a newer one. | whether the name a state is kept under holds the code as well as the inputs. It does, by the stepper's SHA-256; this would test it | two commits of a project | here | |
| A4 | **The same thing sent twice**, or a round's output given to the wrong round | whether a repeat or a misdelivery is refused or silently counted | the notebooks | here || In part, for calls rather than states: willow-mcp's session binding refuses a replayed nonce, and a signature reused for another tool (`tests/test_session_binding.py`, `test_verify_call_rejects_ride_replay_and_tamper`) |

Found by holding A1's draft to what is already here
([lies/README.md](lies/README.md)), and not yet anyone's to run:

| | what is tried | what it would show | needs | from where | already on the maintainer's machine? |
|---|---|---|---|---|---|
| A5 | **A check from the start.** A drawn state is stepped from the trajectory's frozen start, not from the kept state before it. | what it costs to check against something the liar did not write, and how many more lies it finds | a change to how the check steps | here | |
| A6 | **A key on what a machine keeps.** Each kept state signed by the machine that kept it, as the share add-on signs a package. | that a found lie names its teller, and whether a machine's standing can set how much of its work is checked | the share add-on's keys, in the runner | here || In part, for sessions rather than states: willow-mcp's attribution ledger chains each signed session with the verifier who signed it (`tests/test_attribution_ledger.py`); the maintainer has one signing key for seals and sessions |
| A7 | **Received, not yet gone on from.** A state is not used until something has looked at it. | what the saving falls to when nothing is trusted on arrival | a change to the memory | here || In part, for a ledger: Nestor walks its ledger's chain once a process, every N seconds, or on every append (`NESTOR_LEDGER_VERIFY_INTERVAL_SEC`, `nestor/cascade.py`), the cost of not trusting on arrival made a setting |
| A8 | **A recall.** From a found lie, the jobs that went on from it are named. | how many of the wrong jobs can be called back, from what each job already says it took | nothing new: the acts say it | here | |

## B. Machines: more kinds, and one difference at a time

| | what is tried | what it would show | needs | from where | already on the maintainer's machine? |
|---|---|---|---|---|---|
| B1 | **Every job on every kind.** The whole baseline on the laptop and on a cloud session. | closes G2: all 220 jobs in full on three kinds, not 3 of them | about twenty minutes a machine | here, laptop || In part, on other sweeps. The 95-job sweep of the project ran whole on the laptop alone (84 ran, 11 refused), in `~/Forge/workshop/science_bitch-runs`; the small plan's 125 jobs ran on Kaggle, and the laptop stepped 400 of its states and 12 of its jobs again, all the same. Not the study's 220 in full |
| B2 | **A processor that is not x86.** An Apple laptop, a small ARM board, a phone. | whether the rewritten power agrees across architectures, and what the project as written does there | one such machine, Python and NumPy 2.1.3 on it | someone, laptop | |
| B3 | **Another system.** The same processor under Windows or macOS. | whether the system's own maths library changes the bytes | one machine with two systems, or two alike | someone | |
| B4 | **One thing changed at a time.** A grid: processor, NumPy version, Python version, the linear-algebra library under NumPy. | which of them move the bytes and which never do. The study pinned NumPy to hold this still | a few environments on each machine | here, laptop || In part, before the freeze, in `~/Forge/workshop/science_bitch-runs/bits` and `~/willow-stacks/shared-runs-dry/bits`: NumPy 2.1.3 and 2.5.4 gave the same bytes on the laptop, so did Python 3.13 and 3.14, and AVX-512 turned off (`NPY_DISABLE_CPU_FEATURES`) changed nothing. Laptop against Kaggle, `x**1.5` and `x**3` differed; `sqrt`, division, squares, sums, `norm`, `sin` and `cos` did not. Not the linear-algebra library |
| B5 | **Graphics cards.** The same arithmetic on a GPU. | whether any of this survives leaving the processor | a GPU, and Kaggle's weekly hours | Kaggle || Not tried for this arithmetic. The account's quota on 2026-11-11 was 45 GPU hours a week, none used. Four of the account's notebooks have run on its Tesla T4 GPUs (`willow-slm-train`, `willow-slm-train-qwen3b`, `willow-slm-eval`, `yggdrasil-1-0-dpo-sft-sequential-training`), training and testing small models, not this arithmetic |

## C. The blind half: make it hard enough to fail

| | what is tried | what it would show | needs | from where | already on the maintainer's machine? |
|---|---|---|---|---|---|
| C1 | **A chain of three.** Each agent is given only the account before it. | what is lost or added at each hand, which one hand cannot show | the scripts, three calls a model | here | |
| C2 | **Questions that join two figures.** | whether an agent joins them rightly. The larger model wrote that five machines "ran on 3 kinds" where they were two | new questions and a key for them | here | |
| C3 | **A rule for joins.** R8 holds an account to its figures and not to how it puts them together. | whether a wrong joining can be struck by a script at all | a way to say what a sentence claims | here | |
| C4 | **Smaller and local models.** | where "the reports don't say" stops being said | models that run on a laptop | laptop || Not tried on this brief. Thirteen local models run under ollama on the laptop, from 0.5B to about 10B parameters. On another brief, the escalation benchmark asked 8 local models from 1.2B to 9.7B 200 items each, 40 with no answer, and they answered anyway on 77.5 to 95 % of those, but qwen3.5 on 37.5 % (`~/.forge/escalation-runs/step2b-aggregate.md`); hosted models, 0 to 10 % (C5). The maintainer's notes read it as: a small model does not give the zero, and a capable one can |
| C5 | **Many hosted models at once**, as one private Kaggle benchmark task | the spread across a dozen and more models on the same brief | the Kaggle benchmark set-up an earlier trial used | Kaggle || The set-up is there: `~/Forge/workshop/kaggle-escalation/step3` (its `kaggle benchmarks tasks` commands), and the private task connect-pairs on the account. The same benchmark ran as Kaggle tasks over twelve hosted models in two days (`~/.forge/escalation-runs/kaggle-day1`, `kaggle-day2`), false confidence 0 to 10 % but one at 35.7 %; and connect-pairs over ten Kaggle models and three Claude models, one pair a chat (`~/willow-stacks/42/mine/tiers`) |
| C6 | **A report with a wrong line planted in it.** | whether an agent repeats it, which it should, or mends it from what it knows, which it should not | one changed report | here | |
| C7 | **A person as the control.** Someone who was not there answers the same questions. | what the agents are being compared with | a willing reader | someone | |

## W. Other work than one simulation

| | what is tried | what it would show | needs | from where | already on the maintainer's machine? |
|---|---|---|---|---|---|
| W1 | **Willow's own stacks.** A stack run on several machines with a shared memory of steps, under these rules. | the design note's claim that it is one shape at every size. Trial 4 found 27 of 30 steps the same across two folders | a name for a step without its place and clock (I1, I2) | here, laptop || In part, on one machine: the ledger's 95-step stack built twice into two folders, `~/willow-stacks/zero/twice`; written up in the README as "A bigger stack, run the same way". Not on several machines |
| W2 | **Another author's simulation.** | whether any of this is special to one project's care | a deterministic program with a fixed step | here | |
| W3 | **Work with chance in it**, seeded | whether a seed is enough to make a run a thing that can be remembered | such a program | here | |
| W4 | **Work on many cores**, or through the linear-algebra library | whether threads and their order break the bytes | such a program | here | |
| W5 | **Work whose parts must talk.** The plan says this is not helped | a result that says so with a number, as a control | a coupled problem, small | here | |
| W6 | **Not a simulation at all.** Converting files, an index, a model's answers at a fixed setting. | how much everyday computing is the same work done again | whatever is to hand | laptop || In part, three kinds. A model's answers at a fixed setting: the escalation benchmark's 200 items asked twice of four hosted models came back identical on 194 to 199 (`~/.forge/escalation-runs/consistency-preview`), so a model's answer is nearly, not quite, the same work again. Fetching documents: the zero project fetched its ledger's 47 sources again, and 36 were the same bytes, the 11 others web pages made afresh each request (`~/willow-stacks/zero`). Willow's own tests: about 40 minutes in a row, 10 on eight cores, and `ci-memo` pins a run so a change reruns only what it touches |

## E. People and places

| | what is tried | what it would show | needs | from where | already on the maintainer's machine? |
|---|---|---|---|---|---|
| E1 | **A stranger's machine**, by [study/TESTER.md](study/TESTER.md) alone | whether the page can be followed by someone who was not there, and a kind nobody chose | a person | someone | |
| E2 | **A second account.** Kaggle allows one a person, so another person's. | the first run where the machines are not all one person's, and what sharing an output across accounts takes | a person with an account | someone | |
| E3 | **What is in a building.** Old laptops, a school's room of them, a phone. | the first thesis of all this: anything with a chip and a wire | the machines, and B2 | someone | |

## S. Size and cost

| | what is tried | what it would show | needs | from where | already on the maintainer's machine? |
|---|---|---|---|---|---|
| S1 | **Ten times the sweep**, in more rounds | whether the saving holds, and what the memory weighs | hours of a notebook's twelve | Kaggle | |
| S2 | **Time and power, measured.** The agents were right to say the reports don't hold the seconds or the cost. | the saving in what is paid for, not only in steps | a clock in the runner, a meter on one machine | laptop || In part: seconds, not power. Each act in [study/runs/](study/runs/) has its seconds, which the reports leave out. In the workshop, the 95-job sweep took 124.6 s alone and 9.7 s with the memory; the small plan on Kaggle 1,129.7 and 317.2 machine-seconds |
| S3 | **How far apart the kept states are.** The same sweep at 500 and 2,000 steps. | the curve of what is kept against what is saved, and what a check then costs | nothing new | here || In part, on the dry run's stand-in physics, `~/willow-stacks/shared-runs-dry`: R3 at 78.06 with states every 2,000 steps, 80.9 at 500 and 81.8 at 100, against 82.04 predicted |
| S4 | **No rule for who steps what.** | what it costs when machines choose for themselves. An early trial saw about 70% against 82% | the notebooks, changed | here || On the stand-in, `~/willow-stacks/shared-runs-dry`: about 70 with no rule, 80.1 and 81.7 with each trajectory one machine's, two rounds. The "early trial" in the second column |
| S5 | **A machine that stops mid-round.** | what the next round gets back | the notebooks | here || In part, for a stack rather than a round: a stack run on 42's pile was stopped when the machine ran out of memory and was restarted; `stack --resume` onto the same run folder kept the step that had finished (696,621 lines) and ran the rest. What was in `/tmp` was lost (`~/willow-stacks/42/mine/run-ask-2`) |
| S6 | **When the memory is thrown away.** | how much can be dropped before the saving goes | nothing new | here | |

## H. Upstream

| | what is tried | what it would show | needs | from where | already on the maintainer's machine? |
|---|---|---|---|---|---|
| H1 | **The author takes the one-line change.** Then R2 again on their code as written. | 220 of 220 where it was 14, with no patch in memory | their say | someone || Written and not sent: `~/Forge/workshop/science_bitch-runs/for-the-author.md`, what was seen, the line, and the change |
| H2 | **The cube in the step-size check.** It decides when a run halts. | whether two machines can halt one step apart. They did not here | a setup on the edge | here | |

## I. What willow itself lacks, found on the way

| | what is missing | where it was found | already on the maintainer's machine? |
|---|---|---|---|
| I1 | a line on an add-on's card for what a step reads besides the pile: the record, the clock | the 95-step stack, in the README || In part: `stack-bridges` reads which steps read a record from how a step names it, not from a card's line; the fix that counts a record named by its folder (`--box PATH`) is on the branch `addons/boxes-here`, not yet on main, and finds 17 bridges, 8 deep, in the ledger's 95-step stack, where main finds none. The clock is still unsaid |
| I2 | a row's identity without its clock, and a step's output without its place | trial 4 | |
| I3 | the record's state in the mark of a step that reads it | the 95-step stack || |
| I4 | a place a study's verdict record can live. It has to be outside the repository, and a cloud session's outside is gone when it ends; a copy was kept this time | this study || A place exists, not yet used for this: on the laptop each project keeps its box outside any repository, under `~/willow-stacks` (42, zero, money, the shared runs' own folder), and it lasts |

## J. How the next study should be made

Lessons, not experiments.

- **A dry run needs a figure as large as any the real one will hold.** The
  scorer's fault could not show at ten thousand and failed a rule at a
  million.
- **A rule that counts kinds should say per what.** R1 passed on three
  kinds across the machines; per job it was three kinds for 3 of them.
- **Say before the run where each machine's part ends.** The cloud
  session turned out to be the laptop's kind, and added a machine, not a
  kind.
- **A check on an account should be tried on an empty one.** R8 passed
  an answer with no account under it until that was caught.
