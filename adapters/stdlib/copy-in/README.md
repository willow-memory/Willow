<!-- willow-addon
section: Finding things
line: New files from another folder or device copied into yours, each logged with its SHA-256; nothing deleted, a changed file a second copy.
source: new
added: 2026-11-14
version: 0.1.0
writes: to
network: none
role: tools
-->
# copy-in

New files from another folder or device copied into yours, each logged with
its SHA-256; nothing deleted, a changed file a second copy.

    python adapters/stdlib/copy-in/copy_in.py --from FOLDER --to DIR [--skip PREFIX ...] [--dry-run] [--json]

    copy-in: populated, copied 2 new files, 41 already in, 0 there already, 0 not done, 1 skipped
    ## copied
      scan-0412.pdf          copied
    ## beside an earlier copy
      notes.md               copied beside it, as notes (2).md: different bytes

**What it's for.** A phone, a card or another computer has files your
stacks should see. FOLDER is what came from it, however it came: the
carrier is yours (a cable and `adb pull`, a mounted card, a synced folder).
DIR is the folder your stacks already read. Run it again whenever the other
device has new files; only what DIR hasn't had comes in.

**The log is the memory.** Each copy is a line of `<DIR>/copied-in.jsonl`:
its path in FOLDER, where it went in DIR, its size and its SHA-256. A file
whose hash is in the log is "already in", wherever it sits in FOLDER, so a
file moved on the phone isn't copied twice, and one you deleted from DIR
stays deleted. The same bytes twice in FOLDER come in once. Every copy is
read back and must hash the same.

**Nothing is deleted, nothing replaced.** A file gone from FOLDER stays in
DIR. New bytes at a path DIR already holds (the file changed on the phone,
or another file had its name) go beside it as `name (2).ext`, then (3); the
first copy stays as it was.

**Not done, and said.** A file that can't be read, a copy that doesn't hash
the same, and a link (never followed, so nothing outside FOLDER comes in)
are listed under "not done", and it exits 42. A path under `--skip PREFIX`
is passed over and counted. `--dry-run` says the same and writes nothing;
`--json` is the same report as one JSON object.

**Refused** (exit 2): a bad command line, FOLDER not a folder that's there,
DIR a file or its parent missing, one inside the other, or a log line it
didn't write.

**What it misreads.** It knows files by their bytes, so a file whose time
changed and bytes didn't is "already in". It reads only what FOLDER shows;
what the carrier couldn't reach (another app's own storage on a phone) isn't
there to copy.
