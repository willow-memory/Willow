<!-- willow-addon
section: Assistants
line: Your corrections to an assistant (no, wrong, I said) caught by fixed patterns at each prompt and handed in through propose, for you to keep or drop.
source: new
added: 2026-11-07
writes: record
network: none
role: guards
tags: hooks
-->
# hook-feedback

Your corrections to an assistant (`no`, `wrong`, `I said`) caught by fixed
patterns at each prompt and handed in through propose, for you to keep or
drop.

```
python adapters/stdlib/hook-feedback/hook_feedback.py run --box DIR
python adapters/stdlib/hook-feedback/hook_feedback.py check --box DIR
```

`run` is a UserPromptSubmit hook. It reads the JSON Claude Code, Gemini CLI
and Cursor send on standard input:

| Prompt | What happens |
|---|---|
| starts with `no` or `wrong`, or holds `I said` as a word | bites that text and proposes it under `feedback/<hash>.md` (empty cites); a `hook-feedback` row names the proposal for `check` |
| anything else, or not UserPromptSubmit | allowed; nothing written |

Seal or decline the proposal yourself (`kernel.py seal` / `decline`). The
hook never seals.

`check` lists each waiting `hook-feedback` proposal still on the box; exit
42 when any wait, 0 when none (`no feedback waiting`).

To use it, put the `run` line where the assistant's settings name a
UserPromptSubmit hook.

It never reads the key. Exit codes: 0 allowed (or `check` none waiting);
42 `check` found waiting feedback; 2 refused.

**Never:** reads the key; seals or declines for you; invents a prompt the
call didn't send; treats an ordinary ask as a correction.
