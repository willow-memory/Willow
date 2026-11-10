<!-- willow-addon
section: Keeping track
line: Where one project stands, to hand on: what waits on you, what each stack's last run said step by step, and where each line can be checked.
source: new
added: 2026-11-10
version: 0.1.0
writes: nothing
network: none
role: tools
output: report
uses: projects, stack
-->
# handover

Where one project stands, to hand on: what waits on you, what each stack's last run said step by step, and where each line can be checked.

    python adapters/stdlib/handover/handover.py --project FOLDER [--json]

    handover: populated, dashboards: 19 suggestions wait on you, 1 step flagged, 4 stacks run, 2 stacks never run
    ## waits on you
      box-full         10 suggestions waiting, of 24 rows
    ## flagged
      work.md step 03  sort: populated, 435 files: 271 sorted into 8 categories (mine/run-work-2/03-sort.txt)
    ## last runs
      mend.md          mine/run-mend-4: 4 steps, nothing flagged
      mend.md step 04  glance: populated, 18 questions: 9 held whole, 9 in part, 0 found nothing
    ## never run
      full.md          19 steps
    ## changed since its last run
      start.md         a file it was given is not as it was

This is what you would write by hand at the end of a day's work, so the next
person (or you, next week) knows where things stand. It is made from what was
kept, not from memory: the suggestions waiting in each record, and what each
stack's last run said. Every line names the file it came from, so it can be
checked. Nothing here is anyone's account of the work.

FOLDER is one project: a folder that holds a record. Its stacks are the
markdown files beside the record that [stack](../stack/) can run, and its
runs are the folders a stack was run into with `--to`, in the project or one
folder down. [projects](../projects/) finds them, and tells which stack a
run is of.

It prints [a report](../ci/README.md#the-report-contract), the shape every
report add-on shares, and `--json` gives the same as one JSON object. The
first line counts what waits on you, the steps flagged, the stacks that have
run and the ones that never have. Then come the groups, in this order, each
only when it has something to say:

- **waits on you**: each record with suggestions waiting for your yes or no,
  and how many. A record whose chain is broken is here too, with why.
- **flagged**: each step of a stack's last run that ended flagged, by the one
  line it said, and then the file to open to see the rest. Flagged steps come
  before everything else about the runs, since they are what the next person
  meets.
- **last runs**: each stack that has run: the folder of its newest run, how
  many steps, and how it went. Under it, a row for each step that wasn't
  flagged, by the one line it said. A stack with more than eight such steps
  gets one row instead, naming the add-ons that ran and how many times, so a
  long stack doesn't bury the rest.
- **never run**: each stack with no run, and how many steps it has.
- **changed since its last run**: a stack whose steps are no longer the ones
  its last run ran, or that was given a file which has changed since. What
  that run said is old, and isn't handed on as if it were current.

A step's one line is its report's first line, when the run kept its report.
Otherwise it is the first line of what the step printed that isn't blank. A
step that printed lines meant for a program is said by how many. A step
whose output file is no longer there says so. A long line is cut at about
110 characters, with `…` where it was cut.

When nothing waits and nothing is flagged, the first line says so: an empty
hand-on gives its reason.

    handover: populated, dashboards: nothing waits on you and no step is flagged, 4 stacks run

A folder that holds no record is no project, so there was nothing to look
at. That is said too, naming the folder, as a report that couldn't look
(`unreachable`), not as an empty one.

**What it can't carry:** the why. It knows what ran and what each step said,
not why you ran it, what you were trying, or what you would do next. That
belongs in your own notes, beside this.

**Exit codes:** 0 nothing waits and nothing is flagged; 42 a suggestion
waits, a record's chain is broken, a step is flagged, or the folder holds no
record; 2 refused (a bad command line, or FOLDER isn't a folder).

**Uses:** the kernel's `read`, `sealed` and `declined`, through projects'
count of each record; projects' `find`, `tally`, `owner` and `stale`; stack's
`ended`.

**Never:** writes anything, reads your key, runs a stack, or approves or
declines a suggestion; those stay yours.
