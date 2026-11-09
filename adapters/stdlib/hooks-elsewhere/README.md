<!-- willow-addon
section: Assistants
line: The prompt hook for Gemini CLI, Codex and opencode, wherever they take hooks, held to Claude Code's answer byte for byte.
source: box
added: 2026-11-05
writes: record
network: none
hands: the passages served for each prompt, to the model of the assistant it hooks (Gemini CLI, Codex, opencode)
role: guards
tags: hooks
uses: claude-code
looks-for: index-cache, scan
-->
# hooks-elsewhere

Cited passages at each prompt for the assistants that aren't Claude Code,
held to [claude-code](../claude-code/)'s answer byte for byte.

    python adapters/stdlib/hooks-elsewhere/hooks_elsewhere.py list
    python adapters/stdlib/hooks-elsewhere/hooks_elsewhere.py setup --host HOST --box DIR
    python adapters/stdlib/hooks-elsewhere/hooks_elsewhere.py prompt --host HOST --box DIR

`setup` prints what to paste, and changes nothing. `prompt` is what the host
runs: it asks your folder through Claude Code's hook, then wraps only the
envelope the host needs. The framed passages inside are Claude's bytes.

| Host | Event | What the host gets |
|---|---|---|
| gemini-cli | BeforeAgent | JSON; Claude's block in `additionalContext` |
| codex-cli | UserPromptSubmit | Claude's block as plain stdout |
| opencode | `chat.message` plugin | Claude's block as synthetic text (native); Claude-compatible hooks get the same bytes as plain stdout |

**Not Cursor.** Cursor's `beforeSubmitPrompt` hook can only continue or block
a prompt; it has no field for injected context. `setup --host cursor` and
`prompt --host cursor` refuse and point at [cursor](../cursor/) (MCP). Copilot
and Windsurf stay MCP-only the same way, through [hosts](../hosts/).

Empty when your files don't hold the question; one line when the folder
couldn't be read. Always exits 0 once the command line is good, as Claude
Code's hook does.

**A big folder:** pass `--index` the way Claude Code's setup does; this
forwards it, and prints the [index-cache](../index-cache/) line that keeps
it current.

The other way in (tools the host calls) stays [hosts](../hosts/).

**Uses:** [claude-code](../claude-code/) for the bite and the frame.

**Never:** approves, reads your key, writes a host's settings for you, or
goes online. The record keeps the prompt's fingerprint and the places it
found, never its words.
