<!-- willow-addon
section: Assistants
line: Every hook's answer kept as a row with the hashes of what it was given and what it said, and check runs it again to prove the same input still gets the same answer.
source: new
added: 2026-10-24
writes: record, to
network: none
tags: no-install, offline, records, assistant, hooks
-->
# hook-replay

Every hook answer on the record, and each one run again.

    python adapters/stdlib/hook-replay/hook_replay.py --box DIR --to INPUTS run --hook "COMMAND"
    python adapters/stdlib/hook-replay/hook_replay.py --box DIR --from INPUTS check

`run` stands where the hook stood: it hands the hook its input, passes its
output and exit code through, and writes one `hook-replay` row through the
kernel's own append: the command, and the SHA-256 of the input, of the
output and of what it said on standard error, and its exit code. The record
keeps no words, so the input is saved under INPUTS as `<sha256>.in`, once.

`check` runs every row's command again on its saved input:

    differs   row 2: its exit
    1 of 2 hook answers held

| Each row | Means |
|---|---|
| held | the same output, errors and exit code |
| differs | another answer, and which part changed |
| not kept | its input isn't in INPUTS, or isn't the bytes the row hashed: said, never skipped |

A hook that answers from a folder that changes (the claude-code prompt hook,
when you add files) differs for a reason; one that differs on the same
folder isn't deterministic.

**Never:** reads the key, or keeps an input's words on the record.
