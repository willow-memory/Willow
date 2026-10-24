<!-- willow-addon
section: Assistants
line: Windsurf asks your folder and hands in suggestions, through the mcp add-on.
source: new
added: 2026-10-24
writes: nothing
network: none
tags: no-install, offline, read-only, assistant
-->
# windsurf

Windsurf, asking your own folder and handing in suggestions for you to
approve, through [mcp-lite](../mcp-lite/): nothing to install.

    python adapters/stdlib/windsurf/windsurf.py --box DIR

It prints the lines to paste, and where:

| Where | Format |
|---|---|
| ~/.codeium/windsurf/mcp_config.json (%USERPROFILE%\\.codeium\\windsurf on Windows) | JSON |

Each starts `mcp-lite/server.py --box DIR` with the Python that ran this
script, so Windsurf gets the three tools: `ask`, `suggest` and `waiting`.
There's no approve tool: approving stays `python kernel.py seal`, yours.

**Source:** Windsurf's own documentation for registering a stdio MCP server,
as it stood on 2026-10-24. If Windsurf moves the file or renames a key,
this add-on's test is the place to change.

**Uses:** nothing of the kernel's but its exit codes; mcp-lite does the rest.

**Never:** edits Windsurf's settings for you, reads your key, or goes online.
