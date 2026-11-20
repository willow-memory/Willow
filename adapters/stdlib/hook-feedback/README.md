<!-- willow-addon
section: Assistants
line: Your corrections to an assistant (no, wrong, I said) caught by fixed patterns at each prompt and handed in through propose, to keep or drop.
source: new
added: 2026-11-07
version: 0.1.0
writes: record
network: none
role: guards
tags: hooks
-->
# hook-feedback

Your corrections to an assistant (`no`, `wrong`, `I said`) caught by a
words list at each prompt and handed in through propose, for you to keep or
drop.

```
python adapters/stdlib/hook-feedback/hook_feedback.py run --box DIR [--words FILE]
python adapters/stdlib/hook-feedback/hook_feedback.py match [--words FILE]
python adapters/stdlib/hook-feedback/hook_feedback.py check --box DIR
```

**The words list**, [corrections.txt](corrections.txt), says what a
correction is: a `+` phrase the prompt starts with, a `~` phrase anywhere in
it, and never a `-` phrase it starts with, read first. The base list
catches `no`, `wrong`, `nope`, `not what I asked` and `I said`, and leaves
`no thanks`, `no worries`, `no problem`, `no rush`, `no hurry` and `no
need`. A phrase ends at a word's end (`no` is not `now` or `nobody`); case
and curly apostrophes don't matter. Copy it and point `--words` at your
copy to make it yours; it replaces the base list whole.

`run` is a UserPromptSubmit hook. It reads the JSON Claude Code, Gemini CLI
and Cursor send on standard input:

| Prompt | What happens |
|---|---|
| a correction by the words list | bites that text and proposes it under `feedback/<hash>.md` (empty cites); a `hook-feedback` row names the proposal for `check` |
| anything else, or not UserPromptSubmit | allowed; nothing written |

Seal or decline the proposal yourself (`kernel.py seal` / `decline`). The
hook never seals.

`match` says only whether a prompt is a correction: exit 42 when it is, 0
when it isn't, 2 when what it was sent can't be read. It needs no box,
proposes nothing and writes nothing, for a program that keeps the
corrections itself and hands them in later (as session-seal's `--with`
does, a session's at once).

`check` lists each waiting `hook-feedback` proposal still on the box; exit
42 when any wait, 0 when none (`no feedback waiting`).

To use it, put the `run` line where the assistant's settings name a
UserPromptSubmit hook.

It never reads the key. Exit codes: 0 allowed (or `check` none waiting, or
`match` no correction); 42 `check` found waiting feedback (or `match` a
correction); 2 refused, or a words list that isn't one.

**Never:** reads the key; seals or declines for you; invents a prompt the
call didn't send; treats an ordinary ask as a correction.
