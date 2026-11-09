# what the add-ons hand to an assistant's model

A box whose pile is this repo's adapters/ folder. Each step is an exact
search (ripgrep, which needs installing), so a hit is a line, with its file
and the passage id the kernel would cite. Run it when a card's hands: line
is written or checked, or when an add-on that talks to an assistant is
added: a hit is a place to read, not a verdict. The last step lists every
card that hands something on.

    python adapters/stdlib/stack/stack.py --box DIR --stack adapters/stdlib/stack/examples/hands.md

## the hook events that put text in front of the model
# a hook's standard output, or its additionalContext, is read into the prompt
- ripgrep -- --box {box} additionalContext
- ripgrep -- --box {box} UserPromptSubmit
- ripgrep -- --box {box} SessionStart
- ripgrep -- --box {box} PreCompact

## the protocols that hand passages to a client's model
# an MCP server's results, and a sampling request the client's model answers
- ripgrep -- --box {box} jsonrpc
- ripgrep -- --box {box} sampling/createMessage
# a server built on the MCP SDK never spells the protocol out
- ripgrep -- --box {box} mcp.server

## what the cards promise leaves
# the guard-checked line, and the hand-off line once cards have it
- ripgrep -- --box {box} "network: none"
- ripgrep -- --box {box} "hands:"
