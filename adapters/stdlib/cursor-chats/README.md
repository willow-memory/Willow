<!-- willow-addon
section: Reading more kinds of files
line: Cursor agent chats, each kept in its own SQLite database, as plain text with each turn numbered, so you can ask what the agent was told.
source: new
added: 2026-11-11
version: 0.1.0
writes: to
network: none
role: reads
reads: .db
-->
# cursor-chats

Cursor agent chats as numbered turns, so you can ask what the agent was told.

    python adapters/stdlib/cursor-chats/cursor_chats.py \
        mirror --from FOLDER --to MIRROR

    chat 1b2c3d4e-0000-4000-8000-000000000001
    name: Dentist
    started: 2026-10-31T09:00:00Z
    model: some-model
    2 turns

    1  you
    When is the dentist?

    2  assistant
    Tuesday at 3.

Cursor's agent keeps each chat in a SQLite database of its own,
`<project>/<chat>/store.db` under its chats folder. Walks FOLDER for those and
writes each chat as the spoken turns: what you typed and what the assistant
said. System prompts, tool calls, tool results and reasoning are left out.
[agent-transcript](../agent-transcript/) reads Cursor's older line-by-line
sessions; [transcript-redact](../transcript-redact/) takes keys out before you
share a file.

The order comes from the store: `meta` names a root, and the root links the
messages in the order they were said. When it can't be read, nothing is
guessed: the header says `order: not found in the store` and the turns are
listed as SQLite returns them.

Each chat is written to MIRROR at the same relative path with .txt added. A
`store.db` that is not a Cursor chat (not SQLite, no `meta`, no spoken turns)
is skipped and counted. Point the kernel at MIRROR to ask questions of it.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused
(FOLDER is not a folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes.

**Never:** writes inside FOLDER (it opens each store read-only), prints a
tool result, or reads the key.
