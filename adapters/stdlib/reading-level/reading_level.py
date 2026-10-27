"""reading_level.py: how hard each file of your folder reads, easiest first.

    python adapters/stdlib/reading-level/reading_level.py --box DIR

One row per file: its Flesch reading ease, said in a word, and the lengths
the score is made of, so a teacher can find texts for a class:

      97  very easy     7.5 words a sentence  1.21 syllables a word    412 words  stories/frog.md
      54  fairly hard  19.8 words a sentence  1.58 syllables a word   1890 words  letters/bank.md
    too short to score (3 words)  notes/one-liner.md
    2 files scored, 1 too short

The score is Flesch's: 206.835 - 1.015 (words a sentence) - 84.6 (syllables
a word), rounded. 90 or over reads very easy, 80 easy, 70 fairly easy, 60
plain, 50 fairly hard, 30 hard, and under 30 very hard. A sentence ends at
., ! or ? or at its line's end, so a list of notes is read as its items. A
word is its letters ("don't" is one word, a bare number is none), and its
syllables are counted by a rule of thumb (runs of vowels, a silent final e
taken off), not a dictionary. Flesch was made for English prose: on another
language, or a file of tables, the number says little, and the two lengths
beside it say more.

A file under 30 words is listed, not scored: too little text says nothing
about how it reads. It only reads. Exit codes, the kernel's: 0 files
scored; 42 nothing long enough to score; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

WORD = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)*")
VOWELS = re.compile(r"[aeiouy]+")
FLOOR = 30  # words a file needs before its score says anything
BANDS = [(90, "very easy"), (80, "easy"), (70, "fairly easy"), (60, "plain"),
         (50, "fairly hard"), (30, "hard")]  # fmt: skip


def syllables(word: str) -> int:
    """A word's syllables by rule of thumb: its runs of vowels (y a vowel),
    one taken off for a silent final e ("piece" has one, "table" keeps two),
    and never fewer than one."""
    w = word.lower().replace("'", "")
    n = len(VOWELS.findall(w))
    if n > 1 and w.endswith("e") and not w.endswith("le"):
        n -= 1
    return max(n, 1)


def sentences(text: str) -> int:
    """Sentences end at ., ! or ? or at their line's end: prose is counted
    as written, and a list of notes as its items."""
    return sum(
        1 for line in text.splitlines() for part in re.split(r"[.!?]+", line)
        if WORD.search(part)
    )  # fmt: skip


def measure(text: str) -> tuple[int, float, float, int]:
    """(Flesch reading ease, words a sentence, syllables a word, words)."""
    ws = WORD.findall(text)
    wps = len(ws) / max(sentences(text), 1)
    spw = sum(syllables(w) for w in ws) / max(len(ws), 1)
    return round(206.835 - 1.015 * wps - 84.6 * spw), wps, spw, len(ws)


def band(score: int) -> str:
    for floor, name in BANDS:
        if score >= floor:
            return name
    return "very hard"


def rows(pile: list[dict]) -> tuple[list[tuple], list[tuple]]:
    """(scored, too short): per file, over all its passages together. Scored
    rows come easiest first, ties and the too-short by file name."""
    texts: dict[str, list[str]] = {}
    for c in pile:
        texts.setdefault(c["path"], []).append(c["text"])
    scored, short = [], []
    for path in sorted(texts):
        score, wps, spw, n = measure("\n".join(texts[path]))
        if n < FLOOR:
            short.append((n, path))
        else:
            scored.append((score, wps, spw, n, path))
    return sorted(scored, key=lambda r: (-r[0], r[4])), short


def show(scored: list[tuple], short: list[tuple]) -> list[str]:
    out = [
        f"{score:>4}  {band(score):<11} {wps:>5.1f} words a sentence"
        f"  {spw:.2f} syllables a word  {n:>6} words  {path}"
        for score, wps, spw, n, path in scored
    ]
    out += [f"too short to score ({n} word{'s' if n != 1 else ''})  {path}"
            for n, path in short]  # fmt: skip
    out.append(f"{len(scored)} files scored, {len(short)} too short")
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or args:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    scored, short = rows(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not scored:
        print("Nothing long enough to score.")
        return kernel.ESCALATE
    for line in show(scored, short):
        print(line)
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
