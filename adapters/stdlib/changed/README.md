<!-- willow-addon
section: Trust and proof
line: What's new, edited or deleted in your folder since the last check, as fingerprint rows.
source: bot
added: 2026-10-24
writes: record
network: none
tags: everyday
-->
# changed

What's new, edited or gone in your folder since you last looked.

    python adapters/stdlib/changed/changed.py --box DIR

    Since the last check (2026-10-20 09:12):
      new      letters/2026-10-22-bank.txt
      edited   care/log.txt
      deleted  old/insurance.txt

Each check goes on the record as one `changed` row, through the kernel's own
`append`. The row keeps paths and SHA-256 fingerprints, never what a file says.

- **The first check** lists every file and its fingerprint (any file not in a hidden folder; a PDF too).
- **Each later check** keeps only what's new, edited or deleted since the one before.

So what your folder held at any check can be rebuilt from the record alone,
and the record grows by what changed, not by the size of the folder. The
[history](../history/) add-on reads these rows out in plain sentences too.

An approved answer that cites an edited or deleted file may no longer hold;
the [stale](../stale/) add-on says exactly which.

Exit codes, the kernel's: 0 nothing changed, or the first check; 42
something changed; 2 refused (a record that doesn't verify).

**Never:** reads a file's words into the record, or changes your folder.
