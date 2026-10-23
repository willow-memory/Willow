"""chats.py: WhatsApp and Telegram exports, mirrored as one dated line per message.

    python adapters/stdlib/chats/chats.py mirror --from FOLDER --to MIRROR [--day-first | --month-first]

Walks FOLDER and writes each chat export it finds into MIRROR, as text the
kernel can read. A WhatsApp .txt export (`[03/12/2024, 08:10:00] Dev Raman: text`
or `03/12/2024, 08:10 - Dev Raman: text`) and a Telegram .json export (a
`messages` list) each become one line per message:

    2024-12-03 08:10  Dev Raman: I can do 600 tonight

Messages are grouped into paragraphs by day, a blank line between days, so each
passage the kernel serves is one day of one chat. A WhatsApp continuation line
belongs to the message above it. Files that are not chat exports are not
counted; a chat export it cannot read is skipped and counted.

The day and month order of a WhatsApp export is decided once per file: a first
number over 12 means day first, a second number over 12 means month first. A
file that never settles it is written with its dates as they were given and
`(date order unknown)` at the top. `--day-first` or `--month-first` settles it;
a file whose own dates contradict the flag is skipped, not rewritten.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

NOTE = "(date order unknown)"
NAME = {"dmy": "day-first", "mdy": "month-first"}
TIME = r"\d{1,2}:\d{2}(?::\d{2})?(?:[\s  ]?[AaPp][Mm])?"
# "[03/12/2024, 08:10:00] Name: text" or "03/12/2024, 08:10 - Name: text"
START = re.compile(
    r"^‎?\[?(\d{1,2})/(\d{1,2})/(\d{2}|\d{4}), (" + TIME + r")\]?(?:\s-)?\s(.*)$"
)
SENDER = re.compile(r"^([^:]+?): (.*)$")
TIME_PARTS = re.compile(r"(\d{1,2}):(\d{2})(?::\d{2})?(?:[\s  ]?([AaPp][Mm]))?")
ISO_STAMP = re.compile(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})")
JSON_HINT = re.compile(r'"messages"\s*:\s*\[')


class Unreadable(Exception):
    """A chat export this can't read: counted as skipped, with the reason said."""


def one_line(text: str) -> str:
    return " ".join(text.split())


def clock(raw: str) -> str | None:
    """`8:10`, `08:10:00` or `8:10 PM` as 24-hour `HH:MM`, or None if it isn't a time."""
    m = TIME_PARTS.fullmatch(raw)
    if m is None:
        return None
    hour, minute = int(m[1]), int(m[2])
    if m[3]:
        if not 1 <= hour <= 12:
            return None
        hour = hour % 12 + (12 if m[3].lower() == "pm" else 0)
    if hour > 23 or minute > 59:
        return None
    return f"{hour:02d}:{minute:02d}"


def stamps_of(text: str) -> tuple[list[re.Match], int]:
    """The WhatsApp date-prefixed lines of `text`, and how many lines aren't blank."""
    full = [ln.rstrip("\r") for ln in text.split("\n") if ln.strip()]
    found = [m for m in (START.match(ln) for ln in full) if m is not None]
    return found, len(full)


def looks_whatsapp(text: str) -> bool:
    """Most non-empty lines start with a WhatsApp date prefix."""
    found, nonblank = stamps_of(text)
    return bool(found) and 2 * len(found) > nonblank


def order_of(pairs: list[tuple[str, str]], flag: str | None) -> str | None:
    """ "dmy", "mdy", or None when the file's own dates and the flag don't settle it."""
    day_first = any(int(a) > 12 for a, _ in pairs)
    month_first = any(int(b) > 12 for _, b in pairs)
    if day_first and month_first:
        raise Unreadable("its dates read both day-first and month-first")
    if day_first or month_first:
        found = "dmy" if day_first else "mdy"
        if flag is not None and flag != found:
            raise Unreadable(f"its dates say {NAME[found]}, the flag says {NAME[flag]}")
        return found
    return flag


def iso(a: str, b: str, y: str, order: str) -> str | None:
    year = int(y) + (2000 if len(y) == 2 else 0)
    day, month = (int(a), int(b)) if order == "dmy" else (int(b), int(a))
    try:
        return dt.date(year, month, day).isoformat()
    except ValueError:
        return None


def render(rows: list[tuple[str, str, str, str]], note: bool) -> str:
    """`rows` are (day, HH:MM, who, text) in order; one paragraph per day."""
    days: list[list[str]] = []
    last = None
    for day, hhmm, who, text in rows:
        if day != last:
            days.append([])
            last = day
        days[-1].append(f"{day} {hhmm}  {who}: {text}".rstrip())
    body = "\n\n".join("\n".join(d) for d in days) + "\n"
    return f"{NOTE}\n\n{body}" if note else body


