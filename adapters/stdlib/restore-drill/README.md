<!-- willow-addon
section: Trust and proof
line: A backup zip restored into scratch and verified there, chain and every file, so you know it restores before the day you need it.
source: new
added: 2026-10-31
writes: nothing
network: none
tags: no-install, offline, read-only, trust
-->
# restore-drill

A backup zip restored into scratch and verified there, so you know it
restores before the day you need it.

    python adapters/stdlib/restore-drill/restore_drill.py --from ZIP

    restored: willow-backup-20261024-093000.zip, 5 files, 4 rows; the chain holds

Unzips ZIP into scratch this add-on makes itself (never a folder you name),
then checks every member stays inside that scratch, every CRC, that the
zip holds kernel.json and record.jsonl, and that the restored record's
chain holds, read by the kernel. kernel.json is confirmed, never written
into scratch: a folder that holds one is a box. The scratch is deleted
when the run ends.

It never compares the zip to a live box: [backup](../backup/) already
checked the copy the day it was written. This one asks the other question:
does it still restore. It never reads the key.

A file that isn't a zip, or a zip that isn't a willow backup, is "nothing
there". Exit codes, the kernel's: 0 it restores; 42 nothing there, or the
drill failed; 2 refused.

**Uses:** the kernel's `read`.

**Never:** writes beside ZIP, reads the key, or changes the zip.
