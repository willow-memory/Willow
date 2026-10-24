"""emacs.py: willow in Emacs. Python 3.9+.

    python adapters/stdlib/emacs/emacs.py --box DIR

Prints an M-x willow command: the answers fill a grep-mode buffer, each line a jump to its file and line. The lines go in your init file (~/.emacs.d/init.el); it changes nothing itself.
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


def snippet(box: Path, py: str) -> str:
    return (
        "(defun willow (question)\n"
        '  "Ask your willow folder; each answer jumps to its file and line."\n'
        '  (interactive "sAsk willow: ")\n'
        '  (let ((buf (get-buffer-create "*willow*")))\n'
        "    (with-current-buffer buf (let ((inhibit-read-only t)) (erase-buffer)))\n"
        f"    (call-process {json.dumps(py)} nil buf nil {json.dumps(str(PIPE))}\n"
        f'                  "--box" {json.dumps(str(box.resolve()))} "--grep" question)\n'
        "    (with-current-buffer buf (grep-mode) (goto-char (point-min)))\n"
        "    (pop-to-buffer buf)))\n"
    )


def render(box: Path, py: str = None) -> str:
    return "Add this to your init file (~/.emacs.d/init.el):\n\n" + snippet(
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
