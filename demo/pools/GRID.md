# The grid of stacks: a draft, nothing frozen

One part of a study the maintainer asked for: run many stacks over many
piles, from one add-on to every add-on, and let what fires together on
which pile say where the pools are, where the gaps are, and which cards
are in the wrong place. This part is the grid: which stacks run, how they
are made from the cards rather than by hand, and what each run records.
The study's design and the Kaggle side, the laptop's private piles and the
gate, and holding the report's claims to the runs are other sessions'
parts. Nothing here is frozen or promised; it becomes a study only with a
freeze of its own (see [studies.md](../../docs/agents/studies.md)).

## What is already there to make it from

Measured on main at 99e0eeed:

- **A step for 236 add-ons, ready-made.** `COMMANDS` in
  [test_contract.py](../../adapters/stdlib/ci/test_contract.py) is a
  command line for every stdlib add-on a person runs, over a box and pile
  it is given (`{box}`, `{pile}`, `{tmp}`), each answering offline. 177 of
  them name `{box}`. `READERS` and `PILE_EXTRA` there say which need a file
  of a kind in the pile (a PDF, a calendar). That table is the grid's step
  list. All 236, run one at a time over the contract test's small pile,
  took 76 seconds here: about 0.2 seconds each, the box made included.
- **No such table for the 28 in adapters/deps.** Their tests start them,
  but no row says how a person runs one over a box. The grid needs one, in
  the same form, held by a contract test so it can't go stale: the first
  thing to build.
- **Every card has a `role`** (9 of them: reads, tools, page, makes,
  ways, suggests, words, guards, repo) **and a `section`** (10). Fewer say
  what they lean on: `uses` 121 of 368, `reads` 95, `output` 61, `hands` 10,
  `looks-for` 9. None says what kind of thing it takes or gives.
- **[stack-bridges](../../adapters/stdlib/stack-bridges/) reads a stack**
  and says which step takes what an earlier step wrote. That is the only
  "takes" and "gives" anything here can tell today, and it is read from the
  arguments, not seen in a run.
- **Nine made-up lives, all public**: the `make_life.py` of bernadette,
  corwin, hollis, johnson, money-hour, odile, ofrenda, stewart-crossover and
  teodora. With the repo itself, ten piles that can go to Kaggle as they
  are. The private piles stay on the laptop and only their shapes go up.

## Stage 0: every add-on alone, over every pile

Each step, alone, over each pile: about 264 steps times the piles. With the
ten public piles that is some 2,640 runs, most of a second each on small
piles: one Kaggle CPU session, or an evening on the laptop.

What a run records, per step and pile:

- how it ended: 0, 42 or 2, as the kernel's codes are;
- its mass: lines printed, as stack counts it;
- for a card with `output: report`, its first line's state (populated,
  empty);
- what it wrote under `--to`, by count and bytes;
- the SHA-256 of what it printed, as [stack-row](../../adapters/stdlib/stack-row/)
  keeps it, and its time.

**A step fires on a pile** when it ends 0 or 42 and prints something that
isn't a refusal. That rule is the one to freeze; everything below is
counted from it.

Stage 0 alone gives three of the report's answers: the add-ons that fire on
no pile, the ones that fire on one kind of pile only, and the fire matrix,
add-ons by piles. Add-ons whose rows in that matrix are alike are a
candidate pool, found from the runs: the thing to compare with the
sections, the roles, `uses` and similar's `near:`.

## Stage 1: pairs, only where something can pass between them

264 add-ons make about 35,000 pairs. Most can't touch each other: each
step reads the box and prints, and stack only puts the text together. Two
steps can only change each other's output where one takes what the other
made. So stage 1 runs a pair only where something could pass:

- where stack-bridges, over the stack of every step, says B takes what A
  wrote;
- where a card's `uses`, `looks-for` or `hands` names the other.

For each such pair, A then B over each pile: if B's output's hash differs
from B alone, A gave B something, and that is an edge seen in a run, a
"takes" and a "gives" no card says. The claim that the other pairs are
independent is itself tested: 500 pairs drawn with a seed from the
unbridged ones, whose hashes must match their singles'. That is one pass
rule to freeze.

## Stage 2: stacks, made each of the ways a stack could be made

Every stack is written by a script from the cards and the tables, never by
hand, and each way is one grid row:

| way | how it is made | about | tests |
|---|---|---|---|
| section | every add-on of one section | 10 | the headings people read by |
| role | every add-on of one role | 9 | the role field |
| cell | section by role, where both hold three or more | ~40 | whether the two cut the same way |
| near | a card and its three `near:` entries | 368 | similar's word overlap as a grouping |
| leans | a card and everything its `uses` reaches | ~120 | what cards say they need |
| found | each pool stage 0 found | ? | the found pools: do they fire together more than a section does |
| person | forge's suggest on a sentence; stack/examples' ten | ~20 | the way a person makes one |
| random | seeded draws of 3, 10, 30 and 100 | 40 | the control every row is held to |
| all | every step, in stack's order and three shuffles | 4 | order, which should matter only across a bridge |
| all but one | every step but one, for each | ~264 | which add-on, taken out, changes another's output, and which changes nothing (a duplicate, or nobody's input) |

What a stack run records is stage 0's, per step, plus stack-bridges over the
stack before it runs (its expected edges) and stack-row's row after. A
stack whose steps fire more together than its size's random draws is a
pool; one that fires no more than they do is a heading, not a grouping.

The rows "all" and "all but one" are the costly ones. The stack of every
step is some minutes over a small pile; all but one is that, 264 times. Over
two piles (one life, the repo) that is tens of CPU hours: the Kaggle part,
five sessions at once. The dry run gives the real figure before anything is
promised.

## How the stacks are made

A script reads, and nothing else:

1. the cards' headers, as readme.py parses them;
2. `COMMANDS` and the deps table, for each step's line;
3. readme's week.json, for `near:`;
4. stage 0's fire matrix, for the found pools (so those stacks are made
   after stage 0, and frozen in a second freeze, said as such);
5. forge's suggest, for the person row.

It writes one stack file per row, in the form
[stack](../../adapters/stdlib/stack/) reads, and a manifest: each stack's
SHA-256, its way, and why it exists. The manifest is what the freeze holds.
The same script run twice writes the same bytes.

## The dry run, before any freeze

Per [studies.md](../../docs/agents/studies.md): every stack once over a pile
of nonsense, one passage of words in no order ("zzzz qqqq"), so a step that
needs a passage served is called at all. That shows which steps break on a
pile, which COMMANDS rows only work on the contract test's own small pile
(those need their `READERS` or `PILE_EXTRA` file carried onto each pile, or
a mark that they take a file of that kind, which is itself a "takes"), and
whether Kaggle's output lands where the script reads it.

## What the grid hands the report

For each card, each tied to the runs that show it:

- the piles it fires on, and the ones it never does;
- the found pool it sits in, beside its section and role, and where they
  disagree;
- what it was seen to take from and give to which other add-ons: proposed
  `takes:` and `gives:` lines;
- the neighbours it fires with, in place of or beside `near:`;
- whether taking it out of the stack of every step changed anything.

## Open questions for the other parts

- **Which public piles beyond the ten?** The fire matrix is only as wide
  as the piles; a real corpus or two (code, mail, notes) would help.
- **Whether "fires" should count 42.** An add-on that flags something and
  waits on a person did run. Counting it is the draft's choice.
- **The deps table first.** Without it the 28 add-ons that need installs
  are left out; on Kaggle they can be installed.
- **The ways' sizes.** The `near` and `all but one` rows are per card; the
  dry run's times say whether both can run on every pile or only some.
