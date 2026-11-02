<!-- willow-addon
section: Reading more kinds of files
line: CSV and TSV tables as one passage per row, the header row kept once as the first.
source: new
added: 2026-11-02
writes: to
network: none
-->
# csv-rows

Any table you keep as a CSV or TSV file, searchable a row at a time: a census
transcription, a seed log, a ledger, a list of readings.

    python adapters/stdlib/csv-rows/csv_rows.py mirror --from FOLDER --to MIRROR

The kernel reads a raw CSV as runs of 500 characters, since a table has no
blank lines: one passage holds parts of several rows. Here the header row is
the first passage, and each row after it is one passage of its values:

    [1] Surname; Forename; Townland; Age; Occupation

    [3] Considine; Patrick; Caherfeenick; 17; Farm Labourer

    [4] Considine; Mary; Caherfeenick; 14; Scholar

So "how old was Patrick Considine" finds Patrick's row, and only his. The
number in brackets is the line of the source file the row starts on (a quoted
value holding a line break starts on its first line), so you can find it in
the table. Values are copied as written: a date is never turned round, a
number never reformatted.

- **An empty cell** keeps its place (`2020-11-05; ; 148`), so each value
  stays under its header; empty cells at the end of a row are dropped.
- **A wide row**, whose passage would pass the kernel's 500 characters, is cut
  at a cell into lines that each start with its number, and one long cell at
  a space, so the kernel keeps every word of it.
- **The delimiter.** A .tsv is read by tabs. For a .csv, the first line (not a
  note) decides: whichever of comma, tab, semicolon and pipe cuts it into the
  most cells, a tie going to the first of those. Nothing else is tried.
- **The header** is the first line, unless one of its cells is a number or a
  date (30/06/2022, -112.87), as in a bank export with none; then every
  row is data.
- **Notes above the header**, lines starting with `#`, are kept with their
  line number in brackets.
- **Skipped and counted, never a crash:** a file not in UTF-8 (a byte-order
  mark is fine; nothing else is guessed), a table with no data row (a header
  alone, or nothing), and one Python's csv module finds malformed (a stray
  quote, say) rather than read it wrong.

**No word in every row.** The kernel serves a passage holding half a
question's words, so a word written in every row, a label of the reader's or
a column's header, would let a question about something the folder lacks
("religion of Seamus", with no Seamus in the census) be answered by an
unrelated row. So the headers are written once: a question naming a column
finds the header row, never a row it doesn't hold. The cost, on the demo
folders: of 29 real questions, "what pitch was the Steinway D at" is no
longer answered, and in 6 the header row comes first with the right row
after it.

There is no passage naming a table's columns and how many rows it has. On the
demo folders it came up for ordinary questions (3 in 26, one of three places
each time) and answered only questions about the table itself, which any of
its rows already answers.

**Bank and orders read their own exports with more meaning.**
[bank](../bank/) reads a statement as dated amounts and adds up each month;
[orders](../orders/) reads an order history as what you bought, when and for
how much, and both leave out account and card numbers. Use them for those
files, and this for every other table. This copies every cell, as the file
holds it, so a column you wouldn't want in an answer is in the mirror too.

Each file is written to MIRROR at the same relative path with .txt added.
FOLDER is only read: hidden folders and files are skipped, and nothing is
written inside it.

    wrote 9 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`) and its
`MAX_CHUNK`; Python's standard library (`csv`) for the format.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, or goes online.
