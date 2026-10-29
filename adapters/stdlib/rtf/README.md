<!-- willow-addon
section: Reading more kinds of files
line: RTF documents as plain text.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# rtf

Rich Text Format files, as the plain text they show.

    python adapters/stdlib/rtf/rtf.py mirror --from FOLDER --to MIRROR

A .rtf file is text wrapped in control words. This writes the text it
displays: paragraphs and line breaks kept, and everything that only styles it
dropped.

| In the file | In the mirror |
|---|---|
| the font, colour and style tables, the info block | dropped |
| bold, italic, size and other formatting words | dropped |
| an escaped accented letter (backslash, apostrophe, two hex digits) | the letter, read as Windows-1252 |
| a Unicode escape (a letter or number after a backslash and u) | the character, with its fallback letter skipped |
| a field (a link, a page number) | its shown result; the instruction dropped |
| pictures, headers, footers, footnotes, generators and anything marked ignorable | left out |
| paragraphs, line breaks, tabs, dashes, bullets, curly quotes | kept as the characters |

Runs of blank lines are squeezed to one, and trailing spaces are removed. A
file that doesn't begin as RTF, or has no text, is skipped and counted.

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
