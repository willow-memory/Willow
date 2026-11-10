<!-- willow-addon
section: Keeping track
line: Every project under one folder: its records, its stacks, and each stack's runs, so you can see what there is to go back to.
source: new
added: 2026-11-10
version: 0.1.0
writes: nothing
network: none
role: tools
output: report
uses: stack
-->
# projects

Every project under one folder: its records, its stacks, and each stack's runs, so you can see what there is to go back to.

    python adapters/stdlib/projects/projects.py --home FOLDER [--json]

    projects: populated, 2 projects under /home/you/willow-stacks: 3 records, 2 stacks, 4 runs; 9 suggestions wait on you
    ## cv
      box            61 rows: 4 asked, 38 approved, 0 waiting
    ## dashboards
      box            30 rows: 12 asked, 0 approved, 9 waiting
      drafts         1 row: 0 asked, 0 approved, 0 waiting
      full.md        24 steps; never run
      mend.md        4 steps; last run mine/run-mend-3, nothing flagged; 2 runs before it
      mine/run-0412  a run of no stack that is here now: 10 steps, 1 flagged

It is for knowing what there is to switch to. When your work is spread over
several folders, a page, a terminal or an assistant can ask this instead of
looking through them: which projects there are, how each record stands, which
stacks you keep, and how each one's last run went.

It prints [a report](../ci/README.md#the-report-contract), the shape every
report add-on shares: a line that counts everything, then a group for each
project, A to Z, each row a name and what is said of it. `--json` gives the
same report as one JSON object.

## What it lists

**A project** is a folder, directly inside the one you name, that holds a
record. It is found by what it holds, never by what it is called, so any
folder with a record in it is one, and a folder without is left out. So is a
folder whose name starts with a dot.

**A record** is a box: the folder the kernel's `init` made. Its row counts
its rows, the questions asked, the answers you approved, and the suggestions
still waiting for your yes or no. A record that has been edited by hand, so
that its chain no longer holds, is not counted: its row says the chain is
broken, and where.

**A stack** is a markdown file beside the record that the
[stack](../stack/) add-on can run, with at least one step in it. Its row
says how many steps it has, then its last run and how that went (nothing
flagged, or how many steps flagged something), then how many runs came
before. A stack with no run says `never run`. Other markdown files, your
notes say, are left out.

**A run** is a folder a stack was run into with `--to`: it holds the log the
stack add-on kept as it went. Runs are looked for beside the record and one
folder further down, never inside a record, and the newest comes first, by
when its log was last written. A run whose log has no last line was cut
off, and is said to be `not finished`.

## Whose run it is

A run doesn't say which stack made it, and a folder's name proves nothing:
you can rename either. So a run is told by its steps. As each step begins,
the stack add-on writes a mark in the log, eight characters made from the
step's name and its options. The same add-on asked another way has another
mark.

- A run whose marks are a stack's own, in order, as far as the run got, is
  that stack's run. When two stacks begin the same way, a run of the whole
  of one is that one's.
- A run that shares more than half of a stack's marks, but not all in
  order, was made by that stack before you changed it. It still counts as
  that stack's, and its row says `of the stack before it changed`.
- A run that matches no stack here is listed in a row of its own, as `a run
  of no stack that is here now`, with its steps counted. Nothing is hidden
  because its stack was deleted or rewritten.

## Files that have changed since

A step that is given a file (a list of questions, say) notes in the log what
that file held, as a short mark of its bytes. When a stack's last run was
given a file that is no longer what it was then, changed or gone, its row
ends `of files that have changed since`: the run is real, but it was a run
of older files, and running the stack again may say something else.

A run doesn't say which record it was run on either, so a file inside a
record is tried as each record of the project, and counts as unchanged if
it matches in any. A log from before files were noted says nothing about
them, and is taken at its word. Folders are not compared, only files.

## Refusals and exit codes

It refuses, and prints nothing but why, when the command line is wrong or
`--home` is not a folder.

**Exit codes:** 0 everything is listed and nothing waits on you; 42 a
suggestion waits somewhere, a record's chain is broken, or the folder holds
no project at all (the report is then `empty`, and says so); 2 refused.
A step that flagged something in a run does not make it 42: that is the
run's to say, and it is said on the stack's row.

**Uses:** the kernel's `read`, `sealed` and `declined`, and the
[stack](../stack/) add-on's own reading of a stack file and of a run's log,
so the two never disagree about what a step or a run is.

**Never:** writes anything, runs a stack, or reads your key. A record is
counted from its rows alone.
