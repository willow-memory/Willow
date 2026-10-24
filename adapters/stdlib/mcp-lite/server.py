"""server.py: your folder for any MCP client, with nothing to install. Python 3.9+.

    python adapters/stdlib/mcp-lite/server.py --box DIR

The mcp add-on's three tools, over the Model Context Protocol's stdio
transport written by hand with the standard library: one JSON-RPC 2.0
message a line on standard input and output. No port, no network, no pip.

    ask(question)                         the kernel's bite
    suggest(path, answer, cites, reason)  the kernel's propose; it waits for you
    waiting()                             the kernel's out

There is no tool to approve, and the server never reads your key: approving
is `python kernel.py seal`, run by you (CONSTITUTION.md, CONST-0-2). Every
call goes through the kernel's own verbs, so it is on the record as if you'd
typed it. A refusal comes back as a tool error carrying the kernel's reason.

It answers initialize, ping, tools/list and tools/call. A notification gets
no answer; any other request gets the protocol's method-not-found error.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: protocol versions this server speaks, newest first; a client asking for
#: another is answered with the newest, and decides for itself
VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
INSTRUCTIONS = (
    "A person's own folder. ask() serves what their files say, or an answer they "
    "approved. suggest() hands in an answer citing passage ids from the last ask; "
    "it waits for them. You cannot approve anything."
)
TOOLS = [
    {"name": "ask",
     "description": "Ask the folder a question in plain words. Returns an approved answer if "
                    "the person approved one for these words, else up to three passages from "
                    "their files, each with an id to cite, its file and line, and text; `state` "
                    "is \"empty\" when nothing in the folder holds the question.",
     "inputSchema": {"type": "object", "properties": {"question": {"type": "string"}},
                     "required": ["question"]}},
    {"name": "suggest",
     "description": "Hand in a suggested answer for the person to approve. `cites` must be "
                    "passage ids from the last ask's results; `path` is a plain relative file "
                    "name; `reason` says why. It waits for the person: you can't approve it.",
     "inputSchema": {"type": "object",
                     "properties": {"path": {"type": "string"}, "answer": {"type": "string"},
                                    "cites": {"type": "array", "items": {"type": "string"}},
                                    "reason": {"type": "string"}},
                     "required": ["path", "answer", "cites", "reason"]}},
    {"name": "waiting",
     "description": "The suggested answers waiting for the person's approval, by id.",
     "inputSchema": {"type": "object", "properties": {}}},
]  # fmt: skip


class Refused(Exception):
    """The kernel refused; the tool error carries its reason."""


def call(verb, *args) -> str:
    """A kernel verb's output; a refusal raises with the kernel's reason."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = verb(*args)
    if code == kernel.REFUSED:
        raise Refused(err.getvalue().strip() or out.getvalue().strip() or "refused")
    return out.getvalue()


def tool(box: Path, name: str, args: dict) -> dict:
    """One tool call, as the result the client reads."""
    if name == "ask":
        return json.loads(
            call(kernel.bite, box, str(args.get("question", "")), kernel.now())
        )
    if name == "suggest":
        row = {"path": args.get("path"), "data": args.get("answer"),
               "cites": args.get("cites"), "claim": args.get("reason")}  # fmt: skip
        line = call(kernel.propose, box, [json.dumps(row)], kernel.now()).strip()
        if line.startswith("refused"):
            raise Refused(line.split(":", 1)[-1].strip())
        return {"waiting": line.split()[1], "for": "the person's approval"}
    if name == "waiting":
        lines = call(kernel.out, box, kernel.now()).splitlines()
        return {
            "waiting": [
                ln.split(": ", 1)[1] for ln in lines if ln.startswith("waiting")
            ]
        }
    raise Refused(f"no tool {name!r}")


def answer(box: Path, msg: dict) -> dict | None:
    """The reply to one message, or None for a notification."""
    if not isinstance(msg, dict) or "id" not in msg:
        return None
    mid, method, params = msg["id"], msg.get("method"), msg.get("params") or {}

    def ok(result: dict) -> dict:
        return {"jsonrpc": "2.0", "id": mid, "result": result}

    if method == "initialize":
        asked = params.get("protocolVersion")
        return ok({"protocolVersion": asked if asked in VERSIONS else VERSIONS[0],
                   "capabilities": {"tools": {}},
                   "serverInfo": {"name": "willow", "version": kernel.VERSION[:12]},
                   "instructions": INSTRUCTIONS})  # fmt: skip
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": TOOLS})
    if method == "tools/call":
        try:
            result = tool(box, str(params.get("name")), params.get("arguments") or {})
        except Refused as why:
            return ok(
                {"content": [{"type": "text", "text": str(why)}], "isError": True}
            )
        text = json.dumps(result, ensure_ascii=False)
        return ok({"content": [{"type": "text", "text": text}],
                   "structuredContent": result, "isError": False})  # fmt: skip
    return {"jsonrpc": "2.0", "id": mid,
            "error": {"code": -32601, "message": f"method not found: {method}"}}  # fmt: skip


def serve(box: Path, stdin, stdout) -> None:
    for raw in stdin:
        if not raw.strip():
            continue
        try:
            msg = json.loads(raw)
        except ValueError:
            reply = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "parse error"},
            }
        else:
            reply = answer(box, msg)
        if reply is not None:
            stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            stdout.flush()


def main(argv: list[str], stdin=None, stdout=None) -> int:
    if len(argv) != 2 or argv[0] != "--box":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    serve(box, stdin or sys.stdin, stdout or sys.stdout)
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
