<!-- willow-addon
section: Reading more kinds of files
line: .ics events and .vcf contacts as dated lines.
source: new
added: 2026-10-23
writes: to
network: none
-->
# calendar

Calendar files (.ics) and contact cards (.vcf) written out as plain, dated text,
so the kernel can answer questions about them like any other folder. It makes a
mirror folder of text files; the kernel reads that folder, not the calendars.

    python adapters/stdlib/calendar/cal.py mirror --from FOLDER --to MIRROR

Then point a box at the mirror: `kernel.py init --pile MIRROR`.

Each calendar event becomes one paragraph, the date (and time, if it has one)
and the summary on the first line, then `where:` and `notes:` lines when the
event has them:

    2026-10-21  Pay the water bill

    2026-10-28 14:00  Tune - Ybarra
    where: Studio 2, Annex
    notes: Ask about the fee; bring a
      spare string

A recurring event is written once, under its first date, so its first line
says that it repeats, and how, in words; a `repeats:` line keeps the rule
itself. An event marked cancelled says so on its first line too:

    2022-11-03  Car rego due  (yearly, from this date)
    repeats: FREQ=YEARLY

    2026-08-19 10:30  Skin check  (cancelled)

So a line quoted from one, by an assistant or by you, can't pass for this
year's date or a booking that stands. [coming-up](../coming-up/) counts each
repeat in its window.
Each contact in a .vcf becomes one paragraph, with `phone:`, `email:`, `address:`
and `birthday:` lines when the card has them:

    contact: Ana Example
    phone: +1-555-0142
    email: ana@example.org
    address: 12 Oak Lane, Springfield
    birthday: 1990-03-15

Events are sorted by date within a file. A time ending in Z is UTC and is shown
as written, not converted to local time. A file that is not UTF-8 text, or holds
no calendar or card, is skipped and counted in the summary line.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused.

**Uses:** the kernel's exit codes only. The kernel does not know this add-on
exists; it reads the mirror as an ordinary folder.

**Never:** writes inside FOLDER, changes the originals, expands a repeating
event into its occurrences, or goes online.
