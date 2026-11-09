<!-- willow-addon
section: Reading more kinds of files
line: Plain-text files the kernel leaves out (UTF-16, an old code page, over 1 MB, lines past 500 characters) as UTF-8 it reads, line for line.
source: new
added: 2026-11-02
version: 0.1.0
writes: to
network: none
role: reads
reads: .txt, .text
-->
# text

Every .txt file in a folder, as text the kernel reads whole.

    python adapters/stdlib/text/text.py mirror --from FOLDER --to MIRROR [--encoding NAME]

The kernel reads a file only when it is UTF-8, has no NUL byte in its first
8192 bytes and is 1 MB or less, and it keeps only the first 500 characters of
a line. Anything else is left out without a word:

- a Windows Notepad "Unicode" file (UTF-16 with a byte order mark: its NUL
  bytes make it look like a program);
- a Notepad "ANSI" file, or any old code page (Windows-1252, Latin-1, Mac
  Roman): it isn't UTF-8;
- a book-length .txt over 1 MB: dropped whole;
- a paragraph saved as one long line, as Notepad does: everything after its
  500th character.

This writes every .txt and .text file in FOLDER as UTF-8 that the kernel
reads all of, the ones it already could too, so the mirror replaces them for
asking. **Point the kernel at MIRROR instead of the .txt originals**
(`kernel.py init --pile MIRROR`), so nothing is read twice. Only .txt and
.text are read: .nfo files are usually DOS art in code page 437, and .asc is as
often a PGP signature as a note, so neither is plain prose to ask of.

## How a file is decoded

Only when it is certain:

| The file | Read as |
|---|---|
| UTF-8, with or without a byte order mark | UTF-8 |
| starts with a UTF-16 or UTF-32 byte order mark, either byte order | that |
| no mark, and its first 8192 bytes (all of a smaller file, of even length) alternate exactly: one byte of every pair NUL, the other never | UTF-16, low byte first when the NULs come second, else high byte first |
| anything else | skipped and counted, unless you name its encoding |

The no-mark rule fits English or other Latin-1 text saved as UTF-16. A file
with any other letter in its first 8192 bytes (a euro sign, Cyrillic) breaks
the pattern and is not guessed at.

`--encoding NAME` names the encoding of the files the table can't read
(`cp1252`, `latin-1`, `cp1251`, `mac-roman`, `utf-16-le`): it is never used
on a file the table reads. A name Python doesn't know as a text encoding is
refused. A decoded file holding a NUL character is a program or an image
named .txt, and is skipped and counted whatever the encoding. Each skipped
file is named on stderr with the reason:

    skipped minutes.txt: not UTF-8; name its encoding with --encoding
    wrote 4 files to MIRROR; skipped 1

## Line for line

Line N of the mirror is line N of the file, as an editor counts lines:

- CRLF (Windows) and a bare CR (an old Mac) become LF.
- A line that is only a form feed becomes blank, so a page break ends a
  passage. A form feed among a line's text, or another character Python
  would break a line at (vertical tab, NEL, U+2028), becomes a space: a new
  line there would move every line after it.

Two things move lines:

- **A line over 500 characters** is broken at spaces into lines the kernel
  reads whole, every piece the same line of the file.
- **A mirror over 1 MB** is cut into parts: book.txt is mirrored as
  book.txt.txt, then book.txt.part2.txt and on, at a blank line where there
  is one in the second half of a part, else between two lines, never inside
  a long line's pieces. Parts that a shorter earlier run left behind are
  removed.

Nothing is written into the text to say so: a word or a number written into
passage after passage would be served for a question the folder doesn't
answer. Where the lines go is in a hidden file beside the mirror, which the
kernel never reads: `.<file>.lines` (for book.txt, .book.txt.lines), one
row per place the numbering starts again, tab-separated: the mirror file, its
line, the line of the file it is (shown here with spaces). A mirror line is
the line of the last row at or above it, counted on:

    book.txt.txt          1  1
    book.txt.part2.txt    1  20412

So line 3068 of book.txt.part2.txt is line 23479 of book.txt. A file that
moves no line has no map, and a map no longer needed is removed.

**Hard-wrapped prose** (a line break every 70 characters, no blank lines) is
left as it is. The kernel takes it in runs of whole lines up to 500
characters, so a sentence can be cut between two passages; joining the lines
would lose the line numbers.

Each file is written to MIRROR at the same relative path with .txt added
(notes/old.txt becomes notes/old.txt.txt). FOLDER is only read: hidden
folders and files are skipped, and nothing is written inside it. An empty
file, or one over 50 MB, is skipped and counted.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, MIRROR and FOLDER are inside one another, or NAME is not a text
encoding Python knows).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`) and its
limits (`SNIFF`, `MAX_FILE`, `MAX_CHUNK`); Python's standard library.

**Never:** guesses an encoding, writes inside FOLDER, modifies an original,
writes anything outside MIRROR, or goes online.
