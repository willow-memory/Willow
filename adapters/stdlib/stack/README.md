<!-- willow-addon
section: Ways to use it
line: One page made from several add-ons run in the order you list them, their results grouped so the biggest come first.
source: new
added: 2026-10-26
version: 0.4.0
writes: to
network: none
role: ways
-->
# stack

One document from a **stack of add-on steps** over a box. Where
[`across`](../across/) runs one document add-on over many boxes, `stack` runs
many heterogeneous steps over one box and composes what each prints — pooled,
and ordered tallest-first. It is the input side of the serve layer in
`docs/design/serve.md`: the operator's stack, before any seal.

    python adapters/stdlib/stack/stack.py --box DIR --stack FILE [--to FOLDER [--resume]]

## the stack file

A markdown file, pools and steps:

    ## a pool heading
    - digest -- --box {box}
    - export -- --box {box}

    ## another pool
    - timeline -- --box {box} --to {box}-notes "mould landlord"

A `##` heading opens a **pool**; each `- NAME -- ARGS` line under it is a
**step** — the add-on NAME run with the ARGS after the lone `--`. `{box}`
anywhere in a step's args is replaced with the `--box` path, so a step that
reads the box names it and a step that doesn't (a `git` or `pgp` step) leaves
it out. Blank lines, lines beginning `#` (but not `##`), and any other prose
are skipped, so a stack file reads as markdown; a step before any pool is
refused. A worked example is `adapters/stdlib/stack/example.md`; ten more,
each for a different kind of folder, are in `adapters/stdlib/stack/examples/`.
A stack you sealed with the forge add-on, with why each step is there, is
written out to share by [stack-share](../stack-share/).

## pools and peaks

The order is the stacking order — **peaks first**. Each step's **mass** is how
many non-blank lines it printed; a pool's mass is its steps' together. Pools,
and the steps within them, run tallest first, because mass is what decides
attention: the reader meets the biggest stack first. The document is markdown —
a `##` per pool, each step's output fenced under it, a step flagged `(exit N)`
when it didn't run clean.

## a run you can follow

A stack of slow steps (a model, a big index) prints nothing until the last
one ends, because the page is ordered by what every step made. `--to FOLDER`
keeps the run as it happens:

    <FOLDER>/00-stack.txt     a line as each step starts, a line as it ends
    <FOLDER>/01-todo.txt      the first step's output
    <FOLDER>/02-scan.txt      the second's, and so on
    <FOLDER>/reports/         a report step's report as data, for a page

    01 todo: started (3f9a2c1b)
    01 todo: exit 0, 12 lines
    02 scan: started (a04e77d2)

Each step's file is named for its place in the stack file, so the folder
reads in the order things ran. A step that prints as it goes is written as
it prints, so its file can be followed while it runs; a step asked for a
report is written once, when its report is whole. A step that printed
nothing and complained is kept as its complaint, and the line that ends it
says `flagged`. The last line is `done: N of M steps flagged`.

A step that printed a report has it kept twice: as words, in its file, and
as data, in a `reports` folder inside the run's, under the same name ending
in json, so a page can draw
it without running the step again ([browse](../browse/)'s `--run`). It is in
a folder of its own so that what follows the run reads words only. A step
run again that prints no report this time has its old data taken away.

FOLDER must be there and empty, and stack makes no folder but that one: a run is one
folder, and a second run in it would read as part of the first. Follow it
with anything that follows a folder of files; the page is printed at the end
as before, the same with `--to` as without.

## going on with a run

A run that was cut off (a model that took too long, a machine put to sleep),
or one whose stack has had a step added, needn't start again:

    python adapters/stdlib/stack/stack.py --box DIR --stack FILE --to FOLDER --resume

    resumed: 2 of 4 steps had finished
    01 todo: kept from before
    02 scan: kept from before
    03 local-model: started (95d7e44f)

From the top of the stack, a step is kept, and not run, when the earlier run
finished it, it is asked the very same way now (the eight characters after
`started` are the add-on and its arguments, hashed: the same add-on asked
another question is another step), and its output is still in the folder.
From the first step that isn't, every step runs, finished before or not. A
stack is a row where a later step may need what an earlier one made, so
nothing is kept past a step that changed.

A step counts as finished only when the last thing the log says of it is
that it ended. One that was started again and cut off is run, whatever came
before, because its file may be half of the second go.

The page is the one a whole run would print, byte for byte: the log keeps
what each step weighed and how it was flagged, so a kept step sits where it
would have. In an empty folder `--resume` is a run from the start.

**What it can't know** is whether your folder changed since. A kept step's
output is what it was then. `--resume` is for going on with a run, not for
refreshing one; for that, a new folder.

## what it does and doesn't

The step list is **open**: any add-on, built in or user-written, can be a step.
`stack` doesn't care which add-on produced a part — it runs the step, takes
what it printed, and composes. Each step is held to **its own card** by the
guard, so `stack` itself writes no box, reads no key and approves nothing, and
writes only the run folder you name with `--to` (the
one-way arrow, a box to a document); a step's own reach is the step's card, not
this one. `stack` names `network: none` for its own run.

Exit codes, the kernel's: `0` nothing in the stack waits on you; `42` a step
flagged something (or refused), its output shown and flagged; `2` refused — a
bad command line, a box that isn't a kernel box, an unreadable or empty stack,
or a step whose add-on isn't here.
