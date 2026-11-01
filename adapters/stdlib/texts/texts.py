"""texts.py: phone text messages and calls, mirrored as one dated line per message.

    python adapters/stdlib/texts/texts.py mirror --from FOLDER --to MIRROR [--me NAME] [--tz ZONE]

Walks FOLDER and writes each phone backup it finds into MIRROR, as text the
kernel can read:

- an Android backup from SMS Backup & Restore: its messages file
  (`<smses>`, texts and picture messages) and its call log (`<calls>`);
- an iPhone's messages database, `sms.db`, as an iPhone backup keeps it
  (often under a hashed name with no suffix: it is known by what it holds).

Each becomes one section per conversation, `# NAME`, and in it one line per
message or call, grouped into paragraphs by day, so each passage the kernel
serves is one day with one person:

    2024-12-03 08:10  Dev Raman: I can do 600 tonight
    2024-12-03 08:12  me: Done
    2024-12-03 09:40  outgoing call, 3 min

Times are this machine's local time unless `--tz` names a zone
(America/Denver). Your own messages are `me` unless `--me` names you. Drafts
and messages that never sent are left out. Files that are not phone backups
are not counted; a backup it cannot read is skipped and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sqlite3
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

SQLITE = b"SQLite format 3\x00"
APPLE_EPOCH = 978307200  # 2001-01-01, where an iPhone counts time from
#: SMS Backup & Restore's call types
CALL = {
    "1": "incoming call",
    "2": "outgoing call",
    "3": "missed call",
    "4": "voicemail",
    "5": "rejected call",
    "6": "blocked call",
    "7": "call answered on another device",
}
UNKNOWN = ("", "(Unknown)", "null")
#: a picture message's parts that aren't words, as the line names them
MEDIA = {"image": "picture", "video": "video", "audio": "audio"}


class Unreadable(Exception):
    """A backup this can't read: counted as skipped, with the reason said."""


def one_line(text: str) -> str:
    return " ".join(text.split())


def when(seconds: float, tz: dt.tzinfo | None) -> dt.datetime:
    """The moment as a wall clock: in `tz`, or this machine's local time."""
    if tz is None:
        return dt.datetime.fromtimestamp(seconds)
    return dt.datetime.fromtimestamp(seconds, tz)


def render(chats: dict[str, list[tuple[float, str]]], tz: dt.tzinfo | None) -> str:
    """One section per conversation, by name; in each, (seconds, line) in time
    order, a paragraph per day."""
    out = []
    for name in sorted(chats, key=lambda n: (n.casefold(), n)):
        days: list[list[str]] = []
        last = None
        for seconds, line in sorted(chats[name]):
            stamp = when(seconds, tz)
            if stamp.date() != last:
                days.append([])
                last = stamp.date()
            days[-1].append(f"{stamp:%Y-%m-%d %H:%M}  {line}")
        out.append(f"# {name}\n\n" + "\n\n".join("\n".join(d) for d in days))
    return "\n\n".join(out) + "\n"


def who_of(el: ET.Element) -> str:
    """The conversation's name: the contact's, or the number when unnamed."""
    name = one_line(el.get("contact_name") or "")
    if name in UNKNOWN:
        name = one_line(el.get("address") or el.get("number") or "")
    return name or "unknown"


def ms(el: ET.Element) -> float:
    try:
        return int(el.get("date", "")) / 1000
    except ValueError:
        raise Unreadable(f"a {el.tag} with no date it can read") from None


def mms_text(el: ET.Element) -> str:
    """A picture message's words, and `[picture]` (or the like) for each
    part that isn't words."""
    said = []
    for part in el.iter("part"):
        kind = (part.get("ct") or "").lower()
        if kind == "text/plain":
            said.append(one_line(part.get("text") or ""))
        elif kind.split("/")[0] in MEDIA:
            said.append(f"[{MEDIA[kind.split('/')[0]]}]")
    return " ".join(s for s in said if s)


def android_messages(root: ET.Element, me: str) -> dict[str, list]:
    chats: dict[str, list] = {}
    for el in root:
        if el.tag == "sms":
            box, text = el.get("type"), one_line(el.get("body") or "")
        elif el.tag == "mms":
            box, text = el.get("msg_box"), mms_text(el)
        else:
            continue
        if box not in ("1", "2"):  # 3 draft, 4 outbox, 5 failed, 6 queued
            continue
        name = who_of(el)
        sender = me if box == "2" else name
        chats.setdefault(name, []).append((ms(el), f"{sender}: {text or '(no text)'}"))
    return chats


def android_calls(root: ET.Element) -> dict[str, list]:
    chats: dict[str, list] = {}
    for el in root:
        if el.tag != "call":
            continue
        what = CALL.get(el.get("type", ""), f"call of type {el.get('type')}")
        try:
            secs = int(el.get("duration") or 0)
        except ValueError:
            secs = 0
        if secs >= 60:
            what += f", {round(secs / 60)} min"
        elif secs:
            what += f", {secs} s"
        chats.setdefault(who_of(el), []).append((ms(el), what))
    return chats


