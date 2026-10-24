"""aider.py: willow in Aider. Python 3.9+.

    python adapters/stdlib/aider/aider.py --box DIR

Prints the /run line that asks your folder: Aider runs it and offers to add the answers, each with its file and line, to the chat. The lines go in Aider's chat, as a /run command; it changes nothing itself.
Each answer comes from pipe (adapters/stdlib/pipe/pipe.py --grep), so every
question is the kernel's own bite, on the record.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

PIPE = Path(__file__).resolve().parents[1] / "pipe" / "pipe.py"


def snippet(box: Path, py: str) -> str:
    return f'/run {py} {PIPE} --box {box.resolve()} --grep "your question"\n'


def render(box: Path, py: str = None) -> str:
    return "Add this to Aider's chat, as a /run command:\n\n" + snippet(
        box, py or sys.executable or "python3"
    )


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
