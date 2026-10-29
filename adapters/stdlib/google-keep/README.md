<!-- willow-addon
section: Reading more kinds of files
line: Google Keep from Takeout: notes, lists and labels as dated passages.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# google-keep

Your Keep notes and lists, searchable with their day and labels.

    python adapters/stdlib/google-keep/google_keep.py mirror --from FOLDER --to MIRROR

Takeout gives one JSON file for each note. Each is written as:

    note: Shopping (2024-03-02)
    labels: home, food

    [ ] milk
    [x] eggs

The day is when the note was created, in UTC. A text note keeps its text; a
list keeps each item, with a tick for the ones done. The title is the note's
own, or "(untitled)", and an untitled note with nothing in it is not written.
Notes in the bin are skipped and counted, as is any JSON that is not a Keep note.
Pinned, archived, colour and attachments are not copied.

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
