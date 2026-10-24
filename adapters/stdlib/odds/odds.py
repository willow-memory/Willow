"""odds.py: exact odds for a roll of the dice, as fractions. Python 3.9+.

    python adapters/stdlib/odds/odds.py DICE [--at-least N] [--bands HIGH,LOW]

DICE is dice notation: 2d6, 1d20+3, 3d6-2, 1d8+1d6. Every total and its
chance, counted over every way the dice can fall, as a fraction and a
percentage:

    2d6
      2   1/36    2.78%
      7   1/6    16.67%
      ...

--at-least N: the chance of N or more, exactly. --bands 10,7: the chance of
each band, highest first: 10 or more, 7 to 9, 6 or less. That's the strong,
weak and miss of a 2d6 game; any thresholds work, one or more.

Every chance is a fractions.Fraction until it's printed, so the odds add up
to exactly 1. The idea is willow-bot's odds (onescript/odds.py), which counts
2d6 plus a stat over its 36 outcomes for its game; this counts any dice.

It reads nothing and writes nothing. Exit codes, the kernel's: 0 printed;
2 dice it can't read, or a bad command line.
"""

from __future__ import annotations

import re
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

TERM = re.compile(r"([+-]?)\s*(?:(\d*)d(\d+)|(\d+))", re.I)
#: the most dice and the largest die it counts over, so a typo can't hang it
MAX_DICE, MAX_SIDES = 100, 1000


def parse(dice: str) -> tuple[list[tuple[int, int, int]], int]:
    """([(sign, count, sides)], constant) from notation; ValueError if not dice."""
    text = re.sub(r"\s*([+-])\s*", r"\1", dice.strip())  # spaces only around + and -
    if not text or TERM.sub("", text) or re.search(r"\s", text):
        raise ValueError(f"{dice!r} isn't dice notation: 2d6, 1d20+3, 1d8+1d6")
    terms, const, pos = [], 0, 0
    for m in TERM.finditer(text):
        if m.start() != pos or (pos and not m.group(1)):
            raise ValueError(f"{dice!r} isn't dice notation: 2d6, 1d20+3, 1d8+1d6")
        pos = m.end()
        sign = -1 if m.group(1) == "-" else 1
        if m.group(4):
            const += sign * int(m.group(4))
            continue
        count, sides = int(m.group(2) or 1), int(m.group(3))
        if not (1 <= count <= MAX_DICE and 2 <= sides <= MAX_SIDES):
            raise ValueError(
                f"{count}d{sides}: up to {MAX_DICE} dice of 2 to {MAX_SIDES} sides"
            )
        terms.append((sign, count, sides))
    if not terms:
        raise ValueError(f"{dice!r} rolls no dice")
    return terms, const


def distribution(dice: str) -> dict[int, Fraction]:
    """{total: exact chance} over every way the dice can fall."""
    terms, const = parse(dice)
    dist = {const: Fraction(1)}
    for sign, count, sides in terms:
        face = Fraction(1, sides)
        for _ in range(count):
            nxt: dict[int, Fraction] = {}
            for total, p in dist.items():
                for f in range(1, sides + 1):
                    t = total + sign * f
                    nxt[t] = nxt.get(t, Fraction(0)) + p * face
            dist = nxt
    return dict(sorted(dist.items()))


def at_least(dist: dict[int, Fraction], n: int) -> Fraction:
    return sum((p for t, p in dist.items() if t >= n), Fraction(0))


def bands(dist: dict[int, Fraction], cuts: list[int]) -> list[tuple[str, Fraction]]:
    """Each band's chance, highest first: cuts [10, 7] gives 10+, 7-9, 6-."""
    cuts = sorted(set(cuts), reverse=True)
    out, top = [], None
    for c in cuts:
        label = (
            f"{c}+" if top is None else (f"{c}-{top - 1}" if top - 1 > c else f"{c}")
        )
        out.append(
            (
                label,
                sum(
                    (p for t, p in dist.items() if t >= c and (top is None or t < top)),
                    Fraction(0),
                ),
            )
        )
        top = c
    out.append(
        (
            f"{top - 1} or less",
            sum((p for t, p in dist.items() if t < top), Fraction(0)),
        )
    )
    return out


def pct(p: Fraction) -> str:
    return f"{float(p) * 100:6.2f}%"


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--at-least", "--bands"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if len(args) != 1 or args[0].startswith("--"):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    try:
        dist = distribution(args[0])
        n = int(opts["--at-least"]) if "--at-least" in opts else None
        cuts = (
            [int(c) for c in opts["--bands"].split(",")] if "--bands" in opts else None
        )
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    print(args[0])
    if n is not None:
        p = at_least(dist, n)
        print(f"  {n} or more: {p}  {pct(p).strip()}")
    elif cuts:
        for label, p in bands(dist, cuts):
            print(f"  {label:<12} {str(p):<10} {pct(p)}")
    else:
        width = max(len(str(p)) for p in dist.values())
        for t, p in dist.items():
            print(f"  {t:>4}   {str(p):<{width}}  {pct(p)}")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
