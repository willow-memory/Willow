<!-- willow-addon
section: Assistants
line: GitHub Copilot, in VS Code and in its own CLI, asks your folder through the mcp add-on.
source: new
added: 2026-10-24
writes: nothing
network: none
-->
# copilot

GitHub Copilot, asking your own folder and handing in suggestions for you to
approve, through [mcp-lite](../mcp-lite/): nothing to install.

    python adapters/stdlib/copilot/copilot.py --box DIR

It prints the lines to paste, and where:

| Where | Format |
|---|---|
| VS Code: .vscode/mcp.json in the project, or your user mcp.json | JSON |
| Copilot CLI: ~/.copilot/mcp-config.json | JSON |

Each starts `mcp-lite/server.py --box DIR` with the Python that ran this
script, so GitHub Copilot gets the three tools: `ask`, `suggest` and `waiting`.
There's no approve tool: approving stays `python kernel.py seal`, yours.

**Source:** GitHub Copilot's own documentation for registering a stdio MCP server,
as it stood on 2026-10-24. If GitHub Copilot moves the file or renames a key,
this add-on's test is the place to change.

**Uses:** nothing of the kernel's but its exit codes; mcp-lite does the rest.

**Never:** edits GitHub Copilot's settings for you, reads your key, or goes online.
