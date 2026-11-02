<!-- willow-addon
section: Reading more kinds of files
line: Kindle "My Clippings.txt" highlights and .epub text.
source: new
added: 2026-10-23
writes: to
network: none
-->
# books

Your Kindle highlights and your epub books, as plain text the kernel can ask
questions of.

    python adapters/stdlib/books/books.py mirror --from FOLDER --to MIRROR

A highlight or note from a Kindle "My Clippings.txt" becomes one paragraph,
dated by its "Added on" day, with its page (or location, if it has no page):

    2024-03-03  Made-Up Harbour (Ada Example), page 12
    The tide keeps its own calendar.

Books are sorted by title and each keeps its order in the file. A bookmark has
no text, so it is skipped. A highlight whose date can't be read is written as
`undated`.

An epub becomes its text in reading order, with scripts and styles dropped and
each block element as its own paragraph. The first line names the book:

    book: Made-Up Almanac by Cy Sample

Each file is written to MIRROR at the same relative path with .txt added: a
clippings file at `kindle/My Clippings.txt` becomes `kindle/My Clippings.txt.txt`
under MIRROR. A file that can't be parsed is skipped and counted. Point the
kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`) in
`books.py`; the tests run the kernel's `init` and `bite` on the mirror
(`kernel.py`). No kernel function is called by the mirror itself.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, or goes online. English "Added on" dates only.
