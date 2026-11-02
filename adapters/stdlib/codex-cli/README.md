<!-- willow-addon
section: Assistants
line: OpenAI's Codex CLI asks your folder and hands in suggestions, through the mcp add-on.
source: new
added: 2026-10-24
writes: nothing
network: none
-->
# codex-cli

OpenAI's Codex CLI, asking your own folder and handing in suggestions for you to
approve, through [mcp-lite](../mcp-lite/): nothing to install.

    python adapters/stdlib/codex-cli/codex_cli.py --box DIR

It prints the lines to paste, and where:

| Where | Format |
|---|---|
| ~/.codex/config.toml (or .codex/config.toml in a trusted project) | TOML |

Each starts `mcp-lite/server.py --box DIR` with the Python that ran this
script, so OpenAI's Codex CLI gets the three tools: `ask`, `suggest` and `waiting`.
There's no approve tool: approving stays `python kernel.py seal`, yours.

**Source:** OpenAI's Codex CLI's own documentation for registering a stdio MCP server,
as it stood on 2026-10-24. If OpenAI's Codex CLI moves the file or renames a key,
this add-on's test is the place to change.

**Uses:** nothing of the kernel's but its exit codes; mcp-lite does the rest.

**Never:** edits OpenAI's Codex CLI's settings for you, reads your key, or goes online.
