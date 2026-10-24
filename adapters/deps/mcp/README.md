<!-- willow-addon
section: Assistants
line: Lets any MCP client, such as an AI assistant or editor, ask your folder and hand in suggestions.
source: new
added: 2026-10-23
needs: mcp; MIT
floor: mcp 2.0.0; the rule names 0.9.1, its first release, but MCPServer arrived in 2.0.0 and 2.x removed 1.x's server API, so no one server runs on both
writes: record
network: none
tags: needs-install, offline, records, assistant
-->
# mcp

Your folder, for any MCP client (an AI assistant, an editor), which can ask
and suggest but never approve.

    pip install -r adapters/deps/mcp/requirements.txt
    python adapters/deps/mcp/server.py --box DIR

It runs on standard input and output (stdio): no port, no network. A client
gets three tools:

| Tool | The kernel's | What the client gets |
|---|---|---|
| `ask(question)` | `bite` | an approved answer, or up to three passages, each with an id to cite |
| `suggest(path, answer, cites, reason)` | `propose` | a suggestion citing passages from the last ask; it waits for you |
| `waiting()` | `out` | the ids of the suggestions waiting for your approval |

**No approve tool, by design.** The server never reads your key. Approving is
`python kernel.py seal`, run by you; until then a suggestion is never given as
an answer. Every call goes through the kernel's own verbs, so it's on the
record as if you'd typed it, and `verify` holds. A refusal comes back to the
client as an error carrying the kernel's own reason.

To use it from an MCP client, register the command above with the client's
stdio server settings, with `--box` pointing at your record folder.

**Needs:** mcp 2.3.0, pinned in [requirements.txt](requirements.txt), which
needs Python 3.10 or newer (the kernel itself runs on 3.9). Without it, the
server refuses and names the install.

**Source:** the shape of [Jeles's corpus server](https://github.com/hornbook-knowledge/Jeles/blob/master/jeles/corpus_server.py) (an MCP server over stdio with
an ask tool and a tool that records an unchecked claim), rebuilt over the
kernel.

**Uses:** the kernel's `bite`, `propose`, `out` and `now`.

**Never:** approves, reads your key, opens a port, or goes online.
