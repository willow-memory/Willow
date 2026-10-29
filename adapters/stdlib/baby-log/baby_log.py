"""baby_log.py: feeds, sleeps and nappies from your notes, by day: when was the
last one?

    python adapters/stdlib/baby-log/baby_log.py --box DIR [--days N]

The lines of your notes that say a feed, a sleep or a nappy, with the last of
each and the days before:

    last feed    2026-03-02 14:10
    last sleep   2026-03-02 13:00
    last nappy   2026-03-02 14:35
    2026-03-02  feeds 6  sleeps 3  nappies 5
    2026-03-01  feeds 7  sleeps 4  nappies 6
    2 days shown

**What counts.** A line that says a feed (feed, fed, bottle, nursed, breastfed),
a sleep (sleep, slept, nap) or a nappy (nappy, diaper, poo, wee), on a day,
and is about a baby: the line or the path of its file says baby, bub, newborn,
infant, toddler, nappy or diaper (so feeding the bees, or a friend who can't
sleep, is not the baby's). The day is the
line's latest date, else the nearest date written above it in its file, else
the date its file is named for. The first time on the line ("07:30", "7.30pm",
"13:00-14:30") is when; a line with no time still counts for its day. A line is
the first of the three it names, so "fed, then nappy" is a feed. Nothing is
summed from amounts or lengths.

The newest N days with entries are shown (7 unless --days). A last that has no
time written says so. This is your own count, for you and whoever shares the
night; it is not advice. It only reads. Exit codes, the kernel's: 0 entries
found; 42 none; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "habits"))
import habits  # noqa: E402
import kernel  # noqa: E402

KINDS = {
    "feed": re.compile(
        r"\b(?:feed(?:s|ing)?|fed|bottles?|nursed|breastfed|breastfeed(?:ing)?)\b", re.I
    ),
    "sleep": re.compile(r"\b(?:sleep(?:s|ing)?|slept|naps?|napped)\b", re.I),
    "nappy": re.compile(r"\b(?:nappy|nappies|diapers?|poo|poos|wee|wees)\b", re.I),
}
CONTEXT = re.compile(
    r"\b(?:baby|babies|bubs?|newborn|infant|toddler|nappy|nappies|diapers?)\b", re.I
)
TIME = re.compile(r"(?<![\d:.])(\d{1,2})[:.](\d{2})\s*(am|pm)?(?![\d:])", re.I)


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


def clock(line: str) -> str:
    """The first time on the line as HH:MM, or "" when it says none."""
    for m in TIME.finditer(line):
        h, mi, ap = int(m.group(1)), int(m.group(2)), (m.group(3) or "").lower()
        if ap == "pm" and h < 12:
            h += 12
        if ap == "am" and h == 12:
            h = 0
        if h < 24 and mi < 60 and not (ap and not 1 <= int(m.group(1)) <= 12):
            return f"{h:02d}:{mi:02d}"
    return ""


def kind_of(line: str) -> str:
    """The first of feed, sleep, nappy the line names, by where it names it."""
    hits = [(m.start(), k) for k, rx in KINDS.items() if (m := rx.search(line))]
    return min(hits)[1] if hits else ""


def log(pile: list[dict]) -> dict[str, list[tuple[str, str]]]:
    """{day: [(kind, HH:MM or "")]}."""
    out: dict[str, list] = {}
    for day, path, _n, line in entries(pile):
        kind = kind_of(line)
        if kind and CONTEXT.search(path + " " + line):
            out.setdefault(day, []).append((kind, clock(line)))
    return out


def dash(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def show(got: dict, days: int) -> list[str]:
    out = []
    for kind in KINDS:
        stamps = [(d, t) for d, rows in got.items() for k, t in rows if k == kind]
        if stamps:
            d, t = max(stamps)
            out.append(
                f"{'last ' + kind:<12} {dash(d)} {t or '(no time written)'}".rstrip()
            )
    shown = sorted(got, reverse=True)[:days]
    for d in shown:
        c = {k: sum(1 for kk, _ in got[d] if kk == k) for k in KINDS}
        out.append(
            f"{dash(d)}  feeds {c['feed']}  sleeps {c['sleep']}  nappies {c['nappy']}"
        )
    out.append(f"{len(shown)} day{'s' if len(shown) != 1 else ''} shown")
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--days"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    days = opts.get("--days", "7")
    if not opts.get("--box") or args or not days.isdigit() or int(days) < 1:
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    got = log(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not got:
        print("No line of your folder says a feed, a sleep or a nappy.")
        return kernel.ESCALATE
    print("\n".join(show(got, int(days))))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
