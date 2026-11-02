<!-- willow-addon
section: Reading more kinds of files
line: Your Zotero library, from a copy of zotero.sqlite: items, notes and PDF annotations, each with its citation.
source: new
added: 2026-11-02
writes: to
network: none
-->
# zotero

Your Zotero library, searchable: each paper, each note and each highlight,
with the citation that says whose it is.

    python adapters/stdlib/zotero/zotero.py mirror --from FOLDER --to MIRROR

Put a copy of `zotero.sqlite` (from your Zotero data folder, with Zotero
closed) in FOLDER. Each item, note and PDF annotation becomes one passage
that begins with the item's citation, so a question about a paper, a note
or something you highlighted finds which paper it was:

    Example, Sample & Lee (2020). Tides of the Estuary. Journal of Tides.
    journal article, added 2021-03-04 10:22 UTC
    date: March 2020
    creators: Ada Example (author); Cy Sample (author); Bo Lee (author)
    doi: 10.1000/xyz123
    tags: estuaries, tides
    collections: Thesis / Chapter 2

    Example, Sample & Lee (2020). Tides of the Estuary. Journal of Tides, p. 12:
    “the tide turns twice a day” — check this against Lee
    highlight, yellow, made 2023-05-02 08:30 UTC

| Passage | Holds |
|---|---|
| an item | its citation (authors in Zotero's order, the year, the title, where it appeared), its type and when you added it, the date as written, every creator with their role, volume, issue, pages, ISBN, ISSN, DOI and URL, its tags and its collections |
| its abstract | the citation, then the abstract |
| a note | the citation of the item it belongs to, or "note:" for a standalone note; when it was written; the note's words, its formatting taken off |
| an annotation | the citation and the page, the highlighted text in quotes and your comment after a dash; its kind, colour and when it was made |

The year is read from the item's date field alone and never guessed: an item
with none is "(n.d.)", and its date line says "date: none". A citation names
five creators and then "et al."; the creators line names them all. Times are
Zotero's own, in UTC. A long note or abstract is cut into passages that each
start with the citation again, so no part of it loses whose it is.

Only regular items are passages, never attachments, notes or annotations as
items of their own, and nothing in the trash: an item in the trash takes its
notes and annotations with it, and a collection in the trash is not named.
An RSS feed's items are not your library and are left out. An ink or image
annotation with no text is left out and counted on the last line:

    left out: 2 annotations with no text (image 1, ink 1)

A file is read when its name ends in .sqlite and it holds Zotero's tables
(items, itemData, itemDataValues, fields, itemTypes, creators, itemCreators,
creatorTypes, itemNotes and deletedItems); any other .sqlite file is left
alone, skipped and counted. It is opened read-only and immutable, so SQLite
writes no journal or WAL file beside it and FOLDER is unchanged. Hidden
folders and files are skipped. Each library is written to MIRROR at the same
relative path with .txt added, as `MIRROR/<same path>.sqlite.txt`:

    wrote 1 files to MIRROR; skipped 0

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`), its
`MAX_CHUNK` and `html_text`; Python's standard library (`sqlite3`) for the
format.

**Never:** writes inside FOLDER, changes the library, writes anything outside
MIRROR, or goes online.
