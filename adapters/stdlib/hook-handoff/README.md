<!-- willow-addon
section: Assistants
line: A Stop hook that writes where the session ended, and the next session's first prompt gets it back, so nothing rides on the assistant's memory.
source: new
added: 2026-11-07
writes: record
network: none
role: guards
tags: hooks
-->
# hook-handoff

A Stop hook that writes where the session ended, and the next session's
first prompt gets it back, so nothing rides on the assistant's memory.

```
python adapters/stdlib/hook-handoff/hook_handoff.py run --box DIR
python adapters/stdlib/hook-handoff/hook_handoff.py check --box DIR
```

`run` reads the JSON Claude Code, Gemini CLI and Cursor send on standard
input and branches on the hook event:

| Event | What happens |
|---|---|
| Stop | appends a `hook-handoff` row (cwd, session_id, and transcript path when sent). When `stop_hook_active` is true, nothing is written |
| SessionStart, UserPromptSubmit | the latest handoff from a *different* session is printed as JSON `additionalContext`, once per new session; same session or none yet prints nothing |
| anything else | allowed; nothing written or printed |

```
{"additionalContext": "hook-handoff: session s1 ended in /home/you/proj (row 2). Pick up from there; do not invent where you left off."}
```

`check` is the same look for a person: the latest handoff line, or `no
handoff yet` (exit 42 when none).

To use it, put the `run` line where the assistant's settings name a Stop
hook and a SessionStart (or UserPromptSubmit) hook.

It never reads the key. Exit codes: 0 allowed (or `check` has a handoff);
42 `check` found none; 2 refused.

**Never:** reads the key; invents a cwd or session the call didn't name;
hands a session its own Stop back as if it were a prior one.
