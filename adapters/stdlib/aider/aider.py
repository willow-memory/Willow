"""aider.py: willow in Aider. Python 3.9+.

    python adapters/stdlib/aider/aider.py --box DIR

Prints the /run line that asks your folder: Aider runs it and offers to add the answers, each with its file and line, to the chat. The lines go in Aider's chat, as a /run command; it changes nothing itself.
Each answer comes from pipe (adapters/stdlib/pipe/pipe.py --grep), so every
question is the kernel's own bite, on the record.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hosts"))
import hosts  # noqa: E402

PIPE = hosts.PIPE


def command_line(argv: list[str]) -> str:
    """One line for the shell that runs it, each piece quoted as that shell
    reads it, so a folder with a space in its name stays one piece."""
    return subprocess.list2cmdline(argv) if os.name == "nt" else shlex.join(argv)


def snippet(box: Path, py: str) -> str:
    argv = [py, str(PIPE), "--box", str(box.resolve()), "--grep"]
    return f'/run {command_line(argv)} "your question"\n'


def render(box: Path, py: str = None) -> str:
    return "Add this to Aider's chat, as a /run command:\n\n" + snippet(
        box, py or sys.executable or "python3"
    )


def main(argv: list[str]) -> int:
    return hosts.cli(__doc__, render, argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
