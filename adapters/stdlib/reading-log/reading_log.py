"""reading_log.py: a child's reading log: books, pages and minutes, week by
week. Python 3.9+.

    python adapters/stdlib/reading-log/reading_log.py --box DIR

The lines of your notes that say something was read, and for how long or how
far, gathered by week and by book:

    2026-W10  3 days  95 pages  70 min  Charlotte's Web; The BFG
    2026-W11  5 days  140 pages  95 min  The BFG
    Charlotte's Web  60 pages, 45 min  (2026-03-02 to 2026-03-04)
    The BFG  175 pages, 120 min  (2026-03-05 to 2026-03-13)
    2 books, 8 days read, 235 pages, 165 min

**What counts.** A line, on a day, that says read, reads or reading and a
length: pages ("30 pages", "12pp") or time ("20 minutes", "1h", "1h30", "2
hours"). A line with both counts both; the times on a line add. The book is the
title in quotes, "like this" or _like this_ or *like this*, else the capitalised
words after read / reading ("read Charlotte's Web, 20 pages"); a line that
names none is added to its week without a book. A line's day is the latest date
it says, else the nearest date written above it in its file, else the date its
file is named for; a line no day reaches is not counted.

**A week** is an ISO week, oldest first; "days" is the number of different days
read that week. Books are in the order they were first read. Nothing is graded,
and a missing week is simply not listed: the log shows what was written down.
It only reads. Exit codes, the kernel's: 0 reading found; 42 none; 2 refused.
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "habits"))
import habits  # noqa: E402
import kernel  # noqa: E402

READ = re.compile(r"\b(?:read|reads|reading)\b", re.I)
PAGES = re.compile(r"(?<![\w.])(\d+)\s*(?:pages?|pp?)\b\.?", re.I)
HM = re.compile(r"(?<![\w.])(\d+)\s*h\s*(\d{2})(?!\d)", re.I)
HOURS = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)(?![a-z])", re.I)
MINS = re.compile(r"(?<![\w.])(\d+)\s*(?:minutes?|mins?)\b", re.I)
QUOTED = re.compile(r"[\"“_*]([^\"”_*]{2,60})[\"”_*]")
WORD = r"[A-Z][\w'’-]*"
AFTER = re.compile(
    rf"\b(?i:read|reads|reading|finished|started)\s+({WORD}(?:(?: (?:of|the|and|a|in|to|on))* {WORD})*)"
)


def entries(pile: list[dict]) -> list[tuple[str, str, int, str]]:
    """(day, path, line number, text) for each line a day reaches: the latest
    date it says, else the nearest above it in its file, else its file's name."""
    out = []
    for path, rows in habits.file_lines(pile).items():
        above, filed = "", kernel.newest(path)
        for n, line in rows:
            said = kernel.newest(line)
            if said:
                above = said
            day = said or above or filed
            if day and line.strip():
                out.append((day, path, n, line.strip()))
    return out


def minutes(line: str) -> int:
    """The minutes a line says, its times added; 0 when it says none."""
    total = sum(int(h) * 60 + int(m) for h, m in HM.findall(line))
    rest = HM.sub(" ", line)
    total += round(sum(float(x) for x in HOURS.findall(rest)) * 60)
    return total + sum(int(x) for x in MINS.findall(rest))


def pages(line: str) -> int:
    return sum(int(x) for x in PAGES.findall(line))


def title_of(line: str) -> str:
    """The book a line names: a quoted title, else the capitalised words after
    read / reading / finished / started; "" when it names none."""
    q = QUOTED.search(line)
    if q:
        return " ".join(q.group(1).split())
    m = AFTER.search(line)
    return " ".join(m.group(1).split()) if m else ""


def log(pile: list[dict]) -> list[dict]:
    """[{day, title, pages, minutes}] for each dated line that reads something."""
    out = []
    for day, _path, _n, line in entries(pile):
        if not READ.search(line):
            continue
        p, m = pages(line), minutes(line)
        if p or m:
            out.append({"day": day, "title": title_of(line), "pages": p, "minutes": m})
    return out


def week(day: str) -> str:
    y, w, _ = date(int(day[:4]), int(day[4:6]), int(day[6:])).isocalendar()
    return f"{y}-W{w:02d}"


def dash(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def show(rows: list[dict]) -> list[str]:
    weeks: dict[str, list[dict]] = {}
    for r in sorted(rows, key=lambda r: r["day"]):
        weeks.setdefault(week(r["day"]), []).append(r)
    out = []
    for key, rs in weeks.items():
        titles = list(dict.fromkeys(r["title"] for r in rs if r["title"]))
        n = len({r["day"] for r in rs})
        out.append(
            f"{key}  {n} day{'s' if n != 1 else ''}  {sum(r['pages'] for r in rs)} pages"
            f"  {sum(r['minutes'] for r in rs)} min"
            + (f"  {'; '.join(titles)}" if titles else "")
        )
    books: dict[str, list[dict]] = {}
    for r in sorted(rows, key=lambda r: r["day"]):
        if r["title"]:
            books.setdefault(r["title"], []).append(r)
    for title, rs in books.items():
        out.append(
            f"{title}  {sum(r['pages'] for r in rs)} pages, {sum(r['minutes'] for r in rs)} min"
            f"  ({dash(rs[0]['day'])} to {dash(rs[-1]['day'])})"
        )
    days = len({r["day"] for r in rows})
    out.append(
        f"{len(books)} book{'s' if len(books) != 1 else ''}, {days} day{'s' if days != 1 else ''} read, "
        f"{sum(r['pages'] for r in rows)} pages, {sum(r['minutes'] for r in rows)} min"
    )
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
    rows = log(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not rows:
        print("No line of your folder says something read and for how long or how far.")
        return kernel.ESCALATE
    print("\n".join(show(rows)))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
