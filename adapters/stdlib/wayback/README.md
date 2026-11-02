<!-- willow-addon
section: Trust and proof
line: The Wayback Machine's copy of a page from a window of days, saved beside your own snapshot and compared with it byte for byte.
source: new
added: 2026-10-24
writes: to
network: archive.org, to find the archived copy and fetch it
tags: sources
uses: snapshot
-->
# wayback

The Wayback Machine's copy of a page, from a window of days, saved beside
your own and compared with it.

    python adapters/stdlib/wayback/wayback.py find --url URL --to FOLDER
        [--after YYYYMMDD] [--before YYYYMMDD] [--against FILE] [--name NAME]

A copy you fetched yourself says what a page said when you fetched it. The
Wayback Machine at web.archive.org says what someone else saw, so a copy can
be checked by a party that isn't you.

**find** asks the archive's index for the captures of URL that answered
200, keeps those on or after `--after` and before `--before`, and takes the
latest. It saves that capture's bytes as they were archived (without the
archive's banner) through the [snapshot](../snapshot/) add-on, so the copy
has its own line in `<FOLDER>/.snapshots.jsonl`, with `wayback` (the
capture's time) and `of` (the page it is a capture of). With `--against
FILE` it says whether the bytes are the same:

    capture   20261012080000 of https://…   saved as old.wayback.pdf
    same bytes as old.pdf   sha256 …

or `DIFFERS from old.pdf`, with both hashes. A page whose bytes differ may
still say the same words (a web page carries a different script every
time); [clauses](../clauses/) `diff` says whether it does.

**Said, not hidden:** no capture in the window, and no answer from the
archive, are each said as themselves, never as a difference.

**What it was built for:** checking the "before" copy of Google's privacy
policy in
[demo/google-privacy-2026-10-16](../../../demo/google-privacy-2026-10-16/).

**Changed from the idea:** the idea wrote a pairing row to the record.
The capture is a source like any other, so it is saved as a snapshot, in
the folder a box can be pointed at, and the pairing is its line there.

**Exit codes:** 0 a capture saved (and, with `--against`, the same bytes);
42 no capture, no answer, or different bytes; 2 refused.

**Uses:** the snapshot add-on's `get`, `save` and `name_for`; the kernel's
exit codes.

**Never:** goes anywhere but the archive, or writes outside FOLDER.
