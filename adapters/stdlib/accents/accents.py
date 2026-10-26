"""accents.py: a word typed without its accent, read as your files write it. Python 3.9+.

    python adapters/stdlib/accents/accents.py --box DIR "did i promise siobhan anything"
    read siobhan as siobhán: 3 passages hold it
    ask:  did i promise siobhán anything

    python adapters/stdlib/accents/accents.py words --box DIR
    siobhan = siobhán

To the kernel a word is its letters, and "siobhan" isn't "siobhán". A word of
your question that no file of yours holds is compared with your files' words
with every accent taken off both (é is e, ø is o, ß is ss), and read as the
one the most passages hold that way, a tie going to the first in sorted
order. It works both ways: "cafe" finds "café", and "café" finds "cafe".

It never asks for you: the question as read is printed for you to ask.

`words` is the lasting fix: one words-list line for each word of your files
that has an accent, the word without it on the left. Add them to your words
list, and the kernel reads each one that way every time, on its own. Nothing
is written: the lines go to standard output, for you to read before you keep
them.

It reads only, and writes nothing, not even the record. Exit codes, the
kernel's: 0 every word is held, or a reading is offered (`words`: lines
printed, or none needed); 42 a word no file holds, accent or not; 2 refused.
"""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: letters with no accent to take off in Unicode's own decomposition
PLAIN = str.maketrans(
    {"ø": "o", "ł": "l", "đ": "d", "ħ": "h", "ı": "i", "ŧ": "t", "ß": "ss",
     "æ": "ae", "œ": "oe", "þ": "th", "ð": "d"}
)  # fmt: skip


def bare(w: str) -> str:
    """`w` with every accent taken off: é is e, ø is o, ß is ss."""
    split = unicodedata.normalize("NFD", w)
    return "".join(c for c in split if not unicodedata.combining(c)).translate(PLAIN)


def spellings(pile: list[dict]) -> dict[str, dict[str, int]]:
    """{a word with its accents off: {each way the files write it: passages}}."""
    out: dict[str, dict[str, int]] = {}
    for c in pile:
        for w in set(kernel.words(c["text"]) + kernel.words(c["path"])):
            ways = out.setdefault(bare(w), {})
            ways[w] = ways.get(w, 0) + 1
    return out


def readings(question: str, pile: list[dict], alias: dict) -> tuple[dict, list]:
    """({word: (as written, passages holding it)}, [words no file holds,
    accent or not]), for the question's words no file holds."""
    every: set[str] = set()
    for c in pile:
        every |= kernel.toks(c)
    ways = spellings(pile)
    read, missing = {}, []
    for w in dict.fromkeys(kernel.words(question)):
        if w in kernel.FUNCTION or kernel.held_by(w, every, alias):
            continue
        found = {x: n for x, n in ways.get(bare(w), {}).items() if x != w}
        if found:
            best = min((-n, x) for x, n in found.items())
            read[w] = (best[1], -best[0])
        else:
            missing.append(w)
    return read, missing


def words_lines(pile: list[dict]) -> list[str]:
    """`plain = accented` for each accented word, sorted: a words list's lines."""
    out = []
    for plain, ways in sorted(spellings(pile).items()):
        accented = sorted(x for x in ways if x != plain)
        if accented and kernel.words(plain) == [plain]:
            out.append(f"{plain} = {', '.join(accented)}")
    return out


def main(argv: list[str]) -> int:
    verb = "words" if argv[:1] == ["words"] else "read"
    rest = argv[1:] if verb == "words" else argv
    opts: dict[str, str] = {}
    args: list[str] = []
    it = iter(rest)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        else:
            args.append(a)
    if (
        not opts.get("--box")
        or len(args) != (verb == "read")
        or any(a.startswith("--") for a in args)
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    _, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    cfg = kernel.config(box)
    pile = kernel.chunks(Path(cfg["pile"]))
    if verb == "words":
        lines = words_lines(pile)
        print("\n".join(lines) if lines else "No word of your files has an accent.")
        return kernel.ALIVE
    if not kernel.words(args[0]):
        print("refused: a question with no words", file=sys.stderr)
        return kernel.REFUSED
    alias: dict = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            print(f"refused: {why}", file=sys.stderr)
            return kernel.REFUSED
    read, missing = readings(args[0], pile, alias)
    for w, (x, n) in read.items():
        print(f"read {w} as {x}: {n} passage{'s' * (n != 1)} hold{'s' * (n == 1)} it")
    for w in missing:
        print(f"no file has {w}, with its accents or without")
    if read:
        asked = " ".join(read.get(w, (w,))[0] for w in kernel.words(args[0]))
        print(f"ask:  {asked}")
    elif not missing:
        print("Your files hold every word of it; nothing to read differently.")
    return kernel.ESCALATE if missing and not read else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
