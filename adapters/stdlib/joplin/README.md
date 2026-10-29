<!-- willow-addon
section: Reading more kinds of files
line: Joplin's .jex export, read without unpacking it: each note as plain text with its title and dates.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# joplin

Your Joplin notes, searchable with their notebook and dates.

    python adapters/stdlib/joplin/joplin.py mirror --from FOLDER --to MIRROR

Each note in the archive is written with its title, its notebook path and its
dates, then its text:

    note: Tomato notes
    notebook: Garden/Veg
    created: 2024-03-02; updated: 2024-03-05

    Plant out after the last frost.

A `.jex` is a tar archive and is read as one, without unpacking it to disk. The
notebook path is built from the notebooks' own parents. Notes in the trash, the
`key: value` metadata Joplin writes under each note, tags, pictures and other
resources are left out. Notes come in the order of their names in the archive;
a member over 5 MB is left out, and a file that is not a tar archive is
skipped and counted.

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
