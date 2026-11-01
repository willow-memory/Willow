"""quotes.py: every quote in a document, checked against your files.

    python adapters/stdlib/quotes/quotes.py --box DIR --in FILE

quote-check takes one quote; a report, an article or a catalog's notes hold
dozens. This finds each quotation in FILE (words between straight "..." or
curly quotation marks, on one line, of at least four words) and checks it
against the folder the box is pointed at:

    as written   policy.txt:1      "We don't show you personalized ads"
    almost       policy.txt:4      "The council met on Monday"  (8 of 10 words)
      changed    Monday -> Tuesday
      added      quietly
    not there                      "We sell nothing to anyone"

    3 quotes: 1 as written, 1 almost, 1 not there.

"as written" is quote-check's verdict (verbatim, or the same words in the
same order). "almost" is misquote's closest passage, at least half the
quote's words in order, with what the quote adds, drops or changes. "not
there" means no passage holds even half of it. The place given is the line
the passage starts on.

It only reads. Exit codes, the kernel's: 0 every quote is there as written
(or FILE holds no quotes); 42 one isn't; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "quote-check"))
sys.path.insert(0, str(HERE.parent / "misquote"))
import kernel  # noqa: E402
import misquote  # noqa: E402
import quote_check  # noqa: E402

USAGE = "usage: quotes.py --box DIR --in FILE"
MIN_WORDS = 4
QUOTED = re.compile(r'"([^"\n]+)"|“([^”\n]+)”')


def quotations(text: str) -> list[str]:
    """Each quotation in `text`, in order, once: at least MIN_WORDS words."""
    out: list[str] = []
    for m in QUOTED.finditer(text):
        q = " ".join((m.group(1) or m.group(2)).split())
        if len(kernel.words(q)) >= MIN_WORDS and q not in out:
            out.append(q)
    return out


def check(pile: list[dict], quote: str) -> tuple[str, str, int, list]:
    """(verdict, place, words kept, differences) for one quote."""
    found = quote_check.find(pile, quote)
    if found:
        return "as written", found[0][1], len(misquote.tokens(quote)), []
    near = misquote.closest(pile, quote)
    if near is None:
        return "not there", "", 0, []
    c, kept, diffs = near
    return "almost", f"{c['path']}:{c['line']}", kept, diffs


def short(quote: str, n: int = 60) -> str:
    return f'"{quote}"' if len(quote) <= n else f'"{quote[: n - 1]}…"'


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[::2], argv[1::2]))
    if len(argv) != 4 or sorted(opts) != ["--box", "--in"]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    box, doc = Path(opts["--box"]), Path(opts["--in"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    try:
        text = doc.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        print(f"refused: can't read {doc} as UTF-8 text", file=sys.stderr)
        return kernel.REFUSED
    quotes = quotations(text)
    if not quotes:
        print(f"no quotations of {MIN_WORDS} words or more in {doc}")
        return kernel.ALIVE
    pile = kernel.chunks(Path(kernel.config(box)["pile"]))
    tally = {"as written": 0, "almost": 0, "not there": 0}
    for q in quotes:
        verdict, place, kept, diffs = check(pile, q)
        tally[verdict] += 1
        extra = (
            f"  ({kept} of {len(misquote.tokens(q))} words)"
            if verdict == "almost"
            else ""
        )
        print(f"{verdict:<12} {place:<17} {short(q)}{extra}")
        for kind, ws, instead in diffs:
            said = " ".join(ws) + (
                f" -> {' '.join(instead)}" if kind == "changed" else ""
            )
            print(f"  {kind:<10} {said}")
    print(f"\n{len(quotes)} quotes: {tally['as written']} as written, "
          f"{tally['almost']} almost, {tally['not there']} not there.")  # fmt: skip
    return kernel.ALIVE if tally["as written"] == len(quotes) else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
