"""apple_mail.py: Apple Mail's .emlx messages, as plain text the kernel can read.

    python adapters/stdlib/apple-mail/apple_mail.py mirror --from FOLDER --to MIRROR

Apple Mail keeps each message as its own file under ~/Library/Mail/V*/.../
Messages/: NUMBER.emlx, or NUMBER.partial.emlx when its attachments were moved
out. Such a file is three things in a row: the size of the message in bytes,
written as digits on the first line; exactly that many bytes of the message
itself, as it came in; and a short property list of Apple Mail's own flags and
dates (date-received among them).

Walks FOLDER (sorted; a folder or file whose name starts with "." is skipped)
and writes, into MIRROR, one text file for each .emlx it can read, at the same
relative path with ".txt" added: Messages/12.emlx becomes
MIRROR/Messages/12.emlx.txt. Then point the kernel at MIRROR:

    python kernel.py init --box BOX --pile MIRROR --key KEY

Each message reads as the mail add-on writes an .eml (it is mail's own
render): From, To, Date and Subject, a blank line, the body, and then the
attachments, listed by name only. A .partial.emlx is read the same way; its
attachments are still named, though their content is elsewhere.

Date is the message's own Date header, as mail writes it. Only when the message
has no Date header is the property list's date-received used, in UTC. The text
adds no word of its own to say so, since a word on every message would answer
questions the folder can't; the summary line before the last says how many:

    3 had no Date header; their Date is Apple Mail's date received, in UTC

A first line that isn't a number, or a file shorter than the number it gives,
is skipped and counted. Only files ending .emlx are read; others (the .emlxpart
files of attachments among them) are not counted. FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (a bad
command line, FOLDER not a folder, or MIRROR and FOLDER inside each other).
"""

from __future__ import annotations

import email
import email.policy
import os
import plistlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mail"))
import kernel  # noqa: E402
import mail  # noqa: E402

USAGE = "refused: usage: apple_mail.py mirror --from FOLDER --to MIRROR"
COUNT = re.compile(rb"[ \t]*([0-9]+)[ \t\r]*")
NO_DATE = "\nDate: none\n"
RECEIVED = "{} had no Date header; their Date is Apple Mail's date received, in UTC"


def split(raw: bytes) -> tuple[bytes, bytes] | None:
    """(the message, what follows it), or None when the first line isn't a
    byte count or the file is shorter than the count says."""
    first, newline, rest = raw.partition(b"\n")
    m = COUNT.fullmatch(first)
    if not newline or not m:
        return None
    size = int(m.group(1))
    if len(rest) < size:
        return None
    return rest[:size], rest[size:]


def received(tail: bytes) -> str | None:
    """The property list's date-received, as a UTC clock time, or None."""
    try:
        plist = plistlib.loads(tail.strip())
    except Exception:  # no list, or not one: the message is still read
        return None
    when = plist.get("date-received") if isinstance(plist, dict) else None
    if isinstance(when, bool) or not isinstance(when, (int, float)):
        return None
    try:
        day = datetime.fromtimestamp(when, timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None
    return day.strftime("%Y-%m-%d %H:%M")


def read_file(path: Path) -> tuple[str, bool] | None:
    """The text an .emlx mirrors to, and whether its Date is the date received;
    None when it can't be read as one."""
    try:
        parts = split(path.read_bytes())
        if parts is None or b"\0" in parts[0]:
            return None
        msg = email.message_from_bytes(parts[0], policy=email.policy.default)
        if not mail.is_message(msg):
            return None
        text = mail.render(msg)
        has_date = str(msg.get("Date") or "").strip()
    except Exception:  # any message that won't parse is skipped and counted
        return None
    when = None if has_date else received(parts[1])
    if when:
        text = text.replace(NO_DATE, f"\nDate: {when}\n", 1)
    return text, bool(when)


def sources(folder: Path):
    """(path, relative path) of each .emlx under folder, sorted."""
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            if name.startswith(".") or not name.lower().endswith(".emlx"):
                continue
            path = Path(dirpath) / name
            yield path, path.relative_to(folder)


def mirror(folder: Path, dest: Path) -> int:
    if not folder.is_dir():
        print(f"refused: {folder} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    if dest.exists() and not dest.is_dir():
        print(f"refused: {dest} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    src, out = folder.resolve(), dest.resolve()
    if out == src or out.is_relative_to(src) or src.is_relative_to(out):
        print(
            "refused: MIRROR and FOLDER must not be inside each other", file=sys.stderr
        )
        return kernel.REFUSED
    wrote = skipped = dated = 0
    for path, rel in sources(src):
        got = read_file(path)
        if got is None:
            skipped += 1
            continue
        text, by_received = got
        dated += by_received
        target = out / rel.parent / (rel.name + ".txt")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8", "replace"))
        except OSError as err:
            print(f"refused: cannot write {target}: {err}", file=sys.stderr)
            return kernel.REFUSED
        wrote += 1
    if dated:
        print(RECEIVED.format(dated))
    print(f"wrote {wrote} files to {dest}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


def main(argv: list[str]) -> int:
    if (
        len(argv) != 5
        or argv[0] != "mirror"
        or argv[1] != "--from"
        or argv[3] != "--to"
    ):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    return mirror(Path(argv[2]), Path(argv[4]))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
