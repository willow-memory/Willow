<!-- willow-addon
section: Reading more kinds of files
line: Phone text messages, from an Android SMS backup or an iPhone backup's copy, one dated line per message.
source: new
added: 2026-10-31
writes: to
network: none
-->
# texts

Text messages and calls from a phone backup, written out as one dated line
per message, so the kernel can answer from them.

    python adapters/stdlib/texts/texts.py mirror --from FOLDER --to MIRROR [--me NAME] [--tz ZONE]

    # Dev Raman

    2024-12-03 08:10  Dev Raman: I can do 600 tonight
    2024-12-03 08:12  me: Done
    2024-12-03 09:40  outgoing call, 3 min

**What it reads.** From an Android phone, the two files SMS Backup & Restore
writes: its messages (texts, and picture messages with their words and a
`[picture]` for each image) and its call log, each kind of call by name with
its length. From an iPhone, the messages database an iPhone backup keeps,
which is often stored under a hashed name with no suffix; it is known by what
it holds, not by its name, and is opened read-only, so the backup is never
changed. The words newer iPhones keep only inside a message's formatting are
read from there.

**What it writes.** One file in MIRROR for each backup file, at the same
path with .txt added. In it, one section per conversation, `# NAME`, A to
Z: the contact's name, or the number when the phone has none (an iPhone
backup never has names, so its sections are numbers and group chats' names).
In each, the messages and calls in time order, a blank line between days, so
each passage the kernel serves is one day with one person.

**Times** are this machine's local time, unless `--tz` names the zone they
were sent in (`--tz America/Denver`); a zone this machine doesn't know is
refused. Your own messages are `me`, unless `--me` names you.

**Left out:** drafts and messages that never sent. Two backups that overlap
are two mirrors, each whole; a message in both is in both.

Files that are not phone backups are not counted; a backup it cannot read
(not valid XML, no message or call in it, a message with no date) is skipped
and counted.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (MIRROR inside
FOLDER or the other way round, FOLDER not a folder, or a zone it doesn't
know).

**Uses:** nothing from the kernel's functions, only its exit codes. Its tests
run `kernel.py` `init` and `bite` on the mirror it writes.

**Never:** writes inside FOLDER, changes an original, guesses a contact's
name, or goes online.
