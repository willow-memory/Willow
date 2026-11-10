<!-- willow-addon
section: Assistants
line: A PreToolUse hook that refuses an edit to a file the assistant hasn't read this session, or that changed since, each read kept as a hash.
source: new
added: 2026-11-07
version: 0.1.0
writes: record
network: none
role: guards
tags: hooks
-->
# hook-read-first

A PreToolUse hook that refuses an edit until the file was read this session
as the bytes still on disk.

```
python adapters/stdlib/hook-read-first/hook_read_first.py run --box DIR
python adapters/stdlib/hook-read-first/hook_read_first.py check --box DIR FILE
```

`run` reads what the assistant is about to do (the JSON Claude Code, Gemini
CLI and Cursor send on standard input):

| Tool | What happens |
|---|---|
| Read, NotebookRead | the file's SHA-256 is appended as a `hook-read-first` row (path, hash, and the call's `session_id` when sent); the call is allowed |
| Write, Edit, MultiEdit, NotebookEdit | an existing file must have a read row for this session whose hash still matches; else exit 2 and say why. Creating a file (nothing there yet) is allowed without a read. After an edit, the old read no longer matches, so the next edit needs a fresh Read |
| anything else | allowed; nothing is written |

```
blocked: never read  /home/you/notes.md
blocked: changed     /home/you/notes.md (read at row 3)
```

`check` is the same look for a person: each FILE is `read` (row named),
`changed` since that row, or `never read` (exit 42 unless every file is read
and unchanged).

To use it, put the `run` line where the assistant's settings name a
PreToolUse hook (for Claude Code, a hook entry matching Read and the edit
tools, or matching `.*`).

It never reads the key. Exit codes: 0 allowed (or `check` every file read);
42 `check` found a gap; 2 refused or blocked.

**Never:** reads the key; allows an edit of a file that wasn't read as it
is now; invents a path the call didn't name.
