<!-- willow-addon
section: Ways to use it
line: First run in one step: asks where your files are, sets up willow's record and your key, copies in a starter words list, and prints a double-click launcher.
source: new
added: 2026-10-24
writes: record, to
network: none
tags: everyday
-->
# start

Willow set up in one step, without typing three paths.

    python adapters/stdlib/start/start.py

In a terminal it asks two things: where your files are, and where willow
should keep its own (Enter for `~/willow`). Or say both at once:

    python adapters/stdlib/start/start.py --pile ~/Documents --to ~/willow

| Made under `--to` | What it is |
|---|---|
| box/ | The record, made by the kernel's own `init` |
| `key` | Your key, readable only by you. It approves answers. |
| my-words.txt | The [starter-words](../starter-words/) list, yours to edit |

Then it tells you how to open your folder in your browser
([browse](../browse/)), prints a file to double-click next time, and says
how to back it up ([backup](../backup/)).

**Refused:**
- a `--to` inside your files, or willow would read its own record as one of them;
- a `--to` that already holds a box, which it leaves alone and tells you how to open;
- files that aren't a folder.

Asked in a terminal, it runs the same command line it would have been typed
with, so what it may write is always under `--to`.

**Uses:** the kernel's `init`; starter-words' `copy`; browse's `launcher`.
Each sibling is optional: without one, it says so and sets up the rest.

**Never:** writes outside `--to`, or touches your files.
