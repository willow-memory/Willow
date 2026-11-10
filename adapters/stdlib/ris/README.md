<!-- willow-addon
section: Reading more kinds of files
line: RIS citation exports from EndNote, Zotero, Mendeley and the journal databases: each reference as a passage that opens with its citation.
source: new
added: 2026-11-02
version: 0.1.0
writes: to
network: none
role: reads
reads: .ris, .enw
-->
# ris

Your reference library, searchable, each paper with the citation it reads as.

    python adapters/stdlib/ris/ris.py mirror --from FOLDER --to MIRROR

RIS is what EndNote, Zotero, Mendeley, Web of Science, Scopus and Google
Scholar export when you ask for citations: lines like `TY  - JOUR` and
`AU  - Example, Ada`, each reference ending at `ER  -`. Each reference becomes one
paragraph that opens with its citation, so a question about a paper finds who
wrote it, when and where it appeared:

    Example, Ada; Sample, Cy (2020). Tides of the Estuary. Journal of Made-Up Studies 12(3), 45–67.
    JOUR
    2020-03-15
    10.1000/xyz123
    tides; estuaries
    We measure the tide at six harbours.
    Read for chapter 2.

Authors are kept as written, never cut to initials, so a first name you ask
with is there. The title comes from TI or T1, where it appeared from T2, JF, JO
or JA, the pages from SP and EP. Then, each on its own line when the reference
has it: the type as the file writes it (JOUR, BOOK, CHAP), the full date,
editors (A2), other names (A3, A4), publisher and place, doi, links, ISBN or
ISSN, its ID, keywords, the abstract (AB, or N2) and notes (N1, with Zotero's
HTML read as words).

No line carries a label of this reader's ("doi:", "keywords:", "journal
article"): a word written into every passage would let a question about
something your library doesn't hold, such as "volcano abstract", be answered
with any reference. The cost: a field's name in a question ("the abstract of
...") counts for nothing, so the rest of the question has to hold.

The year comes only from the date tags, PY, Y1 or DA, as the four digits they
open with; with none, the citation has no year, never one guessed from the
title or a note. A date with more than the year is said too: 2020/03/15/ as
2020-03-15, anything else (July) as written.

A line with no tag continues the one before it. A byte-order mark, Windows line
ends and blank lines between references are fine. A reference that is broken
(a TY with no ER before the next one, or the file ending inside one) is
skipped and counted in the file's closing passage, never a crash:

    2 references; 1 malformed

A .enw file is read by what it holds: RIS lines, or EndNote's own tagged
lines (`%0 Journal Article`, `%A`, `%T`, references parted by a blank line),
which are read the same way. PubMed's .nbib export is another format and isn't
read.

Each file is written to MIRROR at the same relative path with .txt added.
FOLDER is only read: hidden folders and files are skipped, and nothing is
written inside it. A file that can't be read (not UTF-8, or holding no
reference) is skipped and counted:

    wrote 2 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`); Python's
standard library for the format.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, or goes online.
