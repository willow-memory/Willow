<!-- willow-addon
section: Assistants
line: Throws empty, malformed, oversized and non-UTF-8 input at a hook and fails it if any of them crash it, since a crashed hook lets the tool run.
source: new
added: 2026-10-24
writes: nothing
network: none
tags: no-install, offline, read-only, assistant, hooks
-->
# hook-fuzz

Bad input thrown at a hook, and each one that breaks it named.

    python adapters/stdlib/hook-fuzz/hook_fuzz.py --hook "COMMAND" [--timeout S]

A hook can say it fails closed and still crash on input nobody tried; in
Claude Code a crashed hook lets the tool run. This hands the hook thirteen
inputs, one at a time, always the same thirteen: nothing, blank, JSON that
isn't an object (`null`, `[]`, `5`), `{}`, an object cut off halfway, a
number where the prompt goes, a million-character prompt, bytes that
aren't UTF-8, a NUL, a lone surrogate, and lists nested ten thousand deep.

A hook holds when it exits 0 or 2 within `--timeout` seconds (10 unless
said) and prints no Python traceback. Another exit code, a crash, a hang,
or a traceback even under exit 0 is a break:

    broke  null        exited 1 with a traceback: AttributeError: 'NoneType' object has no attribute 'get'
    9 of 13 inputs held

That is what its first run said of [claude-code](../claude-code/)'s prompt
hook, which says it always exits 0. It crashed on `null`, `[]`, `5` and the
deep lists; it now holds on all thirteen.

**Never:** reads or writes anything. Exit 42 when an input broke the hook.
