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

## The gaps the study left

From "What it cannot show" and "What the passes do and don't say".

| | the gap | entries that would close it |
|---|---|---|
| G1 | every machine was honest | A1, A2, A3 |
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
| A4 | **The same thing sent twice**, or a round's output given to the wrong round | whether a repeat or a misdelivery is refused or silently counted | the notebooks | here | |

## B. Machines: more kinds, and one difference at a time

| | what is tried | what it would show | needs | from where | already on the maintainer's machine? |
|---|---|---|---|---|---|
| B1 | **Every job on every kind.** The whole baseline on the laptop and on a cloud session. | closes G2: all 220 jobs in full on three kinds, not 3 of them | about twenty minutes a machine | here, laptop || In part, on other sweeps. The 95-job sweep of the project ran whole on the laptop alone (84 ran, 11 refused), in `~/Forge/workshop/science_bitch-runs`; the small plan's 125 jobs ran on Kaggle, and the laptop stepped 400 of its states and 12 of its jobs again, all the same. Not the study's 220 in full |
| B2 | **A processor that is not x86.** An Apple laptop, a small ARM board, a phone. | whether the rewritten power agrees across architectures, and what the project as written does there | one such machine, Python and NumPy 2.1.3 on it | someone, laptop | |
| B3 | **Another system.** The same processor under Windows or macOS. | whether the system's own maths library changes the bytes | one machine with two systems, or two alike | someone | |
| B4 | **One thing changed at a time.** A grid: processor, NumPy version, Python version, the linear-algebra library under NumPy. | which of them move the bytes and which never do. The study pinned NumPy to hold this still | a few environments on each machine | here, laptop || In part, before the freeze, in `~/Forge/workshop/science_bitch-runs/bits` and `~/willow-stacks/shared-runs-dry/bits`: NumPy 2.1.3 and 2.5.4 gave the same bytes on the laptop, so did Python 3.13 and 3.14, and AVX-512 turned off (`NPY_DISABLE_CPU_FEATURES`) changed nothing. Laptop against Kaggle, `x**1.5` and `x**3` differed; `sqrt`, division, squares, sums, `norm`, `sin` and `cos` did not. Not the linear-algebra library |
| B5 | **Graphics cards.** The same arithmetic on a GPU. | whether any of this survives leaving the processor | a GPU, and Kaggle's weekly hours | Kaggle || Not tried. The account's quota on 2026-11-11 was 45 GPU hours a week, none used |

## C. The blind half: make it hard enough to fail

| | what is tried | what it would show | needs | from where | already on the maintainer's machine? |
|---|---|---|---|---|---|
| C1 | **A chain of three.** Each agent is given only the account before it. | what is lost or added at each hand, which one hand cannot show | the scripts, three calls a model | here | |
| C2 | **Questions that join two figures.** | whether an agent joins them rightly. The larger model wrote that five machines "ran on 3 kinds" where they were two | new questions and a key for them | here | |
| C3 | **A rule for joins.** R8 holds an account to its figures and not to how it puts them together. | whether a wrong joining can be struck by a script at all | a way to say what a sentence claims | here | |
| C4 | **Smaller and local models.** | where "the reports don't say" stops being said | models that run on a laptop | laptop || Not tried. Thirteen local models run under ollama on the laptop, from 0.5B to 8B parameters |
| C5 | **Many hosted models at once**, as one private Kaggle benchmark task | the spread across a dozen and more models on the same brief | the Kaggle benchmark set-up an earlier trial used | Kaggle || The set-up is there: `~/Forge/workshop/kaggle-escalation/step3` (its `kaggle benchmarks tasks` commands), and the private task connect-pairs on the account |
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
| W6 | **Not a simulation at all.** Converting files, an index, a model's answers at a fixed setting. | how much everyday computing is the same work done again | whatever is to hand | laptop | |

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
| S5 | **A machine that stops mid-round.** | what the next round gets back | the notebooks | here | |
| S6 | **When the memory is thrown away.** | how much can be dropped before the saving goes | nothing new | here | |

## H. Upstream

| | what is tried | what it would show | needs | from where | already on the maintainer's machine? |
|---|---|---|---|---|---|
| H1 | **The author takes the one-line change.** Then R2 again on their code as written. | 220 of 220 where it was 14, with no patch in memory | their say | someone || Written and not sent: `~/Forge/workshop/science_bitch-runs/for-the-author.md`, what was seen, the line, and the change |
| H2 | **The cube in the step-size check.** It decides when a run halts. | whether two machines can halt one step apart. They did not here | a setup on the edge | here | |

## I. What willow itself lacks, found on the way

| | what is missing | where it was found | already on the maintainer's machine? |
|---|---|---|---|
| I1 | a line on an add-on's card for what a step reads besides the pile: the record, the clock | the 95-step stack, in the README | |
| I2 | a row's identity without its clock, and a step's output without its place | trial 4 | |
| I3 | the record's state in the mark of a step that reads it | the 95-step stack | |
| I4 | a place a study's verdict record can live. It has to be outside the repository, and a cloud session's outside is gone when it ends; a copy was kept this time | this study | |

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
