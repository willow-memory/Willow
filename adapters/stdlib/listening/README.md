<!-- willow-addon
section: Reading more kinds of files
line: Spotify's data download: what you listened to, by day, so you can ask what was on that summer.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# listening

What you listened to, searchable by day, artist and track.

    python adapters/stdlib/listening/listening.py mirror --from FOLDER --to MIRROR

Each play is a dated line, oldest first:

    2024-03-02 08:15  Nina Simone - Sinnerman (10:20)
    2024-03-02 09:02  Garden Radio: Staking tomatoes (24:10)

Both shapes of the download are read: the account-data
StreamingHistory files and the extended Streaming_History_Audio files, whose
podcasts are written as the show, a colon and the episode. The time is when the
play ended, as the file gives it; the length in brackets is how much was played.
A play of under 30 seconds is a skip and is left out. IP addresses, device names
and the other fields of the extended history are not copied. Other JSON is
skipped and counted.

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
