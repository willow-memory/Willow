"""cursor_chats.py: Cursor agent chats as numbered turns. Python 3.9+.

    python adapters/stdlib/cursor-chats/cursor_chats.py \\
        mirror --from FOLDER --to MIRROR

Cursor's agent keeps each chat in its own SQLite database,
`~/.cursor/chats/<project>/<chat>/store.db`. Walks FOLDER for `store.db`
files and writes each chat as the spoken turns: what you typed and what the
assistant said. System prompts, tool calls, tool results and reasoning are
left out.

    chat 1b2c3d4e-0000-4000-8000-000000000001
    name: Dentist
    started: 2026-10-31T09:00:00Z
    model: some-model
    2 turns

    1  you
    When is the dentist?

    2  assistant
    Tuesday at 3.

How a store holds a chat. `meta` has one row whose value is hex-encoded
JSON: `agentId`, `name`, `createdAt`, `lastUsedModel` and `latestRootBlobId`.
`blobs` is content-addressed (the id is the hex of a 32-byte hash). A blob
is either a JSON message `{"role": ..., "content": ...}` or a protobuf
node. A node is a list of fields; every length-delimited field of 32 bytes
that names another blob is a link. The root is the blob `latestRootBlobId`
names. Field 1 links to messages, field 13 links to nodes of the same kind,
and the links are read in the order they are written: that is the order of
the conversation. Fields 3, 5, 8, 9 and the rest carry other things (file
states, the working folder, a timezone) and are not followed.

When the root can't be read, or reaches no message, nothing is guessed: the
header says `order: not found in the store` and the turns are listed in the
order SQLite returns them.

The store is opened read-only and never written to. A `store.db` that is not
a Cursor chat (not SQLite, no `meta`, no agent id, no spoken turns) is
skipped and counted. Hidden folders and files are skipped.

A chat too long for the kernel to read (over PART bytes) is written in parts,
`store.db.txt`, `store.db.2.txt`, and so on, cut between turns; each part
has the header and `part N of M`, and the turn numbers go on across parts.

    wrote 2 files to MIRROR; skipped 1

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: cursor_chats.py mirror --from FOLDER --to MIRROR"
ROLES = {"user": "you", "assistant": "assistant"}
LINK_FIELDS = (1, 13)  # 1: a message, 13: a node of the same kind
HASH = 32
MAX_NODES = 1_000_000


PART = 900_000  # bytes a mirror file holds before it goes on; the kernel reads 1 MB
PART_LINE = "part 99999 of 99999\n"  # the widest the "part N of M" line gets


def _cut(line: str, room: int) -> tuple[str, str]:
    """`line` cut after at most `room` bytes, never inside a character."""
    raw = line.encode("utf-8")
    at = room
    while at > 0 and 0x80 <= raw[at] < 0xC0:
        at -= 1
    return raw[:at].decode("utf-8"), raw[at:].decode("utf-8")


def _pieces(block: str, room: int, budget: int) -> list[str]:
    """One turn cut at line ends (inside a line only if it is too long): the
    first piece holds at most `room` bytes, each later one at most `budget`."""
    out, cur, used, cap = [], "", 0, room
    for line in block.splitlines(keepends=True):
        n = len(line.encode("utf-8"))
        if used + n > cap and cur:
            out.append(cur)
            cur, used, cap = "", 0, budget
        while used + n > cap:
            head, line = _cut(line, cap - used)
            out.append(cur + head)
            cur, used, cap = "", 0, budget
            n = len(line.encode("utf-8"))
        cur, used = cur + line, used + n
    return out + [cur] if cur else out


def _parts(blocks: list[str], budget: int) -> list[list[str]]:
    """The turns packed into parts of at most `budget` bytes, cut between
    turns; a turn too long for a part goes on into the next."""
    parts: list[list[str]] = [[]]
    size = 0
    for block in blocks:
        n = len(block.encode("utf-8"))
        sep = 2 if parts[-1] else 0
        if size + sep + n > budget and n <= budget:
            parts.append([])
            size, sep = 0, 0
        if size + sep + n <= budget:
            parts[-1].append(block)
            size += sep + n
            continue
        room = budget - size - sep
        if parts[-1] and room < budget // 4:
            parts.append([])
            size, room = 0, budget
        for i, piece in enumerate(_pieces(block, room, budget)):
            if i:
                parts.append([])
                size = 0
            sep = 2 if parts[-1] else 0
            parts[-1].append(piece)
            size += sep + len(piece.encode("utf-8"))
    return parts


def _written(head: list[str], lead: str, blocks: list[str]) -> list[str]:
    """The session as one text, or as parts of under PART bytes: each part
    has the whole header, then `part N of M`, then its turns."""
    top = "\n".join(head) + lead
    whole = top + "\n\n".join(blocks) + "\n"
    if len(whole.encode("utf-8")) <= PART:
        return [whole]
    room = PART - len((top + PART_LINE).encode("utf-8")) - 1
    parts = _parts(blocks, max(room, 64))
    head_text = "\n".join(head)
    return [
        f"{head_text}\npart {n} of {len(parts)}{lead}" + "\n\n".join(p) + "\n"
        for n, p in enumerate(parts, 1)
    ]


def _write_parts(target: Path, texts: list[str]) -> None:
    """`X.txt`, `X.2.txt`, ... written; an `X.N.txt` left from a longer
    session is removed, and nothing else."""
    target.parent.mkdir(parents=True, exist_ok=True)
    keep = {target.name}
    target.write_bytes(texts[0].encode("utf-8"))
    for n, text in enumerate(texts[1:], 2):
        part = target.with_name(f"{target.stem}.{n}.txt")
        part.write_bytes(text.encode("utf-8"))
        keep.add(part.name)
    stale = re.compile(re.escape(target.stem) + r"\.\d+\.txt")
    for old in target.parent.iterdir():
        if old.name not in keep and stale.fullmatch(old.name) and old.is_file():
            old.unlink()


def _varint(buf: bytes, i: int) -> tuple[int, int]:
    n = shift = 0
    while True:
        b = buf[i]  # IndexError on a short buffer: the caller treats it as unreadable
        i += 1
        n |= (b & 0x7F) << shift
        shift += 7
        if b < 0x80:
            return n, i
        if shift > 63:
            raise ValueError("varint too long")


def fields_of(buf: bytes) -> list[tuple[int, bytes]]:
    """(field number, bytes) of each length-delimited field, in order.

    Other wire types are stepped over. Raises ValueError or IndexError when
    the bytes are not a protobuf message."""
    out, i = [], 0
    while i < len(buf):
        key, i = _varint(buf, i)
        field, wire = key >> 3, key & 7
        if wire == 0:
            _, i = _varint(buf, i)
        elif wire == 1:
            i += 8
        elif wire == 5:
            i += 4
        elif wire == 2:
            size, i = _varint(buf, i)
            if i + size > len(buf):
                raise ValueError("field runs past the end")
            out.append((field, buf[i : i + size]))
            i += size
        else:
            raise ValueError(f"wire type {wire}")
    if i != len(buf):
        raise ValueError("fixed field runs past the end")
    return out


def _message(data) -> dict | None:
    """The JSON message a blob holds, or None for anything else."""
    if not isinstance(data, (bytes, bytearray)) or data[:1] != b"{":
        return None
    try:
        obj = json.loads(bytes(data))
    except ValueError:
        return None
    return obj if isinstance(obj, dict) and "role" in obj else None


def _texts(content) -> list[str]:
    """Spoken text only: a string, or `text` parts. Not tools or reasoning."""
    if isinstance(content, str) and content.strip():
        return [content]
    if not isinstance(content, list):
        return []
    return [
        str(p["text"])
        for p in content
        if isinstance(p, dict)
        and p.get("type") == "text"
        and str(p.get("text") or "").strip()
    ]


def _meta(con: sqlite3.Connection) -> dict | None:
    row = con.execute("SELECT value FROM meta LIMIT 1").fetchone()
    if row is None:
        return None
    value = row[0]
    if isinstance(value, (bytes, bytearray)):
        value = bytes(value).decode("utf-8", "replace")
    try:
        obj = json.loads(bytes.fromhex(str(value)).decode("utf-8"))
    except ValueError:
        try:
            obj = json.loads(str(value))
        except ValueError:
            return None
    if not isinstance(obj, dict) or not str(obj.get("agentId") or "").strip():
        return None
    return obj


def _in_order(blobs: dict[bytes, bytes], root_id: str) -> list[dict] | None:
    """The messages as the root links them, or None when it can't be read."""
    try:
        root = blobs[bytes.fromhex(root_id)]
    except (KeyError, ValueError):
        return None
    msgs: list[dict] = []
    seen = 0
    on_path = {bytes.fromhex(root_id)}
    try:
        stack = [(bytes.fromhex(root_id), iter(_links(root)))]
        while stack:
            owner, it = stack[-1]
            link = next(it, None)
            if link is None:
                stack.pop()
                on_path.discard(owner)
                continue
            data = blobs.get(link)
            if data is None:
                continue
            msg = _message(data)
            if msg is not None:
                msgs.append(msg)
                continue
            seen += 1
            if link in on_path or seen > MAX_NODES:
                return None
            on_path.add(link)
            stack.append((link, iter(_links(data))))
    except (ValueError, IndexError):
        return None
    return msgs or None


