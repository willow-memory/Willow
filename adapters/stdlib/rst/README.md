<!-- willow-addon
section: Reading more kinds of files
line: reStructuredText files as plain prose, line for line, with directives, roles, links and tables read.
source: new
added: 2026-11-02
writes: to
network: none
role: reads
output: mirror
reads: .rst, .rest
-->
# rst

Python docs, Sphinx projects and many READMEs are written in
reStructuredText. This reads them as the text they show.

    python adapters/stdlib/rst/rst.py mirror --from FOLDER --to MIRROR

Reads .rst and .rest files. The mirror has the same number of lines as the
source, and each line is the source's line with its markup taken off, so a
passage found in the mirror is on that same line of the .rst file:

    Tides                                      Tides
    =====                                      (blank)
    .. note:: Bring a coat.                    note: Bring a coat.
    See `the shop <https://x.example>`_.       See the shop (https://x.example).
    :Author: Ada Example                       author: Ada Example
    | 128  | 0.01 sec. |                       128; 0.01 sec.

| Blank | Kept |
|---|---|
| a title's over- and underline rows; transitions; table borders | a title's own text |
| comments; link targets; substitution definitions | a substitution's replacement where it is used |
| contents, toctree, include, raw, index and a directive's options | an admonition as "note:" or "warning:" with its text; a version note as "versionadded 3.2" |
| the marker of a code block or a `::` literal block | the code as written; a line ending in `::` with one colon |
| footnote references | a footnote as "[1] text" |
| an image with no alt text | an image's alt text; a figure's caption |

A link is its text, with an outside address after it; a role (`:ref:`,
`:func:`), a literal and emphasis are their text; backslash escapes are read.
A table's header row and each body row are their cells joined by "; ", on
the row's first line, a grid cell's lines joined; a row whose cells don't line
up with its columns keeps each line's text on that line.

Nothing is added that would repeat from passage to passage: a title is not
written after the titles above it, and a header is written once, not beside
each value, since a word on every passage would answer any question that
names it. The cost: a question naming a column ("what crop is in plot 15")
finds the header row, not the row.

Each file is written to MIRROR at the same relative path with .txt added.
FOLDER is only read: hidden folders and files are skipped, and nothing is
written inside it. A file that can't be read, or holds no text once read, is
skipped and counted, never a crash:

    wrote 2 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`); Python's
standard library for the format. No docutils.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, or goes online.
