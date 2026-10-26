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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hosts"))
import hosts  # noqa: E402

PIPE = hosts.PIPE


#: what VS Code reads in pipe's --grep lines: the file ends at the first
#: ":LINE: ", so a passage that quotes a file:line of its own isn't misread
REGEXP = r"^(.*?):(\d+): (.*)$"


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
    return hosts.cli(__doc__, render, argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
