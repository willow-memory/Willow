<!-- willow-addon
section: Reading more kinds of files
line: System and app logs (syslog, journald's export, nginx): each line dated, so you can ask when it started.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# logs

Your system and web-server logs, searchable by time, host, program and message.

    python adapters/stdlib/logs/logs.py mirror --from FOLDER --to MIRROR

Each entry of a log is a dated line:

    2024-03-02 08:15  host sshd: Accepted publickey for ana from 10.0.0.2
    Mar 02 08:16  host cron: (root) CMD (run-parts /etc/cron.hourly)
    2024-03-02 08:17  192.0.2.7 GET /garden 200 1234

Three kinds are read: syslog (the classic `Mar  2 08:15:30 host sshd[1234]:`
form or rsyslog's ISO form), journald's export (`journalctl -o export`) and a web
server's access log (nginx and Apache combined). A classic syslog line has no
year and none is invented: it keeps its month and day as written. Process ids are
taken off, and a line that is not an entry (a stack trace) is left out. A file is
one of these when most of its first twenty lines are; any other `.log` is
skipped and counted, and one over 50 MB is not read.

Each file is written to MIRROR at the same relative path with .txt added.
A mirror bigger than the kernel reads from one file (1 MB) is cut between
entries into parts it can read, `<name>.txt`, then `<name>.part2.txt` and
on, so a busy day's journal isn't silently left out; parts a shorter earlier
run left behind are removed.
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
