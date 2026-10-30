<!-- willow-addon
section: Reading more kinds of files
line: Google Maps Timeline and other location exports: where you were, by day.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# location-history

Where you were, searchable by day and place.

    python adapters/stdlib/location-history/location_history.py mirror --from FOLDER --to MIRROR

Each place visited and each trip is a dated line, oldest first, with the hours
it covers:

    2024-03-02 08:15-09:10  Kitchen Cafe, 1 High St, Leeds
    2024-03-02 09:10-09:40  walking 1.5 km
    2024-03-02 12:00-17:30  HOME (45.123, 7.456)

Two shapes are read: the Takeout "Semantic Location History" months (an object
with `timelineObjects`) and the newer Timeline export (an object with
`semanticSegments`). A visit is named by its place name and address, or by its
kind of place and position when that is all the export gives; a trip is its
type in lower case and how far, when stated. A stay across midnight shows both
days. The times are the file's own, to the minute. Raw location points are not
read; other JSON is skipped and counted.

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
