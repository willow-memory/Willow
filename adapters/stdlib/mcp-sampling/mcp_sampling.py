"""mcp_sampling.py: suggestions through MCP sampling — the client's model,
no key of willow's. Python 3.9+.

    python adapters/stdlib/mcp-sampling/mcp_sampling.py --box DIR

An MCP server on standard input and output (stdio: no port, no network)
with mcp-lite's three tools, plus `draft(question)`: the kernel bites, the
client's model is asked through `sampling/createMessage` over only the
passages served, and a reply that cites them is proposed for your seal.
Willow never holds a model or an API key; the host does.

    ask(question)                         the kernel's bite
    suggest(path, answer, cites, reason)  the kernel's propose; it waits for you
    waiting()                             the kernel's out
    draft(question)                       bite, sample through the client, propose

There is no tool to approve, and the server never reads your key: approving
is `python kernel.py seal`, run by you. When the bite serves nothing, the
client's model is never asked. A reply whose brackets name no served
passage is returned and proposed to no one.

Exit codes, the kernel's: 0 the server ran; 2 refused (a bad command line,
not a box).
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "willow_openai_compatible_for_sampling",
    HERE.parent / "openai-compatible" / "openai_compatible.py",
)
oc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oc)

VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
INSTRUCTIONS = (
    "A person's own folder. ask() serves what their files say, or an answer they "
    "approved. draft() asks the host's model through MCP sampling over only the "
    "passages ask would serve, then hands in a suggestion; it waits for them. "
    "suggest() hands in an answer citing passage ids from the last ask. You "
    "cannot approve anything."
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
    {"name": "draft",
     "description": "Ask the folder, then ask the host's model through MCP sampling over only "
                    "the passages served, and hand in a suggestion citing the brackets the "
                    "model named. When nothing is served, the model is never asked. A reply "
                    "that cites nothing is proposed to no one.",
     "inputSchema": {"type": "object", "properties": {"question": {"type": "string"}},
                     "required": ["question"]}},
]  # fmt: skip


class Refused(Exception):
    """The kernel refused; the tool error carries its reason."""


class SampleFailed(Exception):
    """The client couldn't sample; the tool error carries why."""


