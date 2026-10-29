<!-- willow-addon
section: Reading more kinds of files
line: Day One's JSON export: each journal entry as a dated passage, with its place and weather.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# day-one

Your Day One journal, searchable with its dates, places and weather.

    python adapters/stdlib/day-one/day_one.py mirror --from FOLDER --to MIRROR

Each entry is a dated passage, oldest first, with the place, weather and tags
Day One kept:

    2024-03-02 08:15  Kitchen, Leeds, United Kingdom  cloudy 8°C  #garden  starred

    Planted out the tomatoes.

The text is Day One's Markdown with its backslash escapes undone. The place is
its name, locality, area and country without repeats; the weather is the
description and the temperature. An entry with no text is left out; photos,
audio and the other fields are not copied. Only a JSON file that is a Day One
export (a `metadata` and a list of `entries`) is read; other JSON is skipped and
counted.

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
