# Pools: where add-ons meet, from what they are seen to do

**Status: a plan in the making. Nothing is frozen, nothing has been run,
and nothing here is a result.** The maintainer's question: run stacks of
every size over many piles and let what happens, not the words on the
cards, say which add-ons belong together, where the gaps are, and what
is in the wrong place; with one report at the end, every line of it
tied to a run.

What is here so far is one thing: a reading of the code, made before
any run, to hold the runs to.

## The reading: [static/](static/)

`python demo/pools/static/static.py say` reads every add-on under
`adapters/stdlib` that has a card, and runs none of them. On main at
99e0eee it says, and [static/static.json](static/static.json) keeps
one entry an add-on:

| | |
|---|---|
| add-ons read | 341 (the 27 under `adapters/deps` are not read) |
| write a row to the record | 32 |
| tell rows apart by kind | 48 |
| read the record at all | 78 |
| name a file suffix in a string | 157 |
| none of those | 129 |
| kinds of row seen | 54 |
| kinds made and taken only by the add-on that makes them | 33 |
| kinds made and taken by nothing | 5 |
| kinds made by one add-on and taken by another | 3: `bite`, the CI add-on's `verdict`, the dice add-on's `roll` |
| links from a maker to another add-on that takes, through the record | 26, over 19 add-ons |

**What it says.** The record is not where add-ons meet: nearly every
kind of row is read only by the add-on that writes it. They meet in
the folder. A reader turns a file into pages, and what comes after
reads pages through the kernel. So what an add-on takes and gives
cannot be read off its rows; it is the files in, the pages out, and
the places those pages name, and only a run on real piles shows that.

**How rough it is.** A suffix is any string shaped like one, so a
number's format (`.1f`) is counted. A kind is any string compared with
a row's `kind`, and a few are not row kinds. Take the sizes, not the
last digit.

## One prediction from it, to be settled by a run

Sixteen add-ons name the folder `.places`, where a reader's mirror
keeps the map from its pages back to the original. Two of them do not
write it (the CI add-on uses the name for something else; deep-links
reads it). That leaves **14 predicted to write the map**: asciidoc,
chats, code-comments, csv-rows, dotfiles, equations, jupyter, latex,
mail, markdown, notation, org, rst, subtitles. A writer is an add-on
seen, in a traced run, to leave a file under a mirror's `.places`;
nothing else settles it. Another session counted the cards that say
`output: mirror` and got the same fourteen.

## The trace: [trace/](trace/)

`python demo/pools/trace/trace.py pile --pile PILE --name NAME --salt SALT --work DIR --to ROWS`
runs every add-on that has a command line (the contract test's tables,
which the [grid](GRID.md) takes its steps from) alone on one pile, each
on a copy of one box and under the add-on guard, and writes one row a
step of what was seen: how it ended, a report's state, the kinds of row
it added, the files it left by suffix and whether a mirror's map is
among them, and the places in the pile its output names, each hashed
with the pile's salt and taken back through a mirror's map to the
original where there is one. A row holds counts, hashes and the
add-on's name, and none of the pile's words; its test holds it to that.

**Tried, not run as a study.** On a pile made of every reader's own
sample file from the contract test (105 files), all 351 steps took 29
seconds on one core, none timed out and the guard refused nothing. 242
ended 0, 77 ended 42 and 32 refused, 9 of those naming a file the pile
did not have. Fourteen steps left a mirror's map, and they are the
fourteen the reading predicted, no more and no fewer. 45 steps named a
place in the pile; none went through a map, since no step was given
another's mirror, which is what a stack is for. These are a trial's
figures on a made-up pile, to show the harness works; the study's
piles, salts and rules are not frozen.

**Stacks, and what is steady.** `trace.py stack` runs stacks of the
grid on a box that carries on from step to step, the same row a step.
A step's output is hashed with the run's own folders and any time of
day taken out, so one run of it can be held to another. Tried on the
same made-up pile: of 351 steps run alone twice, 14 do not print the
same thing twice (they draw at random or say how long something took:
backup, bench, catgrid, dice, dice5e, history, life, merkle, profile,
quiz, ro-crate, session-seal, tarot, tip-pin). Of the other 337, run
in one stack of every step, ten printed something they do not print
alone: again, cloudevents, forecasts, game-master, handover,
nightstand, predict, prov, sent-log and three-two-one in one order,
and serve in place of again in another. Those are the steps that read
what other steps leave on the record, which is what the code reading
said of most of them; and ten seeded steps at random changed nothing.
So on this pile a step's company changes what it says for about one
step in thirty. A trial's figures, again, and a first sight of what
the study would count.

