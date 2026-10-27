"""first_mention.py: when your files first mention something, and the line.

    python adapters/stdlib/first-mention/first_mention.py --box DIR "your words"

The thing is named by words, as a question is: "mould", "knee physio",
"solar quote". A line mentions it when the line itself holds every one of
your content words, each read the kernel's way (your words list, and a
word's plain form, so "owes" is "owe"). The line has to say it: a folder
named dad/ holds the word for asking, but writes no mention.

    first mention of "mould": 2026-03-01
      tenancy/log.md:3  2026-03-01 Reported the mould in the back bedroom.
    48 mentions in 5 files, 2026-03-01 to 2026-09-02; 3 undated, which could be earlier

A line's date is the latest it says, read as the kernel reads one (its
`newest`; 11/03/2026, either way round, is never guessed); a line that says
none takes the nearest date written above it in its file, else the date its
file is named for, and the answer says which. The first mention is the
earliest dated one, ties going to the first file and line in sorted order.
Undated mentions can't be placed, so they are counted beside the answer:
your files don't say when those were, and one of them could be earlier.
When no mention is dated at all, the first by file and line is shown, and
says that.

It only reads. Exit codes, the kernel's: 0 a first mention found; 42 your
files never mention it, or the words are only common ones; 2 refused.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


def day(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}" if d else "undated"


def file_lines(pile: list[dict]) -> dict[str, list[tuple[int, str]]]:
    """Each file's lines with their numbers, put back together from its
    passages (the kernel cuts a long run of lines into passages of 500)."""
    out: dict[str, list[tuple[int, str]]] = {}
    for c in pile:
        rows = out.setdefault(c["path"], [])
        rows += [(c["line"] + i, ln) for i, ln in enumerate(c["text"].splitlines())]
    return out


def mentions(pile: list[dict], want: set[str], alias: dict) -> list[dict]:
    """A row per line that holds every word of `want` in the line's own words
    (the kernel's `held_by`: the words list, and a word's plain form), dated
    by the line, the nearest date above it in its file, or its file's name,
    each saying so. Dated rows oldest first, undated after, by file and line."""
    out = []
    for path, rows in file_lines(pile).items():
        above, src, filed = "", 0, kernel.newest(path)
        for n, line in rows:
            said = kernel.newest(line)
            toks = kernel.forms(kernel.words(line))
            if all(kernel.held_by(w, toks, alias) for w in want):
                if said:
                    when, note = said, ""
                elif above:
                    when, note = above, f"date from line {src}"
                elif filed:
                    when, note = filed, "date from file name"
                else:
                    when, note = "", ""
                out.append({"when": when, "note": note, "path": path,
                            "line": n, "text": line.strip()})  # fmt: skip
            if said:
                above, src = said, n
    return sorted(out, key=lambda r: (r["when"] == "", r["when"], r["path"], r["line"]))


def tally(found: list[dict]) -> str:
    dated = [r["when"] for r in found if r["when"]]
    files = len({r["path"] for r in found})
    n = len(found)
    head = (
        f"{n} mention{'s' if n > 1 else ''} in {files} file{'s' if files > 1 else ''}"
    )
    if not dated:
        return f"{head}, none dated"
    span = (
        day(dated[0])
        if dated[0] == dated[-1]
        else f"{day(dated[0])} to {day(dated[-1])}"
    )
    undated = n - len(dated)
    tail = f"; {undated} undated, which could be earlier" if undated else ""
    return f"{head}, {span}{tail}"


def answer(asked: str, found: list[dict]) -> str:
    first = found[0]
    when = day(first["when"])
    if not first["when"]:
        when = "undated — your files don't say when"
    note = f"  ({first['note']})" if first["note"] else ""
    return "\n".join([
        f'first mention of "{asked}": {when}{note}',
        f"  {first['path']}:{first['line']}  {first['text'][:120]}",
        tally(found),
    ])  # fmt: skip


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or len(args) != 1:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    cfg = kernel.config(box)
    alias = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            print(f"refused: {why}", file=sys.stderr)
            return kernel.REFUSED
    want = set(kernel.words(args[0])) - kernel.FUNCTION
    if not want:
        print(f'"{args[0]}" is only common words, held by everything; say more.')
        return kernel.ESCALATE
    found = mentions(kernel.chunks(Path(cfg["pile"])), want, alias)
    if not found:
        print(f'Your files never mention "{args[0]}".')
        return kernel.ESCALATE
    print(answer(args[0], found))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
