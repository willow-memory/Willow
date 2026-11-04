<!-- willow-addon
section: Reading more kinds of files
line: AsciiDoc documents as the text they show, line for line, markup taken off, cited by the file's own lines.
source: new
added: 2026-11-02
writes: to
network: none
role: reads
reads: .adoc, .asc, .asciidoc
-->
# asciidoc

Your AsciiDoc documents, manuals and notes, as the text they show.

    python adapters/stdlib/asciidoc/asciidoc.py mirror --from FOLDER --to MIRROR

The mirror has the same number of lines as the source, and each line is the
source's line with the markup taken off, so a passage found in the mirror is on
that same line of the .adoc file:

    == Method                                   Method
    :revdate: 2024-03-03                        revdate: 2024-03-03
    See link:https://x.org[the data].           See the data (https://x.org).
    | Leeds | 6 | 2024-03-03                    Leeds; 6; 2024-03-03

| In the file | In the mirror |
|---|---|
| a title, `= Doc`, `== Section`, `.Block title` | its text |
| the author and revision lines under the document title | as written |
| the document's own attributes (author, email, revdate, revnumber, version, description, keywords and their kind) | `name: value` |
| any other attribute line | blank; a `{name}` later on is its value, or as written when nothing set it |
| listing, literal, source and fenced blocks, a `[source]` or indented paragraph | as written; the delimiters and attribute lines blank |
| example, sidebar, quote and open blocks | their text, the delimiters blank; a quote's author and source after a dash |
| comments, `//` lines and `////` blocks | blank |
| an admonition, `NOTE: x` or a `[WARNING]` block | `note: x`, `warning: x` |
| bold, italic, monospace, highlight, superscript, subscript | the words without the marks; never a mark inside a word, as in snake_case; an escaped or passed-through mark stays |
| a link | its text, with the address after it in brackets when it goes outside the folder; a link to a file in the folder is only its text |
| a cross reference, `<<id,text>>` or `xref:` | its text |
| an image | its alt text |
| a footnote | its text in brackets |
| `kbd:`, `btn:`, `menu:` | the keys, the button, the menu path |
| a list item, `*`, `-` or `.` | `- ` (a numbered one keeps its number; a checklist keeps its box, `[ ]` or `[x]`) |
| a description, `term:: text` | `term: text` |
| a table | each line's cells joined by `; `, the header row kept once where it is; a cell running on over lines keeps its later lines as plain text; CSV and DSV tables too |
| `include::`, `ifdef::`, `toc::`, page breaks | blank; an include is never followed |

A macro or a bold that runs on to the next line is read line by line: the
text on each, the address after the line that closes it.

**No word in every passage.** A table's header is not written onto each row:
a header in every row's passage would be a word half of a two-word question
holds, so "volcano role" would be answered with a row of a crew list. The
header row stays once, as the source wrote it, and a question naming two
headers and one value ("boat and role of Cy") no longer lands on the row:
that is the cost. A checklist keeps its box rather than an added "done".

**.asc files.** An .asc file is often a PGP key or signature, not AsciiDoc:
one that starts `-----BEGIN PGP` is passed over without being counted.

Each file (.adoc, .asciidoc or .asc) is written to MIRROR at the same relative
path with .txt added. FOLDER is only read: hidden folders and files are
skipped, and nothing is written inside it. A file that can't be read, or holds
no text, is skipped and counted, never a crash:

    wrote 6 files to MIRROR; skipped 0

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`); Python's
standard library for the format.

**Never:** writes inside FOLDER, modifies an original, follows an include,
writes anything outside MIRROR, or goes online.