def _links(node: bytes) -> list[bytes]:
    return [v for f, v in fields_of(node) if f in LINK_FIELDS and len(v) == HASH]


def _started(ms) -> str:
    try:
        when = datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return ""
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def _line(text) -> str:
    return " ".join(str(text or "").split())


def chat_parts(path: Path) -> list[str] | None:
    """The chat as one text, or as parts when one would be too long for the
    kernel; None when this is not a Cursor chat store."""
    try:
        uri = path.resolve().as_uri() + "?mode=ro"
        con = sqlite3.connect(uri, uri=True)
    except sqlite3.Error:
        return None
    try:
        con.text_factory = bytes
        meta = _meta(con)
        if meta is None:
            return None
        rows = con.execute("SELECT id, data FROM blobs").fetchall()
    except (sqlite3.Error, ValueError):
        return None
    finally:
        con.close()
    blobs: dict[bytes, bytes] = {}
    sqlite_order: list[dict] = []
    for rid, data in rows:
        try:
            key = bytes.fromhex(bytes(rid).decode("ascii"))
        except (ValueError, TypeError):
            key = None
        if key is not None:
            blobs[key] = bytes(data) if data is not None else b""
        msg = _message(data)
        if msg is not None:
            sqlite_order.append(msg)
    ordered = _in_order(blobs, str(meta.get("latestRootBlobId") or ""))
    found = ordered is not None
    turns = []
    for msg in ordered if found else sqlite_order:
        who = ROLES.get(str(msg.get("role")))
        spoken = _texts(msg.get("content")) if who else []
        if spoken:
            turns.append((who, "\n".join(spoken).strip()))
    if not turns:
        return None
    head = [f"chat {_line(meta['agentId'])}"]
    for label, value in (
        ("name", _line(meta.get("name"))),
        ("started", _started(meta.get("createdAt"))),
        ("model", _line(meta.get("lastUsedModel"))),
    ):
        if value:
            head.append(f"{label}: {value}")
    if not found:
        head.append("order: not found in the store")
    head.append(f"{len(turns)} turns")
    blocks = [f"{n}  {who}\n{text}" for n, (who, text) in enumerate(turns, 1)]
    return _written(head, "\n\n", blocks)


