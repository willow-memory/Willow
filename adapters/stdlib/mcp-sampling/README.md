<!-- willow-addon
section: Assistants
line: Suggestions from whatever model your MCP client already runs, asked through MCP sampling, so willow needs no model or key of its own.
source: new
added: 2026-11-05
writes: record
network: none
hands: your question and the passages served, to the model your MCP client runs
role: suggests
uses: openai-compatible
-->
# mcp-sampling

Suggestions from whatever model your MCP client already runs, asked through
MCP sampling: willow holds no model and no API key. The host does. The
suggestion waits for your seal.

    python adapters/stdlib/mcp-sampling/mcp_sampling.py --box DIR

It runs on standard input and output (stdio): no port, no network. A client
gets mcp-lite's three tools, plus one that drafts:

| Tool | The kernel's | What the client gets |
|---|---|---|
| `ask(question)` | `bite` | an approved answer, or up to three passages, each with an id to cite |
| `suggest(path, answer, cites, reason)` | `propose` | a suggestion citing passages from the last ask; it waits for you |
| `waiting()` | `out` | the ids of the suggestions waiting for your approval |
| `draft(question)` | `bite`, then MCP sampling, then `propose` | a suggestion from the host's model over only the passages served |

**`draft` bites first.** Only the passages the kernel served go to the
client's model, under the same rule [openai-compatible](../openai-compatible/)
uses: answer only from them, cite each as [1], [2]. When nothing is served,
the model is never asked. A reply whose brackets name no served passage is
returned and proposed to no one. Asked at temperature 0.

The sample is a server-to-client MCP sampling request
(`<sampling/createMessage>`) on the same stdio pipe; the client must
declare sampling. Protocol revisions that retire server-initiated sampling
will need another way in (a host that still speaks the 2025 form, or
[openai-compatible](../openai-compatible/) with an endpoint the person
holds).

**No approve tool, by design.** Approving stays `python kernel.py seal`.

**Uses:** the kernel's `bite`, `propose`, `out` and `now`;
[openai-compatible](../openai-compatible/)'s passage framing and cite parse.

**Never:** approves, reads your key, opens a port, goes online, or asks a
model when your folder holds nothing for the question.
