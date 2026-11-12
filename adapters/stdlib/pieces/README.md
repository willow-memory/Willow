<!-- willow-addon
section: Finding things
line: Your folder's passages a folder at a time, the same as the kernel reads them, so a big folder is never held in memory all at once.
source: new
added: 2026-11-11
version: 0.1.0
writes: nothing
network: none
role: tools
-->
# pieces

Your folder's passages a folder at a time, the same as the kernel reads them, so a big folder is never held in memory all at once.

    python adapters/stdlib/pieces/pieces.py --box DIR

    pieces: 11867841 passages from 180240 files in 21008 pieces; at most 79040 at once (read/commits/forge-forks-node9-proxy)

The kernel reads a folder into one list, every passage at once. That is
fine for most folders. A folder of a few gigabytes is more than the
machine's memory: one of 3.4 GB, 11.9 million passages, grew a page to
12.8 GB before the system stopped it. Read through this add-on, the same
folder peaked at about 100 MB.

**The passages are the kernel's own.** Each folder's own files are read by
the kernel itself, through a scratch folder of links to just those files,
so every passage is cut exactly as the kernel cuts it, with the same path,
and they come out in the kernel's order. The next folder is read only once
the last is done with. A file is never split between two pieces, so
anything that looks within one file (a date heading over the lines under
it, a calendar event's summary under its start) finds the same thing.

For other add-ons it offers three things:

- `folders(pile)`: the passages, one folder's own files at a time;
- `passages(pile)`: the same, one passage at a time;
- `of_file(pile, path)`: one file's passages, and no other file read.

[coming-up](../coming-up/), [stale](../stale/), [digest](../digest/) (through
those two) and [browse](../browse/) use it when it is beside them, and read
the kernel's way when it isn't. Reading this way saves memory, not time:
every file is still read, so on a big folder a question that needs all of it
still takes minutes.

It follows a linked folder only when the kernel would on this Python, and
leaves out what the kernel leaves out: hidden names, binaries, anything not
UTF-8, a file over the kernel's size cap.

The command line reads the box's pile this way and says how much it held,
and the most passages it held at once.

**Exit codes:** 0 read; 2 refused (not a box, a bad command line).

**Uses:** the kernel's `chunks` and `config`.

**Never:** writes the box or reads the key. Its only writes are scratch
links, in a temporary folder of its own.
