<!-- willow-addon
section: Finding things
line: For a folder you know writes dates month first: each one's ISO form written beside it, so it can be placed.
source: new
added: 2026-10-31
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# month-first

The kernel reads 10/24/2026, since 24 can't be a month, but never
11/03/2026, which reads either way round, and it never guesses. Nor does it
read `Oct 24, 2026` or a two-digit year. When you know who wrote a folder (an
American's letters, a US court's papers, a US school's notices), this says it
for the kernel: every month-first date is written with its ISO form beside
it, in a mirror, so the kernel and the add-ons that read dates (timeline,
gaps, coming-up) can place it.

    python adapters/stdlib/month-first/month_first.py mirror --from FOLDER --to MIRROR

    Hearing moved to 11/03/2026 [2026-11-03]; filed Oct. 2nd, 2026 [2026-10-02].

**What it reads:** 11/03/2026, 11/03/26, Nov 3, 2026, November 3 2026 and
Nov. 3rd, 2026, in each .txt, .md and .html file. A two-digit year from 70 to
99 is the 1900s, from 00 to 69 the 2000s. A date that isn't one (13/03/2026,
Feb 30, 2026), one outside 1900 to 2099 (the years the kernel reads), and
one inside a web address or a longer run of numbers and slashes are left as
they are. A date already followed by its ISO form is not marked again, so a
mirror run through it again comes out the same.

**What it writes.** Every text file, marked or not, at the same path with
.txt added, so MIRROR is a whole folder to build a box from. The original
text stays, with the ISO dates added; a page's tags are dropped, as the
kernel drops them. It says how many dates it gave their ISO form. A file
that isn't UTF-8 is skipped and counted.

**A file that says otherwise is believed.** A file whose own dates say day
first (13/03/2026 reads no other way) keeps its numbered dates as they are,
and is named, as chats leaves a file that contradicts its flag; its dates in
words (Nov 3, 2026) still gain their ISO form, since they read one way only.
On teodora's demo folder, written in England, that leaves 68 files' dates
alone.

**Otherwise it is your word, not its finding.** A day-first file with no day
over 12 can't show its order, so run on one it reads 03/11/2026 as March 11:
teodora's folder still has 13 of those. Only you know who wrote the folder.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (MIRROR inside
FOLDER or the other way round, or FOLDER not a folder).

**Uses:** the kernel's `html_text` and exit codes. Its tests check the
kernel's `newest` reads a date it marks and doesn't read it unmarked.

**Never:** writes inside FOLDER, changes an original, decides a folder's
date order for you, or goes online.
