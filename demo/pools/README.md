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

## What is not here yet

The piles, the rules for a pool, a gap and a duplicate, the dry runs
(a nonsense pile, planted pairs, shuffled labels), the freeze, and
anything for Kaggle. Those are being worked out between sessions and are the
maintainer's to start.
