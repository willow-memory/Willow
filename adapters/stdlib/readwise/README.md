<!-- willow-addon
section: Reading more kinds of files
line: Readwise's highlights export: every highlight with its book or article, and your note on it.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# readwise

Your highlights, searchable by book, article, day and what you wrote beside them.

    python adapters/stdlib/readwise/readwise.py mirror --from FOLDER --to MIRROR

Each highlight of a Readwise export is a dated line, oldest first:

    2024-03-02  The Hobbit by J.R.R. Tolkien, location 120: "In a hole in the ground there lived a hobbit."  (note: the best opening)  [fantasy]
    2024-03-04  Staking tomatoes by Ana Lopez: "Tie the stem loosely."

The line has the day highlighted, the title and author, the location when the
export gives one, your highlight in quotation marks, your note in brackets and the
tags. A highlight with no text but a note is written as the note alone. The Amazon
book id, colour and other columns are not copied. Only a CSV with `Highlight` and
`Book Title` columns is read; other CSV is skipped and counted.

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
