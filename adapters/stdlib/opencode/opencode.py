"""opencode.py: OpenCode asks your folder and hands in suggestions. Python 3.9+.

    python adapters/stdlib/opencode/opencode.py --box DIR

Prints what registers willow's tools with OpenCode: the lines for its
settings, which start mcp-lite (adapters/stdlib/mcp-lite/server.py, the mcp
add-on's three tools with nothing to install) over your box. It changes
nothing: you paste what it prints, where it says.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

SERVER = Path(__file__).resolve().parents[1] / "mcp-lite" / "server.py"


def toml_table(name: str, values: dict) -> str:
    """A TOML table of strings and string lists (JSON's escapes are TOML's)."""
    rows = [f"[{name}]"] + [f"{k} = {json.dumps(v)}" for k, v in values.items()]
    return "\n".join(rows) + "\n"


def places(box: Path, py: str) -> list[tuple[str, str, object]]:
    """Where each piece goes, its format, and what goes there."""
    args = [str(SERVER), "--box", str(box.resolve())]
    return [
        (
            "opencode.json in the project, or ~/.config/opencode/opencode.json",
            "json",
            {
                "$schema": "https://opencode.ai/config.json",
                "mcp": {
                    "willow": {"type": "local", "command": [py, *args], "enabled": True}
                },
            },
        ),
    ]


def render(box: Path, py: str = None) -> str:
    out = []
    for where, kind, value in places(box, py or sys.executable or "python3"):
        text = value if kind == "toml" else json.dumps(value, indent=2) + "\n"
        out.append(f"Add this to {where}:\n\n{text}")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "--box":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    print(render(box), end="")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
