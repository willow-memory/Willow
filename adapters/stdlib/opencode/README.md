<!-- willow-addon
section: Assistants
line: OpenCode asks your folder and hands in suggestions, through the mcp add-on.
source: new
added: 2026-10-24
writes: nothing
network: none
tags: no-install, offline, read-only, assistant
-->
# opencode

OpenCode, asking your own folder and handing in suggestions for you to
approve, through [mcp-lite](../mcp-lite/): nothing to install.

    python adapters/stdlib/opencode/opencode.py --box DIR

It prints the lines to paste, and where:

| Where | Format |
|---|---|
| opencode.json in the project, or ~/.config/opencode/opencode.json | JSON |

Each starts `mcp-lite/server.py --box DIR` with the Python that ran this
script, so OpenCode gets the three tools: `ask`, `suggest` and `waiting`.
There's no approve tool: approving stays `python kernel.py seal`, yours.

**Source:** OpenCode's own documentation for registering a stdio MCP server,
as it stood on 2026-10-24. If OpenCode moves the file or renames a key,
this add-on's test is the place to change.

**Uses:** nothing of the kernel's but its exit codes; mcp-lite does the rest.

**Never:** edits OpenCode's settings for you, reads your key, or goes online.
