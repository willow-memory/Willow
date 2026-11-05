<!-- willow-addon
section: Assistants
line: Google's Gemini CLI asks your folder and hands in suggestions, through the mcp add-on.
source: new
added: 2026-10-24
writes: nothing
network: none
role: ways
uses: hosts
-->
# gemini-cli

The **MCP** way in for Gemini CLI (see [hosts](../hosts/)): it asks your
own folder and hands in suggestions for you to approve, through
[mcp-lite](../mcp-lite/). Nothing to install. At the repo root,
[GEMINI.md](../../../GEMINI.md) tells Gemini CLI to read
[AGENTS.md](../../../AGENTS.md) (Gemini has no `@` import), so the agent
rules stay one copy. The prompt-hook way in is
[hooks-elsewhere](../hooks-elsewhere/) (`setup --host gemini-cli`).

    python adapters/stdlib/gemini-cli/gemini_cli.py --box DIR

It prints the lines to paste, and where:

| Where | Format |
|---|---|
| ~/.gemini/settings.json (or .gemini/settings.json in a project) | JSON |

Each starts `mcp-lite/server.py --box DIR` with the Python that ran this
script, so Google's Gemini CLI gets the three tools: `ask`, `suggest` and `waiting`.
There's no approve tool: approving stays `python kernel.py seal`, yours.

Gemini CLI starts no MCP server in a folder you haven't trusted: until you
say yes when it asks, `gemini mcp list` shows willow as Disabled.
[live](../live/) runs it in a trusted folder and sees it connect.

**Source:** Google's Gemini CLI's own documentation for registering a stdio MCP server,
as it stood on 2026-10-24. If Google's Gemini CLI moves the file or renames a key,
this add-on's test is the place to change.

**Uses:** nothing of the kernel's but its exit codes; mcp-lite does the rest.

**Never:** edits Google's Gemini CLI's settings for you, reads your key, or goes online.
