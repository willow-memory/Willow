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
activity is a paragraph of its own, opening with its line:

    2024-03-03 run: Harbour Loop, 5.2 km in 0:28:14 (Sunday 3 March 2024, started 07:15 UTC)
    description: Easy, legs fresh
    gear: Pegasus 40

| File | One line for | Distance | Time |
|---|---|---|---|
| activities.csv | each row, in the file's order | the later "Distance" column, in metres | the first "Elapsed Time" column, in seconds |
| .gpx, .gpx.gz | each track | haversine between consecutive points, within each segment | elapsed: first point's time to the last, pauses included |
| .tcx, .tcx.gz | each Activity | its laps' DistanceMeters added up | its laps' TotalTimeSeconds added up (the device's timer, pauses left out) |

**activities.csv** is known by its header ("Activity ID", "Activity Date",
"Activity Type"); any other CSV in the folder is not read. Its header names
"Distance" twice: the first is in your display units (and a swim's is metres
there), so the later one, always metres, is the one used; a file without it
says "distance not given" rather than guess a unit. Its "Activity Date"
(`Mar 3, 2024, 7:15:22 AM`) is in UTC. A date written any other way is kept
as written. A row's description, private note and gear are under its line.

**GPX** tracks are named by their `<name>` and typed by their `<type>`.
Strava's older GPX writes the type as a number, kept as written ("activity
(type 9)"); its name usually says it ("Morning Run"). A GPX of waypoints only
has no activity here; [places](../places/) reads those. A track whose
points have no time says "date not given": the file's own `<time>` is when
the file was made, not when you set off.

**Types** are the words a person says: Run is "run", Ride and Biking are
"ride", Virtual Ride is "virtual ride", TrailRun is "trail run".

**Times** are in the zone the file gives: Z is UTC, and +01:00 stays +01:00.
A time with no zone is shown as written, and no zone is ever guessed. A
distance of a kilometre or more is in km to one decimal place, a shorter one
in whole metres. What a file doesn't give is said: "distance not given",
"time not given", "date not given".

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
