<!-- willow-addon
section: Assistants
line: A card for your folder itself (what the files are, their dates, the gaps you know of), made from your files and your notes and handed to a model as context.
source: new
added: 2026-11-01
writes: to
network: none
tags: no-install, offline, writes-output, assistant
-->
# folder-card

A card for your folder itself: what the files are, their dates, and the gaps
you know of, compiled from the pile and your notes, to hand a model as context.

    python adapters/stdlib/folder-card/folder_card.py --box DIR --to card.md [--notes me.txt] [--now TS]

Your notes are a plain file. A line that starts with `gap` and two dates is a
gap you know of, with your reason; every other line is kept as you wrote it:

    gap 2026-03-04 to 2026-03-11 flu, no writing
    Everything before 2025 was typed up from paper.

The card (Markdown) then reads, in part:

    ## Files (11: 10 read, 1 not)
    - `<diary>.md`: 70 bytes, 4 dated days, 2026-01-05 to 2026-01-26; labels itself fiction
    - `<photo>.bin`: 3 bytes, not read (binary, too large or not UTF-8)
    ## Dates and gaps
    - `<folder>/`, files named by a date, 7 entries, 2026-03-01 to 2026-03-14, typical spacing 1 day
      - GAP 2026-03-04 to 2026-03-12, 7 days with no entry; told: flu, no writing
    ## Gaps you know of
    - 2026-03-06 to 2026-03-10: flu, no writing (the files show it too)

**Files.** Every file under the pile, hidden folders aside as the kernel
leaves them: its size, its first and last dated line (or the date in its
name), and "labels itself fiction" when its first line starts with `fiction`
or `fictional`. A file the kernel does not read (binary, over its size cap,
not UTF-8) is listed as not read, never dropped.
Five or more files named by a date in one folder are one line (their count,
first and last date, total size), so a card stays short enough to hand over.

**Gaps.** Found by the `gaps` add-on's own rule, which this loads and does not
repeat: a spacing more than three times the log's typical one. A log lists its ten longest, and says how many shorter it left out; a gap you
named is always listed. Each is marked
`told` with your reason when a gap you named overlaps it, else `untold`. Each
gap you named is marked as shown by the files, as not shown, or as
contradicted, with the count of dated entries the files hold inside it. A
`gap` line that is backwards or not a day (2026-02-31) is listed as not read.

A gap is days with no entry written, never days when nothing happened, and the
card says so for the model. Your notes go into the card word for word, so read
it before you hand it on. The card is a claim made from your files, not a
signature.

FILE is written once, readable only by you, never over a file that exists, and
the same pile and notes give the same bytes. A missing folder is refused, not
made.

Exit codes, the kernel's: 0 written; 2 refused.

**Uses:** the kernel's `chunks`, `newest` and `config`, and the `gaps` add-on's
`logs`, `gaps`, `day` and `starts_with_date`.

**Never:** writes the box or the pile, reads your key, seals, sends the card
anywhere, or reads a gap as nothing having happened.

**Where it comes from:** a one-file sketch that only printed each file's dated
lines, longest gap and fiction label. Here the gaps are the `gaps` add-on's,
the output is a file, and your own notes are in it.
