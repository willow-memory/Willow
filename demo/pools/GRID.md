# The grid of stacks: built, nothing frozen, nothing run

The part of the pools study ([README.md](README.md)) that says which stacks
run: every one written from the cards and the command tables by
[grid/grid.py](grid/grid.py), never by hand, with a manifest of their hashes
for the freeze to hold. The study's design and its Kaggle side, the laptop's
private piles and the gate, and holding the report to the runs are other
sessions' parts. Nothing here is frozen; it becomes part of a study only
with the study's freeze (see [studies.md](../../docs/agents/studies.md)).

    python demo/pools/grid/grid.py write --to DIR
    python demo/pools/grid/grid.py fill  --stack FILE --pile PILE --tmp TMP --to FILE

## What it is made from

- **A step for each add-on a person runs over a box or pile.** `COMMANDS`
  in [test_contract.py](../../adapters/stdlib/ci/test_contract.py) gives
  336 stdlib add-ons a command line that answers offline, over `{box}`,
  `{pile}` and `{tmp}`. All 336, one at a time over the contract test's
  small pile, took 76 seconds here.
- **`DEPS_COMMANDS` and `DEPS_TAKES`, beside it, for adapters/deps.** 15
  deps add-ons run over a box or pile; 12 can't, and say what they must be
  handed first (a kart result for dp, a sealed job for wasm and
  wasi-python, a model file for in-process, the network for robinhood). A
  contract test holds both: each deps add-on with a command line is in
  exactly one; each row runs or refuses by naming what to install; each of
  the 12 refuses a command line with nothing in it. In a grid the 12 are
  steps only after the step that makes what they take.
- **Each card's header**, for its section, role, `uses`, `looks-for` and
  `hands`; **readme's week.json**, for each card's `near:`; **the static
  reading** in [static/](static/), for the rows each add-on's code writes
  and takes.
- **[grid/plan.json](grid/plan.json)**, the only numbers a person chose:
  the seed, the random sizes, how many draws of each, how many shuffles,
  and the smallest cell. The draws are the seed's, never a session's.

17 cards have no step: the 12 above, and 5 that run only on willow's own
repository (ci, github, mutants, readme, similar).

## What it writes, on willow-pool-test at 8125716 (main merged in, 2026-11-13)

1,473 stacks of 357 steps (2,629 with the kind stacks added after the first report), in half a second, the same bytes every time:

| way | stacks | what each is |
|---|---|---|
| single | 357 | one step alone: stage 0, the fire matrix |
| bridge | 207 | the giver, then the taker, for each bridge |
| section | 10 | every step of one card section |
| role | 9 | every step of one card role |
| cell | 19 | a section and a role, where three steps or more share both |
| near | 357 | a card and its three `near:` entries |
| leans | 113 | a card and everything its `uses` reaches |
| random | 40 | ten seeded draws each of 3, 10, 30 and 100 steps: the control |
| all | 4 | every step, in name order and in three running orders |
| all-but-one | 357 | every step but one, for each |
| kind | 1,156 | a step that wrote kinds of row alone in stage 0, then each of the 78 readers of the record (added after the first report, from stage 0's rows) |

Over one pile that is 133,442 step runs, 127,092 of them in all-but-one.
At 0.2 to 1 second a step, some 7 to 36 CPU hours a pile: all-but-one is
the row that decides how many piles the study can afford, and the dry
run's times are the figure to plan by.

## Two rules the grid keeps

**The order a stack lists is the order it runs.** stack.py goes pool by
pool and step by step (lines 523 to 527 on main); only the document it
prints is sorted tallest first. So the three shuffled rows of `all` are
three running orders, and shuffling the list is how to shuffle the run.

**A bridge is frozen from code and cards, before any run.** A pair is
bridged when the static reading says the taker takes a kind of record row
the giver writes (26 pairs), or the taker's card names the giver in
`uses`, `looks-for` or `hands` (183). Two pairs are both, and are one
bridge with both reasons. A run tests a bridge (does the taker's output
change when the giver runs first?); a run doesn't make one.

**A record bridge is the third kind, frozen the same way.** A step whose
code reads the record at all (78 with a step) is reached by any step that
adds a row to it (53): its code writes a kind of row, appends one whose
kind can't be read, or asks for a bite, which the kernel writes a row
for; or its own command line is a bite. That is what a trial run on a
made-up pile showed: steps that read the record print otherwise in a
stack of every step than alone. It is too wide (some four thousand pairs)
for each to get a stack of its own, so the manifest keeps it apart, in
`record_bridges`, as the two lists; the null reads it with the other two,
and the seeded pairs no bridge joins leave its pairs out.

## What a run of a stack is held to

Each step's `{tmp}` is a folder of its own under the run's, so no two steps
write the same path. `fill` writes a stack for one pile, `{pile}` and
`{tmp}` filled in and each step's folder made; `{box}` stays stack.py's.
25 steps name a file under `{pile}` (a calendar, a catalog): on a pile
without it they refuse, and the manifest lists which, so a refusal of
that kind is read as "takes a file of this kind", not as a failure.

What each run records (exit, mass, a report's state, what it wrote, the
hashes of what it printed and the places it named) and the rules for a pool,
a bridge seen, a gap and a duplicate are the study's, in its freeze.

## What the grid hands the report

For each card, each tied to the runs that show it: the piles it fires on and
the ones it never does; the pool it was seen in beside its section, role and
`near:`; the bridges that held and the ones that didn't; and whether taking
it out of the stack of every step changed anyone else's output.

## Not in the grid yet

- **Stacks a person would make.** forge's suggest needs forge-play
  installed; the ten stacks in adapters/stdlib/stack/examples are by hand.
  Both can be added as a way once the study says which sentences.
- **The pools stage 0 finds.** They are stacks made from runs, so they come
  after stage 0, in a second freeze, said as such.
