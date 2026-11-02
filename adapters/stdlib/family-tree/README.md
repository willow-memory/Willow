<!-- willow-addon
section: Reading more kinds of files
line: Family trees from GEDCOM files: who was born where and when, and which record says so.
source: new
added: 2026-10-29
writes: to
network: none
-->
# family-tree

Your family tree, searchable by who, where and when, each passage naming its own record.

    python adapters/stdlib/family-tree/family_tree.py mirror --from FOLDER --to MIRROR

Each person is a paragraph that names the record it came from:

    John Smith (@I1@): born 2 Mar 1850 in Leeds; died 1920 in York; father
    Arthur Smith (@I4@); mother Ann Jones (@I5@); married Mary Brown (@I2@)
    1875 in Hull; note: A weaver and a singer.

The name is read from NAME, with the slashes round the surname dropped. The
facts are BIRT, CHR, DEAT and BURI with their DATE and PLAC (a bare event with
no date or place says just "died"); parents come from the family the person is
a child of (FAMC), spouses and the marriage from the families they are a spouse
in (FAMS). A NOTE is kept whole, its CONT and CONC lines joined. The @I..@ in
brackets is the record's own id. Dates are kept as the file writes them (ABT
1850, BEF 1851): none is guessed or reformatted. A family member who is not in
the file is named by their id. Sources, media and other tags are not copied. A file that does not open
with a `0 HEAD` line is not a GEDCOM file and is skipped and counted.

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
