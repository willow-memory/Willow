"""people.py: everyone your files name, and every place each is mentioned.

    python adapters/stdlib/people/people.py --box DIR [WHO]

The roster of the people your folder speaks of, most mentioned first, and,
named, any one of them with every place they're mentioned:

    $ python adapters/stdlib/people/people.py --box DIR
      212  Kati      in 41 files, 2020-11-07 to 2026-10-16
       96  Ferris    in 18 files, 2021-02-12 to 2026-09-30
    2 people, by what the files do with a name

    $ python adapters/stdlib/people/people.py --box DIR ferris
    2021-02-12  hives/2021.txt:4   Ferris came by for the frames.
    ...
    96 mentions of "Ferris" in 18 files

**A name is known by what the files do with it**, not by a list of names:

- it is written capitalized at least as often as lowercase ("Walked" starts
  sentences, but "walked" outnumbers it, so it is no one; a "kati" typed
  quickly in a chat doesn't cost Kati her name);
- and at least once it does a person's thing: it speaks (a chat's
  `[stamp] Kati:`, "Kati said" and the other speech verbs), or it comes,
  goes, calls, rings, visits, meets, asks, tells, thanks, pays, helps or is
  rung, met, told or thanked by name ("rang Kati", "met Priya at the
  market");
- and it isn't a month's or a weekday's name, which also come and go.

Every word that passes is a person, and every time the files write it, in
any case, is a mention. What slips past the shapes is still shown, for you
to weigh: a company that "called" will stand in the roster, and the roster
says what it counted, never who matters.

A mention's date is the latest its line says (the kernel's `newest`), else
the nearest date written above it in its file, else the date its file is
named for; the roster's spans skip what no date reaches, and the drill-down
lists undated mentions last. WHO is matched as a word, case aside.

It only reads. Exit codes, the kernel's: 0 people found; 42 none, or WHO is
no one the files name; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: a capitalized word, diacritics welcome, as a name is written
CAP = re.compile(r"\b[A-ZÀ-Ö][a-zà-öø-ÿ'’]+\b")
VERBS = ("said|says|asked|asks|replied|replies|wrote|writes|texted|texts|came"
         "|comes|called|calls|rang|rings|visited|visits|met|meets|told|tells"
         "|thanked|thanks|paid|pays|helped|helps|left|arrived|loves|loved")  # fmt: skip
#: a word doing a person's thing, before or after the verb
DOES = re.compile(rf"\b(?P<who1>[A-ZÀ-Ö][a-zà-öø-ÿ'’]+)\s+(?:{VERBS})\b")
DONE_TO = re.compile(rf"\b(?:{VERBS})\s+(?P<who2>[A-ZÀ-Ö][a-zà-öø-ÿ'’]+)\b")
SPEAKER = re.compile(
    r"^\s*(?:\[[^\]]+\]|\(?\d{1,4}[/:.-]\d[\d/.:,\s-]*(?:[ap]\.?m\.?)?)[\s,–-]*"
    r"(?P<who3>[A-ZÀ-Ö][a-zà-öø-ÿ'’]+)(?: [A-ZÀ-Ö][a-zà-öø-ÿ'’]+)?\s*:"
)
NEVER = frozenset(
    "january february march april may june july august september october "
    "november december monday tuesday wednesday thursday friday saturday "
    "sunday".split()
)


def persons(pile: list[dict]) -> set[str]:
    """The words the files treat as people: capitalized at least as often as
    lowercase, at least once doing a person's thing, and no month or
    weekday."""
    cased: dict[str, list[int]] = {}
    acted: set[str] = set()
    for c in pile:
        for line in c["text"].splitlines():
            for m in CAP.finditer(line):
                w = m.group().lower()
                cased.setdefault(w, [0, 0])[0] += 1
            for shape in (DOES, DONE_TO, SPEAKER):
                got = shape.search(line)
                if got:
                    acted.add(next(filter(None, got.groups())).lower())
        for w in re.findall(r"\b[a-zà-öø-ÿ][a-zà-öø-ÿ'’]+\b", c["text"]):
            if w in cased:
                cased[w][1] += 1
    return {
        w
        for w in acted
        if w not in NEVER
        and w not in kernel.FUNCTION
        and w in cased
        and cased[w][0] >= cased[w][1]
    }


def file_lines(pile: list[dict]) -> dict[str, list[tuple[int, str]]]:
    """Each file's lines with their numbers, put back together from its
    passages (the kernel cuts a long run of lines into passages of 500)."""
    out: dict[str, list[tuple[int, str]]] = {}
    for c in pile:
        rows = out.setdefault(c["path"], [])
        rows += [(c["line"] + i, ln) for i, ln in enumerate(c["text"].splitlines())]
    return out


def mentions(pile: list[dict], names: set[str]) -> dict[str, list[dict]]:
    """{person: every line mentioning them, dated by the line, the nearest
    date above it, or the file's name}, in file order."""
    out: dict[str, list[dict]] = {w: [] for w in names}
    for path, rows in file_lines(pile).items():
        above, filed = "", kernel.newest(path)
        for n, line in rows:
            said = kernel.newest(line)
            here = set(kernel.words(line)) & names
            for w in here:
                out[w].append({"when": said or above or filed, "path": path,
                               "line": n, "text": line.strip()})  # fmt: skip
            if said:
                above = said
    return out


def day(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}" if d else "undated"


def roster(found: dict[str, list[dict]]) -> list[str]:
    rows = sorted(found.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    width = max(len(w) for w, _ in rows)
    out = []
    for w, ms in rows:
        files = len({m["path"] for m in ms})
        dated = sorted(m["when"] for m in ms if m["when"])
        span = f", {day(dated[0])} to {day(dated[-1])}" if dated else ""
        out.append(f"{len(ms):>5}  {w.capitalize():<{width}}  in {files}"
                   f" file{'s' if files != 1 else ''}{span}")  # fmt: skip
    out.append(f"{len(rows)} people, by what the files do with a name")
    return out


def drill(who: str, ms: list[dict]) -> list[str]:
    ms = sorted(ms, key=lambda m: (m["when"] == "", m["when"], m["path"], m["line"]))
    wp = max(len(f"{m['path']}:{m['line']}") for m in ms)
    out = []
    for m in ms:
        where = f"{m['path']}:{m['line']}"
        out.append(f"{day(m['when']):<10}  {where:<{wp}}  {m['text'][:100]}")
    files = len({m["path"] for m in ms})
    out.append(f'{len(ms)} mention{"s" if len(ms) != 1 else ""} of'
               f' "{who.capitalize()}" in {files} file{"s" if files != 1 else ""}')  # fmt: skip
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or len(args) > 1 or any(a.startswith("-") for a in args):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    pile = kernel.chunks(Path(kernel.config(box)["pile"]))
    names = persons(pile)
    if not names:
        print("No word of your folder does what the files do with a name.")
        return kernel.ESCALATE
    found = mentions(pile, names)
    if args:
        who = args[0].lower()
        if who not in found:
            print(f'No one your files name answers to "{args[0]}".')
            return kernel.ESCALATE
        for line in drill(who, found[who]):
            print(line)
        return kernel.ALIVE
    for line in roster(found):
        print(line)
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
