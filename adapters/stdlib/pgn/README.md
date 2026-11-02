<!-- willow-addon
section: Reading more kinds of files
line: Chess games from PGN files: players, dates, openings and your annotations.
source: new
added: 2026-10-29
writes: to
network: none
-->
# pgn

Your chess games, searchable by who, when and what you said.

    python adapters/stdlib/pgn/pgn.py mirror --from FOLDER --to MIRROR

Each game is a paragraph: who played, when, at what event and where, the result
and the opening, and then every comment in the moves with the move it
follows. The moves themselves are not copied.

    game: Ada Example vs Cy Sample, 2024-03-03, Club Championship, Leeds
    result: 1-0 (Sicilian Defense, B20)
    note after 1.e4: My usual start.
    note after 14.Qd7: I missed the fork here.

A move is written with its number, and Black's with three dots (14...Qd7).
Brace comments and semicolon comments are kept whole; comments inside a
variation are kept, with the last main-line move before them. An unknown date,
event or site (the question marks a PGN uses) is left out, an unknown player is
a question mark, and an Annotator tag is kept. The Event, Site, Date, White,
Black, Result, Opening and ECO tags are used; a file with several games gives
several paragraphs.

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
