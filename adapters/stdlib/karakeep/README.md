<!-- willow-addon
section: Reading more kinds of files
line: Karakeep's JSON export: bookmarks, notes and tags as plain text.
source: new
added: 2026-10-29
writes: to
network: none
-->
# karakeep

Your Karakeep bookmarks, searchable with their notes and tags.

    python adapters/stdlib/karakeep/karakeep.py mirror --from FOLDER --to MIRROR

Each bookmark is written, oldest first, with its day, title, URL, tags, your
note and Karakeep's summary, then the page's description (or, for a text
bookmark, its text):

    2024-03-09  Tomato growing guide
    url: https://example.org/tomatoes
    tags: garden, veg
    note: Read the section on staking.

    A guide to tomatoes.

The day is when the bookmark was created: Unix seconds or milliseconds, or an
ISO date. A bookmark with no title, URL or text is left out. Archived and
favourite marks, images and the saved copy of the page are not copied. Only a
JSON file with a `bookmarks` list is read; other JSON is skipped and counted.

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
