"""typos.py: a question's misspellings, read as your files spell them. Python 3.9+.

    python adapters/stdlib/typos/typos.py --box DIR "what did the jeweler say"
    read jeweler as jeweller: 2 passages hold it
    ask:  what did the jeweller say

A word of your question that no file of yours holds, in any form the kernel
looks for, is tried at every spelling one edit away inside it: a letter
dropped, added, changed, or two side by side swapped, with its first and last
letters kept as you typed them. The spelling the most passages hold is how
it's read, a tie going to the first in alphabetical order. A word your words
list reads as one of yours is held already and left alone.

Inside it, because that is where a slip of the fingers lands, and where a
different word doesn't: on willow's demo questions, an edit at either end read
"gave" as "have", "along" as "long" and "spend" as "pend", while all three
real misspellings ("jeweler", "dermatoligist", "referal") were inside.

It never asks for you. The question as read is printed for you to ask, so a
word spelt right that your files just don't have ("owe", when they say
"lent") can't turn into an answer to a question nobody asked. It reads only,
and writes nothing: not even the record.

Words shorter than six letters, and words with a letter outside a to z,
are left as they are: a short word has too many neighbours that are other
words ("gave" and "give", "spend" and "send"), and an accent is the accents
add-on's to read.

Exit codes, the kernel's: 0 every word is held, or a spelling is offered;
42 a word no file holds and nothing one edit away does; 2 refused (a bad
command line, a box that isn't one, a record that doesn't verify).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: the shortest word tried. willow-bot's one script's rung 2 tries 4
#: (REPAIR_MIN); on willow's demo questions 4 and 5 read "gave" as "give" and
#: "spend" as "send", and every real misspelling was 7 letters or more
SHORTEST = 6
ALPHABET = "abcdefghijklmnopqrstuvwxyz"


def edits1(w: str) -> list[str]:
    """Every spelling one edit from `w` (a deletion, a swap of neighbours, a
    replacement or an insertion, over a-z), sorted, `w` itself left out:
    willow-bot's `onescript/pile.py` edits1, as it is."""
    s = [(w[:i], w[i:]) for i in range(len(w) + 1)]
    out = {a + b[1:] for a, b in s if b}
    out |= {a + b[1] + b[0] + b[2:] for a, b in s if len(b) > 1}
    out |= {a + x + b[1:] for a, b in s if b for x in ALPHABET}
    out |= {a + x + b for a, b in s for x in ALPHABET}
    out.discard(w)
    return sorted(out)


def inside(w: str) -> list[str]:
    """`edits1(w)` with the first and last letters kept as typed."""
    return [x for x in edits1(w) if x[:1] == w[:1] and x[-1:] == w[-1:]]


def readings(question: str, pile: list[dict], alias: dict) -> tuple[dict, list]:
    """({word: (spelling, passages holding it)}, [words nothing one edit
    away holds either]), for the question's words no file holds."""
    every: set[str] = set()
    held_in: dict[str, int] = {}
    for c in pile:
        t = kernel.toks(c)
        every |= t
        for x in t:
            held_in[x] = held_in.get(x, 0) + 1
    read, missing = {}, []
    for w in dict.fromkeys(kernel.words(question)):
        if w in kernel.FUNCTION or kernel.held_by(w, every, alias):
            continue
        if len(w) < SHORTEST or not (w.isascii() and w.isalpha()):
            missing.append(w)
            continue
        best = min(((-held_in[x], x) for x in inside(w) if x in held_in), default=None)
        if best is None:
            missing.append(w)
        else:
            read[w] = (best[1], -best[0])
    return read, missing


def as_read(question: str, read: dict) -> str:
    """The question in its words, each misspelt one as your files spell it."""
    return " ".join(read.get(w, (w,))[0] for w in kernel.words(question))


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    args: list[str] = []
    it = iter(argv)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or len(args) != 1 or args[0].startswith("--"):
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    _, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    if not kernel.words(args[0]):
        print("refused: a question with no words", file=sys.stderr)
        return kernel.REFUSED
    cfg = kernel.config(box)
    alias: dict = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            print(f"refused: {why}", file=sys.stderr)
            return kernel.REFUSED
    read, missing = readings(args[0], kernel.chunks(Path(cfg["pile"])), alias)
    for w, (x, n) in read.items():
        print(f"read {w} as {x}: {n} passage{'s' * (n != 1)} hold{'s' * (n == 1)} it")
    for w in missing:
        print(f"no file has {w}, nor anything one edit from it")
    if read:
        print(f"ask:  {as_read(args[0], read)}")
    elif not missing:
        print("Your files hold every word of it; nothing to read differently.")
    return kernel.ESCALATE if missing and not read else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
