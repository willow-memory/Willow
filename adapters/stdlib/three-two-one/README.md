<!-- willow-addon
section: Trust and proof
line: How many verified copies of your record exist and where, held to three copies, on two kinds of storage, one away from home.
source: new
added: 2026-10-31
writes: nothing
network: none
tags: no-install, offline, read-only, trust
-->
# three-two-one

How many verified copies of your record exist, and whether that is enough.

    python adapters/stdlib/three-two-one/three_two_one.py --box DIR \
        --copy usb:FOLDER_OR_ZIP --copy away:FOLDER_OR_ZIP

    3-2-1 holds: 3 copies on 2 kinds of storage, one away from home
      disk  the box                         holds (4 rows)
      usb   willow-backup-20261024-093000.zip holds (4 rows)
      away  box                             holds (4 rows)

The box is the first copy, kind `disk`. Each `--copy` is another: a folder
that is a box, or a zip [backup](../backup/) wrote. A copy counts when its
record's chain holds, read by the kernel. The kinds are the words you give
(`disk`, `usb`, `away`); `away`, `offsite` and `remote` count as the one
away from home.

The rule is three copies, on two kinds of storage, one away from home. A
copy that isn't a box, or whose chain doesn't hold, is said and not
counted. It writes nothing.

Exit codes, the kernel's: 0 the rule holds; 42 it doesn't, or a copy
failed; 2 refused.

**Uses:** the kernel's `read`.

**Never:** writes anything, or reads the key.
