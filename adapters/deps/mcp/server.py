"""server.py: your folder, for any MCP client, which can ask and suggest but
never approve.

    pip install -r adapters/deps/mcp/requirements.txt
    python adapters/deps/mcp/server.py --box DIR

Runs an MCP server on standard input and output (stdio: no port, no network)
over one kernel record folder. An AI assistant or an editor that speaks MCP
gets three tools:

    ask(question)                     the kernel's bite: an approved answer, or
                                      up to three passages, each with an id
    suggest(path, answer, cites, reason)
                                      the kernel's propose: a suggested answer
                                      that cites passage ids from the last ask;
                                      it waits for you
    waiting()                         the kernel's out: the ids of what waits for your
                                      approval

There is no tool to approve, and the server never reads your key: approving
is `python kernel.py seal`, run by you. Every call goes through the kernel's
own verbs, so each is on the record as if you'd typed it, and `verify` holds.

A refusal (a cite the last ask didn't serve, a record that doesn't verify)
comes back to the client as an error carrying the kernel's own reason.

The shape is Jeles's corpus server (MCPServer, stdio, an ask tool and a
tool that records an unchecked claim), rebuilt over the kernel.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

INSTALL = "pip install -r adapters/deps/mcp/requirements.txt"


def call(verb, *args) -> tuple[int, str, str]:
    """A kernel verb, its exit code and what it printed, out and err."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = verb(*args)
    return code, out.getvalue(), err.getvalue()


def build(box: Path):
    """The server, bound to one record folder. Imported here so that the
    module loads (and refuses with the install) without mcp present."""
    from mcp.server.mcpserver import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError

    server = MCPServer(
        "willow",
        instructions=(
            "A person's own folder. ask() serves what their files say, or an answer "
            "they approved. suggest() hands in an answer citing passage ids from the "
            "last ask; it waits for them. You cannot approve anything."
        ),
    )

    def refused(code: int, err: str) -> None:
        if code == kernel.REFUSED:
            raise ToolError(err.strip() or "refused")

    @server.tool()
    def ask(question: str) -> dict:
        """Ask the folder a question in plain words. Returns an approved answer
        if the person approved one for these words, else up to three passages
        from their files, each with an id to cite, its file and line, and text;
        `state` is "empty" when nothing in the folder holds the question."""
        code, out, err = call(kernel.bite, box, question, kernel.now())
        refused(code, err)
        return json.loads(out)

    @server.tool()
    def suggest(path: str, answer: str, cites: list[str], reason: str) -> dict:
        """Hand in a suggested answer for the person to approve. `cites` must be
        passage ids from the last ask's results; `path` is a plain relative
        file name the answer is written to once approved; `reason` says why.
        It waits for the person: nothing is written, and you can't approve it."""
        row = {"path": path, "data": answer, "cites": cites, "claim": reason}
        code, out, err = call(kernel.propose, box, [json.dumps(row)], kernel.now())
        refused(code, err)
        line = out.strip()
        if line.startswith("refused"):
            raise ToolError(line.split(":", 1)[-1].strip())
        return {"waiting": line.split()[1], "for": "the person's approval"}

    @server.tool()
    def waiting() -> dict:
        """The suggested answers waiting for the person's approval, by id."""
        code, out, err = call(kernel.out, box, kernel.now())
        refused(code, err)
        lines = out.splitlines()
        return {
            "waiting": [
                ln.split(": ", 1)[1] for ln in lines if ln.startswith("waiting")
            ]
        }

    return server


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "--box":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    try:
        server = build(box)
    except ImportError:
        print(f"refused: mcp isn't installed: {INSTALL}", file=sys.stderr)
        return kernel.REFUSED
    server.run(transport="stdio")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
