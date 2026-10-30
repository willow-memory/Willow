<!-- willow-addon
section: Reading more kinds of files
line: IRC logs from WeeChat, irssi or ZNC, one dated line per message, by network and channel.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# irc

Your IRC logs, searchable by day, channel and nick.

    python adapters/stdlib/irc/irc.py mirror --from FOLDER --to MIRROR

Each message is a dated line with the channel it was said in:

    2024-03-02 08:15  #garden  ana: Six hours of sun, I read.
    2024-03-02 08:16  #garden  * ben waves

Three loggers are read, told apart by their lines: WeeChat's tab-separated
`date time, nick, message`; irssi's `08:15 < nick> message`, whose dates come
from its "Log opened" and "Day changed" lines; and ZNC's `[08:15:30] <nick>`
message, whose date is in the file name. The channel is read from the file name,
with the network and the date dropped. Messages and actions are kept; joins,
parts, quits, modes and topics are not. A `.log` that is something else (a
syslog, say) is skipped and counted.

Each file is written to MIRROR at the same relative path with .txt added.
FOLDER is only read: hidden folders and files are skipped, and nothing is
written inside it. A file that can't be read is skipped and counted, never a
crash:

    wrote 2 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`); Python's
standard library for the format.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, or goes online.
