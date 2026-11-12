"""duplicates.py: passages saying the same thing in two files, the newer said.

    python adapters/stdlib/duplicates/duplicates.py --box DIR [--runs]

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

A passage is where the kernel cut the file: at a blank line, or after 500
characters. The same text with its paragraphs broken in other places, or cut
at the 500th character on a different word, is cut differently in two files,
and its passages never match. With `--runs` the passages are not what is
compared: each file is its words in order, and a run of 8 words or more that
two files share is a copy, wherever each file broke its paragraphs:

    2 copies of a run of 214 words
      cox-1905-part17.txt:45         the following winter father was at omaha ...
      dar-reminiscences.txt:135      the following winter father was at omaha ...

A word in order is still the only thing a copy is: a word changed ends the
run, and so does a word one file breaks across two lines. A run also ends
where the files that share it change, so a stretch three files hold and the
next stretch only two hold are two runs, each listing the files that hold it.
Each copy is shown at the line its first word is on, with no date: which is
newer is the other mode's question.

It only reads. Exit codes, the kernel's: 0 duplicates found; 42 none; 2
refused.
"""

from __future__ import annotations

import hashlib
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


def streams(pile: list[dict]) -> dict[str, list[tuple[str, int]]]:
    """Each file's words in order, each with the line it is on, in the order
    the files first come in the pile."""
    out: dict[str, list[tuple[str, int]]] = {}
    for c in pile:
        ws = out.setdefault(c["path"], [])
        for i, line in enumerate(c["text"].splitlines()):
            ws += [(w, c["line"] + i) for w in kernel.words(line)]
    return out


def _window(ws: list[tuple[str, int]], i: int) -> bytes:
    """A fingerprint of the FLOOR words starting at i."""
    return hashlib.md5(" ".join(w for w, _ in ws[i : i + FLOOR]).encode()).digest()


def runs_of(pile: list[dict]) -> list[list[dict]]:
    """Groups of runs of FLOOR words or more that two files share, the words
    the same in order, however each file broke its lines. A run lasts as long
    as the same files share it: where a third file stops sharing, or starts,
    a new run begins, so each group is the copies of one stretch of words in
    exactly the files that hold it. A group lists its copies in file order
    then line order."""
    by = streams(pile)
    seen: dict[bytes, set[str]] = {}  # a window of FLOOR words -> the files with it
    for path, ws in by.items():
        for i in range(len(ws) - FLOOR + 1):
            seen.setdefault(_window(ws, i), set()).add(path)
    groups: dict[tuple[str, ...], list[dict]] = {}
    for path, ws in by.items():
        last = len(ws) - FLOOR + 1  # one past the last window
        i = 0
        while i < last:
            held_by = seen[_window(ws, i)]
            if len(held_by) < 2:
                i += 1
                continue
            j = i  # the window at i is shared: grow the run while the same files share
            while j + 1 < last and seen[_window(ws, j + 1)] == held_by:
                j += 1
            words = tuple(w for w, _ in ws[i : j + FLOOR])
            groups.setdefault(words, []).append(
                {"path": path, "line": ws[i][1], "words": words}
            )
            i = j + 1
    found = []
    for rows in groups.values():
        if len({r["path"] for r in rows}) >= 2:
            found.append(sorted(rows, key=lambda r: (r["path"], r["line"])))
    return found


def show_runs(found: list[list[dict]]) -> list[str]:
    out = []
    for rows in found:
        n = len(rows[0]["words"])
        out.append(f"{len(rows)} copies of a run of {n} words")
        width = max(len(f"{r['path']}:{r['line']}") for r in rows)
        for r in rows:
            where = f"{r['path']}:{r['line']}"
            out.append(f"  {where:<{width}}  {' '.join(r['words'])[:100]}")
    runs = len(found)
    copies = sum(len(rows) for rows in found)
    out.append(f"{runs} run{'s' if runs > 1 else ''} said in two or more files,"
               f" {copies} copies in all")  # fmt: skip
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        elif a == "--runs":
            opts[a] = "yes"
        else:
            args.append(a)
    if not opts.get("--box") or args:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    pile = kernel.chunks(Path(kernel.config(box)["pile"]))
    if opts.get("--runs"):
        found = runs_of(pile)
        if not found:
            print("No run of 8 words or more is in two files.")
            return kernel.ESCALATE
        for line in show_runs(found):
            print(line)
        return kernel.ALIVE
    found = copies_of(pile)
    if not found:
        print("No passage of 8 words or more is in two files.")
        return kernel.ESCALATE
    for line in show(found):
        print(line)
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
