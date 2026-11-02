<!-- willow-addon
section: Reading more kinds of files
line: Strava's export and GPX files: each run, ride and walk as a dated line with its distance and time.
source: new
added: 2026-11-02
writes: to
network: none
-->
# strava

Your runs, rides and walks, each as one line you can ask about.

    python adapters/stdlib/strava/strava.py mirror --from FOLDER --to MIRROR

It reads Strava's bulk export (its activities.csv and the activity files
beside it) and any GPX or TCX file, from Strava, a watch or another app. Each
activity is a paragraph of its own, opening with its line: when it started
(date, clock and zone), its name, its distance in km, and its time as
H:MM:SS. A row's description, private note and gear follow, each on its own
line:

    2024-03-03 07:15Z Harbour Loop, 5.2, 0:28:14
    Easy, legs fresh
    Pegasus 40

| File | One line for | Distance | Time |
|---|---|---|---|
| activities.csv | each row, in the file's order | the later "Distance" column, in metres | the first "Elapsed Time" column, in seconds |
| .gpx, .gpx.gz | each track | haversine between consecutive points, within each segment | elapsed: first point's time to the last, pauses included |
| .tcx, .tcx.gz | each Activity, with its Notes | its laps' DistanceMeters added up | its laps' TotalTimeSeconds added up (the device's timer, pauses left out) |

**Only the file's own values.** No type word, unit, label, or weekday or
month name is added: a word written into every passage would let a question
about something your files don't hold ("when did I run a marathon") be
answered by any run. The cost: a question that only names the type or a
unit ("my rides in March", "how many km") finds an activity only where its
name, notes or date hold the words you ask with; "Morning Run", Strava's
default name, does.

**activities.csv** is known by its header ("Activity ID", "Activity Date",
"Activity Type"); any other CSV in the folder is not read. Its header names
"Distance" twice: the first is in your display units (and a swim's is metres
there), so the later one, always metres, is the one used; a file without it
gives no distance rather than a guessed unit. Its "Activity Date"
(`Mar 3, 2024, 7:15:22 AM`) is in UTC. A date written any other way is kept
as written.

**GPX** tracks are named by their `<name>`. A GPX of waypoints only has no
activity here; [places](../places/) reads those. A track whose points have
no time has no date: the file's own `<time>` is when the file was made, not
when you set off.

**Times** are in the zone the file gives: Z is UTC, and +01:00 stays +01:00.
A time with no zone is shown as written, and no zone is ever guessed. A
distance of a kilometre or more is to one decimal place, a shorter one to
two (0.64). A value the file doesn't give (a date, a distance, a time) is
written as "?".

**.fit files** (and .fit.gz) are a binary format this doesn't read: each is
skipped, counted, and the first is named on stderr. In Strava's export, the
same activities are in activities.csv.

Each file is written to MIRROR at the same relative path with .txt added
(activities/123.gpx.gz becomes `MIRROR/<same path>.txt`). FOLDER
is only read: hidden folders and files are skipped, and nothing is written
inside it. A file with no activity, or that can't be read, is skipped and
counted, never a crash; a .gz that opens to more than 256 MB is skipped:

    wrote 2 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`); Python's
standard library for the formats.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, guesses a time zone or a unit, or goes online.
