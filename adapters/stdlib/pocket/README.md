<!-- willow-addon
section: Reading more kinds of files
line: Pocket's export, the HTML and CSV in its zip, as one dated line per saved article, now that Pocket is gone.
source: new
added: 2026-11-02
writes: to
network: none
role: reads
-->
# pocket

What you saved to Pocket, and when, searchable now that Pocket has closed.

    python adapters/stdlib/pocket/pocket.py mirror --from FOLDER --to MIRROR

Each saved article becomes one line, the day you saved it first, then only
what Pocket held:

    2023-03-04 How to keep a sourdough starter alive & happy <https://example.org/sourdough> [baking, bread] (unread)

    2024-06-02 https://example.org/bare (archive)

It reads both shapes Pocket exported, and knows them by what they hold, not
by their names:

| Export | How it's known |
|---|---|
| the older ril_export.html | an "Unread" and a "Read Archive" heading over lists of links carrying `time_added` |
| the 2025 CSVs (part_000000.csv and on) | a header of exactly `title,url,time_added,tags,status`, tags joined by `\|` |
| the zip Pocket emailed (pocket.zip, or any .zip holding those files) | read without unpacking it; every Pocket file in it goes into one mirror, `<zip path>.txt` |

Any other .csv, .html or .zip is left alone and not counted. Hidden members of
a zip, and the `__MACOSX` folder a Mac adds, are left out. The annotations
file Pocket put in the zip for highlights is left alone too: its shape isn't
documented anywhere this could check, and a guess could put words in your
mouth.

**The line.** The day is the UTC day of Pocket's `time_added`, so the same
export gives the same lines on any machine. A title that is blank, or is the
address itself, is written as just the address. Tags are left out when there
are none. The status is written as Pocket wrote it ("unread", "archive"; the
HTML's "Read Archive" heading as "archive"), and left out when it gave none.
An article with no time starts "undated", never given one.

**No word of its own on every line.** The kernel serves a passage only when
it holds half the question's words, so a word this added to every line (such
as "saved") would answer "what did I save about volcanoes" with an unrelated
article. It adds none, and that question gets an honest nothing. The cost:
"when did I save that article about sourdough" misses too; ask "that
sourdough article". The status is Pocket's own word and stays, so
"what is unread about volcanoes" is still half held by every unread line.

**Why a line per article, a blank line between.** Each article is a passage
of its own, served with its own day, not inside a run of other titles. The
lines go oldest first, undated ones at the top, because the kernel dates a
passage by the latest date at or above it in its file: newest first, every
article would wear the newest one's day.

Each file is written to MIRROR at the same relative path with .txt added.
FOLDER is only read: hidden folders and files are skipped, and nothing is
written inside it. A zip member over 64 MB is left out. A Pocket file with no
articles, or a file that can't be read, is skipped and counted, never a
crash:

    wrote 2 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`); Python's
standard library for the formats.

**Never:** writes inside FOLDER, unpacks a zip, modifies an original, writes
anything outside MIRROR, or goes online.