def call(verb, *args) -> str:
    """A kernel verb's output; a refusal raises with the kernel's reason."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = verb(*args)
    if code == kernel.REFUSED:
        raise Refused(err.getvalue().strip() or out.getvalue().strip() or "refused")
    return out.getvalue()


def reply_text(result: dict) -> str:
    """The assistant text from a sampling/createMessage result."""
    content = result.get("content")
    if isinstance(content, dict):
        return str(content.get("text") or "")
    if isinstance(content, list):
        parts = [
            str(p.get("text") or "")
            for p in content
            if isinstance(p, dict) and p.get("type", "text") == "text"
        ]
        return "".join(parts)
    return ""


def sample(
    stdout, lines, question: str, served: list[dict], *, next_id: list
) -> tuple[str, str]:
    """Ask the client for one completion; returns (reply text, model name)."""
    next_id[0] += 1
    mid = f"willow-sample-{next_id[0]}"
    chat = oc.messages(question, served)
    system = chat[0]["content"]
    user = chat[1]["content"]
    req = {
        "jsonrpc": "2.0",
        "id": mid,
        "method": "sampling/createMessage",
        "params": {
            "messages": [{"role": "user", "content": {"type": "text", "text": user}}],
            "systemPrompt": system,
            "maxTokens": 1024,
            "temperature": 0,
        },
    }
    stdout.write(json.dumps(req, ensure_ascii=False) + "\n")
    stdout.flush()
    for raw in lines:
        if not raw.strip():
            continue
        try:
            msg = json.loads(raw)
        except ValueError as e:
            raise SampleFailed(f"client reply was not JSON: {e}") from e
        if not isinstance(msg, dict) or msg.get("id") != mid:
            raise SampleFailed("client replied to a different request during sampling")
        if "error" in msg:
            err = msg["error"]
            raise SampleFailed(
                err.get("message") if isinstance(err, dict) else str(err)
            )
        result = msg.get("result")
        if not isinstance(result, dict):
            raise SampleFailed("client sampling result was missing")
        return reply_text(result), str(result.get("model") or "client-model")
    raise SampleFailed("client closed before answering sampling")


def draft(box: Path, question: str, stdout, lines, next_id: list) -> dict:
    """Bite, sample through the client, propose a cited reply."""
    out = call(kernel.bite, box, question, kernel.now())
    try:
        doc = json.loads(out)
    except ValueError as e:
        raise Refused(out.strip() or str(e)) from e
    served = [s for s in doc.get("served", []) if not s.get("echo")]
    if doc.get("state") == "sealed":
        return {
            "state": "sealed",
            "answer": doc.get("answer", "").strip(),
            "sampled": False,
        }
    if not served:
        return {
            "state": "empty",
            "sampled": False,
            "reason": "nothing in your folder holds that; no model was asked",
        }
    try:
        text, model = sample(stdout, lines, question, served, next_id=next_id)
    except SampleFailed as why:
        return {"state": "unreachable", "sampled": False, "reason": str(why)}
    text = text.strip()
    cites = oc.cited(text, served)
    if not cites:
        return {
            "state": "uncited",
            "sampled": True,
            "model": model,
            "reply": text,
            "reason": "cited no passage; proposed to no one",
        }
    row = {
        "path": f"answers/{oc.slug(question)}.md",
        "data": text + "\n",
        "cites": cites,
        "claim": f"{model} via MCP sampling answered from"
        f" {len(cites)} of the {len(served)} passages served",
    }
    line = call(kernel.propose, box, [json.dumps(row)], kernel.now()).strip()
    if line.startswith("refused"):
        _, _, rest = line.partition(":")
        raise Refused(rest.strip())
    waiting = line.split()[1] if line.startswith("pass") else ""
    if not waiting.startswith("proposal:"):
        raise Refused("propose refused")
    return {
        "state": "waiting",
        "sampled": True,
        "model": model,
        "reply": text,
        "waiting": waiting,
        "cites": cites,
        "served": len(served),
        "for": "the person's approval",
    }


def tool(box: Path, name: str, args: dict, stdout, lines, next_id: list) -> dict:
    """One tool call, as the result the client reads."""
    if name == "ask":
        return json.loads(
            call(kernel.bite, box, str(args.get("question", "")), kernel.now())
        )
    if name == "suggest":
        row = {
            "path": args.get("path"),
            "data": args.get("answer"),
            "cites": args.get("cites"),
            "claim": args.get("reason"),
        }
        line = call(kernel.propose, box, [json.dumps(row)], kernel.now()).strip()
        if line.startswith("refused"):
            _, _, rest = line.partition(":")
            raise Refused(rest.strip())
        waiting = line.split()[1] if line.startswith("pass") else ""
        if not waiting.startswith("proposal:"):
            raise Refused("propose refused")
        return {"waiting": waiting, "for": "the person's approval"}
    if name == "waiting":
        lines_out = call(kernel.out, box, kernel.now()).splitlines()
        prefix = "waiting on your seal: "
        return {
            "waiting": [ln[len(prefix) :] for ln in lines_out if ln.startswith(prefix)]
        }
    if name == "draft":
        return draft(box, str(args.get("question", "")), stdout, lines, next_id)
    raise Refused(f"no tool {name!r}")


def answer(box: Path, msg: dict, stdout, lines, next_id: list) -> dict | None:
    """The reply to one message, or None for a notification."""
    if not isinstance(msg, dict) or "id" not in msg:
        return None
    mid, method, params = msg["id"], msg.get("method"), msg.get("params") or {}

    def ok(result: dict) -> dict:
        return {"jsonrpc": "2.0", "id": mid, "result": result}

    if method == "initialize":
        asked = params.get("protocolVersion")
        return ok(
            {
                "protocolVersion": asked if asked in VERSIONS else VERSIONS[0],
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "willow-sampling",
                    "version": kernel.VERSION[:12],
                },
                "instructions": INSTRUCTIONS,
            }
        )
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": TOOLS})
    if method == "tools/call":
        try:
            result = tool(
                box,
                str(params.get("name")),
                params.get("arguments") or {},
                stdout,
                lines,
                next_id,
            )
        except Refused as why:
            return ok(
                {"content": [{"type": "text", "text": str(why)}], "isError": True}
            )
        text = json.dumps(result, ensure_ascii=False)
        return ok(
            {
                "content": [{"type": "text", "text": text}],
                "structuredContent": result,
                "isError": False,
            }
        )
    return {
        "jsonrpc": "2.0",
        "id": mid,
        "error": {"code": -32601, "message": f"method not found: {method}"},
    }


def serve(box: Path, stdin, stdout) -> None:
    lines = iter(stdin)
    next_id = [0]
    for raw in lines:
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
            reply = answer(box, msg, stdout, lines, next_id)
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
