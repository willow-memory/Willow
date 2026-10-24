"""gaps.py: where a log you keep stops, said as gaps, not left out.

    python adapters/stdlib/gaps/gaps.py --box DIR [--now TS]

A log is a folder of files named by a date (daily notes: 2026-03-04.md), or
one file whose lines start with a date (a diary's "## 2026-03-04", a
reading log's "2026-03-04 Middlemarch, ch. 3"). Its rhythm is the typical
spacing between its dates, one after another: the middle one, sorted. A gap
is a spacing more than three times that.

    notes/  files named by a date  10 entries, 2026-03-01 to 2026-03-16, typical spacing 1 day
      GAP       2026-03-04 to 2026-03-11  6 days with no entry
      UNDATED   notes/index.md  no date in its name or at the start of a line, not counted

A gap is days with no entry written, never days when nothing happened. A
log needs 4 dates for a rhythm; one with fewer is said, not judged. Dates
are read as the kernel reads them (its `newest`): 11/03/2026 is never
guessed. With --now, the days since a log's last entry count too.

It only reads. Exit codes, the kernel's: 0 found some gaps; 42 none, or no
log has enough dates for a rhythm (the last line says which); 2 refused.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

FEWEST = 4  # dates a log needs before it has a rhythm
TIMES = 3  # a gap is a spacing more than this many times the typical one
LEAD = " \t#*->"  # what may come before a line's date: a heading, a bullet


def day(d: str) -> date | None:
    """A YYYYMMDD the kernel read, as a day; None when it isn't one (the
    kernel reads 2026-02-31 as a date's shape, not a day)."""
    try:
        return date(int(d[:4]), int(d[4:6]), int(d[6:]))
    except ValueError:
        return None


def starts_with_date(line: str) -> date | None:
    """The date a line starts with, after any heading marks or bullet."""
    return day(kernel.newest((line.lstrip(LEAD).split() or [""])[0]))


def plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def logs(pile: list[dict]) -> list[dict]:
    """Every log in the pile: folders of files named by a date, and files
    whose lines start with one. A file named by a date belongs to its folder's
    log and is never also a log of its own lines."""
    named: dict[str, set[date]] = {}
    lined: dict[str, set[date]] = {}
    plain: dict[str, set[str]] = {}
    for c in pile:
        path = PurePosixPath(c["path"].replace("\\", "/"))
        folder = f"{path.parent}/" if str(path.parent) != "." else "./"
        if d := day(kernel.newest(path.name)):
            named.setdefault(folder, set()).add(d)
            continue
        found = {d for ln in c["text"].splitlines() if (d := starts_with_date(ln))}
        lined.setdefault(str(path), set()).update(found)
        plain.setdefault(folder, set()).add(str(path))
    out = []
    for folder, days in named.items():
        undated = sorted(p for p in plain.get(folder, ()) if not lined.get(p))
        out.append({"name": folder, "how": "files named by a date", "days": days,
                    "undated": undated})  # fmt: skip
    for path, days in lined.items():
        if days:
            out.append({"name": path, "how": "lines that start with a date",
                        "days": days, "undated": []})  # fmt: skip
    return sorted(out, key=lambda x: x["name"])


def gaps(days: set[date], now: date | None) -> tuple[int, list[tuple]]:
    """(typical spacing, [(from, to, days with no entry, open)]). Typical is
    the middle spacing, sorted (the smaller middle one of an even count)."""
    seq = sorted(days)
    steps = [(b - a).days for a, b in zip(seq, seq[1:])]
    typical = sorted(steps)[(len(steps) - 1) // 2]
    found = [(a, b, (b - a).days - 1, False) for a, b in zip(seq, seq[1:])
             if (b - a).days > TIMES * typical]  # fmt: skip
    if now and (now - seq[-1]).days > TIMES * typical:
        found.append((seq[-1], now, (now - seq[-1]).days - 1, True))
    return typical, found


def show(log: dict, now: date | None) -> tuple[list[str], int | None]:
    """A log's lines, and how many gaps it has (None: too few dates)."""
    seq = sorted(log["days"])
    entries = "1 entry" if len(seq) == 1 else f"{len(seq)} entries"
    head = f"{log['name']}  {log['how']}  {entries}"
    rows, count = [], None
    if len(seq) < FEWEST:
        rows.append(f"{head}: too few for a rhythm (it needs {FEWEST})")
    else:
        typical, found = gaps(log["days"], now)
        count = len(found)
        rows.append(f"{head}, {seq[0]} to {seq[-1]}, typical spacing "
                    f"{plural(typical, 'day')}")  # fmt: skip
        for a, b, empty, open_ in found:
            if open_:
                rows.append(f"  SINCE     {a} to {b} (--now)  "
                            f"{plural(empty, 'day')} with no entry so far")  # fmt: skip
            else:
                rows.append(f"  GAP       {a} to {b}  "
                            f"{plural(empty, 'day')} with no entry")  # fmt: skip
        if not found:
            rows.append("  no gap")
    for p in log["undated"]:
        rows.append(
            f"  UNDATED   {p}  no date in its name or at the start of a line, "
            "not counted"
        )
    return rows, count


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    now = None
    if "--now" in opts:
        now = day(kernel.newest(opts["--now"]))
    if not opts.get("--box") or args or ("--now" in opts and now is None):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    found = logs(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not found:
        print("Nothing dated in your folder: no file named by a date, and no "
              "line that starts with one.")  # fmt: skip
        return kernel.ESCALATE
    counts = []
    for log in found:
        rows, count = show(log, now)
        print("\n".join(rows))
        counts.append(count)
    kept = [c for c in counts if c is not None]
    total, short = sum(kept), counts.count(None)
    tail = f"; {plural(short, 'log')} too short for a rhythm" if short else ""
    if not kept:
        print(f"No log has enough dates for a rhythm (it needs {FEWEST}).")
    elif total:
        hit = sum(1 for c in kept if c)
        print(f"{plural(total, 'gap')} in {hit} of {plural(len(kept), 'log')} "
              f"with a rhythm{tail}.")  # fmt: skip
    else:
        print(f"No gaps in {plural(len(kept), 'log')} with a rhythm{tail}.")
    print("A gap is days with no entry written, not days when nothing happened.")
    return kernel.ALIVE if total else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
