<!-- willow-addon
section: Reading more kinds of files
line: Claude Code, Codex, Gemini CLI, Cursor and Copilot session files as plain text, each turn numbered, so you can ask what an agent was told.
source: new
added: 2026-10-31
version: 0.3.0
writes: to
network: none
role: reads
reads: .jsonl
-->
# agent-transcript

Agent session files as numbered turns, so you can ask what an agent was told.

    python adapters/stdlib/agent-transcript/agent_transcript.py \
        mirror --from FOLDER --to MIRROR

    session f601db41-9cd9-44dd-9fee-6e7494413255
    started: 2026-10-31T09:00:00.000Z
    ended: 2026-10-31T09:00:05.000Z
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

When a session ran is read from the file, so sessions sort by day:
`started:` and `ended:` are the earliest and latest ISO `timestamp` on its
lines, as the file writes them (a line with a malformed one is ignored). A
file with no such field but a `<timestamp>...</timestamp>` tag in a user
turn, as Cursor writes, gets `started:` with that text and "(from the
text)", and no `ended:`. A file with neither says `time: not in the file`.
The file's modification time is never used: it says when a file changed,
not when a session ran.

Each session is written to MIRROR at the same relative path with .txt
added. A session whose text would pass 900,000 bytes (the kernel reads 1 MB
of a file, and a pile leaves out a longer one) is written in parts instead:
X.txt, then X.2.txt, X.3.txt, named as
[ai-code-tracking](../ai-code-tracking/) names its parts, so a pile reads them
in order. Parts are cut between turns; a turn longer than a part is cut at a
line end, and a line longer than a part between characters. Every part opens
with the session's header and a line `part 2 of 3`, so a passage still says
which session it is and when it ran, and the turn numbers go on across parts.
A session that fits is one file with no `part` line. A rerun removes an
X.N.txt left by a longer run, and nothing else. A file that is not a
session is skipped and counted. Point the
kernel at MIRROR to ask questions of it.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused
(FOLDER is not a folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes.

**Never:** writes inside FOLDER, prints a tool result, or reads the key.
