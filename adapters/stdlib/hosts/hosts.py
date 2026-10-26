"""hosts.py: the lines that register willow with an assistant. Python 3.9+.

    python adapters/stdlib/hosts/hosts.py list
    python adapters/stdlib/hosts/hosts.py show NAME --box DIR

Every assistant that takes an MCP server is one row of HOSTS: where its
settings live, and the shape it wants. `show` prints the lines that start
mcp-lite (adapters/stdlib/mcp-lite/server.py) over your box, byte for byte
what the add-on for that assistant prints. It changes nothing: you paste
what it prints, where it says. A new assistant is a new row, not a new
script.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

SERVER = Path(__file__).resolve().parents[1] / "mcp-lite" / "server.py"


def mcp_servers(py: str, args: list[str]) -> dict:
    """The shape most assistants read: {"mcpServers": {name: command, args}}."""
    return {"mcpServers": {"willow": {"command": py, "args": args}}}


def context_servers(py: str, args: list[str]) -> dict:
    """Zed's shape."""
    return {"context_servers": {"willow": {"command": py, "args": args, "env": {}}}}


def local_command(py: str, args: list[str]) -> dict:
    """OpenCode's shape: the command and its arguments in one list."""
    return {
        "$schema": "https://opencode.ai/config.json",
        "mcp": {"willow": {"type": "local", "command": [py, *args], "enabled": True}},
    }


#: name -> (title, where its settings live, shape). Sorted by name.
HOSTS = {
    "cursor": (
        "Cursor",
        "~/.cursor/mcp.json (or .cursor/mcp.json in a project)",
        mcp_servers,
    ),
    "opencode": (
        "OpenCode",
        "opencode.json in the project, or ~/.config/opencode/opencode.json",
        local_command,
    ),
    "windsurf": (
        "Windsurf",
        "~/.codeium/windsurf/mcp_config.json (%USERPROFILE%\\.codeium\\windsurf on Windows)",
        mcp_servers,
    ),
    "zed": (
        "Zed",
        "~/.config/zed/settings.json (zed: open settings file)",
        context_servers,
    ),
}


def render(name: str, box: Path, py: str = None) -> str:
    """What to paste, and where, for the assistant called name."""
    _, where, shape = HOSTS[name]
    args = [str(SERVER), "--box", str(box.resolve())]
    value = shape(py or sys.executable or "python3", args)
    return f"Add this to {where}:\n\n{json.dumps(value, indent=2)}\n"


def main(argv: list[str]) -> int:
    if argv == ["list"]:
        for name, (title, where, _) in HOSTS.items():
            print(f"{name}\t{title}\t{where}")
        return kernel.ALIVE
    if len(argv) == 4 and argv[0] == "show" and argv[2] == "--box":
        if argv[1] not in HOSTS:
            print(f"refused: no host called {argv[1]}; try list", file=sys.stderr)
            return kernel.REFUSED
        box = Path(argv[3])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        print(render(argv[1], box), end="")
        return kernel.ALIVE
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
