# Trial 2: the rules, written before any agent was started

Not the study. [Trial 1](../trial-1/RESULTS.md) asked agents closed
questions about a run. This one lets them build: each link of a chain adds
a step to a stack, from the built add-ons, and the script runs it.

- **The start** is a fresh box over [demo/kept](../../kept/README.md)'s
  pinned pile and the first seven steps of its stack, run once.
  [chain.py](../chain.py) makes it.
- **What a link is handed** is one page and nothing else:
  [the brief](brief.txt); the line the hook-handoff add-on gives a new
  session about the one before; what the handover add-on says of the
  project; the stack as it stands; and the 266 built add-ons a stack can
  run, each with its card's line. [handoff-1.txt](handoff-1.txt) is the
  first link's page, whole.
- **What a link may do**: read up to two add-on cards, and reply with one
  want, one step and one why. The script, not the link, puts the step on
  the stack and runs it.
- **What the script refuses**, leaving the stack as it was: a step that
  names no built add-on a stack can run, that is already on the stack,
  that names a seal, a proposal or a key, or that names a path of its own.
- **After each link** the script has hook-handoff write the link's Stop row
  on the record, so the next link is told by the record, not by the link.
- **Three links**: the smallest model, one size up, the smallest again.
  The want each link is working to is the person's own sentence, in the
  brief.

What will be counted, with no threshold:

- **U1**: steps offered that the script refused, and why.
- **U2**: of the steps added, how each ended: clean, flagged, a bad command
  line, or not run.
- **U3**: steps offered that were already on the stack.
- **U4**: for each link, whether the add-on it chose and each figure in
  its why are on the page it was handed.
- **U5**: rows on the record when the chain ends: one handoff row a link.
- **U6**: whether each step is the next thing the stack needs, read by a
  person afterwards. This is a judgement, and is said as one.

What it cannot show: a link is started in this repository and can read
more than the brief allows. It is asked which cards it read, and nothing
checks its answer. One run of each link says it can happen, not how
often.
