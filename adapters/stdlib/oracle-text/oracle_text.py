"""oracle_text.py: readings written by a Tracery grammar, every branch picked
by the seeded stream, so each one can be replayed. Python 3.9+.

    python adapters/stdlib/oracle-text/oracle_text.py --seed TEXT [--grammar FILE] [--count N] [--origin NAME]

A grammar is a JSON object of symbols, each a string or a list of strings to
choose from, as [Tracery](https://tracery.io/) writes them:

    {"origin": ["#animal.a.capitalize# will cross your path, #mood#."],
     "animal": ["owl", "heron", "otter"],
     "mood": ["and say nothing", "carrying #thing.s#"],
     "thing": ["stone", "apple"]}

`#name#` is replaced by one of that symbol's rules, expanded in turn;
`#name.a#` puts an indefinite article before it (a heron, an owl), `.s` makes
it plural, `.ed` past tense, `.capitalize` and `.capitalizeAll` and `.allCaps`
change its case, and they chain (`#name.s.capitalize#`). `[who:#animal#]` sets
a name for the rest of the reading, so `#who#` says the same animal again. Text
that is none of those is kept as written. With no --grammar, a small grammar of
its own is used.

**Every branch is picked by willow's seeded stream** (sha256-stream/v1, the one
[tarot](../tarot/) deals from): SHA-256 over the seed and a counter, `below(k)`
by rejection. The reading numbered i is made from the seed "TEXT:oracle:i"
alone, so the same seed, grammar and number give the same reading on any
machine, whoever runs it, and a reading can be made again to check it. Nothing
is random and nothing is predicted: it is a toy that can't be rigged.

--count N (1 unless said) prints that many readings, one to a line. --origin
names the symbol to start from (origin unless said).

It reads the grammar file if you name one, and writes nothing. Exit codes, the
kernel's: 0 readings printed; 2 refused: a bad command line, a grammar that
isn't a JSON object of strings and lists of strings, a symbol it doesn't have,
or rules that expand without end.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "tarot"))
import kernel  # noqa: E402
import tarot  # noqa: E402

DEPTH = 40  # nested expansions before rules are called endless
BUILTIN = {
    "origin": [
        "#animal.a.capitalize# will cross your path today, #mood#.",
        "Look for #thing.a# in #place#; #animal.s# know where it is.",
        "[who:#animal#]The #who# in #place# has seen #thing.a#, and is #mood#.",
    ],
    "animal": ["owl", "heron", "otter", "fox", "moth", "hare"],
    "mood": ["carrying #thing.a#", "saying nothing", "in no hurry", "looking at you"],
    "thing": ["stone", "apple", "key", "feather", "letter", "umbrella"],
    "place": ["the garden", "a doorway", "the second drawer", "an old coat"],
}
TOKEN = re.compile(r"#([^#]*)#|\[([^\[\]:]+):((?:[^\[\]]|\[[^\[\]]*\])*)\]")


class Refused(Exception):
    pass


def article(word: str) -> str:
    return ("an " if word[:1].lower() in "aeiou" else "a ") + word


def plural(word: str) -> str:
    if word.endswith(("s", "x", "z", "h")):
        return word + "es"
    if len(word) > 1 and word.endswith("y") and word[-2] not in "aeiou":
        return word[:-1] + "ies"
    return word + "s"


def past(word: str) -> str:
    if word.endswith("e"):
        return word + "d"
    if len(word) > 1 and word.endswith("y") and word[-2] not in "aeiou":
        return word[:-1] + "ied"
    return word + "ed"


MODIFIERS = {
    "a": article,
    "s": plural,
    "ed": past,
    "capitalize": lambda w: w[:1].upper() + w[1:],
    "capitalizeAll": lambda w: " ".join(x[:1].upper() + x[1:] for x in w.split(" ")),
    "allCaps": lambda w: w.upper(),
}


def check(grammar) -> None:
    ok = isinstance(grammar, dict) and all(
        isinstance(k, str)
        and (
            isinstance(v, str)
            or (isinstance(v, list) and v and all(isinstance(x, str) for x in v))
        )
        for k, v in grammar.items()
    )
    if not ok:
        raise Refused(
            "a grammar is a JSON object of strings and non-empty lists of strings"
        )


def expand(text: str, grammar: dict, rng, names: dict, depth: int = 0) -> str:
    """text with every #symbol# and [name:rule] in it expanded."""
    if depth > DEPTH:
        raise Refused("rules that expand without end")

    def one(m: re.Match) -> str:
        if m.group(2) is not None:  # [name:rule]
            names[m.group(2)] = expand(m.group(3), grammar, rng, names, depth + 1)
            return ""
        symbol, *mods = m.group(1).split(".")
        if symbol in names:
            out = names[symbol]
        elif symbol in grammar:
            rules = grammar[symbol]
            rule = rules if isinstance(rules, str) else rules[rng.below(len(rules))]
            out = expand(rule, grammar, rng, names, depth + 1)
        else:
            raise Refused(f"no symbol {symbol!r} in the grammar")
        for mod in mods:
            if mod not in MODIFIERS:
                raise Refused(f"no modifier {mod!r}: {', '.join(MODIFIERS)}")
            out = MODIFIERS[mod](out)
        return out

    return TOKEN.sub(one, text)


def reading(grammar: dict, seed: str, i: int, origin: str = "origin") -> str:
    """The i-th reading of a seed: the origin expanded from the stream alone."""
    if origin not in grammar:
        raise Refused(f"no symbol {origin!r} in the grammar")
    rng = tarot.Stream(f"{seed}:oracle:{i}".encode())
    return expand(f"#{origin}#", grammar, rng, {})


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--seed", "--grammar", "--count", "--origin"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    count = opts.get("--count", "1")
    if not opts.get("--seed") or args or not count.isdigit() or int(count) < 1:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    try:
        grammar = BUILTIN
        if opts.get("--grammar"):
            try:
                grammar = json.loads(
                    Path(opts["--grammar"]).read_text(encoding="utf-8")
                )
            except (OSError, ValueError, UnicodeDecodeError):
                raise Refused(f"could not read {opts['--grammar']} as JSON") from None
        check(grammar)
        lines = [
            reading(grammar, opts["--seed"], i, opts.get("--origin", "origin"))
            for i in range(1, int(count) + 1)
        ]
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    print("\n".join(lines))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
