"""vscode.py: willow in VS Code. Python 3.9+.

    python adapters/stdlib/vscode/vscode.py --box DIR

Prints a task, willow: ask, that prompts for a question and puts each answer in the Problems panel, a click away from its file and line. The lines go in .vscode/tasks.json in your project; it changes nothing itself.
Each answer comes from pipe (adapters/stdlib/pipe/pipe.py --grep), so every
question is the kernel's own bite, on the record.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

PIPE = Path(__file__).resolve().parents[1] / "pipe" / "pipe.py"


#: what VS Code reads in pipe's --grep lines
REGEXP = r"^(.*):(\d+): (.*)$"


def snippet(box: Path, py: str) -> str:
    tasks = {"version": "2.0.0", "tasks": [{
        "label": "willow: ask", "type": "process", "command": py,
        "args": [str(PIPE), "--box", str(box.resolve()), "--grep", "${input:willowQuestion}"],
        "problemMatcher": {"owner": "willow", "fileLocation": "absolute", "severity": "info",
                           "pattern": {"regexp": REGEXP, "file": 1, "line": 2, "message": 3}},
        "presentation": {"reveal": "silent"},
    }], "inputs": [{"id": "willowQuestion", "type": "promptString",
                    "description": "Ask willow"}]}  # fmt: skip
    return json.dumps(tasks, indent=2) + "\n"


def render(box: Path, py: str = None) -> str:
    return "Add this to .vscode/tasks.json in your project:\n\n" + snippet(
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
