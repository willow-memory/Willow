"""lines_veils.py: what never happens at a table, what happens off-screen, and the X-card and the pause, on the record. Python 3.9+.

    python adapters/stdlib/lines-veils/lines_veils.py --page PAGE show
    python adapters/stdlib/lines-veils/lines_veils.py --page PAGE touches TEXT
    python adapters/stdlib/lines-veils/lines_veils.py --box DIR x [--game N] [--at I] [--part KIND] [--now TS]
    python adapters/stdlib/lines-veils/lines_veils.py --box DIR pause [--game N] [--at I] [--now TS]

A table writes its lines and veils once, in its own words, as a page:

    ## Lines
    - spiders
    - a pet getting hurt

    ## Veils
    - kissing

A line never happens in the story: a part that touches one isn't read, and
the person running the game says what happens instead. A veil can happen,
off-screen: the part isn't played out, and it is said in passing. `show`
prints the page as read; `touches` says whether a text touches a line or a
veil, and which. A line or veil touches a text when every word of it that
carries meaning is there (spiders, spider; a pet getting hurt: pet, hurt),
so a line is never missed for a plural, and a word alone in a longer line
doesn't trip it. No page, nothing is touched.

The X-card is the other half: anyone at the table sets the next part aside,
no reason asked. `x` keeps only that it happened, as a `table-x` row: never
who, never why; `--game` and `--at` say where (a game's row and a part's
place in it), `--part` what kind of part it was. `pause` stops the whole
night the same way, as a `table-pause` row, no one named.

Exit codes, the kernel's: 0 done (touches: touched); 42 touches: nothing
touched; 2 refused, with why.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

PAGE = "our-lines.md"  # the page's usual name, in a table's pile
X, PAUSE, WHO = "table-x", "table-pause", "lines-veils"
QUIET = frozenset({"a", "an", "the", "of", "to", "and", "or", "in", "on", "at", "for", "with", "by", "any", "no", "not", "being", "getting", "get", "gets", "is", "are", "be"})  # fmt: skip
USAGE = __doc__.split("\n\n")[1]


def refuse(why: str) -> int:
    print(f"lines-veils: {why}", file=sys.stderr)
    return kernel.REFUSED


def words(text: str) -> list[str]:
    """A text's words, lower case, a possessive's 's left off."""
    return [w[:-2] if w.endswith("'s") else w for w in re.findall(r"[a-z0-9']+", text.lower())]  # fmt: skip


def same(w: str, t: str) -> bool:
    """One word and another, the same but for a plural."""
    return t == w or t in (w + "s", w + "es") or w in (t + "s", t + "es")


def read_page(page: Path) -> tuple[list[str], list[str]]:
    """The page's (lines, veils), each as written; both empty with no page."""
    if not page.is_file():
        return [], []
    got: dict[str, list[str]] = {"line": [], "veil": []}
    under = None
    for raw in page.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if s.startswith("#"):
            head = set(words(s))  # "Lines", "Our lines", "## Veils"
            under = "line" if {"line", "lines"} & head else "veil" if {"veil", "veils"} & head else None  # fmt: skip
        elif under and s[:1] in ("-", "*") and s[1:].strip():
            got[under].append(s[1:].strip())
    return got["line"], got["veil"]


def read(table: Path) -> tuple[list[str], list[str]]:
    """A table folder's (lines, veils), from its pile's page."""
    return read_page(Path(table) / "pile" / PAGE)


def touches(entries: list[str], text: str) -> str | None:
    """The first entry every meaning word of which is in TEXT, or None."""
    ts = words(text)
    for e in entries:
        need = [w for w in words(e) if w not in QUIET] or words(e)
        if need and all(any(same(w, t) for t in ts) for w in need):
            return e
    return None


def mark(box: Path, kind: str, ts: str, game: int | None, at: int | None, part: str | None) -> dict:  # fmt: skip
    """A table-x or table-pause row: where, and of what kind of part; never who or why."""
    more = {k: v for k, v in (("game", game), ("at", at), ("part", part)) if v is not None}  # fmt: skip
    return kernel.append(box, ts, kind, who=WHO, **more)


def whole(v: str | None, name: str) -> int | None:
    if v is None:
        return None
    if not re.fullmatch(r"\d+", v):
        raise ValueError(f"{name} is a row or a place, a whole number: {v!r}")
    return int(v)


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--page", "--box", "--game", "--at", "--part", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    cmd = args[0] if args else ""
    if cmd == "show" and len(args) == 1 and opts.get("--page"):
        lines, veils = read_page(Path(opts["--page"]))
        if not lines and not veils:
            print(f"no lines or veils at {opts['--page']}")
        for what, es in (("line", lines), ("veil", veils)):
            for e in es:
                print(f"{what}  {e}")
        return kernel.ALIVE
    if cmd == "touches" and len(args) == 2 and opts.get("--page"):
        lines, veils = read_page(Path(opts["--page"]))
        line, veil = touches(lines, args[1]), touches(veils, args[1])
        if line is None and veil is None:
            print("it touches no line and no veil")
            return kernel.ESCALATE
        if line is not None:
            print(f"line  {line}: it doesn't happen; say what happens instead")
        if veil is not None:
            print(f"veil  {veil}: it happens off-screen; say it in passing")
        return kernel.ALIVE
    if cmd in ("x", "pause") and len(args) == 1 and opts.get("--box") and not (cmd == "pause" and "--part" in opts):  # fmt: skip
        box = Path(opts["--box"])
        if not (box / "kernel.json").is_file():
            return refuse(f"{box} isn't a box: make one with kernel.py init")
        try:
            game, at = whole(opts.get("--game"), "--game"), whole(opts.get("--at"), "--at")  # fmt: skip
        except ValueError as e:
            return refuse(str(e))
        _rows, breaks = kernel.read(box / "record.jsonl")
        if breaks:
            return refuse("the record doesn't verify: " + "; ".join(breaks))
        row = mark(box, X if cmd == "x" else PAUSE, opts.get("--now") or kernel.now(), game, at, opts.get("--part") or None)  # fmt: skip
        said = "set aside" if cmd == "x" else "paused"
        print(f"{said}, no reason asked and no one named   (row {row['n']})")
        return kernel.ALIVE
    print(USAGE, file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