## What the report may say: [truth/](truth/)

`python demo/pools/truth/truth.py measure ...` reads the trace's rows and
nothing else, by the rules in [truth/rules.json](truth/rules.json), and
`report` writes the one report from what it found, each claim with the
rows it stands on. No line of the report is typed by hand.

| rule | what it takes |
|---|---|
| fires | exit 0 or 42, not timed out, no guard breach, and a report's `populated` (or, with no report state, a line printed). Empty is silence; the rest is refused, counted, never read as silence |
| a pair | fired together, on the piles both apply to, beyond chance (the exact hypergeometric tail, on 5 piles or more), held at a false discovery rate of 0.05 (Benjamini-Hochberg), **and** the same places named, within each pile, overlapping 0.2 or more. Places overlapping is "acts on the same thing"; only files overlapping is "shares files" |
| a duplicate | the same places, 0.8 or more, on every pile both fired, 5 or more |
| never fires | applies to a pile (its card's `reads:`, or every pile when it names none) and fires on none; kept apart from "had no pile it applies to" |
| a gap | a kind of file in the piles that no step's output named; an idea whose line names it is said beside it |
| a section | at least half of a step's partners are under one other heading |
| neighbours | a step's three best partners, places before files; "none found" when it has none |
| the null | a step in a stack may print other than it did alone on the pile only when an earlier step bridges to it, directly or through others (bridges frozen in the grid). A step that differs from itself alone is unsteady, listed, and not held |
| a known gap | 3 or more probes, questions with their answer's place set by hand before any run; found when most miss and every control probe of the same reader hits; otherwise it can't be read |

**Where the places come from.** A step's places on a pile are what it
named in every run there, alone and in stacks. Alone, no step is given
another's mirror, so a reader and a step that reads its pages meet only
in a stack, through the map: firing together is read from the runs
alone, the places from all of them. And a place is seen only when an
output names a file of the pile as one word, so the places, and every
pair and gap read from them, are a floor.

**The dry runs, and that they can fail.** `truth.py dry --box BOX` runs
the measure on made-up rows and writes each verdict as a kernel row
named `study:dry:...` on a box outside the repo, never the study's:

- **nonsense**: steps that fire at random and name places of their own;
  any pair or duplicate is invented. Held: none.
- **planted**: a and b on the same places; c a duplicate of d; a kind of
  file, `.zzz`, nothing names; a reader and a taker of its mirror, which
  meet only through the map; and a and r firing on the same piles with
  no place in common. Held: exactly a-b, c-d and r-t, c-d the one
  duplicate, `.zzz` the one gap, and never a-r.
- **map off**: the same, with the taker's places those of the mirror's
  pages. Held: the reader and its taker no longer act on the same thing.
  The taker meets the reader only in their bridge stack, as in a real run:
  with the stack's rows left out, they don't pair.
- **shuffled**: the planted rows moved between piles at random. Held: no
  planted pair survives.

The tests break each rule on purpose and the dry run that should notice
does: with the place rule taken off, a and r pair on firing alone; with
the false discovery rate at 1, chance pairs are kept. The planted run's
result and report are kept in [truth/sample/](truth/sample/), and the
report is made from them again byte for byte.

**For the freeze.** It holds `rules.json`, `truth.py`, the grid's
manifest, each pile's shape (`truth.py shape`, a pile's kinds of file
and its files' salted hashes, never their names or words), the cards
(`truth.py cards`), the seeded pairs no bridge joins (`truth.py pairs`,
500 by the rules' seed, each run in both orders), and the probes, each
with its answer's place, before any of them is asked.

## What is not here yet

The piles, the probes' questions and answers, the freeze, and anything
for Kaggle. Those are the maintainer's to start.
