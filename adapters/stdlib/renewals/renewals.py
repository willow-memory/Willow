"""renewals.py: when each thing you hold expires, from your own documents.

    python adapters/stdlib/renewals/renewals.py --box DIR [--now TS]

Every line of your folder that says an expiry and its date: passports,
licences, insurance, registrations, memberships, soonest first, what's
already gone by marked:

    gone by  2024-01-31  ids/passport.md:3      Passport expires 2024-01-31.
             2026-03-04  mail/racv.eml:12       Your policy HC-7718203 renews on 4 March 2026.
             2026-10-31  work/insurance.txt:4   Your cover ends on 31/10/2026 unless renewed.
    3 renewals: 1 gone by, 2 to come

**What counts.** A line that says one of the expiry words — expires, expiry,
expiration, renew and its forms, valid until (till, through, thru), cover
ends, ends on — and says its own date on the same line. A date is read as
the kernel reads one (its `newest`; 03/11/2025, reading either way round, is
never guessed), or written out with a month's name and its day (4 March
2026, March 4, 2026). A renewal line that names no day ("renews March") says
too little to place, and an expiry whose date only a nearby line holds is
not stitched together: the line that tells you when is the one cited.

**Gone by is by the clock you give.** `--now` (an ISO timestamp, the
kernel's kind) marks what has passed; without it, today. Nothing is
reminded, totalled or renewed for you: the kernel's own `coming-up` add-on
is the window onto the next weeks, this is the register of the things
themselves.

It only reads. Exit codes, the kernel's: 0 renewals found; 42 none; 2
refused.
"""

from __future__ import annotations

import calendar
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

WORDS = re.compile(
    r"\b(?:expir\w*|renew\w*|valid\s+(?:until|till|through|thru)|cover\s+ends"
    r"|ends\s+on)\b",
    re.IGNORECASE,
)
MONTHS = {m: i + 1 for i, m in enumerate(
    "january february march april may june july august september october "
    "november december".split()
)}  # fmt: skip
for _m, _i in list(MONTHS.items()):
    MONTHS[_m[:3]] = _i
MONTH = "|".join(sorted(MONTHS, key=len, reverse=True))
#: a date written out: 4 March 2026, March 4, 2026, 4th of March 2026
PROSE = re.compile(
    rf"\b(?:(?P<d1>\d{{1,2}})(?:st|nd|rd|th)?(?:\s+of)?\s+(?P<m1>{MONTH})"
    rf"|(?P<m2>{MONTH})\s+(?P<d2>\d{{1,2}})(?:st|nd|rd|th)?,?)"
    rf"\s+(?P<y>[12]\d{{3}})\b",
    re.IGNORECASE,
)


def prose_date(line: str) -> str:
    """The latest date the line writes out with a month's name and its day,
    as YYYYMMDD, or "" for none; a day a month hasn't is no date."""
    best = ""
    for m in PROSE.finditer(line):
        day = int(m.group("d1") or m.group("d2"))
        month = MONTHS[(m.group("m1") or m.group("m2")).lower()]
        if 1 <= day <= calendar.monthrange(int(m.group("y")), month)[1]:
            best = max(best, f"{m.group('y')}{month:02}{day:02}")
    return best


def found(pile: list[dict]) -> list[dict]:
    """A row per line that says an expiry word and its own date (the kernel's
    `newest`, or written out), soonest first, then by file and line."""
    out = []
    for c in pile:
        for i, line in enumerate(c["text"].splitlines()):
            if not WORDS.search(line):
                continue
            when = max(kernel.newest(line), prose_date(line))
            if when:
                out.append({"when": when, "path": c["path"],
                            "line": c["line"] + i, "text": line.strip()})  # fmt: skip
    return sorted(out, key=lambda r: (r["when"], r["path"], r["line"]))


def day(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def show(rows: list[dict], today: str) -> list[str]:
    wp = max(len(f"{r['path']}:{r['line']}") for r in rows)
    out = []
    for r in rows:
        mark = "gone by" if r["when"] < today else ""
        where = f"{r['path']}:{r['line']}"
        out.append(f"{mark:<7}  {day(r['when'])}  {where:<{wp}}  {r['text'][:110]}")
    gone = sum(r["when"] < today for r in rows)
    out.append(f"{len(rows)} renewal{'s' if len(rows) != 1 else ''}:"
               f" {gone} gone by, {len(rows) - gone} to come")  # fmt: skip
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    now = opts.get("--now") or kernel.now()
    if not opts.get("--box") or args or not re.match(r"\d{4}-\d{2}-\d{2}", now):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows = found(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not rows:
        print("No line of your folder says an expiry and its date.")
        return kernel.ESCALATE
    for line in show(rows, now[:10].replace("-", "")):
        print(line)
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
