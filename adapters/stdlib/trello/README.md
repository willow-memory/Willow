<!-- willow-addon
section: Reading more kinds of files
line: A Trello board's JSON export: cards, checklists and comments, by list.
source: new
added: 2026-10-29
writes: to
network: none
-->
# trello

Your Trello boards, searchable by list, card and comment.

    python adapters/stdlib/trello/trello.py mirror --from FOLDER --to MIRROR

A board is written as its name, then each open list with its open cards:

    board: Garden

    list: To do
    - Stake the tomatoes (due 2024-03-09) [urgent, veg]
      Use the long canes.
      checklist Tools: [x] canes, [ ] twine
      comment 2024-03-02 Ana: Borrow Ben's.

A card keeps its name, due day, label names, description, checklists (each item
ticked or not) and its comments, oldest first, with the day and who wrote them.
Archived lists and cards are left out, as are members, attachments and custom
fields. Only a JSON file with `lists` and `cards` is read; other JSON is skipped
and counted.

Each file is written to MIRROR at the same relative path with .txt added.
FOLDER is only read: hidden folders and files are skipped, and nothing is
written inside it. A file that can't be read is skipped and counted, never a
crash:

    wrote 2 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`); Python's
standard library for the format.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, or goes online.
