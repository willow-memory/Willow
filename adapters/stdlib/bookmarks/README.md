<!-- willow-addon
section: Reading more kinds of files
line: Browser bookmarks (HTML export, Firefox JSON) and history, read from a copy of its SQLite file.
source: new
added: 2026-11-02
writes: to
network: none
-->
# bookmarks

Your browser's bookmarks and history, so you can ask when you saved or last
looked at a page about something.

    python adapters/stdlib/bookmarks/bookmarks.py mirror --from FOLDER --to MIRROR

Each bookmark is one passage, in the browser's own order, with the day it was
added, its title, URL, folder, tags and description:

    2024-03-02  bookmarked  Tomato growing guide
    url: https://example.org/tomatoes
    folder: Bookmarks Toolbar / Garden
    tags: garden, veg
    description: Staking and pruning, step by step.

Each page in a history is one passage too, not one line per visit, so a page
read fifty times is still one answer: its last visit, how many visits, and the
days it was visited (the newest twenty, or fewer when a long address would
cut the passage in two for the kernel; older days are counted, not listed).
Pages come oldest last visit first:

    2024-03-05  visited  Tomato blight: what to do
    url: https://example.org/blight
    visits: 3, last 2024-03-05 15:02 UTC
    days: 2024-03-01, 2024-03-05

| Read | Recognised by | Its times |
|---|---|---|
| the bookmark HTML export every browser writes | `<!DOCTYPE NETSCAPE-Bookmark-file-1>` | Unix seconds |
| a Firefox bookmarks backup, .json or compressed .jsonlz4 | its text/x-moz-place nodes | microseconds since 1970 |
| the `Bookmarks` file of Chrome, Chromium, Edge or Brave | its `roots` with `bookmark_bar` and `other` | microseconds since 1601 |
| a copy of Firefox's `places.sqlite`: its bookmarks, then its history | its `moz_places` and `moz_historyvisits` tables | microseconds since 1970 |
| a copy of Chrome's `History` | its `urls` and `visits` tables | microseconds since 1601 |

A file is read for what it holds, whatever its name; any other file is left
alone and not counted. Days are UTC. A bookmark with no date says `no date`;
one with no title says `(no title)`. Firefox's saved searches (`place:`
addresses), separators and its tag folders are not bookmarks; a bookmark's
tags are kept on it. A history leaves out the pages a browser hides, and
visits to a page's frames or embedded parts, which you did not make. When a
browser has let a page's visits expire but kept its count and last visit,
those are kept and no days are listed.

The databases are opened read-only and immutable, so nothing is written
beside them. Close the browser before you copy one: visits it hasn't saved
yet are in a `-wal` file beside the database, which is not read.

Each file is written to MIRROR at the same relative path with .txt added.
A mirror bigger than the kernel reads from one file (1 MB) is cut between
passages into parts it can read, `<name>.txt`, then `<name>.part2.txt` and
on; parts a shorter earlier run left behind are removed.
FOLDER is only read: hidden folders and files are skipped, and nothing is
written inside it. A file that is one of these but can't be read, or that
holds no bookmark or page, is skipped and counted, never a crash:

    wrote 2 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`) and
`MAX_FILE`; Python's standard library for the formats, including SQLite and
the LZ4 decompression a .jsonlz4 needs.

**Never:** writes inside FOLDER, modifies an original, opens a database for
writing, writes anything outside MIRROR, or goes online.
