<!-- willow-addon
section: Reading more kinds of files
line: Home Assistant's history export: sensor readings as dated numbers the readings add-on can trend.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# home-sensors

Your Home Assistant sensors, as a table of daily numbers the readings add-on can read.

    python adapters/stdlib/home-sensors/home_sensors.py mirror --from FOLDER --to MIRROR

What Home Assistant's history API returns (a list with one list of states for
each entity) is written as a comma-separated table with a header and one row
for each day, oldest first, which is the form [readings](../readings/) reads for
"what moved this week":

    date,Kitchen temperature (C),Hall humidity (%)
    2024-03-02,21.4,48.5
    2024-03-03,20.9,

Each column is an entity, headed by its friendly name (else its entity id) and
its unit; each cell is the mean of that day's numeric states to one decimal
place. States that are not numbers (on, off, unavailable, unknown) are ignored
and an entity with no number is left out. The day is the state's `last_changed`
day as the file writes it. Other JSON is skipped and counted.

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
