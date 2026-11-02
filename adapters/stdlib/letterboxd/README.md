<!-- willow-addon
section: Reading more kinds of files
line: Letterboxd's export: the films you've watched, your ratings and reviews, as dated lines.
source: new
added: 2026-10-29
writes: to
network: none
-->
# letterboxd

The films you've watched, searchable by title, year, rating and what you said.

    python adapters/stdlib/letterboxd/letterboxd.py mirror --from FOLDER --to MIRROR

Each row of a Letterboxd export's CSV files is a dated line, oldest first:

    2024-03-02  watched Heat (1995)  4.5/5  rewatch  [crime, night]
    2024-03-04  rated Alien (1979)  5/5
    2024-03-09  watched Paddington 2 (2017)  4/5  Funnier than it has any right to be.

A row with a watched date is "watched", dated by when it was watched rather than
logged; one with a rating and no watched date is "rated"; the rest (the watchlist
and watched lists) are "listed". The rating is out of five as Letterboxd gives it.
A review follows as written, and tags go in brackets. Only a CSV with `Name` and
`Letterboxd URI` columns is read; any other CSV is skipped and counted.

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
