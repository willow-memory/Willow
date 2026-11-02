<!-- willow-addon
section: Assistants
line: Zed's assistant asks your folder and hands in suggestions, through the mcp add-on.
source: new
added: 2026-10-24
writes: nothing
network: none
-->
# zed

Zed, asking your own folder and handing in suggestions for you to
approve, through [mcp-lite](../mcp-lite/): nothing to install.

    python adapters/stdlib/zed/zed.py --box DIR

It prints the lines to paste, and where:

| Where | Format |
|---|---|
| ~/.config/zed/settings.json (zed: open settings file) | JSON |

Each starts `mcp-lite/server.py --box DIR` with the Python that ran this
script, so Zed gets the three tools: `ask`, `suggest` and `waiting`.
There's no approve tool: approving stays `python kernel.py seal`, yours.

**Source:** Zed's own documentation for registering a stdio MCP server,
as it stood on 2026-10-24. If Zed moves the file or renames a key,
this add-on's test is the place to change.

**Uses:** nothing of the kernel's but its exit codes; mcp-lite does the rest.

**Never:** edits Zed's settings for you, reads your key, or goes online.
