<!-- willow-addon
section: Reading more kinds of files
line: jrnl journals: each [YYYY-MM-DD HH:MM] entry as a dated passage.
source: new
added: 2026-10-27
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# jrnl

Your [jrnl](https://jrnl.sh) journals as plain text the kernel reads: each
entry one dated paragraph, so "when did I last oil the gate" finds the day
you wrote it down.

```
python adapters/stdlib/jrnl/jrnl.py mirror --from FOLDER --to MIRROR

2024-03-03 10:15  Fixed the gate.
The hinge wanted oil, not force.

2024-03-04 09:00  Rain all day.
```

**A journal is known by its own stamp.** A .txt file whose first line that
says anything opens with jrnl's `[YYYY-MM-DD HH:MM]` is a journal; any
other .txt is someone else's and is skipped, counted, never guessed at.
Each entry keeps its order in the file, the stamp's brackets come off so
the kernel reads the date, and blank lines inside an entry close up so the
entry stays one passage. A stamp with seconds is kept as written.

Each journal is written to MIRROR at the same relative path with .txt
added. FOLDER is only read: originals are never modified, nothing is
written inside it, and hidden files and folders are never read. A file that
cannot be read is skipped and counted, never a crash.

It keeps [the readers' contract](../ci/test_contract.py): the same folder
gives the same bytes, and `wrote N files to MIRROR; skipped M` says what
happened. Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2
refused (FOLDER is not a folder, or MIRROR and FOLDER are inside one
another).

Point the kernel at MIRROR (`kernel.py init --pile MIRROR ...`) to ask
questions of your journal.

**Uses:** the kernel's exit codes; the mirror is for `chunks` to read.

**Never:** changes your files; writes outside MIRROR; reads a hidden file;
guesses at a .txt that wears no stamp.
