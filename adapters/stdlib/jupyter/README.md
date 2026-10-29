<!-- willow-addon
section: Reading more kinds of files
line: Jupyter notebooks: Markdown cells, code and text outputs as passages, cited by cell.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# jupyter

Your notebooks, searchable, cell by cell.

    python adapters/stdlib/jupyter/jupyter.py mirror --from FOLDER --to MIRROR

Each notebook becomes text with one block for each cell, headed by its number
and kind, so a passage is cited by its cell:

    notebook: Tide analysis (python3, python)

    cell 1 (markdown)
    # Tides at the estuary

    cell 2 (code)
    df = load("harbours.csv")
    output:
    6 rows

A cell's source is written as it is. A code cell's text outputs follow under
"output:": printed text, a result's plain-text form, and an error's name and
message; the first 20 lines of each, and how many more. Pictures and other
binary outputs are left out, not guessed at. Raw cells are written as "raw",
and a cell with no source and no output is left out. Notebooks in the older
nbformat 3 are read too. The .ipynb_checkpoints folders Jupyter keeps are
skipped like any hidden folder.

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
