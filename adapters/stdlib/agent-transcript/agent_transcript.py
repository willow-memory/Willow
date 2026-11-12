"""agent_transcript.py: agent session files as numbered turns. Python 3.9+.

    python adapters/stdlib/agent-transcript/agent_transcript.py \\
        mirror --from FOLDER --to MIRROR

Walks FOLDER for `.jsonl` session files (Claude Code, Cursor, and others
that store one JSON object a line with a user or assistant message). Each
file becomes numbered turns of what you said and what the assistant said,
so the kernel can ask what an agent was told. Tool calls, tool results and
hidden thinking are left out: those are not what you were told.

    session f601db41-9cd9-44dd-9fee-6e7494413255
    started: 2026-10-31T09:00:00.000Z
    ended: 2026-10-31T09:00:05.000Z
    2 turns

    1  you
    When is the dentist?

    2  assistant
    Tuesday at 3.

When it ran is read from the file, never from the file's modification time
(which says when a file changed, not when a session ran). A line with an
ISO `timestamp` gives `started:` (the earliest) and `ended:` (the latest);
a line whose timestamp is not ISO is ignored. A file with none but a
`<timestamp>...</timestamp>` tag in a user turn (Cursor writes one) gives
`started: <the tag's text> (from the text)` and no `ended:`. A file with
neither says `time: not in the file`.

Each session is written to MIRROR at the same relative path with `.txt`
added. One too long for the kernel to read (over PART bytes) is written in
parts, `X.txt`, `X.2.txt`, and so on, cut between turns; each part has the
header and `part N of M`, and the turn numbers go on across parts. A file that is not a session (not JSONL, or no turns) is skipped
and counted. Hidden folders and files are skipped.

    wrote 2 files to MIRROR; skipped 1

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: agent_transcript.py mirror --from FOLDER --to MIRROR"


_ISO = re.compile(
    r"(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,9}))?"
    r"(Z|[+-]\d{2}:\d{2})?"
)
_TAG = re.compile(r"<timestamp>\s*(.*?)\s*</timestamp>", re.DOTALL)


def _instant(value) -> datetime | None:
    """An ISO timestamp as a moment, or None if it is not one."""
    if not isinstance(value, str):
        return None
    m = _ISO.fullmatch(value.strip())
    if m is None:
        return None
    y, mo, d, h, mi, sec, frac, zone = m.groups()
    try:
        when = datetime(int(y), int(mo), int(d), int(h), int(mi), int(sec))
        when += timedelta(microseconds=int((frac or "0")[:6].ljust(6, "0")))
        if zone and zone != "Z":
            off = timedelta(hours=int(zone[1:3]), minutes=int(zone[4:6]))
            return when.replace(tzinfo=timezone(-off if zone[0] == "-" else off))
    except (ValueError, OverflowError):
        return None
    return when.replace(tzinfo=timezone.utc)


def _texts(content) -> list[str]:
    """Spoken text only: a string, or `text` parts. Not tools or thinking."""
    if isinstance(content, str) and content.strip():
        return [content]
    if not isinstance(content, list):
        return []
    out = []
    for part in content:
        if (
            isinstance(part, dict)
            and part.get("type") == "text"
            and str(part.get("text") or "").strip()
        ):
            out.append(str(part["text"]))
    return out


def _who(obj: dict, msg: dict) -> str | None:
    role = str(msg.get("role") or obj.get("role") or "")
    typ = str(obj.get("type") or "")
    if role == "user" or typ == "user":
        return "you"
    if role == "assistant" or typ == "assistant":
        return "assistant"
    return None


def turns_of(raw: bytes) -> tuple[str, list[tuple[str, str]], list[str]] | None:
    """(session id, [(who, text), ...], time lines) or None if not a session."""
    sid, turns = "", []
    first = last = None  # (moment, the text as the file has it)
    tagged = ""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            return None
        if not isinstance(obj, dict):
            return None
        sid = sid or str(obj.get("sessionId") or obj.get("session_id") or "")
        when = _instant(obj.get("timestamp"))
        if when is not None:
            stamp = (when, obj["timestamp"].strip())
            first = stamp if first is None or when < first[0] else first
            last = stamp if last is None or when >= last[0] else last
        msg = obj.get("message")
        if not isinstance(msg, dict):
            continue
        who = _who(obj, msg)
        if who is None:
            continue
        spoken = _texts(msg.get("content"))
        if not spoken:
            continue
        said = "\n".join(spoken).strip()
        if who == "you" and not tagged:
            found = _TAG.search(said)
            tagged = found.group(1) if found else ""
        turns.append((who, said))
    if not turns:
        return None
    if first is not None and last is not None:
        when = [f"started: {first[1]}", f"ended: {last[1]}"]
    elif tagged:
        when = [f"started: {tagged} (from the text)"]
    else:
        when = ["time: not in the file"]
    return sid, turns, when


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


def session_parts(raw: bytes) -> list[str] | None:
    """The session as one text, or as parts when one would be too long for
    the kernel; None if it is not a session."""
    got = turns_of(raw)
    if got is None:
        return None
    sid, turns, when = got
    head = ([f"session {sid}"] if sid else []) + when + [f"{len(turns)} turns"]
    blocks = [f"{n}  {who}\n{text}" for n, (who, text) in enumerate(turns, 1)]
    return _written(head, "\n\n\n", blocks)


def session_text(raw: bytes) -> str | None:
    """The session's text, or its first part if it is long."""
    got = session_parts(raw)
    return None if got is None else got[0]


def _sources(folder: Path) -> list[Path]:
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            if name.startswith(".") or not name.endswith(".jsonl"):
                continue
            p = Path(dirpath) / name
            if p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


# differs on purpose: session_text skips what isn't a session, so only OSError is left to catch
def mirror(src: Path, dst: Path) -> tuple[int, int]:
    wrote = skipped = 0
    for path in _sources(src):
        try:
            texts = session_parts(path.read_bytes())
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
