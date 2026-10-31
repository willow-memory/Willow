<!-- willow-addon
section: Trust and proof
line: A box's health in one line: files it can't read, readers out of date, and when the chain was last checked.
source: new
added: 2026-10-29
writes: nothing
network: none
tags: no-install, offline, read-only, trust
-->
# box-health

Is the box all right? One line.

    python adapters/stdlib/box-health/box_health.py --box DIR [--long]

    box ok: 214 rows hold; 3 approved, 2 waiting; every file readable; words list as last used; last out row 2026-10-20 (4 days ago)

    box needs you: 9 files can't be read (3 .docx, read by office; 2 .pdf, read by pdf); 3 rows hold; 0 approved, 0 waiting; no out row yet

What it looks at, in this order:

| Part | Says |
|---|---|
| the chain | whether every row's hash holds; a break is said first and alone, since nothing after it can be trusted |
| approvals | how many hold under your key, how many suggestions wait, and any approval that fails its proof or whose proposal file is no longer the bytes you approved |
| files it can't read | the files in your folder the bite skips (binary, too large, not UTF-8 text), counted by extension, with the add-on that reads that kind of file when this repository has one, and how many of them are over the kernel's 1 MB |
| the words list | whether it is still the one the last question used, and that it reads at all |
| `out` | when the record last had an out row, the kernel's look at what waits on you, and how long ago |

Hidden files and folders are not counted: the bite doesn't read them either.
A waiting suggestion, an unreadable file, a changed words list or a box that
has never had an out row each says "needs you", since each is something you
can act on. `--long` puts every part on its own line, what needs you first.

The approvals are checked through the kernel's `sealed`, which reads your key
there and nowhere here. It writes nothing, not even an out row, so asking
how the box is doesn't move the record's tip.

Exit codes, the kernel's: 0 ok; 42 something needs you; 2 refused (a chain
that doesn't hold, or a bad command line).

**What it doesn't do:** run the readers or say what is inside an unreadable
file. It points at the add-on; running it is yours.

**Uses:** the kernel's `read`, `sealed`, `standing` and `read_words`.

**Never:** writes anything, or reads the key.
