"""cal.py: .ics calendars and .vcf contact cards, as dated, readable lines.

    python adapters/stdlib/calendar/cal.py mirror --from FOLDER --to MIRROR

Walks FOLDER (sorted; any part of a path that starts with "." is skipped) and,
for each .ics or .vcf file, writes MIRROR/<the same relative path>.txt, so
`home/cal.ics` becomes `MIRROR/home/cal.ics.txt`. MIRROR is then a text folder
the kernel can read, with `kernel.py init --pile MIRROR`.

Each calendar event is one paragraph: its date (and time, if it has one) and
its summary, then `where:` and `notes:` lines when present, then a blank line:

    2026-10-21  Pay the water bill

    2026-10-28 14:00  Tune - Ybarra
    where: Studio 2, Annex
    notes: Ask about the fee; bring a
      spare string

A recurring event (RRULE) is written once, under its first date, so its
first line says it repeats, and how, in words, and a `repeats:` line keeps
the rule itself; it is not expanded here ([coming-up](../coming-up/) counts
each repeat in its window):

    2022-11-03  Car rego due  (yearly, from this date)
    repeats: FREQ=YEARLY

so a line quoted from it, by an assistant or by you, can't pass for this
year's date. An event marked cancelled says `(cancelled)` on its first line.
Events are sorted by date within a file. A time ending in Z is UTC and is
shown as written, not converted.

Each contact in a .vcf is one paragraph: `contact:` with the full name, then
`phone:`, `email:`, `address:` and `birthday:` lines when present.

A file that is not UTF-8 text, or holds no calendar or card, is skipped and
counted. Nothing is written inside FOLDER and the originals are not changed.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

SUFFIXES = (".ics", ".vcf")
ESCAPED = re.compile(r"\\([\\,;nN])")
ESCAPES = {"n": "\n", "N": "\n"}
UNESCAPED_SEMI = re.compile(r"(?<!\\);")
DATE = re.compile(r"(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2})(\d{2})Z?)?")
BIRTHDAY = re.compile(r"(\d{4})-?(\d{2})-?(\d{2})(?:T.*)?")


def unfold(text: str) -> list[str]:
    """Lines of a file, with each folded line (one that starts with a space or
    tab) joined to the line before it."""
    lines: list[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def prop(line: str) -> tuple[str, str] | None:
    """(NAME, value) of a property line, the name upper-cased and without its
    parameters or vCard group; None for a line with no colon."""
    head, sep, value = line.partition(":")
    if not sep:
        return None
    return head.split(";")[0].split(".")[-1].strip().upper(), value.strip()


def unescape(value: str) -> str:
    return ESCAPED.sub(lambda m: ESCAPES.get(m.group(1), m.group(1)), value)


def flat(value: str) -> str:
    """One line: the value's own line breaks become spaces."""
    return " ".join(p.strip() for p in unescape(value).split("\n") if p.strip())


def block(value: str) -> str:
    """A value that may span lines: continuation lines are indented under it,
    and blank lines are dropped so the paragraph does not end early."""
    parts = [p.strip() for p in unescape(value).split("\n")]
    return "\n  ".join(p for p in parts if p)


def when(value: str) -> tuple[str, str] | None:
    """(ISO date, HH:MM or "") for a DATE or DATE-TIME value, None if it is
    neither or is not a real date."""
    m = DATE.fullmatch(value.strip())
    if m is None:
        return None
    y, mo, d, h, mi, s = (int(g) if g else 0 for g in m.groups())
    try:
        datetime(y, mo, d, h, mi, s)
    except ValueError:
        return None
    return f"{y:04d}-{mo:02d}-{d:02d}", (f"{h:02d}:{mi:02d}" if m.group(4) else "")


def birthday(value: str) -> str:
    """YYYY-MM-DD for a vCard BDAY that has a year, else ""."""
    m = BIRTHDAY.fullmatch(value.strip())
    if m is None:
        return ""
    try:
        datetime(int(m[1]), int(m[2]), int(m[3]))
    except ValueError:
        return ""
    return f"{m[1]}-{m[2]}-{m[3]}"


#: a rule's FREQ, in words, and the unit an INTERVAL counts in
EVERY = {"YEARLY": ("yearly", "years"), "MONTHLY": ("monthly", "months"),
         "WEEKLY": ("weekly", "weeks"), "DAILY": ("daily", "days")}  # fmt: skip


def in_words(rule: str) -> str:
    """An RRULE said plainly: `yearly`, `every 2 weeks`, `monthly, until
    2026-06-01`, `weekly, 10 times`; a FREQ it doesn't know, as `repeating`."""
    parts = dict(p.split("=", 1) for p in rule.upper().split(";") if "=" in p)
    word, unit = EVERY.get(parts.get("FREQ", ""), ("repeating", ""))
    step = parts.get("INTERVAL", "1")
    said = f"every {step} {unit}" if unit and step.isdigit() and int(step) > 1 else word
    if until := when(parts.get("UNTIL", "")):
        said += f", until {until[0]}"
    if parts.get("COUNT", "").isdigit():
        said += f", {parts['COUNT']} times"
    return said


