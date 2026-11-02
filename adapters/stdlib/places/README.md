<!-- willow-addon
section: Reading more kinds of files
line: KML and GeoJSON files: each place's name, note and coordinates as a passage.
source: new
added: 2026-10-29
writes: to
network: none
-->
# places

Your saved places, searchable by name and by what you wrote about them.

    python adapters/stdlib/places/places.py mirror --from FOLDER --to MIRROR

Each place becomes a paragraph, so a question about a place finds its name,
your note on it, and where it is. Three kinds of file are read, by extension:
.kml, .geojson and .gpx.

    place: Allotment (Leeds / Plots)
    note: Plot 14, the gate sticks.
    at 53.80080, -1.54910

| File | Each place is | Its note is |
|---|---|---|
| KML | a Placemark, with the folders it is in | the description, HTML taken off |
| GeoJSON | a Feature, named by name, title or label | description, note, comment, text or address |
| GPX | a waypoint, route or track | the description and comment |

A point is written as latitude then longitude, five decimals. A line or an area
is written as its kind and its first point ("line of 120 points from ..."); the
rest of its shape is not copied. A place with no name is "unnamed place".

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
