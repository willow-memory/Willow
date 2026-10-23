<!-- willow-addon
section: Reading more kinds of files
line: WhatsApp and Telegram exports, one dated line per message.
source: new
added: 2026-10-23
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# chats

WhatsApp text exports and Telegram JSON exports, written out as one dated line
per message, so the kernel can answer from them.

    python adapters/stdlib/chats/chats.py mirror --from FOLDER --to MIRROR [--day-first | --month-first]

    2024-12-03 08:10  Dev Raman: I can do 600 tonight

Each message is one line: its day, its time, who sent it and the text. A
WhatsApp continuation line belongs to the message above it, and a Telegram text
given as a list of pieces is joined into one. Messages are grouped by day, with
a blank line between days, so each passage the kernel serves is one day of one
chat. chats/Dev.txt in FOLDER becomes MIRROR/chats/Dev.txt.txt. Files that
are not chat exports are not counted; a chat it cannot read is skipped and
counted. Telegram service messages (no sender) are left out.

**Date order.** A WhatsApp export writes day and month in the phone's order, so
the order is decided once per file from the file's own dates: a first number
over 12 means day first, a second number over 12 means month first. A file that
never settles it is written with its dates as they were given, and
`(date order unknown)` is written once at the top. `--day-first` or
`--month-first` settles it. A file whose dates contradict the flag is skipped.
It never guesses.

A WhatsApp file counts as a chat only when most of its non-blank lines start with
a date, so a file of long multi-line messages can fall below that and is not
counted.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (MIRROR inside
FOLDER or the other way round, or FOLDER not a folder).

**Uses:** nothing from the kernel's functions, only its exit codes. Its tests
run `kernel.py` `init` and `bite` on the mirror it writes.

**Never:** writes inside FOLDER, changes an original, guesses a date order, or
goes online.
