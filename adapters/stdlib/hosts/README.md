<!-- willow-addon
section: Assistants
line: One table of the assistants that take an MCP server, printing the lines that register willow with any of them.
source: new
added: 2026-10-26
writes: nothing
network: none
-->
# hosts

Every assistant that takes an MCP server is one row in a table: where its
settings live, and the shape it wants. This prints the lines for any row,
starting [mcp-lite](../mcp-lite/) over your box. Nothing to install.

    python adapters/stdlib/hosts/hosts.py list
    python adapters/stdlib/hosts/hosts.py show NAME --box DIR

`list` names each assistant and where its settings live. `show` prints what
to paste there. The table holds codex-cli, copilot, cursor, gemini-cli,
opencode, windsurf and zed.

The twelve add-ons for one assistant each (those seven, and aider, emacs,
jetbrains, vim and vscode) are thin files over this one: each keeps its own
card and command line, and takes its table row, its `--box DIR` handling and
its refusals from here. The five that run `pipe` rather than mcp-lite keep
their own snippets and share only the command line. Their tests still hold
each to the bytes it printed before.

The tools are `ask`, `suggest` and `waiting`. There's no approve tool:
approving stays `python kernel.py seal`, yours.

**Adding an assistant:** a row in `HOSTS` in `hosts.py`, with one of the
shapes beside it (or a new one), and a test that its lines parse. For its own
card and command line, a short file that names the row and calls
`hosts.cli`, as the zed add-on does.

**Source:** each assistant's own documentation for registering a stdio MCP
server, as it stood on 2026-10-26. If one moves its file or renames a key,
that row is the place to change.

**Uses:** nothing of the kernel's but its exit codes; mcp-lite does the rest.

**Never:** edits an assistant's settings for you, reads your key, or goes
online.
