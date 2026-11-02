<!-- willow-addon
section: Reading more kinds of files
line: Claude Code, Codex, Gemini CLI, Cursor and Copilot session files as plain text, each turn numbered, so you can ask what an agent was told.
source: new
added: 2026-10-31
writes: to
network: none
-->
# agent-transcript

Agent session files as numbered turns, so you can ask what an agent was told.

    python adapters/stdlib/agent-transcript/agent_transcript.py \
        mirror --from FOLDER --to MIRROR

    session f601db41-9cd9-44dd-9fee-6e7494413255
    2 turns

    1  you
    When is the dentist?

    2  assistant
    Tuesday at 3.

Walks FOLDER for jsonl session files (Claude Code, Cursor, and others
that store one JSON object a line). Each file becomes the spoken turns:
what you typed and what the assistant said. Tool calls, tool results and
hidden thinking are left out. [transcript-redact](../transcript-redact/)
is the one that takes keys out before you share a file.

Each session is written to MIRROR at the same relative path with .txt
added. A file that is not a session is skipped and counted. Point the
kernel at MIRROR to ask questions of it.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused
(FOLDER is not a folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes.

**Never:** writes inside FOLDER, prints a tool result, or reads the key.
