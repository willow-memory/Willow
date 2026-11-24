"""exhaustion.py: what a level of exhaustion does to a roll, a speed and a hit point maximum. Python 3.9+.

    python adapters/stdlib/exhaustion/exhaustion.py LEVEL [--edition 5.1|5.2] [--speed FEET] [--hp-max N]

A pure rule, no box and no record: a level in, its effects out. The two SRD
editions say different things about the same word, so both are kept, named,
never mixed; 5.2 unless 5.1 is asked for:

  5.1  six cumulative levels: 1 disadvantage on ability checks, 2 speed
       halved, 3 disadvantage on attack rolls and saving throws, 4 hit point
       maximum halved, 5 speed 0, 6 death (SRD 5.1, CC-BY-4.0).
  5.2  every d20 test is reduced by 2 per level, Speed by 5 feet per level,
       level 6 is death (SRD 5.2, CC-BY-4.0).

In both, a finished long rest eases one level (5.1's food and drink are not
modelled). LEVEL is 0 to 6. It prints the effect as a game master would say
it, then each number: the d20 change, each kind of roll's mode, the speed
and hit point maximum after it when given, and the level after a long rest.

Exit codes, the kernel's: 0 said; 2 refused, with why.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

EDITIONS = ("5.1", "5.2")
DEFAULT = "5.2"
MAX_LEVEL = 6
KINDS = ("check", "attack", "save")
USAGE = __doc__.split("\n\n")[1]


def _level(level: int) -> int:
    if isinstance(level, bool) or not isinstance(level, int) or not 0 <= level <= MAX_LEVEL:  # fmt: skip
        raise ValueError(f"exhaustion level is 0 to {MAX_LEVEL}, not {level!r}")
    return level


def _edition(edition: str) -> str:
    if edition not in EDITIONS:
        raise ValueError(f"edition is one of {', '.join(EDITIONS)}, not {edition!r}")
    return edition


def dead(level: int) -> bool:
    """Level 6 is death, in both editions."""
    return _level(level) >= MAX_LEVEL


def after_long_rest(level: int) -> int:
    """A finished long rest eases one level, never below 0, in both editions."""
    return max(0, _level(level) - 1)


def d20_modifier(level: int, edition: str = DEFAULT) -> int:
    """What every d20 test is changed by: 5.2, -2 a level; 5.1 none (it gives
    disadvantage instead, see roll_mode)."""
    _level(level)
    return -2 * level if _edition(edition) == "5.2" else 0


def speed_change(level: int, speed: int, edition: str = DEFAULT) -> int:
    """A speed in feet, after exhaustion: 5.2, 5 feet off a level, never below
    0; 5.1, halved (rounded down) from level 2, 0 from level 5."""
    _level(level)
    if isinstance(speed, bool) or not isinstance(speed, int) or speed < 0:
        raise ValueError(f"a speed is a whole number of feet, 0 or more, not {speed!r}")  # fmt: skip
    if _edition(edition) == "5.2":
        return max(0, speed - 5 * level)
    if level >= 5:
        return 0
    return speed // 2 if level >= 2 else speed


def roll_mode(kind: str, level: int, edition: str = DEFAULT) -> str:
    """'disadvantage' or 'normal' for a kind of roll ('check', 'attack',
    'save'). Only 5.1 gives disadvantage (checks from level 1, attacks and
    saves from 3); in 5.2 it is always 'normal', the penalty is d20_modifier."""
    _level(level)
    if kind not in KINDS:
        raise ValueError(f"a kind of roll is one of {', '.join(KINDS)}, not {kind!r}")
    if _edition(edition) != "5.1":
        return "normal"
    return "disadvantage" if level >= (1 if kind == "check" else 3) else "normal"


def hp_max(level: int, maximum: int, edition: str = DEFAULT) -> int:
    """Hit point maximum: halved from level 4 in 5.1 (rounded down, at least
    1); unchanged in 5.2."""
    _level(level)
    if isinstance(maximum, bool) or not isinstance(maximum, int) or maximum < 1:
        raise ValueError(f"a hit point maximum is a whole number, 1 or more, not {maximum!r}")  # fmt: skip
    if _edition(edition) == "5.1" and level >= 4:
        return max(1, maximum // 2)
    return maximum


def said(level: int, edition: str = DEFAULT) -> str:
    """The effect in a table's words, as a game master would say it."""
    if _level(level) == 0:
        return "not worn out"
    if dead(level):
        return "worn out to death"
    if _edition(edition) == "5.2":
        return f"worn out ({level}): every d20 roll {d20_modifier(level)}, speed {-5 * level} feet"  # fmt: skip
    parts = ["disadvantage on ability checks"]
    if level >= 2:
        parts.append("speed halved")
    if level >= 3:
        parts.append("disadvantage on attacks and saves")
    if level >= 4:
        parts.append("hit point maximum halved")
    if level >= 5:
        parts.append("speed 0")
    return f"worn out ({level}): " + ", ".join(parts)


def whole(text: str, what: str) -> int:
    """A command line's number; ValueError naming what it was for."""
    try:
        return int(text, 10)
    except ValueError:
        raise ValueError(f"{what} is a whole number, not {text!r}") from None


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--edition", "--speed", "--hp-max"):
            opts[a] = next(it, None)
        else:
            args.append(a)
    if len(args) != 1 or None in opts.values():
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    edition = opts.get("--edition", DEFAULT)
    try:
        level = whole(args[0], "LEVEL")
        lines = [said(level, edition), f"d20 tests: {d20_modifier(level, edition):+d}"]
        lines.append("; ".join(f"{k}s: {roll_mode(k, level, edition)}" for k in KINDS))  # fmt: skip
        if "--speed" in opts:
            speed = whole(opts["--speed"], "--speed")
            lines.append(f"speed: {speed} feet, {speed_change(level, speed, edition)} worn out")  # fmt: skip
        if "--hp-max" in opts:
            most = whole(opts["--hp-max"], "--hp-max")
            lines.append(f"hit point maximum: {most}, {hp_max(level, most, edition)} worn out")  # fmt: skip
        lines.append(f"after a long rest: level {after_long_rest(level)}")
    except ValueError as e:
        print(f"exhaustion: {e}", file=sys.stderr)
        return kernel.REFUSED
    print(f"SRD {edition}, level {level}")
    print("\n".join(lines))
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
