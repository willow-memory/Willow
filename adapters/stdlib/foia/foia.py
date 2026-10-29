"""foia.py: freedom-of-information requests: what you asked, when, and when
the answer is due by law. Python 3.9+.

    python adapters/stdlib/foia/foia.py --box DIR [--law us|uk|au|ca|nz|ie] [--now TS]

The lines of your notes about information requests, gathered by who you asked:

    City Council  sent 2026-03-01  due 2026-03-29  open, overdue 31 days
    Home Office   sent 2026-02-02  due 2026-03-02  answered 2026-02-27 (3 days early)
    Police        sent 2026-03-05  due not known (name --law)  open
    3 requests: 1 answered, 2 open

**A request** is a line, on a day, that says freedom of information, FOI, FOIA,
public records, OIA, ATIP or right to information, and that you sent, filed,
submitted, requested, asked, made, emailed or posted it. **An answer** is a later
line about the same body that says received, replied, response, answered,
released, disclosed, refused, denied, rejected or withheld; it closes the latest
earlier request to that body that is still open. A line that only says the
request was acknowledged is neither. The body is the capitalised words after to,
with, from, at or by ("FOI request to City Council"), else the name the line
starts with.

**When it is due** is the date the line says after "due", else the day sent plus
the time the law of --law gives: us 20 working days, uk 20 working days, nz 20
working days, ie 20 working days, au 30 days, ca 30 days. Days are counted from
the day after it was sent; working days are Monday to Friday, and public holidays
are not known to this, so a real deadline can fall a few days later than the one
shown here. Without --law, and with no "due" on the line, no deadline is
guessed. Distances are from --now (an ISO timestamp, the kernel's kind; today if
not given).

These are the general times; a body may extend them, and an appeal has its own.
Nothing is sent or chased for you. It only reads. Exit codes, the kernel's: 0
requests found; 42 none; 2 refused.
"""

from __future__ import annotations

import re
import sys
from datetime import date, timedelta
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "habits"))
import habits  # noqa: E402
import kernel  # noqa: E402

LAWS = {"us": (20, True), "uk": (20, True), "nz": (20, True), "ie": (20, True), "au": (30, False), "ca": (30, False)}  # fmt: skip
ABOUT = re.compile(
    r"\b(?:freedom of information|foia?|public records?|oia|atip|right to information)\b",
    re.I,
)
SENT = re.compile(
    r"\b(?:sent|filed|submitted|requested|asked|made|emailed|posted)\b", re.I
)
ANSWER = re.compile(
    r"\b(?:received|replied|response|answered|released|disclosed|refused|denied|rejected|withheld)\b",
    re.I,
)
WORD = r"[A-Z][\w&.'’-]*"
AFTER = re.compile(rf"\b(?:to|with|from|at|by)\s+({WORD}(?: {WORD}){{0,3}})")
LEAD = re.compile(rf"^\s*[-*•]?\s*(?:[\d./-]+\s+)?({WORD}(?: {WORD}){{0,2}})\s*[:\-–]")
NOT_BODIES = {"foi", "foia", "oia", "atip", "note", "notes", "request", "sent", "subject", "re"}  # fmt: skip
DUE = re.compile(r"\bdue\b(.*)", re.I)
NONE = "(unnamed)"


def entries(pile: list[dict]) -> list[tuple[str, str, int, str]]:
    """(day, path, line number, text) for each line a day reaches: the latest
    date it says before any "due", else the nearest above it in its file, else
    its file's name."""
    out = []
    for path, rows in habits.file_lines(pile).items():
        above, filed = "", kernel.newest(path)
        for n, line in rows:
            said = kernel.newest(DUE.sub("", line))
            if said:
                above = said
            day = said or above or filed
            if day and line.strip():
                out.append((day, path, n, line.strip()))
    return out


def to_date(day: str) -> date:
    return date(int(day[:4]), int(day[4:6]), int(day[6:]))


def body_of(line: str) -> str:
    for rx in (AFTER, LEAD):
        m = rx.search(line)
        if m and m.group(1).lower() not in NOT_BODIES:
            return m.group(1)
    return NONE


def deadline(sent: date, law: str) -> date:
    """The day an answer is due under law, counted from the day after sent."""
    n, working = LAWS[law]
    if not working:
        return sent + timedelta(days=n)
    d = sent
    while n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def requests(pile: list[dict], law: str = "") -> tuple[list[dict], int]:
    """([{body, sent, due, answered}], responses that matched no request)."""
    found: list[dict] = []
    stray = 0
    lines = [
        (d, bool(ANSWER.search(t)), t)
        for d, _p, _n, t in entries(pile)
        if ABOUT.search(t)
    ]
    for day, _answer, line in sorted(lines):  # by day, a request before its answer
        body = body_of(line)
        if SENT.search(line) and not ANSWER.search(line):
            said = DUE.search(line)
            due = kernel.newest(said.group(1)) if said else ""
            sent = to_date(day)
            found.append({
                "body": body, "sent": sent, "answered": None,
                "due": to_date(due) if due else (deadline(sent, law) if law else None),
            })  # fmt: skip
        elif ANSWER.search(line):
            open_ = [
                r
                for r in found
                if r["answered"] is None
                and r["body"] == body
                and r["sent"] <= to_date(day)
            ]
            if open_:
                open_[-1]["answered"] = to_date(day)
            else:
                stray += 1
    return found, stray


def show(found: list[dict], stray: int, today: date) -> list[str]:
    def key(r):
        return (
            r["answered"] is not None,
            r["due"] is None,
            r["due"] or date.max,
            r["sent"],
            r["body"],
        )

    rows = sorted(found, key=key)
    w = max(len(r["body"]) for r in rows)
    out = []
    for r in rows:
        due = f"due {r['due']}" if r["due"] else "due not known (name --law)"
        if r["answered"]:
            late = (r["answered"] - r["due"]).days if r["due"] else None
            how = (
                ""
                if late is None
                else f" ({-late} day{'s' if late != -1 else ''} early)"
                if late < 0
                else " (on the day)"
                if late == 0
                else f" ({late} day{'s' if late != 1 else ''} late)"
            )
            end = f"answered {r['answered']}{how}"
        else:
            d = (today - r["due"]).days if r["due"] else None
            end = (
                "open"
                if d is None
                else f"open, overdue {d} day{'s' if d != 1 else ''}"
                if d > 0
                else "open, due today"
                if d == 0
                else f"open, {-d} day{'s' if d != -1 else ''} left"
            )
        out.append(f"{r['body']:<{w}}  sent {r['sent']}  {due}  {end}")
    n, a = len(rows), sum(1 for r in rows if r["answered"])
    tail = (
        f", {stray} response{'s' if stray != 1 else ''} named no request"
        if stray
        else ""
    )
    out.append(f"{n} request{'s' if n != 1 else ''}: {a} answered, {n - a} open{tail}")
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--law", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    law, ts = opts.get("--law", ""), opts.get("--now") or kernel.now()
    if (
        not opts.get("--box")
        or args
        or (law and law not in LAWS)
        or not re.match(r"\d{4}-\d{2}-\d{2}", ts)
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    try:
        today = date(int(ts[:4]), int(ts[5:7]), int(ts[8:10]))
    except ValueError:
        print(f"refused: --now {ts!r} isn't a date, YYYY-MM-DD", file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    found, stray = requests(kernel.chunks(Path(kernel.config(box)["pile"])), law)
    if not found:
        print("No line of your folder says an information request was sent.")
        return kernel.ESCALATE
    print("\n".join(show(found, stray, today)))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
