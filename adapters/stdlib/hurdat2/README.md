<!-- willow-addon
section: Reading more kinds of files
line: NOAA's hurricane track file (HURDAT2) with each storm's name and id on every track row, so 'Maria' finds Maria's rows.
source: new
added: 2026-11-12
version: 0.1.0
writes: to
network: none
role: reads
output: mirror
reads: .txt
-->
# hurdat2

NOAA's hurricane database, one track row at a time, each row saying whose it
is: the Atlantic file with 1,988 storms since 1851, or the Pacific one.

    python adapters/stdlib/hurdat2/hurdat2.py mirror --from FOLDER --to MIRROR

HURDAT2 names a storm once, on a header line, and the rows under it are
numbers and codes. A question naming "Maria" finds none of Maria's rows, and
the rows a question about "landfall" does find belong to no one. Here the
header is the first passage of its storm and every row starts with the
storm's name and id:

    [52489] MARIA AL152017; 68 track rows, 2017-09-16 to 2017-10-02; each row: date time UTC; status; record; position; wind kt; pressure mb

    [52508] MARIA AL152017; 2017-09-20 10:15; hurricane; landfall; 18.0N 65.9W; 135; 920

So "Maria hurricane landfall 2017-09-20" finds the row above, and not
another storm's. The number in brackets is the line of the source file, so
the row is found again in it; the places are written beside the mirror as
the mirror contract asks.

- **The labels once.** "wind kt" and "pressure mb" are on the header, never
  in a row: the kernel serves a passage holding half a question's words, so
  a label in every row would let a question about something the file lacks
  be answered by an unrelated row. The cost: a question that is only
  labels ("wind pressure") finds headers.
- **Two codes in words.** The status (`HU` hurricane, `TS` tropical storm,
  and the rest of NHC's list) and the record identifier (`L` landfall, `I`
  peak intensity, and the rest) are written as NHC's format document names
  them; a code not on those lists is kept as written.
- **Values as written.** Position, wind in knots, pressure in millibars; a
  missing value (-99, -999) is an empty cell. An unnamed storm is its id.
- **Not carried:** the wind-radii columns (the 34, 50 and 64-knot radii by
  quadrant).
- **A long file in parts.** The kernel reads no more than a megabyte of a
  file, so the Atlantic file (7 MB) is written as six parts,
  `<name>.part0.txt` and on, cut between storms.
- **Skipped and counted, never repaired:** a text file that isn't UTF-8, whose
  first line isn't a storm header, or whose header counts rows that aren't
  the rows that follow. Any other text file in the folder is left to
  [text](../text/).

On the Atlantic file, the question "Maria hurricane landfall 2017-09-20 UTC"
puts the row above first (10:15 UTC, 135 knots, about 155 mph), and a
second Maria row, her landfall on Dominica the day before. Both are in the
file; the Spanish and English Wikipedia pages on the storm give the same
hour and speed for Puerto Rico.

It only reads; the same bytes give the same mirror. Exit codes, the kernel's:
0 wrote some; 42 nothing readable; 2 refused.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, guesses a code, a value or an encoding, or goes online.
