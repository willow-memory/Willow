<!-- willow-addon
section: Reading more kinds of files
line: LaTeX sources as plain prose, commands stripped, cited by the .tex file's own lines.
source: new
added: 2026-10-29
writes: to
network: none
role: reads
output: mirror
reads: .tex
-->
# latex

Your papers and notes in LaTeX, as the prose they say.

    python adapters/stdlib/latex/latex.py mirror --from FOLDER --to MIRROR

The mirror has the same number of lines as the source, and each line is the
source's line with its commands taken off, so a passage found in the mirror is
on that same line of the .tex file:

    Method                                              (the section heading)
    We measure the tide at six harbours [smith2020].    (with its citation)

| Dropped | Kept |
|---|---|
| comments; the preamble; math, inline and display; equation, align, verbatim, listing and picture environments | a title and author from the preamble, as "title:" and "author:" |
| label, ref, usepackage, includegraphics, vspace, newcommand and their kind, with their arguments | the text of a section, bold, emphasis, caption, footnote and link |
| begin and end lines | a citation as [key]; an item as "- "; escaped characters as themselves |

`--` and `---` become dashes, double backquotes become curly quotes, and accents
(an umlaut, an acute, a cedilla, the German sharp s) become the letters they
make. A line that held only dropped material is blank, so the numbering holds.

Each file is written to MIRROR at the same relative path with .txt added.
FOLDER is only read: hidden folders and files are skipped, and nothing is
written inside it. A file is read as UTF-8, else as Windows-1252, else as
Latin-1, so a paper holding one stray byte of another encoding (an en dash
pasted from a word processor, as in some arXiv sources) is still read, as the
[equations](../equations/) reader reads it. A file holding a NUL byte (UTF-16,
or a binary) or that can't be read is skipped and counted, never a crash:

    wrote 2 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`); Python's
standard library for the format.

**Where each passage came from** is in a hidden map beside its mirror,
`MIRROR/.places/<same path>.txt.json`, which the kernel never reads: each
passage's line, which is the source's own, as
[the mirror contract](../ci/README.md#the-mirror-contract) says.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, or goes online.
