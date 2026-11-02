<!-- willow-addon
section: Finding things
line: Exact search through ripgrep, much faster on a big folder, its hits checked against the kernel's hashes.
source: new
added: 2026-10-30
needs: the ripgrep program, from the ripgrep wheel on PyPI or your own rg; MIT or Unlicense
floor: ripgrep 14.1.0
writes: nothing
network: none
-->
# ripgrep

Every line of your pile that holds some exact text, found by ripgrep, then
checked against the kernel: each hit is shown with the id of the passage
that holds it, the one the kernel would serve and cite.

    pip install -r adapters/deps/ripgrep/requirements.txt
    python adapters/deps/ripgrep/ripgrep.py --box DIR [--ignore-case] "TEXT"
    letters/county.txt:4  3f2a9c1b04de  You may file a response within 180 days.
    1 hit in 1 passage

The pinned wheel brings its own `rg`; one already on your PATH is used when
it doesn't.

**Exact.** TEXT is matched as written, not as a pattern: `f.le` finds
`f.le`, never `file`. `--ignore-case` matches any case.

**What it reads is the kernel's.** Hidden files and folders are skipped, as
the kernel skips them, and `.gitignore` is not obeyed, since the kernel
doesn't obey it. The files holding a hit are cut into passages by the
kernel's own `chunks` (on a scratch copy of them, removed after),
so a passage's id here is the id the kernel has. A hit the kernel doesn't
read as written, in a binary, a file not UTF-8 or too big, a web page's
markup, or past where it cuts a long line, is counted, never shown as a
passage.

**On willow's own repo** (10 MB, as a pile) "MAX_CHUNK" gives 33 hits in 28
passages, the same 28 the kernel finds reading every file in Python, in 0.09
seconds against 0.24; the gap grows with the folder.

**The guard sees Python, not rg.** rg is a program, so its
reads are its own. It is run with only `--json --fixed-strings
--no-ignore`, the text and the pile, and writes nothing.

**Without rg** it refuses and names the install: exit 2, never a quiet skip.

**Uses:** `chunks`, `read`, `config`, and the kernel's exit codes: 0 a hit
in a passage; 42 none; 2 refused.

**Never:** writes anything, not even the record, or goes online.
