"""duplicates.py: passages saying the same thing in two files, the newer said.

    python adapters/stdlib/duplicates/duplicates.py --box DIR

Every passage of your folder that says the same thing as a passage in
another file, grouped, each copy with its date and place, the newest first
and named:

    2 copies, newer garden/2026-05-02.md:3
      2026-05-02  garden/2026-05-02.md:3   Tomatoes want sun and deep watering.
      2024-04-01  garden/2024-04-01.md:3   Tomatoes want sun and deep watering!
    2 copies, which is newer the files don't say
      undated     recipes/bread.md:1   Knead, prove twice, bake at 230.
      undated     old/notes.md:40      Knead, prove twice, bake at 230.

Two passages say the same thing when their words match, in order, read the
kernel's way (its `words`): case, punctuation and spacing aside, nothing
else forgiven. A word changed is another passage, not a copy. A passage
under 8 words is never reported: a short line ("see above", a heading)
repeats without being a copy of anything.

A copy's date is the latest its text says, read as the kernel reads one
(its `newest`; 11/03/2026, either way round, is never guessed), else the
date its file is named for. The newest copy is named only when its date
beats every other; copies tied to the day, or a newest that is undated,
leave it unsaid: your files don't say which is newer.

Copies in one file count only when the passage is also in another: the same
line twice in one log is the log's business, not a duplicate.

It only reads. Exit codes, the kernel's: 0 duplicates found; 42 none; 2
refused.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

FLOOR = 8  # words a passage needs before a match means a copy


def day(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}" if d else "undated"


def copies_of(pile: list[dict]) -> list[list[dict]]:
    """Groups of passages whose words match in order, each group spanning at
    least two files, its copies newest first (undated last, then by file and
    line). Groups come in the order their first copy has in the pile."""
    by: dict[str, list[dict]] = {}
    for c in pile:
        ws = kernel.words(c["text"])
        if len(ws) >= FLOOR:
            by.setdefault(" ".join(ws), []).append(c)
    out = []
    for cs in by.values():
        if len({c["path"] for c in cs}) < 2:
            continue
        rows = [
            {"when": kernel.newest(c["text"]) or kernel.newest(c["path"]),
             "path": c["path"], "line": c["line"],
             "text": " ".join(c["text"].split())}
            for c in cs
        ]  # fmt: skip
        rows.sort(key=lambda r: (r["path"], r["line"]))
        # newest first, and "" sorts below every date: undated copies last
        rows.sort(key=lambda r: r["when"], reverse=True)
        out.append(rows)
    return out


def newer(rows: list[dict]) -> str | None:
    """The one copy dated after every other, or None: tied to the day, or a
    first copy with no date, says nothing about which is newer."""
    if rows[0]["when"] and (len(rows) < 2 or rows[0]["when"] > rows[1]["when"]):
        return f"{rows[0]['path']}:{rows[0]['line']}"
    return None


def show(found: list[list[dict]]) -> list[str]:
    out = []
    for rows in found:
        first = newer(rows)
        head = f"newer {first}" if first else "which is newer the files don't say"
        out.append(f"{len(rows)} copies, {head}")
        width = max(len(f"{r['path']}:{r['line']}") for r in rows)
        for r in rows:
            where = f"{r['path']}:{r['line']}"
            out.append(f"  {day(r['when']):<10}  {where:<{width}}  {r['text'][:100]}")
    things = len(found)
    copies = sum(len(rows) for rows in found)
    out.append(f"{things} passage{'s' if things > 1 else ''} said in two or more"
               f" files, {copies} copies in all")  # fmt: skip
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
    found = copies_of(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not found:
        print("No passage of 8 words or more is in two files.")
        return kernel.ESCALATE
    for line in show(found):
        print(line)
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