def chat_text(path: Path) -> str | None:
    """The chat's text, or its first part if it is long."""
    got = chat_parts(path)
    return None if got is None else got[0]


def _sources(folder: Path) -> list[Path]:
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            if name == "store.db" and (Path(dirpath) / name).is_file():
                found.append(Path(dirpath) / name)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


# differs on purpose: chat_text skips what isn't a chat, so only OSError is left to catch
def mirror(src: Path, dst: Path) -> tuple[int, int]:
    wrote = skipped = 0
    for path in _sources(src):
        try:
            texts = chat_parts(path)
            if texts is None:
                skipped += 1
                continue
            rel = path.relative_to(src)
            _write_parts(dst.joinpath(rel.parent, rel.name + ".txt"), texts)
        except OSError:
            skipped += 1
            continue
        wrote += 1
    return wrote, skipped


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2])) if argv[:1] == ["mirror"] else {}
    if len(argv) != 5 or sorted(opts) != ["--from", "--to"]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    if not Path(opts["--from"]).is_dir():
        print(f"refused: not a folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    src, dst = Path(opts["--from"]).resolve(), Path(opts["--to"]).resolve()
    if _within(dst, src) or _within(src, dst):
        print(
            "refused: MIRROR and FOLDER must not be inside one another",
            file=sys.stderr,
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
