"""todo.py: the things you wrote down to do, across your folder, oldest first.

    python adapters/stdlib/todo/todo.py --box DIR

Every line that marks something to do: `TODO`, `FIXME`, `- [ ]`, "need to",
"don't forget", "remember to". Oldest first, by the kernel's own date for the
passage the line is in (its `dates`: the latest date in the passage, its
file's name, or the log heading above it); undated ones last, by file.

    2021-04-02  memos/2021-04-02.txt:3   Need to call Mesa Mutual and take it off the policy.
    2024-09-09  notes/todo_2024-09-09.txt:2   - Q3 estimate by 15th
    undated     README.md:40   TODO: fix the install step

The oldest open item is often the one that matters: a thing said once and
never done doesn't get newer.

It only reads. Exit codes, the kernel's: 0 found some; 42 none; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

MARK = re.compile(
    r"\bTODO\b|\bFIXME\b|^\s*[-*]\s*\[ \]|\bneed to\b|\bdon'?t forget\b|\bremember to\b",
    re.IGNORECASE,
)


def todos(pile: list[dict]) -> list[tuple[str, str, str]]:
    out = []
    for c, d in zip(pile, kernel.dates(pile)):
        when = f"{str(d)[:4]}-{str(d)[4:6]}-{str(d)[6:]}" if d else "undated"
        for i, line in enumerate(c["text"].splitlines()):
            if MARK.search(line):
                out.append((when, f"{c['path']}:{c['line'] + i}", line.strip()))
    return sorted(out)  # "undated" sorts after every YYYY-MM-DD, so undated come last


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "--box":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    hits = todos(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not hits:
        print("Nothing in your folder is marked to do.")
        return kernel.ESCALATE
    width = max(len(p) for _, p, _ in hits)
    for when, place, line in hits:
        print(f"{when:<10}  {place:<{width}}  {line[:120]}")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
