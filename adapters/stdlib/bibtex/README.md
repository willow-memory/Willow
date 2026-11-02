<!-- willow-addon
section: Reading more kinds of files
line: .bib files: each reference as a passage, so you can ask which paper said it and get its key.
source: new
added: 2026-10-29
writes: to
network: none
-->
# bibtex

Your bibliography, searchable, with the key to cite.

    python adapters/stdlib/bibtex/bibtex.py mirror --from FOLDER --to MIRROR

Each reference becomes one paragraph that begins with its citation key, so a
question about a paper finds the key to cite:

    smith2020 (article): Tides of the Estuary, 2020
    by Example, Ada; Sample, Cy
    in Journal of Made-Up Studies, 12(3), pages 45--67
    doi: 10.1000/xyz123
    keywords: tides, estuaries
    abstract: We measure the tide at six harbours.

Braces and quotes round a value are taken off, `#` joins pieces, an `@string`
macro is filled in (and the three-letter month names), and the common LaTeX
accents (an umlaut, an acute, the German sharp s, an escaped ampersand, a tie)
are read as the letters they make; a logo like LaTeX keeps its name. Authors are
split at "and". `@comment` and `@preamble` are skipped, text between entries is
ignored, and a byte-order mark is fine. Only the fields above are kept: title,
authors, editors, where it appeared, volume, pages, doi, url, keywords,
abstract and note.

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