def whatsapp(text: str, flag: str | None) -> str | None:
    """The mirror text of a WhatsApp export, or None when `text` isn't one."""
    if not looks_whatsapp(text):
        return None
    lines = [ln.rstrip("\r") for ln in text.split("\n") if ln.strip()]
    order = order_of(
        [(m[1], m[2]) for m in (START.match(ln) for ln in lines) if m], flag
    )
    messages: list[list] = []
    cur: list | None = None
    for ln in lines:
        m = START.match(ln)
        if m is None:  # no date prefix: continues the message above it
            if cur is not None:
                cur[5].append(ln.strip())
            continue
        said = SENDER.match(m[5])  # a dated line with no "Name: " is a system line
        cur = [m[1], m[2], m[3], m[4], said[1], [said[2]]] if said else None
        if cur is not None:
            messages.append(cur)
    rows = []
    for a, b, y, raw_time, who, parts in messages:
        hhmm = clock(raw_time)
        day = iso(a, b, y, order) if order else f"{a}/{b}/{y}"
        if hhmm is not None and day is not None:
            rows.append((day, hhmm, one_line(who), one_line(" ".join(parts))))
    if not rows:
        raise Unreadable("no message it could date")
    return render(rows, note=order is None)


def flatten(text: object) -> str:
    """A Telegram text: a string, or a list of strings and {"text": ...} pieces."""
    if isinstance(text, str):
        return text
    if not isinstance(text, list):
        return ""
    out = []
    for part in text:
        if isinstance(part, dict):
            part = part.get("text", "")
        if isinstance(part, str):
            out.append(part)
    return "".join(out)


def telegram(data: dict) -> str:
    rows = []
    for m in data["messages"]:
        if not isinstance(m, dict) or not isinstance(m.get("from"), str):
            continue  # service messages have no "from"
        stamp = m.get("date")
        got = ISO_STAMP.match(stamp) if isinstance(stamp, str) else None
        if got is None:
            continue
        try:
            day = dt.date(int(got[1]), int(got[2]), int(got[3])).isoformat()
        except ValueError:
            continue
        hhmm = clock(f"{got[4]}:{got[5]}")
        if hhmm is not None and one_line(m["from"]):
            rows.append(
                (day, hhmm, one_line(m["from"]), one_line(flatten(m.get("text"))))
            )
    if not rows:
        raise Unreadable("no message it could date")
    return render(rows, note=False)


def telegram_shaped(data: object) -> bool:
    if not isinstance(data, dict) or not isinstance(data.get("messages"), list):
        return False
    return any(isinstance(m, dict) and "date" in m for m in data["messages"])


def convert(raw: bytes, suffix: str, flag: str | None) -> str | None:
    """The mirror text for one file. None: not a chat export, so not counted."""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:  # not UTF-8: say so only for a chat it can see
        seen = raw.decode("utf-8", errors="replace")
        if (suffix == ".json" and JSON_HINT.search(seen)) or (
            suffix == ".txt" and looks_whatsapp(seen)
        ):
            raise Unreadable("not UTF-8") from None
        return None
    if suffix == ".json":
        try:
            data = json.loads(text)
        except ValueError:
            if JSON_HINT.search(text):
                raise Unreadable("not valid JSON") from None
            return None
        return telegram(data) if telegram_shaped(data) else None
    return whatsapp(text, flag)


def sources(root: Path) -> list[Path]:
    """Every file under `root`, skipping hidden names, sorted by path."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            full = Path(dirpath, name)
            if not name.startswith(".") and full.is_file():
                found.append(full.relative_to(root))
    return sorted(found, key=lambda p: p.as_posix())


def mirror(folder: Path, to: Path, flag: str | None) -> int:
    if not folder.is_dir():
        print(f"refused: {folder} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    src, dst = folder.resolve(), to.resolve()
    if dst == src or src in dst.parents or dst in src.parents:
        print(
            "refused: MIRROR and FOLDER must not be inside each other", file=sys.stderr
        )
        return kernel.REFUSED
    if to.exists() and not to.is_dir():
        print(f"refused: {to} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    written = skipped = 0
    for rel in sources(src):
        suffix = rel.suffix.lower()
        if suffix not in (".txt", ".json"):
            continue
        try:
            text = convert((src / rel).read_bytes(), suffix, flag)
        except (OSError, Unreadable) as why:
            skipped += 1
            print(f"skipped {rel.as_posix()}: {why}", file=sys.stderr)
            continue
        if text is None:
            continue
        out = to / rel
        out = out.with_name(out.name + ".txt")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(text.encode("utf-8"))
        written += 1
    print(f"wrote {written} files to {to}; skipped {skipped}")
    return kernel.ALIVE if written else kernel.ESCALATE


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="chats.py", description=__doc__.split("\n")[0])
    verbs = ap.add_subparsers(dest="verb", required=True)
    m = verbs.add_parser("mirror", help="write each chat export as dated lines")
    m.add_argument("--from", dest="folder", required=True, type=Path)
    m.add_argument("--to", dest="to", required=True, type=Path)
    order = m.add_mutually_exclusive_group()
    order.add_argument("--day-first", dest="flag", action="store_const", const="dmy")
    order.add_argument("--month-first", dest="flag", action="store_const", const="mdy")
    args = ap.parse_args(argv)
    return mirror(args.folder, args.to, args.flag)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
