<!-- willow-addon
section: Reading more kinds of files
line: Goodreads and StoryGraph exports: the books you've read, when, and what you thought of them.
source: new
added: 2026-10-29
writes: to
network: none
-->
# goodreads

The books you've read, searchable by title, author, day, rating and what you said.

    python adapters/stdlib/goodreads/goodreads.py mirror --from FOLDER --to MIRROR

Each book of a Goodreads or StoryGraph library export is a dated line, oldest
first:

    2024-03-02  read The Hobbit by J.R.R. Tolkien  4/5  A comfort read. [fantasy, favourites]
    2024-03-09  reading Dune by Frank Herbert
    2023-12-01  to read Piranesi by Susanna Clarke

The date is when you finished the book (Date Read, Last Date Read); a book you
have not finished takes the day it was added. The verb is the shelf: read,
reading, to read, or gave up on for StoryGraph's did-not-finish. The rating is
out of five (a 0 is no rating); your review follows as written; shelves or tags
go in brackets. Private notes, ISBNs and page counts are not copied. Only a CSV
with `Title` and an `Exclusive Shelf` or `Read Status` column is read; other CSV
is skipped and counted.

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
