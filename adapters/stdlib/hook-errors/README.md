<!-- willow-addon
section: Assistants
line: Each failed command an assistant runs kept as a row of its hash and exit code, so the third time it fails it's named, not retried blind.
source: new
added: 2026-11-07
version: 0.1.1
writes: record
network: none
role: guards
tags: hooks
-->
# hook-errors

Each failed command an assistant runs kept as a row of its hash and exit
code, so the same failure the third time is named, not retried blind.

```
python adapters/stdlib/hook-errors/hook_errors.py run --box DIR
python adapters/stdlib/hook-errors/hook_errors.py check --box DIR
```

`run` is both a PreToolUse and a PostToolUse hook for shell tools (Bash,
Shell, run_terminal_cmd). It reads the JSON Claude Code, Gemini CLI and
Cursor send on standard input:

| Event | What happens |
|---|---|
| PostToolUse (an exit code is present) | a non-zero exit appends a `hook-errors` row (command hash, exit, and the call's `session_id` when sent), never the command's words; the call is allowed |
| PreToolUse (no exit code yet) | if this session already has two rows for the same command hash and the same exit, the third try is blocked (exit 2) and named; otherwise allowed |
| anything else | allowed; nothing is written |

```
blocked: this command has failed 2 times with exit 1 (last at row 3); look at those before trying again
```

`check` is the same look for a person: each (command hash, exit) that has
failed at least once is listed by its hash and last row; exit 42 when any
has reached the block rung (two or more). A command can carry the person's
words, and the record keeps acts, not words, so the command is kept by its
hash alone: the assistant that ran it has it in hand at the third try.

To use it, put the `run` line where the assistant's settings name a
PreToolUse hook for Bash (or Shell) and a PostToolUse hook for the same
tools, so failures are recorded and the third identical try is stopped.

It never reads the key. Exit codes: 0 allowed (or `check` none at the block
rung); 42 `check` found a repeated failure; 2 refused or blocked.

**Never:** reads the key; lets the same (command, exit) fail a third time
blind; invents a command the call didn't name; keeps a command's words in
the record.
