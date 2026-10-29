"""dialect.py: the words you use far more than the world does.

    python adapters/deps/dialect/dialect.py --box DIR [--lang CODE] [--top N]

Needs wordfreq (Apache-2.0; its word counts are CC BY-SA 4.0), pinned in
requirements.txt beside this file:

    pip install -r adapters/deps/dialect/requirements.txt

Every word of your files (letters only, three or more, not a function word,
and not one only ever written in capitals, which is a file's code, DTSTART
or a bank's EFTPOS) is counted, once a passage, a passage said many times
over counting once. Each held by at least `MIN_PASSAGES` passages is set
against wordfreq's counts for LANG (en unless --lang says), on wordfreq's
Zipf scale: a word's frequency per billion words as a power of ten, "the"
about 7.7, a word in a million 3. Two lists, the top N of each (30 unless
--top says):

    Words the world's counts don't have:
      petrak     in 55 passages
      keybed     in 35 passages

    Words you use far more than the world does (Zipf, you and it):
      odile   6.9 to 2.5, +4.4  in 166 passages

the first by passages, the second by how far beyond the world you use it,
ties by word. These are the words a newcomer's question won't use and your
files will: the first lines of a words list, or what a stranger needs
explained.

It reads only, and writes nothing, not even the record. If wordfreq isn't
installed it refuses and names the install; it never skips quietly. Exit
codes, the kernel's: 0 words listed; 42 none held by enough passages; 2
refused.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

INSTALL = "pip install -r adapters/deps/dialect/requirements.txt"
MIN_PASSAGES = 3  # fewer, and one letter's quirks look like a dialect
TOP = 30


def counts(pile: list[dict]) -> tuple[dict[str, int], dict[str, int], int, set]:
    """({word: times written}, {word: passages holding it}, words in all,
    {words ever written with a small letter}), each distinct passage once."""
    times: dict[str, int] = {}
    held: dict[str, int] = {}
    cased: set[str] = set()
    total, seen = 0, set()
    for c in pile:
        if c["id"] in seen:
            continue
        seen.add(c["id"])
        ws = kernel.words(c["text"])
        total += len(ws)
        for w in ws:
            times[w] = times.get(w, 0) + 1
        for w in set(ws):
            held[w] = held.get(w, 0) + 1
        cased |= {w for w in kernel.WORD.findall(c["text"]) if not w.isupper()}
    return times, held, total, {w.lower() for w in cased}


def dialect(pile: list[dict], world, top: int = TOP) -> tuple[list, list]:
    """([(word, your zipf, passages)] for words the world's counts don't
    have, most passages first; [(word, your zipf, the world's zipf,
    passages)] for the rest, most beyond the world's first; ties by word,
    `top` of each. `world` gives a word's Zipf, 0 for one it doesn't know.
    A word only ever written in capitals (DTSTART, a bank's EFTPOS) is a
    file's code, not a person's word, and is left out."""
    times, held, total, cased = counts(pile)
    unknown, known = [], []
    for w, n in held.items():
        if n < MIN_PASSAGES or len(w) < 3 or not w.isalpha() or w in kernel.FUNCTION:
            continue
        if w not in cased:
            continue
        yours = round(math.log10(times[w] / total * 1e9), 2)
        theirs = round(world(w), 2)
        if theirs:
            known.append((w, yours, theirs, n))
        else:
            unknown.append((w, yours, n))
    unknown.sort(key=lambda r: (-r[2], r[0]))
    known.sort(key=lambda r: (-(r[1] - r[2]), r[0]))
    return unknown[:top], [r for r in known if r[1] > r[2]][:top]


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {"--lang": "en", "--top": str(TOP)}
    it = iter(argv)
    bad = False
    for a in it:
        if a in ("--box", "--lang", "--top"):
            opts[a] = next(it, "")
        else:
            bad = True
    if (
        bad
        or not opts.get("--box")
        or not opts["--top"].isdigit()
        or opts["--top"] == "0"
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    try:
        import wordfreq
    except ImportError:
        print(f"refused: dialect needs wordfreq: {INSTALL}", file=sys.stderr)
        return kernel.REFUSED
    lang = opts["--lang"]
    if lang not in wordfreq.available_languages():
        print(f"refused: wordfreq has no counts for {lang!r}", file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    _, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    pile = kernel.chunks(Path(kernel.config(box)["pile"]))
    unknown, known = dialect(
        pile, lambda w: wordfreq.zipf_frequency(w, lang), int(opts["--top"])
    )
    if not unknown and not known:
        print(f"No word is held by {MIN_PASSAGES} passages or more: too few files.")
        return kernel.ESCALATE
    passages = len({c["id"] for c in pile})
    print(f"Your words against wordfreq's {lang}, from {passages} passages.")
    if unknown:
        print("\nWords the world's counts don't have:")
        width = max(len(w) for w, *_ in unknown)
        for w, _, n in unknown:
            print(f"  {w:<{width}}  in {n} passages")
    if known:
        print("\nWords you use far more than the world does (Zipf, you and it):")
        width = max(len(w) for w, *_ in known)
        for w, yours, theirs, n in known:
            print(f"  {w:<{width}}  {yours:.1f} to {theirs:.1f}, {yours - theirs:+.1f}"
                  f"  in {n} passages")  # fmt: skip
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
