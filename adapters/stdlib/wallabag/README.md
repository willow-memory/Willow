<!-- willow-addon
section: Reading more kinds of files
line: wallabag's JSON or HTML export: saved entries as plain text, with their tags.
source: new
added: 2026-10-29
writes: to
network: none
-->
# wallabag

Your wallabag articles, searchable with their tags and highlights.

    python adapters/stdlib/wallabag/wallabag.py mirror --from FOLDER --to MIRROR

Each entry is written, oldest first by the day it was saved, with its title,
URL, tags and highlights, then the article's text:

    2024-03-02  Tomato growing guide
    url: https://example.org/tomatoes
    tags: garden, veg
    highlight: "Stake early." (note: do this in April)

    Plant after frost.

The article is wallabag's saved HTML read as the kernel reads a page: scripts,
styles and tags out, entities read. An entry with no title is named by its URL.
Your annotations are kept as highlights with the note written on them. The
reading time, language and archived or starred marks are not copied. Only a
JSON file that is a list of entries with a `url` and a `content` is read (the
HTML export is not); other JSON is skipped and counted.

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
