"""quote_check.py: is this exact quote in my files, and where?

    python adapters/stdlib/quote-check/quote_check.py --box DIR "the quote"

For writers, journalists and students checking a quote against their own
sources. Every place your folder holds the quote's words in the same order:

    verbatim     interviews/2024-05-02.txt:31
    same words   notes/draft.md:12   (spacing, case or punctuation differ)

"verbatim" means the very characters (spacing aside); "same words" means the
same words in the same order, which is how a quote is usually mangled. Words
are split the kernel's way (its `words`), so "can't" and "cant" are not the
same. A quote is matched within one passage of a file (a paragraph); one
split across a blank line is two quotes.

It only reads. Exit codes, the kernel's: 0 found; 42 not in your folder; 2
refused.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


def squash(text: str) -> str:
    return " ".join(text.split())


def find(pile: list[dict], quote: str) -> list[tuple[str, str]]:
    """(kind, place) for every passage holding the quote's words in order."""
    want = kernel.words(quote)
    if not want:
        return []
    n, exact, out = len(want), squash(quote), []
    for c in pile:
        ws = kernel.words(c["text"])
        if any(ws[i : i + n] == want for i in range(len(ws) - n + 1)):
            text = squash(c["text"])
            line = c["line"]
            if exact in text:
                kind = "verbatim"
                lines = c["text"].splitlines()
                # the line it starts on: the last j from which the rest still holds it
                start = max(
                    j
                    for j in range(len(lines))
                    if exact in squash("\n".join(lines[j:]))
                )
                line = c["line"] + start
            else:
                kind = "same words"
            out.append((kind, f"{c['path']}:{line}"))
    return sorted(out, key=lambda x: (x[0] != "verbatim", x[1]))


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[0] != "--box":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    if not kernel.words(argv[2]):
        print("refused: a quote with no words", file=sys.stderr)
        return kernel.REFUSED
    hits = find(kernel.chunks(Path(kernel.config(box)["pile"])), argv[2])
    if not hits:
        print("Not in your folder, in those words and that order.")
        return kernel.ESCALATE
    for kind, place in hits:
        tail = (
            "   (spacing, case or punctuation differ)" if kind == "same words" else ""
        )
        print(f"{kind:<12} {place}{tail}")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
