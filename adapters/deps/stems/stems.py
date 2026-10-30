"""stems.py: a word's other forms, in 20+ languages, read as your files write it.

    python adapters/deps/stems/stems.py --box DIR [--lang LANG] "QUESTION"

    python adapters/deps/stems/stems.py --box DIR --lang german "häuser am see"
    read häuser as haus: 2 passages hold it
    ask:  haus am see

Needs snowballstemmer (BSD-3-Clause), pinned in requirements.txt beside this
file:

    pip install -r adapters/deps/stems/requirements.txt

The kernel's own `stem` knows a few English endings, and only for words of
ASCII letters, so "häuser" isn't "haus" and "книги" isn't "книга". A word
of your question that no file of yours holds is cut to its stem by Snowball's
stemmer for LANG (english unless --lang says: french, german, spanish,
russian and the rest Snowball has), and so is every word of your files; it's
read as the form of the same stem that the most passages hold, a tie going to
the first in sorted order. A word your files hold as typed, or that your
words list reads, is left alone.

It never asks for you: the question as read is printed for you to ask.

It reads only, and writes nothing, not even the record. If snowballstemmer
isn't installed it refuses and names the install; it never skips quietly.
Exit codes, the kernel's: 0 every word is held, or a reading is offered; 42
a word no file holds in any form; 2 refused.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

INSTALL = "pip install -r adapters/deps/stems/requirements.txt"


def forms(pile: list[dict], stem) -> dict[str, dict[str, int]]:
    """{a stem: {each word of the files with it: passages holding it}}."""
    out: dict[str, dict[str, int]] = {}
    for c in pile:
        for w in set(kernel.words(c["text"]) + kernel.words(c["path"])):
            ways = out.setdefault(stem(w), {})
            ways[w] = ways.get(w, 0) + 1
    return out


def readings(question: str, pile: list[dict], alias: dict, stem) -> tuple[dict, list]:
    """({word: (the form the files hold, passages holding it)}, [words no file
    holds in any form]), for the question's words no file holds."""
    every: set[str] = set()
    for c in pile:
        every |= kernel.toks(c)
    ways = forms(pile, stem)
    read, missing = {}, []
    for w in dict.fromkeys(kernel.words(question)):
        if w in kernel.FUNCTION or kernel.held_by(w, every, alias):
            continue
        found = {x: n for x, n in ways.get(stem(w), {}).items() if x != w}
        if found:
            best = min((-n, x) for x, n in found.items())
            read[w] = (best[1], -best[0])
        else:
            missing.append(w)
    return read, missing


def stemmer(lang: str):
    """Snowball's stemmer for `lang`, as a function of one word; None when it
    has none by that name. Asked by name: 2.0.0's list of languages is broken."""
    import snowballstemmer

    try:
        s = snowballstemmer.stemmer(lang)
    except KeyError:
        return None
    return s.stemWord


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {"--lang": "english"}
    args: list[str] = []
    it = iter(argv)
    for a in it:
        if a in ("--box", "--lang"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or len(args) != 1 or args[0].startswith("--"):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    try:
        import snowballstemmer  # noqa: F401
    except ImportError:
        print(f"refused: stems needs snowballstemmer: {INSTALL}", file=sys.stderr)
        return kernel.REFUSED
    stem = stemmer(opts["--lang"])
    if stem is None:
        print(f"refused: Snowball has no stemmer for {opts['--lang']!r}",
              file=sys.stderr)  # fmt: skip
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
    pile = kernel.chunks(Path(cfg["pile"]))
    read, missing = readings(args[0], pile, alias, stem)
    for w, (x, n) in read.items():
        print(f"read {w} as {x}: {n} passage{'s' * (n != 1)} hold{'s' * (n == 1)} it")
    for w in missing:
        print(f"no file has {w}, in any form")
    if read:
        asked = " ".join(read.get(w, (w,))[0] for w in kernel.words(args[0]))
        print(f"ask:  {asked}")
    elif not missing:
        print("Your files hold every word of it; nothing to read differently.")
    return kernel.ESCALATE if missing and not read else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