def event_record(event: dict[str, str]) -> tuple[str, str, str, str] | None:
    """(date, time, summary, paragraph) for one VEVENT, None if it has no
    readable DTSTART: an event that cannot be dated is not written."""
    got = when(event["DTSTART"]) if "DTSTART" in event else None
    if got is None:
        return None
    iso, tm = got
    summary = flat(event.get("SUMMARY", "")) or "(untitled)"
    head = f"{iso} {tm}" if tm else iso
    first = f"{head}  {summary}"
    if rule := event.get("RRULE", ""):
        first += f"  ({in_words(rule)}, from this date)"
    if event.get("STATUS", "").upper() == "CANCELLED":
        first += "  (cancelled)"
    lines = [first]
    if where := flat(event.get("LOCATION", "")):
        lines.append(f"where: {where}")
    if notes := block(event.get("DESCRIPTION", "")):
        lines.append(f"notes: {notes}")
    if rule := event.get("RRULE", ""):
        lines.append(f"repeats: {rule}")
    return iso, tm, summary, "\n".join(lines)


def calendar_events(lines: list[str]) -> list[tuple[str, str, str, str]]:
    """Every event in the unfolded lines, sorted by date then time then summary.
    Properties inside a VALARM (its own DESCRIPTION, say) are not the event's."""
    found = []
    event: dict[str, str] | None = None
    alarm = False
    for line in lines:
        got = prop(line)
        if got is None:
            continue
        name, value = got
        if name == "BEGIN" and value.upper() == "VEVENT":
            event, alarm = {}, False
        elif name == "END" and value.upper() == "VEVENT":
            if event is not None and (made := event_record(event)) is not None:
                found.append(made)
            event = None
        elif event is None:
            continue
        elif name == "BEGIN" and value.upper() == "VALARM":
            alarm = True
        elif name == "END" and value.upper() == "VALARM":
            alarm = False
        elif not alarm:
            event.setdefault(name, value)
    return sorted(found)


def contact_paragraph(card: list[tuple[str, str]]) -> str | None:
    """One vCard as a paragraph; None if it has no name at all."""
    full = next((flat(v) for n, v in card if n == "FN" and flat(v)), "")
    if not full:
        for n, v in card:
            if n == "N":
                parts = [unescape(p).strip() for p in UNESCAPED_SEMI.split(v)]
                given = (parts + ["", ""])[1]
                full = " ".join(x for x in (given, parts[0]) if x)
                break
    if not full:
        return None
    out = [f"contact: {full}"]
    for n, v in card:
        if n == "TEL" and (t := flat(v)):
            out.append(f"phone: {t}")
        elif n == "EMAIL" and (t := flat(v)):
            out.append(f"email: {t}")
        elif n == "ADR":
            parts = [flat(p) for p in UNESCAPED_SEMI.split(v)]
            if addr := ", ".join(p for p in parts if p):
                out.append(f"address: {addr}")
        elif n == "BDAY" and (b := birthday(v)):
            out.append(f"birthday: {b}")
    return "\n".join(out)


def contact_paragraphs(lines: list[str]) -> list[str]:
    out = []
    card: list[tuple[str, str]] | None = None
    for line in lines:
        got = prop(line)
        if got is None:
            continue
        name, value = got
        if name == "BEGIN" and value.upper() == "VCARD":
            card = []
        elif name == "END" and value.upper() == "VCARD":
            if card is not None and (made := contact_paragraph(card)) is not None:
                out.append(made)
            card = None
        elif card is not None:
            card.append((name, value))
    return out


def paragraphs(path: Path) -> list[str]:
    """The paragraphs written for one file. Raises ValueError when the file is
    not UTF-8 text or holds no calendar or card; the caller skips it."""
    raw = path.read_bytes()
    if b"\0" in raw:
        raise ValueError("binary")
    lines = unfold(raw.decode("utf-8-sig"))
    if path.suffix.lower() == ".ics":
        if not any(line.strip().upper() == "BEGIN:VCALENDAR" for line in lines):
            raise ValueError("no calendar in it")
        return [text for *_, text in calendar_events(lines)]
    if not any(line.strip().upper() == "BEGIN:VCARD" for line in lines):
        raise ValueError("no card in it")
    return contact_paragraphs(lines)


def sources(folder: Path):
    """The .ics and .vcf files under `folder`, sorted, skipping any folder or
    file whose name starts with a dot."""
    for root, dirs, names in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for name in sorted(names):
            path = Path(root, name)
            if name.startswith(".") or path.suffix.lower() not in SUFFIXES:
                continue
            if path.is_file():
                yield path


def mirror_folder(folder: Path, mirror: Path) -> int:
    if not folder.is_dir():
        print(f"refused: {folder} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    src, dst = folder.resolve(), mirror.resolve()
    if dst.is_relative_to(src):
        print(
            "refused: MIRROR is inside FOLDER; nothing is written there",
            file=sys.stderr,
        )
        return kernel.REFUSED
    if src.is_relative_to(dst):
        print("refused: FOLDER is inside MIRROR", file=sys.stderr)
        return kernel.REFUSED
    if dst.exists() and not dst.is_dir():
        print(f"refused: {mirror} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    written = skipped = 0
    for path in sources(src):
        try:
            texts = paragraphs(path)
        except (OSError, ValueError):
            texts = []
        if not texts:
            skipped += 1
            continue
        rel = path.relative_to(src)
        out = dst / rel.with_name(rel.name + ".txt")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(("\n\n".join(texts) + "\n").encode("utf-8"))
        written += 1
    print(f"wrote {written} files to {mirror}; skipped {skipped}")
    return kernel.ALIVE if written else kernel.ESCALATE


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="cal.py")
    verbs = parser.add_subparsers(dest="verb", required=True)
    mirror = verbs.add_parser("mirror", help="write each calendar and card as text")
    mirror.add_argument("--from", dest="folder", type=Path, required=True)
    mirror.add_argument("--to", dest="mirror", type=Path, required=True)
    args = parser.parse_args(argv)
    return mirror_folder(args.folder, args.mirror)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
