"""hours.py: hours worked or volunteered, per client or group, from your notes.

    python adapters/stdlib/hours/hours.py --box DIR [--since DATE] [--until DATE]

The lines of your files that say time spent working, added up for whoever
they name:

      12.5 h  acme  (5 entries, 2026-03-01 to 2026-03-20)
         6 h  the food bank  (2 entries, 2026-03-07 to 2026-03-14)
       1.5 h  (no one named)  (1 entry, 2026-03-12 to 2026-03-12)
    3 groups, 20 h in 8 entries

**What counts.** A line that says a work word (worked, volunteered, shift,
billed, billable, logged, consulting, meeting, session) and a length of time:
2.5 hours, 3h, 1h30, 45 min, 2 hrs 15 min. The times on one line add; a line
counts once. A time with no work word ("slept 8 hours") is not counted, and
a line no day reaches (its own date, else the nearest date written above it
in its file, else the date its file is named for) is not counted either.

**Whom it is for** is the words after "for", "at", "with" or "@", up to a
comma, a digit or a word like "on" or "from": "worked 3 hours for Acme on the
site" is acme. A line that names no one is added up under "(no one named)",
so nothing is left out, and the list says so.

--since and --until (YYYY-MM-DD) keep to those days, both ends included.
Biggest total first. It only reads. Exit codes, the kernel's: 0 hours found;
42 none; 2 refused.
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

WORK = re.compile(
    r"\b(?:work(?:ed|ing)?|volunteer(?:ed|ing)?|shift|bill(?:ed|able)|logged|consult(?:ed|ing)|meeting|session)\b",
    re.I,
)
HM = re.compile(r"(\d+)\s*h\s*(\d{2})(?!\d)", re.I)
HOURS = re.compile(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)(?![a-z])", re.I)
MINS = re.compile(r"(\d+)\s*(?:minutes?|mins?)\b", re.I)
WHOM = re.compile(
    r"(?:\bfor|\bat|\bwith|@)\s*([^,.;:()\d]+?)(?=\s+(?:on|from|to|until|and|about|re|today|yesterday)\b|[,.;:()\d]|$)",
    re.I,
)
NONE = "(no one named)"


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


def spent(line: str) -> float:
    """The hours a line says: its times added, 0 when it says none."""
    total = 0.0
    for h, m in HM.findall(line):
        total += int(h) + int(m) / 60
    rest = HM.sub(" ", line)
    total += sum(float(x) for x in HOURS.findall(rest))
    total += sum(int(x) for x in MINS.findall(rest)) / 60
    return total


def whom(line: str) -> str:
    m = WHOM.search(line)
    if not m:
        return NONE
    name = " ".join(m.group(1).lower().split())
    return name or NONE


def tally(pile: list[dict], since: str = "", until: str = "") -> dict[str, list]:
    """{who: [hours, [days]]} for the lines that say work and a time."""
    out: dict[str, list] = {}
    for day, _path, _n, line in entries(pile):
        if (since and day < since) or (until and day > until) or not WORK.search(line):
            continue
        h = spent(line)
        if h:
            got = out.setdefault(whom(line), [0.0, []])
            got[0] += h
            got[1].append(day)
    return out


def dash(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def amount(h: float) -> str:
    return f"{round(h, 2):g}"


def show(found: dict[str, list]) -> list[str]:
    rows = sorted(found.items(), key=lambda kv: (-kv[1][0], kv[0]))
    out = []
    for who, (h, days) in rows:
        n = len(days)
        out.append(
            f"{amount(h):>8} h  {who}  ({n} {'entry' if n == 1 else 'entries'},"
            f" {dash(min(days))} to {dash(max(days))})"
        )
    n = sum(len(d) for _, d in found.values())
    out.append(
        f"{len(rows)} group{'s' if len(rows) != 1 else ''},"
        f" {amount(sum(h for h, _ in found.values()))} h in {n} {'entry' if n == 1 else 'entries'}"
    )
    return out


def day_arg(text: str) -> str:
    """YYYY-MM-DD as the kernel's YYYYMMDD, or "" when it is not a date."""
    return text.replace("-", "") if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text) else ""


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--since", "--until"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    since, until = opts.get("--since", ""), opts.get("--until", "")
    if (
        not opts.get("--box")
        or args
        or (since and not day_arg(since))
        or (until and not day_arg(until))
    ):
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    found = tally(
        kernel.chunks(Path(kernel.config(box)["pile"])), day_arg(since), day_arg(until)
    )
    if not found:
        print("No line of your folder says work and a length of time.")
        return kernel.ESCALATE
    print("\n".join(show(found)))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
