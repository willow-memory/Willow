r"""matrix.py: Element's room export, JSON: one dated line per message in each Matrix room. Python 3.9+.

    python adapters/stdlib/matrix/matrix.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .json files that are an Element room export, an object with a
`room_name` and a list of `messages` (hidden folders and files skipped; other
JSON skipped and counted), and writes each message, oldest first, as a dated
line:

    2024-03-02 08:15  Garden Club  @ana:example.org: Six hours of sun.
    2024-03-02 08:16  Garden Club  * @ben:example.org waves

The time is the message's origin_server_ts, in UTC. A plain message (m.text),
a notice and an emote are kept; a message with an empty body, and joins,
topic changes, reactions, redactions and other events, are left out. A room
with no name is named by its topic, else "(unnamed room)". Media files are not
copied; an image or file message is written as its description, as
"[image] name.png".

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import json
from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


def text(v: object) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def when(ms: object) -> str:
    if isinstance(ms, bool) or not isinstance(ms, (int, float)):
        return ""
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M"
        )
    except (OverflowError, OSError, ValueError):
        return ""


def line(msg: dict) -> str:
    content = msg.get("content") if isinstance(msg.get("content"), dict) else {}
    kind, body = text(content.get("msgtype")), text(content.get("body"))
    if msg.get("type") != "m.room.message" or not body:
        return ""
    who = text(msg.get("sender")) or "(unknown)"
    if kind == "m.emote":
        return f"* {who} {body}"
    if kind in ("m.image", "m.file", "m.video", "m.audio"):
        return f"{who}: [{kind[2:]}] {body}"
    return f"{who}: {body}"


def convert(data: bytes) -> str | None:
    doc = json.loads(data.decode("utf-8-sig"))
    if not (
        isinstance(doc, dict)
        and "room_name" in doc
        and isinstance(doc.get("messages"), list)
    ):
        return None
    room = text(doc.get("room_name")) or text(doc.get("topic")) or "(unnamed room)"
    rows = []
    for m in doc["messages"]:
        if not isinstance(m, dict) or not (said := line(m)):
            continue
        stamp = when(m.get("origin_server_ts"))
        rows.append((stamp, f"{stamp}  {room}  {said}" if stamp else f"{room}  {said}"))
    return (
        "\n".join(t for _s, t in sorted(rows, key=lambda r: r[0])) + "\n"
        if rows
        else None
    )


EXTS = (".json",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: matrix.py mirror --from FOLDER --to MIRROR"


def _sources(folder: Path) -> list[Path]:
    """Files under `folder` this reads, sorted by relative path. Hidden folders
    and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if not name.startswith(".") and name.lower().endswith(EXTS) and p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            text = convert(path.read_bytes())
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except ERRORS:
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
    src = Path(opts["--from"]).resolve()
    dst = Path(opts["--to"]).resolve()
    if _within(dst, src) or _within(src, dst):
        print(
            "refused: MIRROR and FOLDER must not be inside one another", file=sys.stderr
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
