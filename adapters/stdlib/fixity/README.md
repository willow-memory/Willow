<!-- willow-addon
section: Trust and proof
line: Your folder's files hashed again now and then, the hashes kept on the record, and a file that changed with no edit of yours flagged as rot.
source: new
added: 2026-10-31
writes: record
network: none
-->
# fixity

Your folder's files hashed again now and then, so a silent change is said.

    python adapters/stdlib/fixity/fixity.py --box DIR

    Fixity needs you:
      rot      care/log.txt
      edited   notes.txt

Each check goes on the record as one `fixity` row, through the kernel's own
`append`. The row keeps paths, SHA-256, size and mtime, never what a file
says.

- **The first check** hashes every file not in a hidden folder.
- **Each later check** hashes them again and compares with the last.

A hash that changed with a newer mtime is an edit of yours. A hash that
changed with the same or an older mtime is rot: the bytes moved and no
edit did. [changed](../changed/) says what is new or gone since you last
looked; this one says which of those edits never happened.

Exit codes, the kernel's: 0 the first check, or every file matches; 42
something changed; 2 refused (a record that doesn't verify).

**Uses:** the kernel's `read`, `append` and `config`.

**Never:** reads a file's words into the record, or changes your folder.
