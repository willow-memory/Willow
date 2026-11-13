# A memory that has been lied to: a study, drafted

**Status: drafted 2026-11-12. Nothing is frozen and no lie has been told
to the real run.** Every number of trials, every rate and every rule here
is a proposal for the maintainer to set or change. What is below was
tried only on a made-up sweep, and what that found is not a result.

It follows from [the study before it](../README.md), which found that a
shared memory saved 73% of the work and served only what a run would
give. Every machine in that study was honest. This asks what the same
checks do when one is not, which is entry A1 of [NEXT.md](../NEXT.md).

## The claim

> When a memory holds something false, the checks the study already has
> find it whenever they look at it; how often they look decides how
> often they find it; and what they find, they find after the wrong
> answer has been handed out, not before.

The last part is the one the first study could not say, and it is as
likely to come out badly as well.

## The setup

- **The honest run** is the first study's own, kept in
  [../study/runs/](../study/runs/): the baseline, which is the truth for
  every job, and each machine's first round.
- **A trial** is one lie told to a copy of one machine's first-round
  memory. Then that machine's second round is run on it, and the check
  after it, both by the first study's runner.py, unchanged.
- **Six kinds of trial**, forty in all as proposed:

| kind | the lie | proposed |
|---|---|---|
| none | nothing: the control | 3 |
| one-bit | one bit of one kept state, anywhere on a trajectory | 12 |
| last-bit | one bit of a trajectory's last kept state, the one most likely to be gone on from | 8 |
| false-halt | the memory says a trajectory halted where it did not | 8 |
| no-halt | the memory forgets a halt, or a refusal, that happened | 3 |
| stepped-otherwise | every kept state of a trajectory is what the project *as it is written* gives, under the name of the rewritten one: a machine that did not do what the others did | 6 |

- **Two arms**, each running all forty: `as-run` checks what the first
  study checked, one kept state in 8 and one served job in 10;
  `everything` checks every state and runs every served job afresh.
- **Which state, trajectory and bit** come from one seed, so
  [lies.py](lies.py) lists every trial before one is run. The list for
  the real run is made from [lies.json](lies.json) and the kept run; it
  is not kept here until the freeze.
- **One machine runs it all**, a cloud session or the laptop. This is
  about the checks, not the processors: the first study's R1 is what
  says a second round stepped here is the second round Kaggle stepped.

## The rules, proposed

| rule | passes when |
|---|---|
| L1, no false alarm | in every trial with no lie, the check finds nothing and every job is right |
| L2, a lie looked at is found | every lied-about state the check steps again comes out not the same |
| L3, a wrong job looked at is found | every wrong job the check runs afresh comes out different from what was served |
| L4, full checking finds every lie in a state | in the arm that checks everything, every one-bit, last-bit and stepped-otherwise lie is found |
| L5, how often, measured | no threshold: the share of lies found, by arm and kind |
| L6, the harm, measured | no threshold: the wrong jobs each kind hands out, how many of those in trials where nothing was found, and how many lies reach no job at all |
| L7, a lie stays where it was told | no job on any other trajectory comes out wrong |

What is expected, said now so it can be wrong:

- A one-bit lie is found about one time in eight in the `as-run` arm,
  since only the check of that one state shows it, and many reach no job.
- A false halt is **never** found by stepping states again, because the
  check steps states and a halt is not one. Only a served job run afresh
  can show it.
- A forgotten halt is found by nothing, and harms nothing: the next
  machine steps into the halt again and gets the true answer.
- A machine that stepped otherwise is found nearly every time, since
  every one of its states is wrong against the one before.
- **Finding is not preventing.** The check runs after the round. In the
  arm that checks everything, every lie in a state should be found and
  the wrong jobs still have been handed out.

## The dry run

On six made-up trajectories of whole numbers under nonsense names
([dry-plan.json](dry-plan.json), [dry-lies.json](dry-lies.json)): an
honest run made by the first study's dry.py, then 22 trials an arm, 44
in all. The trials are listed in [dry/trials.txt](dry/trials.txt) and
what the judge made of them is [dry/verdicts.json](dry/verdicts.json).

| rule | in the dry run |
|---|---|
| L1 | passed, 4 of 4 |
| L2 | passed, 23 of 23 |
| L3 | passed, 18 of 18 |
| L4 | passed, 15 of 15 |
| L5 | as run: one-bit 3 of 8, last-bit 3 of 4, false-halt 3 of 4, no-halt 0 of 1, stepped-otherwise 3 of 3. Everything checked: all found but the forgotten halt |
| L6 | the same wrong jobs in both arms: 3 from the one-bit lies, 3 from last-bit, 6 from false-halt, 8 from stepped-otherwise |
| L7 | passed, 44 of 44 |

What the dry run could see: that every kind of lie can be told, that the
honest run is not written to (a test holds its bytes before and after),
that each rule fails when what it guards is broken (a test with made-up
rows), and that the arm that checks everything hands out exactly the
wrong jobs the other arm does.

