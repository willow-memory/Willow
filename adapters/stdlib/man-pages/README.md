<!-- willow-addon
section: Reading more kinds of files
line: The man pages installed on this machine as plain text, so you can ask your own system's docs.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# man-pages

A directory of man pages as text, so you can ask your own system's documentation.

    python adapters/stdlib/man-pages/man_pages.py mirror --from FOLDER --to MIRROR

Point it at your system's man directory (the system keeps pages gzipped,
`ls.1.gz`) or any folder of pages named like `ls.1`, `printf.3` or `intro.7`.
Each is written as the text a reader sees:

    LS(1)

    NAME
    ls - list directory contents

    DESCRIPTION
    List information about the FILEs.

The `.TH` line gives the title; section headings stay on their own line; the
font escapes, hyphen and dash escapes, quotes and the usual macros (.B, .I,
.BR, .TP, .IP, .PP, .RS, .nf) are read as the words they hold. Comments, macro
definitions and other roff requests are dropped. A gzipped page is read to
10 MB; a page with no text, or one that only redirects to another with `.so`,
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
