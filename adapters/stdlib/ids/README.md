<!-- willow-addon
section: Trust and proof
line: Every file and passage given its Software Heritage ID and IPFS CID, names the rest of the world already uses.
source: new
added: 2026-10-27
writes: nothing
network: none
tags: no-install, offline, read-only, trust
-->
# ids

Every file of your folder, named as Software Heritage names it and as IPFS
does, so what you hold can be cited in a paper, looked up in the world's
archives, or matched against anyone else's copy without sending a byte.

```
python adapters/stdlib/ids/ids.py --box DIR [PATH]

notes/garden.md
  swh:1:cnt:ce013625030ba8dba906f756967f9e9ca394464a
  bafkreicysg23kiwv34eg2d7qweipxwosdo2py4ldv42nbauguluen5v6am
2 files named
```

PATH narrows it to one file and adds its passages, each by its first line,
so a single paragraph can be cited on its own.

**The names are computed, not looked up.** The Software Heritage ID is
`swh:1:cnt:` and the file's git blob SHA-1, exactly as `git hash-object`
writes it (the tests hold it to git's own answer), so it matches the
archive's whether or not your file is there. The IPFS name is a CIDv1, raw
codec, SHA-256, base32: what `ipfs add --raw-leaves --cid-version=1` gives
a file of one chunk.

**Past one chunk, the name is said, not guessed.** A file over 256 KiB gets
an IPFS name only by a chunker's choices, which are the adder's, not the
bytes'; its row says `too big for a one-chunk CID`, and its Software
Heritage ID, which has no such ceiling, stands. A passage is named by its
own text's bytes, so the same paragraph in two folders carries the same
names.

Nothing goes online: the names are for the world, made at home. Hidden
files and folders are never read, and the same folder gives the same bytes.
Exit codes, the kernel's: 0 files named; 42 nothing in the folder, or PATH
isn't a file of it; 2 refused.

**Uses:** the kernel's `chunks` and `config`.

**Never:** changes your files; writes anything, even the record; goes
online to ask what a thing is called; guesses a name that depends on a
chunker's choices.
