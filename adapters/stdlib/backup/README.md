<!-- willow-addon
section: Trust and proof
line: Your record in one zip, every byte and the chain checked before it's kept; never beside your key, and it never reads the key.
source: new
added: 2026-10-24
writes: to
network: none
tags: everyday
-->
# backup

Your record copied somewhere safe, and checked.

    python adapters/stdlib/backup/backup.py --box DIR --to /media/usb

It writes one file, `willow-backup-YYYYMMDD-HHMMSS.zip`. The zip holds the
record, the box's settings, the suggestions handed in and the answers you
approved. Then it checks the copy before keeping it:

- every file's bytes match the box's;
- the copied record's chain holds, row by row, read by the kernel's own `read`.

A copy that doesn't check out is deleted and the run fails, so a zip that's
there is one that held. It never overwrites one.

**Your key isn't in it.** No add-on reads the key, and this one doesn't
either. The key approves answers, so it belongs somewhere other than the
backup: a USB stick, a password manager. The output says where your key is
and how to copy it.

**Refused:** a `--to` that is the key's own folder, or that is inside the
box or your files. A backup beside the key, or inside what it backs up,
isn't a backup.

**To restore:** unzip it where you want the box, and copy your key back to
where the box's kernel.json says it lives. `kernel.py verify` then holds.

**Uses:** the kernel's `read` and `config`.

**Never:** reads your key, changes the box, or overwrites a file.