What it could not: the real project, where a state is a few hundred
bytes of floating point and not two whole numbers; the real
stepped-otherwise, which here is another multiplier and there is the
project's own arithmetic; and any rate, since its sweep is six
trajectories and its numbers are its own.

## What is already here, and what this adds

Asked 2026-11-12 of three places: willow's own demos and add-ons, by
[novelty.py](../../novelty.py) and by reading; the homestead-affairs
repositories, through the box made for them on the branch
`health/minors-boxes`; and the four-minors scene on that same branch.

**The novelty check says these pieces have not been put together
before**: nothing on the idea list is close, and no other demo holds half
of the description's words.

What exists catches a lie of another kind:

| what is lied to | what catches it here already | where |
|---|---|---|
| a record, rewritten after the fact | each row holds the hash of the one before; where the record ends, kept out of its reach; the people who were sent something, holding it to what they kept | the kernel, the tip-pin and share add-ons, and [the Johnson scene](../../johnson/README.md), where a rewritten record still verifies for its owner and is caught by everyone else |
| something in transit, edited on the way | a signature over every layer | the Johnson scene's edited copy, refused where it lands |
| a file that is not the one named | its SHA-256 held to a pinned one | the weights-pin add-on; and this study's own runner, which refuses a stepper that is not the plan's |
| a summary that says more than its source | figures in one and not the other, side by side | the pair-drift add-on. The first study's R8 is the same idea, written again for an agent's account |
| a log, forged whole with its anchor | a key the forger does not have | homestead's integrity log, with what it still cannot catch written down: a row deleted so the log looks as if it never had a key |

**What none of them is:** every one of those finds a thing changed
*after* it was written down. The lies here are false *when* they are
written down. A kept state that is wrong has a true hash of a wrong
state; no chain breaks and no signature fails. The only thing that can
find it is doing some of the work again. That is the gap between a
record being whole and a record being right, and it is this draft's
whole subject.

Four things the comparison turned up that the draft lacks:

- **It checks a lie against itself.** Homestead's audit found a check
  that "compared a poisoned reading against itself and reported
  nothing", and mended it by taking the baseline before anything was
  declared. This draft's check steps a kept state again *from the kept
  state before it*. When that one is the lie, everything after it agrees
  with it. The dry run shows exactly this: a one-bit lie is found only
  when that one state is looked at. The start of a trajectory, frozen as
  exact numbers, is the only thing the liar did not write.
- **Nothing says who told it.** The memory is rows in a file, unsigned.
  Willow's share add-on gives every sender a key and a standing earned
  from the packages of theirs that held: rookie, then steady, then
  veteran. A pool of machines needs just that, and how much of a
  machine's work is checked could turn on it.
- **What arrives is used as if it were approved.** In the minors scene a
  box that receives a package says "received, not sealed by you", and
  what was received counts for nothing until its owner seals something
  of their own. The shared memory does the opposite: a state is gone on
  from the moment it arrives. This study measures what that costs.
- **A lie found is not a lie recalled.** In the Johnson scene a wrong
  answer is replaced, and the replacement follows the first along every
  hand it passed through. Here a found lie is a line in a list. Every
  job says which kept state it went on from, so the wrong jobs could be
  named from the lie; nothing does it yet.

And one it shares with what is here: homestead's deleted row and this
draft's forgotten halt are the same thing. An absence is the one lie no
check of what is present can find.

## Before the freeze

The maintainer's to settle:

- **How many trials.** Forty an arm is a guess. The `as-run` arm is
  about half a minute a trial on the real project; the `everything` arm
  steps every state and every served job again, some minutes a trial, so
  near two and a half hours for forty. Fewer trials in that arm, or the
  trials run several at once, would cut it.
- **Whether L5 should have a threshold.** As drafted it is a
  measurement. A prediction worked out beforehand from the draw, as R3
  had, would make it a rule that can fail.
- **Whether a check of halts belongs in this study or the next.** If a
  false halt is found only by luck of the draw, the mend is a check that
  steps up to a halt and sees it. That is a change to runner.py, which
  the first study froze; here it would be a finding, not a fix.
- **Whether to add the four things the comparison found** before it is
  frozen, or leave them as what it finds: a check from the start and not
  only from the state before; a key on what a machine keeps; a memory
  that is not gone on from until something has looked at it; and a
  recall that names the jobs a found lie reached.
- **Whether the lie should know the seed.** These lies are placed by a
  seed of their own. A liar who knew the check's seed would lie only
  where it does not look, and the `as-run` arm would find nothing. That
  is a harder study and a different one.

## The order

1. Settle the list above.
2. Dry run. Done, above.
3. Freeze, in one commit, alone: lies.py, lies.json, the list of trials
   it makes, and the first study's runner.py and sweep.py by the hashes
   they already have.
4. Run both arms, on one machine.
5. Judge, each verdict a row on a record outside the repository.
6. Write down what held, what did not, and what was found after.
