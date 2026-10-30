<!-- willow-addon
section: Reading more kinds of files
line: Apple Health and Google Fit exports as daily numbers the readings add-on can trend.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# health

Your Apple Health export, as a table of daily numbers the readings add-on can read.

    python adapters/stdlib/health/health.py mirror --from FOLDER --to MIRROR

Apple Health's `export.xml` is written as a comma-separated table with a header
and one row for each day, oldest first, which is the form [readings](../readings/)
reads for "what moved this week":

    date,steps,walking km,heart rate,weight kg
    2024-03-02,8123,5.8,71,72.4
    2024-03-03,10442,,,

Steps, walking and running distance, active energy and exercise minutes are
summed over the day; heart rate and resting heart rate are the day's mean;
weight is the day's last reading. Miles become kilometres and pounds become
kilograms. A column no record fills is left out, and a day with no reading in a
column leaves the cell empty. The day is the record's start date as written.
Workouts, sleep and the rest are not read. The export is read as a stream, but
one over 400 MB, and one that declares entities, is not read. Google Fit's
exports are not read by this one.

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
