<!-- willow-addon
section: Reading more kinds of files
line: SARIF reports from code scanners such as CodeQL and Semgrep: each finding as a passage with its rule and place.
source: new
added: 2026-10-29
writes: to
network: none
-->
# sarif

Your scanners' findings, searchable by rule, file and line.

    python adapters/stdlib/sarif/sarif.py mirror --from FOLDER --to MIRROR

Each finding is a short passage:

    CodeQL: py/sql-injection (error) at src/db.py:42
    SQL injection: This query depends on a user-provided value.

The first line is the scanner (the tool's name), the rule, its level (warning
when the report gives none) and where it was found; the second is the rule's
short description, when the report has one, and the finding's message. Findings
come in order of file, line and rule, and one with no location is written
without "at". Fixes, code flows, fingerprints and the rules' long help are not
copied. A .sarif or .sarif.json file that is not a SARIF report is skipped
and counted.

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
