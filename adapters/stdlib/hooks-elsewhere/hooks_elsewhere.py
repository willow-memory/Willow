"""hooks_elsewhere.py: the prompt hook for Gemini CLI, Codex and OpenCode,
held to Claude Code's answer byte for byte. Python 3.9+.

    python adapters/stdlib/hooks-elsewhere/hooks_elsewhere.py list
    python adapters/stdlib/hooks-elsewhere/hooks_elsewhere.py setup --host HOST --box DIR [--index INDEX]
    python adapters/stdlib/hooks-elsewhere/hooks_elsewhere.py prompt --host HOST --box DIR [--index INDEX]

`setup` prints what to paste into the host's settings, and changes nothing.
`prompt` is what the host runs at each prompt: it asks the box the way
[claude-code](../claude-code/) does, and wraps that answer only as far as
the host needs. The framed passages themselves are Claude Code's bytes.

| Host | Event | Envelope |
|---|---|---|
| gemini-cli | BeforeAgent | JSON; Claude's block in additionalContext |
| codex-cli | UserPromptSubmit | Claude's block as plain stdout |
| opencode | UserPromptSubmit | same as Codex (Claude-compatible hooks) |

`--index` is passed through to Claude Code's hook (scan + index-cache). Exit
codes, the kernel's: 0 answered (or nothing to say); 2 refused. `prompt`
always exits 0 once the command line is good, as Claude Code's does.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

HERE = Path(__file__).resolve()

#: name -> (title, where to paste, event name for that host's hooks).
HOSTS = {
    "codex-cli": (
        "Codex CLI",
        "~/.codex/hooks.json (or .codex/hooks.json in a trusted project)",
        "UserPromptSubmit",
    ),
    "gemini-cli": (
        "Gemini CLI",
        "~/.gemini/settings.json (or .gemini/settings.json in a project)",
        "BeforeAgent",
    ),
    "opencode": (
        "OpenCode",
        "~/.claude/settings.json or .claude/settings.json (Claude-compatible hooks), "
        "or a plugin that runs this prompt command and injects its stdout",
        "UserPromptSubmit",
    ),
}


def claude():
    """claude-code's hook module, or None when that add-on isn't beside this."""
    path = STDLIB / "claude-code" / "hook.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("willow_claude_code_hook", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def wrap(host: str, body: str) -> str:
    """Claude's framed answer in the shape this host's prompt hook accepts."""
    if not body:
        return ""
    if host == "gemini-cli":
        return (
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "BeforeAgent",
                        "additionalContext": body,
                    }
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    return body  # codex-cli and opencode: plain text is the context


def prompt(host: str, box: Path, stdin, index: Path | None = None) -> str:
    """What the host's hook prints for one prompt."""
    hk = claude()
    if hk is None:
        return "willow: claude-code isn't here; add it beside hooks-elsewhere\n"
    title = HOSTS[host][0]
    try:
        sent = json.loads(stdin.read() or "{}")
    except (ValueError, RecursionError):
        sent = None
    if not isinstance(sent, dict):
        return f"willow: couldn't read the prompt {title} sent\n"
    text = str(sent.get("prompt", "")).strip()
    if not text:
        return ""
    # Claude Code's bite+frame, fed a clean prompt object so its answer is
    # the passage contract; host-specific unreadables stay above.
    body = hk.prompt(box, io.StringIO(json.dumps({"prompt": text})), index)
    return wrap(host, body)


def command_line(host: str, box: Path, index: Path | None = None) -> str:
    """The shell command the host runs at each prompt."""
    hk = claude()
    py = sys.executable or "python3"
    run = [py, str(HERE), "prompt", "--host", host, "--box", str(box.resolve())]
    if index is not None:
        run += ["--index", str(index.resolve())]
    return hk.command_line(run) if hk else " ".join(run)


def settings(host: str, box: Path, index: Path | None = None) -> dict:
    """The hooks object to paste for this host."""
    event = HOSTS[host][2]
    cmd = {
        "type": "command",
        "command": command_line(host, box, index),
        "timeout": 60 if host == "gemini-cli" else 10,
    }
    if host == "gemini-cli":
        cmd["name"] = "willow-passages"
        return {"hooks": {event: [{"matcher": "*", "hooks": [cmd]}]}}
    return {"hooks": {event: [{"hooks": [cmd]}]}}


def setup(host: str, box: Path, index: Path | None = None) -> str:
    """What to paste, and where; with an index, the index-cache line too."""
    title, where, _ = HOSTS[host]
    said = (
        f"Add this to {where}:\n\n"
        + json.dumps(settings(host, box, index), indent=2)
        + "\n"
    )
    if host == "opencode":
        said += (
            "\nOpenCode's native plugins are JavaScript; a plugin that runs the "
            "`prompt` command above and injects its stdout (Claude's framed "
            "passages) as synthetic text gets the same answer. Claude-compatible "
            "hook runners paste the JSON as written.\n"
        )
    if index is not None:
        hk = claude()
        pile = kernel.config(box)["pile"]
        py = sys.executable or "python3"
        keep = [
            py,
            str(STDLIB / "index-cache" / "index_cache.py"),
            "--from",
            str(pile),
            "--to",
            str(index.resolve()),
        ]
        line = hk.command_line(keep) if hk else " ".join(keep)
        said += (
            "\nAnd keep the index current, now and whenever your folder changes"
            " (until it is, each prompt reads the whole folder, as without one):\n\n"
            f"    {line}\n"
        )
    # hosts show also registers MCP; point at that for the other way in
    said += (
        f"\nMCP tools (ask, suggest, waiting) for {title} stay "
        f"`python adapters/stdlib/hosts/hosts.py show {host} --box DIR`.\n"
    )
    return said


def main(argv: list[str], stdin=None) -> int:
    if argv == ["list"]:
        for name, (title, where, event) in HOSTS.items():
            print(f"{name}\t{title}\t{event}\t{where}")
        return kernel.ALIVE

    index = None
    if len(argv) >= 2 and argv[-2] == "--index":
        if not argv[-1]:
            print(__doc__.split("\n\n")[1], file=sys.stderr)
            return kernel.REFUSED
        index, argv = Path(argv[-1]), argv[:-2]
    # setup|prompt --host HOST --box DIR
    if (
        len(argv) != 5
        or argv[0] not in ("setup", "prompt")
        or argv[1] != "--host"
        or argv[3] != "--box"
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    host, box = argv[2], Path(argv[4])
    if host not in HOSTS:
        way = (
            "; Claude Code's way in is adapters/stdlib/claude-code"
            if host == "claude-code"
            else ""
        )
        print(f"refused: no host called {host}{way}; try list", file=sys.stderr)
        return kernel.REFUSED
    if argv[0] == "setup":
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        hk = claude()
        if hk is None:
            print(
                "refused: claude-code isn't here; add it beside hooks-elsewhere",
                file=sys.stderr,
            )
            return kernel.REFUSED
        if index is not None and hk.sibling("index-cache", "index_cache") is None:
            print(
                "refused: --index needs index-cache and scan; add them",
                file=sys.stderr,
            )
            return kernel.REFUSED
        print(setup(host, box, index), end="")
        return kernel.ALIVE
    print(prompt(host, box, stdin or sys.stdin, index), end="")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
