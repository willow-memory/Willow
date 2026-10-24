<!-- willow-addon
section: Assistants
line: Wraps any hook so a crash, a timeout or output it can't read blocks the tool, since Claude Code, Gemini CLI, Codex and Cursor all let the tool run by default.
source: new
added: 2026-10-24
writes: nothing
network: none
tags: no-install, offline, read-only, assistant, hooks
-->
# hook-fail-closed

A hook that breaks blocks the tool instead of letting it run.

    python adapters/stdlib/hook-fail-closed/hook_fail_closed.py --hook "COMMAND" [--timeout S] [--json]

Claude Code, Gemini CLI, Codex and Cursor all let a tool run when its hook
crashes, times out or prints something they can't read. Put this where the
hook's command was, with the hook's command in `--hook`:

| The hook | What happens |
|---|---|
| exits 0 | its output passes through: allowed |
| exits 2 | its reason passes through: blocked |
| exits anything else, crashes, runs past `--timeout` (30 s unless said), or won't start | blocked, and why is said |
| prints output that isn't JSON, with `--json` | blocked (empty output is fine) |

Exit 2 is how all four assistants spell "block". Use `--json` for a hook
whose answer is JSON, such as a PreToolUse decision; a hook that answers in
words, like [claude-code](../claude-code/)'s prompt hook, runs without it.

The command is one string, split the way a shell splits words, and run
without a shell.

**Never:** reads or writes anything, or lets a broken hook's tool run.
