"""pile_poetry.py: verse from the word pairs your own files use most, in your
own dialect. Python 3.9+.

    python adapters/stdlib/pile-poetry/pile_poetry.py --box DIR [--seed TEXT] [--lines N]

Your files are read line by line, and the pairs of words that sit side by side
more than once are counted: "tomatoes want", "want six", "six hours". A poem
is walked along those pairs, each next word drawn with the weight of how often
your files put it there:

    Tomatoes want six hours of sun
    Bins go out on thursday night
    Hours of sun and the bins go

    Thursday night and the garden
    ...

No word is in it that your files don't have, and no two words sit together that
your files never put side by side. Every draw is made by willow's seeded stream
(the one [tarot](../tarot/) deals from) from the seed and a counter, so the same
folder, seed and line count give the same poem on any machine, and it can be
made again to check. The seed is "poem" unless --seed says; --lines is 8
unless it says (1 to 40), set in stanzas of four.

**What counts as a pair.** Two words next to each other on one line, as the
kernel reads words (lower case, punctuation gone, a word with a digit in it
left out so a date or an id never gets in), seen at least twice across your
files. A line that shouts throughout (a calendar's DTSTART) or opens as a field
("From:", "UID=") is a machine's and is not read. A pair never crosses the end of a line or of a file. Pairs are counted
from the folder alone: no list of the world's words, no model.

A line of verse starts at a word that begins a pair, and goes on up to eight
words, stopping early where a word has no pair to follow. With fewer than
twelve different pairs seen twice, there is too little to write from, and it
says so (exit 42) instead of padding from anywhere else.

It only reads. Exit codes, the kernel's: 0 a poem; 42 too little repeated to
write from; 2 refused.
"""

from __future__ import annotations

import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "tarot"))
import kernel  # noqa: E402
import tarot  # noqa: E402

MIN_SEEN = 2  # times a pair must be seen to count
MIN_PAIRS = 12  # pairs needed before there is anything to write from
LONGEST = 8  # words in a line of verse
STANZA = 4  # lines in a stanza


def yours(line: str) -> bool:
    """Whether a line is one you wrote: it has a lowercase letter in it (a
    calendar's DTSTART shouts) and doesn't open as a field ("From:", "UID=")."""
    first = line.strip().split(" ", 1)[0]
    return any(c.islower() for c in line) and not any(c in ":;=<" for c in first)


def pairs(pile: list[dict]) -> dict[tuple[str, str], int]:
    """{(word, next word): times seen} for pairs seen at least MIN_SEEN times,
    counted line by line over every passage."""
    seen: dict[tuple[str, str], int] = {}
    for c in pile:
        for line in c["text"].splitlines():
            if not yours(line):
                continue
            ws = [w for w in kernel.words(line) if not any(ch.isdigit() for ch in w)]
            for a, b in zip(ws, ws[1:]):
                seen[(a, b)] = seen.get((a, b), 0) + 1
    return {p: n for p, n in seen.items() if n >= MIN_SEEN}


def follows(counts: dict[tuple[str, str], int]) -> dict[str, list[tuple[str, int]]]:
    """{word: [(next word, weight)]} in a fixed order, so a draw is repeatable."""
    out: dict[str, list[tuple[str, int]]] = {}
    for (a, b), n in sorted(counts.items()):
        out.setdefault(a, []).append((b, n))
    return out


def draw(options: list[tuple[str, int]], rng) -> str:
    """One word from (word, weight) options, in proportion to the weights."""
    pick = rng.below(sum(n for _, n in options))
    for word, n in options:
        if pick < n:
            return word
        pick -= n
    raise AssertionError("the draw is below the total")


def poem(counts: dict[tuple[str, str], int], seed: str, lines: int) -> list[str]:
    nxt = follows(counts)
    starts = [(a, sum(n for _, n in opts)) for a, opts in sorted(nxt.items())]
    rng = tarot.Stream(f"{seed}:poetry".encode())
    out = []
    for _ in range(lines):
        word = draw(starts, rng)
        line = [word]
        while len(line) < LONGEST and word in nxt:
            word = draw(nxt[word], rng)
            line.append(word)
        text = " ".join(line)
        out.append(text[:1].upper() + text[1:])
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--seed", "--lines"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    n = opts.get("--lines", "8")
    if (
        not opts.get("--box")
        or args
        or not n.isdigit()
        or not 1 <= int(n) <= 40
        or opts.get("--seed") == ""
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    counts = pairs(kernel.chunks(Path(kernel.config(box)["pile"])))
    if len(counts) < MIN_PAIRS:
        print(
            f"Too little to write from: {len(counts)} word pairs seen twice, {MIN_PAIRS} needed."
        )
        return kernel.ESCALATE
    verse = poem(counts, opts.get("--seed", "poem"), int(n))
    print(
        "\n\n".join(
            "\n".join(verse[i : i + STANZA]) for i in range(0, len(verse), STANZA)
        )
    )
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
