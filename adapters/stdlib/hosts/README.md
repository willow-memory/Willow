<!-- willow-addon
section: Assistants
line: One table of the assistants that take an MCP server, printing the lines that register willow with any of them.
source: new
added: 2026-10-26
writes: nothing
network: none
tags: no-install, offline, read-only, assistant
-->
# hosts

Every assistant that takes an MCP server is one row in a table: where its
settings live, and the shape it wants. This prints the lines for any row,
starting [mcp-lite](../mcp-lite/) over your box. Nothing to install.

    python adapters/stdlib/hosts/hosts.py list
    python adapters/stdlib/hosts/hosts.py show NAME --box DIR

`list` names each assistant and where its settings live. `show` prints what
to paste there. For the four it holds (cursor, opencode, windsurf, zed) the
test holds it to the same bytes that assistant's own add-on prints, so a row
here and a script there cannot drift apart.

The tools are `ask`, `suggest` and `waiting`. There's no approve tool:
approving stays `python kernel.py seal`, yours.

**Adding an assistant:** a row in `HOSTS` in `hosts.py`, with one of the
three shapes beside it (or a new one), and a test that its lines parse. No
new script, card or command line.

**Source:** each assistant's own documentation for registering a stdio MCP
server, as it stood on 2026-10-26. If one moves its file or renames a key,
that row is the place to change.

**Uses:** nothing of the kernel's but its exit codes; mcp-lite does the rest.

**Never:** edits an assistant's settings for you, reads your key, or goes
online.
