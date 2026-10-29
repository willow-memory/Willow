"""flag.py: which question lines break the writer rules, and the questions' folders.

    python demo/known-gaps/flag.py QUESTIONS_DIR

The blind writers were told to write without identifiers: no snake_case names,
dotted paths, calls, camelCase, slashes, line numbers, issue numbers or hashes.
A line that still holds one is `flagged`, by one pattern, fixed before any
question was asked of any code:

    [A-Za-z0-9]_[A-Za-z0-9] | [a-z]\\.[a-z] | \\(\\) | [a-z][A-Z] | / | :[0-9] | #[0-9] | [0-9a-f]{7,}

with one exception: `allow_localhost` is the name of a flag a user types, so a
line whose only match is that word is not flagged.

The questions of a gap are QUESTIONS_DIR/{writer}/{ID}.txt, for the writers
`local` and `claude`; the null set is QUESTIONS_DIR/null/null.txt. A line
starting `#` is a header and a blank line is nothing; every other line is one
question. A question's name is `ID writer N` (N counts from 1 among the
questions) or `null N`. Prints, per writer, how many questions are flagged
before and after the exception. Exit 0.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PATTERN = re.compile(
    r"[A-Za-z0-9]_[A-Za-z0-9]|[a-z]\.[a-z]|\(\)|[a-z][A-Z]|/|:[0-9]|#[0-9]|[0-9a-f]{7,}"
)
EXCEPTION = "allow_localhost"
WRITERS = ("local", "claude")


def flagged(line: str, exception: bool = True) -> bool:
    """The line holds an identifier-like thing (see the module docstring)."""
    if exception:
        line = line.replace(EXCEPTION, " ")
    return bool(PATTERN.search(line))


def read(path: Path) -> list:
    """The question lines of a file: no header (`#`), no blank line."""
    return [
        x
        for x in path.read_text(encoding="utf-8").splitlines()
        if x.strip() and not x.startswith("#")
    ]


def questions(qdir: Path, gap: str, nulls: bool) -> list:
    """[(name, question, writer)] for a gap's questions by each writer, and, if
    `nulls`, the null set. A missing file is an error, never an empty set."""
    out = []
    for writer in WRITERS:
        for n, q in enumerate(read(qdir / writer / f"{gap}.txt"), 1):
            out.append((f"{gap} {writer} {n}", q, writer))
    if nulls:
        for n, q in enumerate(read(qdir / "null" / "null.txt"), 1):
            out.append((f"null {n}", q, "null"))
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    qdir = Path(argv[0])
    try:
        sets = {
            w: [q for n in range(1, 13) for q in read(qdir / w / f"KG{n:02d}.txt")]
            for w in WRITERS
        }
        sets["null"] = read(qdir / "null" / "null.txt")
    except OSError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    for w, qs in sets.items():
        before = sum(flagged(q, False) for q in qs)
        after = sum(flagged(q) for q in qs)
        print(
            f"{w}: {len(qs)} questions, flagged {before} before the exception, {after} after"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
