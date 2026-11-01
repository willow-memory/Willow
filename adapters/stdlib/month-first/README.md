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

**It is your word, not its finding.** Run on a folder written day first, it
reads 03/11/2026 as March 11. Only you know who wrote the folder; a file
whose own dates say day first (a first number over 12) still gains no wrong
date from those, as they can't be read month first.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (MIRROR inside
FOLDER or the other way round, or FOLDER not a folder).

**Uses:** the kernel's `html_text` and exit codes. Its tests check the
kernel's `newest` reads a date it marks and doesn't read it unmarked.

**Never:** writes inside FOLDER, changes an original, decides a folder's
date order for you, or goes online.
