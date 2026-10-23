"""starter.py: copy the first-day words list to where yours will live.

    python adapters/stdlib/starter-words/starter.py copy --to FILE

Writes `words.txt` (beside this file) to FILE, readable only by you (mode
600), because the kernel refuses a words list anyone else can read. It never
overwrites: FILE must not exist yet. Then edit it, and give it to
`kernel.py init --words FILE`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

LIST = Path(__file__).resolve().parent / "words.txt"


def copy(to: Path) -> int:
    text = LIST.read_text(encoding="utf-8")
    _, why = kernel.parse_words(text)
    if why is not None:  # never hand anyone a list the kernel would refuse
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        print(f"refused: {to} exists; this never overwrites", file=sys.stderr)
        return kernel.REFUSED
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"wrote {to} (readable only by you): edit it, then init --words {to}")
    return kernel.ALIVE


if __name__ == "__main__":
    if sys.argv[1:3] != ["copy", "--to"] or len(sys.argv) != 4:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        raise SystemExit(kernel.REFUSED)
    raise SystemExit(copy(Path(sys.argv[3])))
