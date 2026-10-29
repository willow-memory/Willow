<!-- willow-addon
section: Reading more kinds of files
line: Evernote's .enex files: each note as plain text with its notebook, tags and dates.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# evernote

Your Evernote notes, searchable, from a .enex export.

    python adapters/stdlib/evernote/evernote.py mirror --from FOLDER --to MIRROR

Each note is a paragraph with its title, notebook, dates and tags, then its
text:

    note: Allotment plan (notebook: Garden)
    created: 2024-03-03 10:15; updated: 2024-03-05 08:00
    tags: garden, plots
    from: Ada Example, https://example.org/plots
    attachments: plan.pdf

    Plot 14 gets the beans.
    [x] Order seed
    [ ] Fix the gate

The notebook is the export file's name, since a .enex file is one notebook or a
selection from one. A note's body is Evernote's own markup read as text:
paragraphs and line breaks kept, list items as "- ", checkboxes as [ ] and [x],
tables as their cells, and an attachment named but not read. Dates are
Evernote's UTC times written as year-month-day hour:minute. Notes keep the
file's order.

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