def apple_text(text: str | None, body: bytes | None) -> str:
    """A message's words: its `text`, or, as newer iPhones keep them, the
    string inside its `attributedBody`."""
    if text:
        return one_line(text)
    if not body:
        return ""
    i = body.find(b"NSString")
    j = body.find(b"\x01+", i) if i >= 0 else -1
    if j < 0 or j + 3 > len(body):
        return ""
    p, n = j + 3, body[j + 2]
    if n == 0x81:
        n, p = int.from_bytes(body[p : p + 2], "little"), p + 2
    elif n == 0x82:
        n, p = int.from_bytes(body[p : p + 3], "little"), p + 3
    return one_line(body[p : p + n].decode("utf-8", errors="replace"))


def apple_seconds(raw: int) -> float:
    """An iPhone's date: seconds since 2001, or nanoseconds since iOS 11."""
    return (raw / 1e9 if abs(raw) > 1e11 else raw) + APPLE_EPOCH


def iphone(path: Path, me: str) -> dict[str, list] | None:
    """The conversations in an iPhone's sms.db, or None when it isn't one."""
    try:
        con = sqlite3.connect(
            f"{path.resolve().as_uri()}?mode=ro&immutable=1", uri=True
        )
    except sqlite3.Error as why:
        raise Unreadable(str(why)) from None
    try:
        tables = {
            r[0]
            for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if not {"message", "handle"} <= tables:
            return None
        cols = {r[1] for r in con.execute("PRAGMA table_info(message)")}
        body = "m.attributedBody" if "attributedBody" in cols else "NULL"
        chat = "chat" in tables and "chat_message_join" in tables
        rows = con.execute(
            f"SELECT m.date, m.is_from_me, m.text, {body}, h.id, "
            + ("c.display_name, c.chat_identifier " if chat else "NULL, NULL ")
            + "FROM message m LEFT JOIN handle h ON h.ROWID = m.handle_id "
            + (
                "LEFT JOIN chat_message_join j ON j.message_id = m.ROWID "
                "LEFT JOIN chat c ON c.ROWID = j.chat_id "
                if chat
                else ""
            )
            + "ORDER BY m.date, m.ROWID"
        ).fetchall()
    except sqlite3.Error as why:
        raise Unreadable(str(why)) from None
    finally:
        con.close()
    chats: dict[str, list] = {}
    for date, mine, text, blob, handle, title, ident in rows:
        if not isinstance(date, int):
            continue
        name = one_line(title or "") or one_line(ident or "") or one_line(handle or "")
        name = name or "unknown"
        sender = me if mine else one_line(handle or "") or name
        said = apple_text(text, blob if isinstance(blob, bytes) else None)
        chats.setdefault(name, []).append(
            (apple_seconds(date), f"{sender}: {said or '(no text)'}")
        )
    return chats


def convert(path: Path, me: str, tz: dt.tzinfo | None) -> str | None:
    """The mirror text for one file. None: not a phone backup, so not counted."""
    with path.open("rb") as f:
        head = f.read(512)
    if head.startswith(SQLITE):
        chats = iphone(path, me)
    elif path.suffix.lower() == ".xml":
        start = head.decode("utf-8", errors="replace")
        if "<smses" not in start and "<calls" not in start:
            return None
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as why:
            raise Unreadable(f"not valid XML ({why})") from None
        if root.tag == "smses":
            chats = android_messages(root, me)
        elif root.tag == "calls":
            chats = android_calls(root)
        else:
            return None
    else:
        return None
    if chats is None:
        return None
    if not chats:
        raise Unreadable("no message or call in it")
    return render(chats, tz)


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


def mirror(folder: Path, to: Path, me: str, zone: str | None) -> int:
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
    tz = None
    if zone is not None:
        try:
            tz = ZoneInfo(zone)
        except (ZoneInfoNotFoundError, ValueError):
            print(
                f"refused: {zone} is not a time zone this machine knows",
                file=sys.stderr,
            )
            return kernel.REFUSED
    written = skipped = 0
    for rel in sources(src):
        try:
            text = convert(src / rel, me, tz)
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
    ap = argparse.ArgumentParser(prog="texts.py", description=__doc__.split("\n")[0])
    verbs = ap.add_subparsers(dest="verb", required=True)
    m = verbs.add_parser("mirror", help="write each phone backup as dated lines")
    m.add_argument("--from", dest="folder", required=True, type=Path)
    m.add_argument("--to", dest="to", required=True, type=Path)
    m.add_argument("--me", default="me", help="the name for your own messages")
    m.add_argument("--tz", help="the time zone to write times in, as America/Denver")
    args = ap.parse_args(argv)
    me = one_line(args.me) or "me"
    return mirror(args.folder, args.to, me, args.tz)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
