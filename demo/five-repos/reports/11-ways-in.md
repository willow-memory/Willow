# Report 6: the five, askable from anywhere, 2026-11-03

A fresh box over the five repos and a thirteen-step stack, `ways-in.md`:
each step either answers a question in the shape a tool reads, or prints
the lines that register willow with an editor, a shell, a launcher or an
MCP host. Then each printed setup was tried for real where the tool is
on this machine, and driven by hand where it isn't.

## Answers in a tool's shape

| way | what came back for the question |
|---|---|
| pipe `--grep` | three `file:line: text` lines, grep's own shape, the first `rss-out/test_rss_out.py:216` |
| plain | the same three passages as sentences, each "From FILE, line N", and a note that nothing else names the function |
| launcher, lines format | tab-separated title, place and absolute path, for Alfred, Raycast, KRunner or PowerToys Run |
| deep-links | each passage as `file:///…/README.md#line=158,164`, an RFC 5147 fragment; lines 159 to 165 of that file are the passage |

## The setups, printed and then tried

- **vim**: the printed vimrc function runs pipe and loads its output
  with `cgetexpr`. Tried headlessly, `vim -Es` with `cfile` on pipe's
  output: the quickfix list holds the three answers, numbered, each a
  jump to its file and line.
- **vscode**: a tasks.json whose problem matcher is the same
  `file:line: text` regex, so answers land in the Problems panel. Not run
  here (no VS Code), but the matcher and pipe's shape are one line.
- **emacs** and **jetbrains**: an init.el function in grep-mode and an
  External Tools entry with a file-and-line filter, over the same pipe.
- **shell**: a `willow` function and tab completion for bash; the wrapper
  ran `verify` on the box.
- **browse**: a launcher for macOS, Windows and Linux, then the server
  itself on loopback. Its three guards all fired before an answer did:
  a request without the start key the server printed is "Not allowed";
  a post without the token the page made is "That form wasn't made by
  this page"; with the key through a cookie and the token from the page,
  POST /ask returned the three passages under "Your files say". The bite
  went on the record like any other.
- **claude-code**: a UserPromptSubmit hook, not MCP. Run on a prompt, it
  hands Claude Code the served passages under a line that says they are
  data from the person's files and not instructions, cited by file and
  line.
- **hosts**: seven MCP hosts listed with their config file (Codex,
  Copilot, Cursor, Gemini CLI, OpenCode, Windsurf, Zed); `show cursor`
  printed the mcp.json block pointing at mcp-lite's server. `show
  claude-code` refused: no host called that, since Claude Code's way in
  is the hook above.
- **mcp-lite**: driven over stdio as an editor would: initialize answered
  with the server's name and version hash; tools/list gave `ask`,
  `suggest` and `waiting`; tools/call `ask` returned the kernel's own
  JSON for "who may approve", the same three passages.

Every way in is the same bite, in a different envelope, and the record
counted them: five asks of the same question from five directions, each
a row.

## Two small things

- `hosts show claude-code` refusing is right, but a line pointing at the
  claude-code add-on would save the next person the detour.
- browse's launcher and the vscode task both bake in the absolute path
  of this machine's Python and box, which is what a launcher must do and
  what makes the printed setups unportable by design.

## Files

`ways-in.md` (the stack), `ways-in.out` (the page), `qf.txt` and
`clist.txt` (pipe's output and vim's quickfix list of it),
`browse-ask.html` (the answer page), `five-box/` (the record with the
five asks).
