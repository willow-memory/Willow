<!-- willow-addon
section: Reading more kinds of files
line: .docx, .odt, .pptx, .xlsx and .ods, which are all zipped XML.
source: new
added: 2026-10-23
-->
# office

The text inside your office files, written beside them as plain text, so the
kernel can answer from them. The kernel reads only text files; this turns each
Word, OpenDocument, PowerPoint, Excel or OpenDocument spreadsheet into a text
file it can read.

    python adapters/stdlib/office/office.py mirror --from FOLDER --to MIRROR

Each office file under FOLDER becomes MIRROR, then the same relative path,
then .txt: reports/q3.docx becomes MIRROR/reports/q3.docx.txt. Then point the kernel at
MIRROR with `init --pile MIRROR`.

    wrote 3 files to /home/you/mirror; skipped 1

**How each format becomes lines:** paragraphs are lines, separated by blank
lines. A paragraph is the text of a Word paragraph (docx), an OpenDocument
paragraph or heading (odt), or a PowerPoint paragraph (pptx). A slide or sheet
starts with a heading line, `== slide 3` or `== sheet Budget`. In a
spreadsheet (xlsx, ods) a row is one line, its cells joined by ` | `, and the
rows of one sheet sit together under its heading. Formulas show their
stored result. Numbers show as stored, without the cell's formatting.

A file that will not parse (not a zip, a part missing, bad XML, a part larger
than 64 MB) is skipped and counted, never a crash. Folders and files whose name
starts with `.` are not read. Files that are not one of the five formats are
not counted either way.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused. A refusal says
why: FOLDER is not a folder, or MIRROR is inside FOLDER (or FOLDER inside
MIRROR).

**Uses:** `kernel.py`'s exit codes (`ALIVE`, `ESCALATE`, `REFUSED`). The kernel
is not otherwise called; it reads the mirror like any folder.

**Never:** writes inside FOLDER, changes an original, or goes online. Headers,
footers, footnotes, comments and speaker notes are not read.
