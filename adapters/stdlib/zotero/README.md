<!-- willow-addon
section: Reading more kinds of files
line: Your Zotero library, from a copy of zotero.sqlite: items, notes and PDF annotations, each with its citation.
source: new
added: 2026-11-02
writes: to
network: none
role: reads
reads: zotero.sqlite
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
    2021-03-04 10:22
    March 2020
    Ada Example; Cy Sample; Bo Lee; Di Moss
    12(3), 45-67
    10.1000/xyz123
    estuaries, tides
    Thesis / Chapter 2

    Example, Sample & Lee (2020). Tides of the Estuary. Journal of Tides, at 12:
    “the tide turns twice a day” — check this against Lee
    2023-05-02 08:30

| Passage | Holds, one line each when it has one |
|---|---|
| an item | its citation (authors in Zotero's order, the year, the title, where it appeared); when you added it; its date as written; every creator; volume(issue), pages; place; ISBN; ISSN; DOI; URL; the rest of where it appeared (a book section's publisher); its tags; its collections |
| its abstract | the citation, then the abstract |
| a note | the citation of the item it belongs to, or for a standalone note its own first line; when it was written; its tags; the note's words, its formatting taken off |
| an annotation | the citation and "at" the page; the highlighted text in quotes and your comment after a dash; when it was made; its tags |

Only the library's own words and numbers are written, and times as digits
(Zotero's own, in UTC): no labels ("doi:", "tags:"), no "added", no type,
role or colour words. A word written into nearly every passage would let a
question about something the library doesn't hold ("doi volcano") be
answered by any of them, and a wrong answer is worse than none.

The year is read from the item's date field alone and never guessed: an item
with none has no year in its citation and no date line. A citation names
five creators and then "et al."; the creators line names them all. A long
note or abstract is cut into passages that each start with the citation
again, so no part of it loses whose it is.

The cost, measured: "when did I add Tides of the Estuary" or "the DOI of
Tides of the Estuary" finds that paper, but when it has newer notes or
highlights those come first, and the item with the date or DOI may not be
among the three served. And a paper with many notes and highlights puts its
citation in most passages of the mirror, so a question naming one of its
authors and something the library doesn't hold is served that paper.

Only regular items are passages, never attachments, notes or annotations as
items of their own, and nothing in the trash: an item in the trash takes its
notes and annotations with it, and a collection in the trash is not named.
An RSS feed's items are not your library and are left out. An ink or image
annotation with no text is left out and counted in a passage of its own at
the end, and a library with nothing in it says so:

    2 annotations with no text: 1 image, 1 ink

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
