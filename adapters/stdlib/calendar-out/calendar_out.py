"""calendar_out.py: the dates coming up, as an .ics file. Python 3.9+.

    python adapters/stdlib/calendar-out/calendar_out.py --box DIR --to FILE [--days N] [--now TS]

The dates your files hold in the next N days (30 unless said), found the way
[coming-up](../coming-up/) finds them, written as an iCalendar file that any
calendar app can import or subscribe to:

    BEGIN:VCALENDAR
    ...
    BEGIN:VEVENT
    UID:4f2a...@willow
    DTSTAMP:20261024T000000Z
    DTSTART;VALUE=DATE:20261030
    SUMMARY:Your cover ends on 31/10/2026 unless renewed.
    DESCRIPTION:From work/insurance.txt:4
    END:VEVENT
    END:VCALENDAR

Each date is an all-day event whose title is the line it was found on and whose
description says where, so you can go back to the file. A date that repeats (a
birthday, a yearly renewal) is one event on each repeat in the window. The
UID is made from the date, the place and the line, so reimporting the file
updates an event and doesn't double it; DTSTAMP is --now, so the same folder
and day give the same bytes.

To subscribe, put FILE where your calendar app can fetch it. Nothing here
serves it or sends it anywhere. A date found in a calendar file (an .ics, or a mirror of one) is not written
again: it is already in a calendar. A folder with nothing dated in the window
writes nothing. Lines are folded at 75 bytes and text is escaped as the
standard asks.

FILE is written once, readable only by you, never over a file that exists.
It only reads your folder. Exit codes, the kernel's: 0 written; 42 nothing
dated in the window, nothing written; 2 refused.
"""

from __future__ import annotations

import hashlib
import os
import sys
from datetime import timedelta
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "coming-up"))
import coming_up  # noqa: E402
import kernel  # noqa: E402

DAYS = "30"


def escape(text: str) -> str:
    """Text as iCalendar writes it: backslash, semicolon, comma and newline."""
    bs = chr(92)
    return (
        text.replace(bs, bs + bs)
        .replace(";", bs + ";")
        .replace(",", bs + ",")
        .replace("\r\n", bs + "n")
        .replace("\n", bs + "n")
    )


def is_calendar(place: str) -> bool:
    """Whether a hit is from a calendar file already (a.ics, or a mirror of one)."""
    return place.rsplit(":", 1)[0].lower().endswith((".ics", ".ics.txt"))


def fold(line: str) -> str:
    """A content line folded at 75 octets, never inside a character."""
    out, cur = [], b""
    for ch in line:
        enc = ch.encode("utf-8")
        if len(cur) + len(enc) > (75 if not out else 74):
            out.append(cur.decode("utf-8"))
            cur = b""
        cur += enc
    out.append(cur.decode("utf-8"))
    return "\r\n ".join(out)


def calendar(hits: list[tuple], stamp: str) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//willow//calendar-out//EN",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:Willow: coming up",
    ]
    for d, place, text in hits:
        uid = hashlib.sha256(f"{d}\n{place}\n{text}".encode()).hexdigest()[:32]
        title = " ".join(text.split())
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}@willow",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{(d + timedelta(days=1)).strftime('%Y%m%d')}",
            f"SUMMARY:{escape(title[:120])}",
            f"DESCRIPTION:{escape('From ' + place)}",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]  # fmt: skip
    lines.append("END:VCALENDAR")
    return "".join(fold(x) + "\r\n" for x in lines)


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--to", "--days", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    days = opts.get("--days", DAYS)
    if not opts.get("--box") or not opts.get("--to") or args or not days.isdigit():
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    box, to = Path(opts["--box"]), Path(opts["--to"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    ts = opts.get("--now") or kernel.now()
    try:
        today = coming_up.ymd(ts[:10].replace("-", ""))
    except ValueError:
        print(f"refused: --now {ts!r} isn't a date, YYYY-MM-DD", file=sys.stderr)
        return kernel.REFUSED
    found = coming_up.coming(
        kernel.chunks(Path(kernel.config(box)["pile"])), today, int(days)
    )
    hits = [h for h in found if not is_calendar(h[1])]
    if not hits:
        print(
            f"Nothing dated between {today} and {today + timedelta(days=int(days))}, so no file was written."
        )
        return kernel.ESCALATE
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as e:
        print(f"refused: could not write {to}: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(calendar(hits, today.strftime("%Y%m%dT000000Z")))
    print(
        f"wrote {to}: {len(hits)} event{'s' if len(hits) != 1 else ''}, {today} to {today + timedelta(days=int(days))}"
    )
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
