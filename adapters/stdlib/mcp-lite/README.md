<!-- willow-addon
section: Assistants
line: The mcp add-on's three tools with nothing to install: the protocol by hand, standard library only.
source: box
added: 2026-10-24
writes: record
network: none
-->
# mcp-lite

Your folder, for any MCP client (an AI coding tool, an editor), with nothing
to install: the [mcp](../../deps/mcp/) add-on's three tools, with the Model
Context Protocol's stdio transport written by hand in the standard library.

    python adapters/stdlib/mcp-lite/server.py --box DIR

| Tool | The kernel's | What the client gets |
|---|---|---|
| `ask(question)` | `bite` | an approved answer, or up to three passages, each with an id to cite |
| `suggest(path, answer, cites, reason)` | `propose` | a suggestion citing passages from the last ask; it waits for you |
| `waiting()` | `out` | the ids of the suggestions waiting for your approval |

**No approve tool, by design.** The server never reads your key: approving
is `python kernel.py seal`, run by you. Every call goes through the kernel's
own verbs, so it's on the record as if you'd typed it, and `verify` holds. A
refusal comes back to the client as a tool error with the kernel's reason.

Each AI tool's own add-on prints the lines that register this server with
it: claude-code, codex-cli, gemini-cli, copilot, cursor, windsurf, zed and
opencode.

**Source:** the mcp add-on, rebuilt without its one install. It answers
the protocol's initialize, ping, tools/list and tools/call, speaking protocol
versions 2025-06-18, 2025-03-26 and 2024-11-05.

**Uses:** the kernel's `bite`, `propose`, `out` and `now`.

**Never:** approves, reads your key, opens a port, or goes online.
