<!-- willow-addon
section: Trust and proof
line: Files in formats that may stop opening (old office files, proprietary ones, those no reader handles) flagged while you can still convert them.
source: new
added: 2026-10-31
writes: nothing
network: none
tags: no-install, offline, read-only, trust
-->
# format-rot

Files in formats that may stop opening, flagged while you can still
convert them.

    python adapters/stdlib/format-rot/format_rot.py --from FOLDER

    format-rot needs you: 3 files
      .apk   2  no reader in this repository
      .doc   1  old office; convert while it still opens

Walks FOLDER (not hidden parts) and counts old office files (`.doc`,
`.xls`, `.ppt` and their kin), proprietary ones (`.pages`, `.numbers`),
and installers this repository has no reader for (`.apk`, `.dmg`). Current
`.docx` and `.pdf` are not flagged: [office](../office/) and
[pdf](../../deps/pdf/) still read them. [box-health](../box-health/) says
which files the bite skips; this one says which of those formats may stop
opening.

It only reads. Exit codes, the kernel's: 0 nothing at risk; 42 something
flagged; 2 refused.

**Uses:** the kernel's exit codes.

**Never:** converts a file, writes anything, or reads the key.
