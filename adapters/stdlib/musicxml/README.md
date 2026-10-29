<!-- willow-addon
section: Reading more kinds of files
line: MusicXML scores: titles, lyrics, tempo and performance markings as passages.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# musicxml

Your scores, searchable by title, composer, words and markings.

    python adapters/stdlib/musicxml/musicxml.py mirror --from FOLDER --to MIRROR

Each score is written as what can be read in words:

    title: Evening Song
    composer: Ana Example; lyricist: Ben Sample
    parts: Soprano
    key: G major; time: 3/4; tempo: 72
    markings: m.1 Andante; m.1 p
    lyrics (Soprano): Evening comes

The title is the work title, then the movement title when it differs; the
composer and lyricist are the credits of that type. The key, time and tempo are
the first the score gives. Markings are the words and dynamics of the first
part, each with its measure. Lyrics are each verse's syllables in order, joined
where the score splits a word across notes. The notes themselves are not copied. Only a
partwise score is read (a `.mxl` is a zip and is not), `.xml` files that are
not a score are skipped and counted, and a file that declares entities is not
read.

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
