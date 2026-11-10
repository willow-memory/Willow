<!-- willow-addon
section: Reading more kinds of files
line: Google Takeout's My Activity and YouTube history, JSON or HTML, as dated lines.
source: new
added: 2026-11-02
version: 0.1.0
writes: to
network: none
role: reads
reads: .json, .html
-->
# takeout

What you searched for and watched, from a Google Takeout export, one dated line
for each.

    python adapters/stdlib/takeout/takeout.py mirror --from FOLDER --to MIRROR

Point it at the unpacked Takeout folder. It reads every My Activity file
(`My Activity/<Product>/MyActivity.json`, or `.html`) and YouTube's watch and
search history (`YouTube and YouTube Music/history/<watch or search>-history`,
JSON or HTML), and writes each activity as a line:

    2024-03-03 10:15 Searched for leek soup

    2024-03-02 19:40 Watched Leek and potato soup in 10 minutes (Soup Kitchen)

    2024-03-01 07:59 Watched Garden hose 50% off [From Google Ads]

A file is told by what it holds, not by its name: a JSON list of activities
(each with a `header`, the product, and a `title`), or an HTML page of
`outer-cell` blocks. Any other JSON or HTML in the export is left alone and
counted as skipped. Keep notes are read by [google-keep](../google-keep/) and
Maps Timeline by [location-history](../location-history/); this reads neither.

**When.** A JSON time is in UTC and is written so, to the minute. An HTML date
is in your account's time zone and language: an English one (`Mar 3, 2024,
10:15:22 AM GMT`, or `3 Mar 2024, 10:15:22 GMT`) is written to the minute as
it reads. When a zone other than GMT or UTC appears, the zones the file uses
are named once, in a passage of their own at the top (`time zone: CET, CEST`),
so a line's time is the local one and which of those zones it was in is not
said beside it. A date in another language, or one that doesn't read in full,
is kept as written in brackets (`[3 mars 2024, 10:15:22 UTC]`), never guessed.

**Only what the file says.** The title as Google wrote it, then its subtitles
(a watch's channel) in brackets and its details (`From Google Ads`) in square
brackets. Nothing is added to every line: no product name (the file's path
holds it), no labels, and no placeholder for a missing part. An activity with
no date starts with its title, one with no title is its date, and one with
neither is left out. Links, the products list, the activity controls and
places are not copied.

**One activity, one passage.** Each line has a blank line after it, so the
kernel takes each activity as its own passage. It serves a passage holding
half of a question's words, so "when did I search for leek soup" is answered by
the line that holds the search and its date. Lines run together would make
passages of eight or so activities, and one holding "soup" in one line and
"leek" in another would be served for a search that never happened. For the
same reason no word of this reader's is in every passage: one would be half of
any two-word question, and would serve an activity for something the export
doesn't hold. The words that do repeat are Google's own ("Searched for",
"Watched") and the file's path: every passage under `My Activity/Search`
holds "search", so a visit to a leek soup page is served beside the search
itself.

Each file is written to MIRROR at the same relative path with .txt added,
in the file's own order (Takeout's is newest first). Years of YouTube history
make a mirror bigger than the kernel reads from one file (1 MB), so a big one
is cut between activities into `<name>.txt`, `<name>.part2.txt` and on; parts
an earlier, longer run left are removed. FOLDER is only read: hidden folders
and files are skipped, and nothing is written inside it.

    wrote 3 files to MIRROR; skipped 2

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`) and its
`MAX_FILE`; Python's standard library for JSON and HTML.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, or goes online.
