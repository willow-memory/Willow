# A study, for agents

A result tested against what anyone can rerun, as in
[demo/php2shell/README.md](../../demo/php2shell/README.md). Part of
[AGENTS.md](../../AGENTS.md).

## The rules

- **Freeze first.** The source hashes, the questions, the hit rule and every
  pass rule go in a FROZEN.json held by a test, as
  `demo/php2shell/FROZEN.json` is, committed alone before any question is
  asked. That commit is the pre-registration; a later change is a new freeze,
  with its reason.
- **Find the bugs without the results.** Run the pipeline once with every
  question replaced by nonsense ("qqqq zzzz"), so wiring breaks show up before
  the freeze, and say in the README what that dry run could see.
- **Verdicts are kernel rows**, one per pass rule, appended to a box outside
  the repo with the answers' and tools' SHA-256; `kernel.py verify` on it
  goes in the README.
- **Sources that aren't the repo's** (news, a company's pages) are kept by
  address, time and SHA-256, never their text, with a script that fetches
  them again and checks the hashes offline.
- **Write down what failed** with its frozen numbers, beside what held, and
  what was written after reading the sources.

## What a dry run misses

- **A dry run that serves nothing exercises nothing after the kernel.**
  Nonsense finds no passage, so a step that only runs on a served passage (a
  model asked to answer from it, a check of what it holds) is never called,
  and its wiring goes untested. Give such steps, in the dry run only, a box
  of one nonsense passage the dry run's questions find.
- **A passage that asks its question back is an echo, and the kernel serves
  no echo** ([searching.md](searching.md) says exactly when). A dry-run passage
  holding the nonsense question's words in a row, in order, comes back as
  `"state": "echo"`, not as an answer: put its words in another order.
- **A dry-run verdict must never read as the study's.** Name its rows apart
  (`study:dry:R1`) on the same box, or use another box.

## Boxes a study makes

- **A words list the kernel reads is its owner's alone.** `kernel.py init
  --words FILE` refuses a file anyone else can read (`chmod 600` it), and git
  can't keep that mode: copy a words list the study keeps in the repo to its
  work folder, made private, and point the box there.
- **A box, its key and the pile it reads all live outside the repo.** The
  study's scripts take their places as arguments.

## What came from outside

- **A model's or a person's input read before the freeze is said plainly**,
  by its SHA-256, with what (if anything) was changed after reading it.
- **Code from outside the repo is run only with the person's say**, in a
  folder of its own, its libraries in a virtual environment there, so the
  repo's own Python isn't changed under a running job.
