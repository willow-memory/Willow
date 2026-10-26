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
PIPE = Path(__file__).resolve().parents[1] / "pipe" / "pipe.py"


def toml_table(name: str, values: dict) -> str:
    """A TOML table of strings and string lists (JSON's escapes are TOML's)."""
    rows = [f"[{name}]"] + [f"{k} = {json.dumps(v)}" for k, v in values.items()]
    return "\n".join(rows) + "\n"


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


def servers_stdio(py: str, args: list[str]) -> dict:
    """VS Code's shape, which Copilot reads there."""
    return {"servers": {"willow": {"type": "stdio", "command": py, "args": args}}}


def local_tools(py: str, args: list[str]) -> dict:
    """Copilot CLI's shape."""
    return {
        "mcpServers": {
            "willow": {"type": "local", "command": py, "args": args, "tools": ["*"]}
        }
    }


def codex_table(py: str, args: list[str]) -> str:
    """Codex's shape, the one TOML one: text, not a document."""
    return toml_table("mcp_servers.willow", {"command": py, "args": args})


#: name -> (title, [(where its settings live, shape)]). Sorted by name.
HOSTS = {
    "codex-cli": (
        "Codex CLI",
        [
            (
                "~/.codex/config.toml (or .codex/config.toml in a trusted project)",
                codex_table,
            )
        ],
    ),
    "copilot": (
        "Copilot",
        [
            (
                "VS Code: .vscode/mcp.json in the project, or your user mcp.json",
                servers_stdio,
            ),
            ("Copilot CLI: ~/.copilot/mcp-config.json", local_tools),
        ],
    ),
    "cursor": (
        "Cursor",
        [("~/.cursor/mcp.json (or .cursor/mcp.json in a project)", mcp_servers)],
    ),
    "gemini-cli": (
        "Gemini CLI",
        [
            (
                "~/.gemini/settings.json (or .gemini/settings.json in a project)",
                mcp_servers,
            )
        ],
    ),
    "opencode": (
        "OpenCode",
        [
            (
                "opencode.json in the project, or ~/.config/opencode/opencode.json",
                local_command,
            )
        ],
    ),
    "windsurf": (
        "Windsurf",
        [
            (
                "~/.codeium/windsurf/mcp_config.json (%USERPROFILE%\\.codeium\\windsurf on Windows)",
                mcp_servers,
            )
        ],
    ),
    "zed": (
        "Zed",
        [("~/.config/zed/settings.json (zed: open settings file)", context_servers)],
    ),
}


def places(name: str, box: Path, py: str) -> list[tuple[str, str, object]]:
    """Where each piece goes for the assistant called name, its format
    (json, or toml when the shape gives text), and what goes there."""
    args = [str(SERVER), "--box", str(box.resolve())]
    out = []
    for where, shape in HOSTS[name][1]:
        value = shape(py, args)
        out.append((where, "toml" if isinstance(value, str) else "json", value))
    return out


def render_places(found: list[tuple[str, str, object]]) -> str:
    """The text that says where to paste each piece, and the piece."""
    out = []
    for where, kind, value in found:
        text = value if kind == "toml" else json.dumps(value, indent=2) + "\n"
        out.append(f"Add this to {where}:\n\n{text}")
    return "\n".join(out)


def render(name: str, box: Path, py: str = None) -> str:
    """What to paste, and where, for the assistant called name."""
    return render_places(places(name, box, py or sys.executable or "python3"))


def cli(doc: str, render_one, argv: list[str]) -> int:
    """The command line every one-assistant add-on shares: `--box DIR`
    prints render_one(box); anything else is refused, with doc's usage line."""
    if len(argv) != 2 or argv[0] != "--box":
        print(doc.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    print(render_one(box), end="")
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    if argv == ["list"]:
        for name, (title, found) in HOSTS.items():
            print(f"{name}\t{title}\t{'; '.join(where for where, _ in found)}")
        return kernel.ALIVE
    if len(argv) == 4 and argv[0] == "show" and argv[2] == "--box":
        if argv[1] not in HOSTS:
            print(f"refused: no host called {argv[1]}; try list", file=sys.stderr)
            return kernel.REFUSED
        return cli(__doc__, lambda box: render(argv[1], box), argv[2:])
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
