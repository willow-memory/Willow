<!-- willow-addon
section: Ways to use it
line: A note written into your folder in one line, with its type and tags, so the next question can find it.
source: new
added: 2026-11-01
writes: to
network: none
tags: no-install, offline, writes-output, interface
-->
# capture

A note written into your folder in one line, so the next question can find it.

    python adapters/stdlib/capture/capture.py --to DIR [--type WORD] [--tags a,b] [--now TS] "the note"

`DIR` is a folder that already exists, usually the pile a box reads. One small
text file goes into it, one paragraph, no blank line:

    Plant out the tomatoes after the last frost.
    type: idea
    tags: garden, veg
    captured: 2026-11-01T09:30:00Z

The kernel serves a paragraph whole, so `kernel.py bite` finds it by the note's
words, its type (`idea`) or its tags (`garden`), and says the file and line.
The type is one lowercase word and defaults to `note`; a tag is one lowercase
word too, repeats are kept once, and with no `--tags` the line is left out
rather than written empty. The note's whitespace is folded to single spaces. A
note whose paragraph would run past the kernel's 500-character chunk is refused,
because a longer one would be cut in two and its type and tags parted from it.

The file is named for the second of capture and a fingerprint of what it holds,
`20261101T093000Z-<8 hex>.txt`, and is created, never opened over one that is
there: two captures never overwrite each other, and the same note twice in one
second becomes `-2`, `-3`. After you add notes, `kernel.py scan --box BOX` to
pick them up.

**Exit codes:** 0 written; 2 refused (a bad command line, DIR missing, not a
folder or a box, a type, tag or time that is not one, or a note that is empty or
too long).

**Uses:** the kernel's `chunks` (by its tests), `MAX_CHUNK`, `h256`, `now` and
exit codes.

**Never:** writes anything but that one file; makes DIR for you (a missing
folder is refused); writes into a box or touches its record, pile or key;
opens a file that is already there; or goes online.
