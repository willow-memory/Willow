<!-- willow-addon
section: Reading more kinds of files
line: Spreadsheets with formulas and formatting kept, beyond what the office add-on reads.
source: new
added: 2026-10-29
needs: openpyxl; MIT
floor: openpyxl 3.0.5
writes: to
network: none
-->
# sheets

A spreadsheet as a person sees it, and what made each number, into a mirror
folder the kernel can search. The [office](../../stdlib/office/) add-on reads
a sheet's stored values and needs nothing installed; this one keeps what
they leave out: each cell's address, its number format, its formula, and
the notes on it.

    pip install -r adapters/deps/sheets/requirements.txt
    python adapters/deps/sheets/sheets.py mirror --from FOLDER --to MIRROR
    python kernel.py init --box BOX --pile MIRROR --key KEY

Each .xlsx or .xlsm becomes `MIRROR/<same path>.txt`, one passage a sheet,
one line a row:

    == sheet Budget
    A1 Item | B1 Cost | C1 Due
    A2 Rent | B2 £1,200.00 | C2 2026-03-01
    A4 Total | B4 £1,450.50 =SUM(B2:B3)
    note B4 (Ana): check the deposit

**How a cell is shown.** A number as the first part of its format shows it:
decimals, thousands, percent, a currency or a word around it, scientific;
rounded half away from zero, as Excel rounds. A negative takes a minus,
whatever the format's own negative part says, and a format it can't draw
(a fraction) shows the number plainly. A date is written YYYY-MM-DD, whatever
its format, so the kernel reads it as dated. A formula follows the result the
file last saved for it; a file saved by a program that keeps none shows the
formula alone. A hidden sheet is read, and headed `(hidden)`.

**The reader contract** (shared with every file reader): hidden files and
folders are skipped, and so is Excel's `~$` lock file; nothing is written
inside FOLDER and no original changes; MIRROR inside FOLDER, or the other way
round, is refused; the same file always gives the same bytes; a file openpyxl
can't read (corrupt, or encrypted) is skipped and counted, never a crash.

**Can't:** recalculate a formula (the result shown is the one the file
saved), or read .xls, .ods or .numbers. Charts, pictures and colours aren't
read.

On Bernadette's two demo spreadsheets it writes what office writes and the
working too: her budget's annual column as `C4 9360 =B4*12`, each line a
monthly figure times twelve. On 18 of pandas' own test workbooks it wrote all
18 at the pins; at the floor, openpyxl 3.0.5 skips the one whose dates run
past what it can read. The other demo folders hold no spreadsheet.

**Never runs a macro.** An .xlsm's macros are read as nothing; openpyxl
doesn't run them.

**Without openpyxl** it refuses and names the install: exit 2, never a quiet
skip.

**Uses:** the kernel's exit codes: 0 wrote at least one file; 42 nothing
readable; 2 refused.

**Never:** writes inside your folder, changes an original, or goes online.
