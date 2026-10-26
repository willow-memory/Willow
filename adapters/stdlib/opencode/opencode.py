"""opencode.py: OpenCode asks your folder and hands in suggestions. Python 3.9+.

    python adapters/stdlib/opencode/opencode.py --box DIR

Prints what registers willow's tools with OpenCode: the lines for its
settings, which start mcp-lite (adapters/stdlib/mcp-lite/server.py, the mcp
add-on's three tools with nothing to install) over your box. It changes
nothing: you paste what it prints, where it says.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hosts"))
import hosts  # noqa: E402

NAME = "opencode"
SERVER = hosts.SERVER
toml_table = hosts.toml_table


def places(box: Path, py: str) -> list[tuple[str, str, object]]:
    """Where each piece goes, its format, and what goes there."""
    return hosts.places(NAME, box, py)


def render(box: Path, py: str = None) -> str:
    return hosts.render(NAME, box, py)


def main(argv: list[str]) -> int:
    return hosts.cli(__doc__, render, argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
