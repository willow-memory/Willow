<!-- willow-addon
section: Finding things
line: For a folder you know writes dates day first: each one's ISO form written beside it, so it can be placed.
source: new
added: 2026-11-16
version: 0.1.0
writes: to
network: none
role: makes
uses: month-first
-->
# day-first

The kernel reads 24/10/2026, since 24 can't be a month, but never
03/11/2026, which reads either way round, and it never guesses. Nor does it
read `3 Nov 2026`. When you know who wrote a folder (an English, Irish,
Australian or Indian hand; most of Europe's), this says it for the kernel:
every day-first date is written with its ISO form beside it, in a mirror,
so the kernel and the add-ons that read dates (coming-up, renewals, car,
gaps, timeline) can place it. It is [month-first](../month-first/)'s twin,
and shares its walk, its date check and its month names.

    python adapters/stdlib/day-first/day_first.py mirror --from FOLDER --to MIRROR

    Your cover ends on 03/11/2026 [2026-11-03]; MOT due 9 Nov 2026 [2026-11-09].

**What it reads:** 03/11/2026, 03/11/26, 3.11.2026, 3 Nov 2026, Tue 3 Nov
2026, 3rd November 2026 and 3 November, 2026. A two-digit year from 70 to
99 is the 1900s, from 00 to 69 the 2000s. A dotted date needs all four
digits of its year: 1.1.11 is a section or an MOT item's number far more
often than a day. A date that isn't one (31/02/2026), one outside 1900 to
2099 (the years the kernel reads), one inside a path or a longer run of
numbers, and one with no year (Mon 26 Oct, whose year is a guess) are left as
they are. A date already followed by its ISO form is not marked again, so a
mirror run through it again comes out the same.

**Which files.** Every file the kernel itself reads, by what it holds and
not its name: UTF-8, no NUL byte in its first 8,192 bytes, under its
million-byte cap. So mail (.eml), calendars (.ics) and statements (.csv)
come through with notes and letters, where month-first takes only .txt, .md
and .html. Each keeps its name, so a passage is cited where it was; a page
gains .txt, its tags dropped as the kernel drops them. The original text
stays. A file the kernel wouldn't read is left out, so MIRROR is the folder
to build the box from.

**A file that says otherwise is believed.** A file whose own dates say
month first (11/24/2026 reads no other way) keeps its numbered dates as they
are, and is named; its dates in words (3 Nov 2026) still gain their ISO
form, since they read one way only.

**Otherwise it is your word, not its finding.** A month-first file with no
day over 12 can't show its order, so run on one it reads 03/11/2026 as the
3rd of November. Only you know who wrote the folder. On teodora's demo
folder, written in England, it gives 939 dates their ISO form, among them
her insurance ending 03/11/2026 and her car's MOT running out 09/11/2026,
which coming-up and renewals then find.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (MIRROR inside
FOLDER or the other way round, or FOLDER not a folder).

**Uses:** month-first's walk (`mirror_with`), its `iso` and its month names;
the kernel's `MAX_FILE`, `SNIFF`, `html_text` and exit codes. Its tests check
the kernel's `newest` reads a date it marks and doesn't read it unmarked.

**Never:** writes inside FOLDER, changes an original, decides a folder's
date order for you, or goes online.
