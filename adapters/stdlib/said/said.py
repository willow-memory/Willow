"""said.py: your files' quotes, gathered into a dated timeline of who said what.

    python adapters/stdlib/said/said.py --box DIR [WHO]

Every line of your folder that quotes someone, oldest first, each with who
said it, the words as written, and where:

    2023-04-17  Mags        Terry says Gerry owes him $10 from the footy   chats/mags.txt:3
    2024-02-28  Teo         first £100 back, thank you again x             chats/teo.txt:12
    undated     Sam         we'll cover the parts ourselves                minutes.md:4  (date from line 2)

A line quotes someone when it says so by shape, and three shapes are read:

- **a chat's line**: a timestamp, then a name and a colon
  (`[13/12/2024, 08:10] Teo: trimis`, `17/04/2023, 12:27 pm - Mags: ...`),
  as chats are written and as the chats reader mirrors them;
- **a speech verb**: a name, then said, says, wrote, writes, asked, asks,
  replied, replies, texted or texts, at the line's start
  (`Sam said: we'll cover the parts`, `Ana wrote that ...`);
- **a quotation**: a name, a colon, and the words in quotation marks
  (`Mags: "no way"`).

A bare `Name: words` with none of those marks is not read: a mail's
`Subject:` and a note's `TODO:` wear the same shape, and a quote needs its
marks. A name is one to three capitalized words, so `RE:` and `TODO:` never
pass for one.

A line's date is the latest it says, read as the kernel reads one (its
`newest`; 11/03/2026, either way round, is never guessed); a line that says
none takes the nearest date written above it in its file, else the date its
file is named for, and the timeline says which. Undated quotes come last:
your files don't say when.

WHO narrows it to one speaker: every quote whose speaker's words hold each
of WHO's, so "mags" finds Mags Doyle, and "mags doyle" doesn't find Mags
Riley. It only reads. Exit codes, the kernel's: 0 quotes found; 42 none, or
none by WHO; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: one to three capitalized words: Mags, Dev Raman, O'Brien, Siobhán; never
#: an all-caps label (RE, TODO) or a field's lone capital
WORD = r"[A-ZÀ-Ö][a-zà-öø-ÿ'’.]*(?:[A-ZÀ-Ö][a-zà-öø-ÿ'’]+)*"
NAME = rf"(?P<who>{WORD}(?: {WORD}){{0,2}})"
#: a chat line's timestamp: bracketed, or a bare date or time, which always
#: joins its digits with / : . or - (a lone number, a house's 12, is none)
STAMP = r"(?:\[[^\]]+\]|\(?\d{1,4}[/:.-]\d[\d/.:,\s-]*(?:[ap]\.?m\.?)?)[\s,–-]*"
VERBS = "said|says|wrote|writes|asked|asks|replied|replies|texted|texts"
SHAPES = (
    re.compile(rf"^\s*{STAMP}{NAME}\s*:\s*(?P<what>\S.*)"),
    re.compile(rf"^\s*{NAME}\s+(?:{VERBS})[,:]?\s+(?P<what>\S.*)"),
    re.compile(rf"^\s*{NAME}\s*:\s*(?P<what>[\"'“‘].*)"),
)


def spoken(line: str) -> tuple[str, str] | None:
    """(who, what they said) when the line quotes someone by shape, else
    None. The shapes are tried in turn, a chat's timestamp first, so a
    stamped line never needs quotation marks and a bare one always does."""
    for shape in SHAPES:
        m = shape.match(line)
        if m:
            return m.group("who"), " ".join(m.group("what").split())
    return None


def file_lines(pile: list[dict]) -> dict[str, list[tuple[int, str]]]:
    """Each file's lines with their numbers, put back together from its
    passages (the kernel cuts a long run of lines into passages of 500)."""
    out: dict[str, list[tuple[int, str]]] = {}
    for c in pile:
        rows = out.setdefault(c["path"], [])
        rows += [(c["line"] + i, ln) for i, ln in enumerate(c["text"].splitlines())]
    return out


def quotes(pile: list[dict]) -> list[dict]:
    """A row per quote, dated by its line, the nearest date above it in its
    file, or its file's name, each saying so; dated rows oldest first,
    undated after, by file and line."""
    out = []
    for path, rows in file_lines(pile).items():
        above, src, filed = "", 0, kernel.newest(path)
        for n, line in rows:
            said = kernel.newest(line)
            got = spoken(line)
            if got:
                if said:
                    when, note = said, ""
                elif above:
                    when, note = above, f"date from line {src}"
                elif filed:
                    when, note = filed, "date from file name"
                else:
                    when, note = "", ""
                out.append({"when": when, "note": note, "who": got[0],
                            "what": got[1], "path": path, "line": n})  # fmt: skip
            if said:
                above, src = said, n
    return sorted(out, key=lambda r: (r["when"] == "", r["when"], r["path"], r["line"]))


def by(who: str, rows: list[dict]) -> list[dict]:
    """The rows whose speaker's words hold each of WHO's: "mags" finds Mags
    Doyle, and "mags doyle" doesn't find Mags Riley."""
    want = set(kernel.words(who))
    return [r for r in rows if want <= set(kernel.words(r["who"]))]


def day(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}" if d else "undated"


def show(rows: list[dict]) -> list[str]:
    ww = max(len(r["who"]) for r in rows)
    wp = max(len(f"{r['path']}:{r['line']}") for r in rows)
    out = []
    for r in rows:
        where = f"{r['path']}:{r['line']}"
        tail = f"  ({r['note']})" if r["note"] else ""
        out.append(
            f"{day(r['when']):<10}  {r['who']:<{ww}}  {r['what'][:90]:<90}"
            f"  {where:<{wp}}{tail}"
        )
    undated = sum(r["when"] == "" for r in rows)
    speakers = len({r["who"] for r in rows})
    out.append(f"{len(rows)} quotes by {speakers}"
               f" speaker{'s' if speakers != 1 else ''}, {undated} undated")  # fmt: skip
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
    rows = quotes(kernel.chunks(Path(kernel.config(box)["pile"])))
    if args:
        rows = by(args[0], rows)
        if not rows:
            print(f'No one your files quote answers to "{args[0]}".')
            return kernel.ESCALATE
    if not rows:
        print("No line of your folder quotes anyone by shape.")
        return kernel.ESCALATE
    for line in show(rows):
        print(line)
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
