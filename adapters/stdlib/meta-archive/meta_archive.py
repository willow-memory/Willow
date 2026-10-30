r"""meta_archive.py: Facebook and Instagram's Download Your Information files: posts, comments and messages. Python 3.9+.

    python adapters/stdlib/meta-archive/meta_archive.py mirror --from FOLDER --to MIRROR

Walks FOLDER for the JSON files of a Download Your Information export (hidden
folders and files skipped; any other JSON skipped and counted) and writes the
three kinds that are your words, oldest first, as dated lines:

    2024-03-02 08:15  Garden chat (Ana, Ben)  Ana: Six hours of sun.
    2024-03-02 09:00  post: Planted out the tomatoes.
    2024-03-03 19:40  comment: The slugs are winning.

Messages (message_1.json: an object with `participants` and `messages`) are
written with the conversation's title, or its participants if it has none, and
who sent each one. Posts (your_posts_1.json: a list with `timestamp` and
`data[].post`) and comments (an object with a list of `timestamp` and
`data[].comment.comment`) are written as "post" and "comment". The export writes
its text as UTF-8 read as Latin-1, so an accented letter arrives garbled
("Ã©" for "é"); that is undone where it can be. Times are UTC. Photos, videos,
reactions and the other fields are not copied.

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


def fix(s: object) -> str:
    """Text as the export garbles it (UTF-8 read as Latin-1), put right when it can be."""
    if not isinstance(s, str):
        return ""
    try:
        s = s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return " ".join(s.split())


def when(ts: object, ms: bool = False) -> str:
    if isinstance(ts, bool) or not isinstance(ts, (int, float)):
        return ""
    try:
        return datetime.fromtimestamp(
            ts / (1000 if ms else 1), tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M")
    except (OverflowError, OSError, ValueError):
        return ""


def messages(doc: dict) -> list[tuple[str, str]]:
    names = (
        [
            fix(p.get("name"))
            for p in doc.get("participants", [])
            if isinstance(p, dict) and fix(p.get("name"))
        ]
        if isinstance(doc.get("participants"), list)
        else []
    )
    title = fix(doc.get("title")) or ", ".join(names)
    label = (
        f"{title} ({', '.join(names)})"
        if title and names and title not in names and ", ".join(names) != title
        else title
    )
    rows = []
    for m in doc["messages"]:
        if isinstance(m, dict) and fix(m.get("content")):
            stamp = when(m.get("timestamp_ms"), ms=True)
            line = f"{label}  {fix(m.get('sender_name')) or '(unknown)'}: {fix(m['content'])}".strip()
            rows.append((stamp, f"{stamp}  {line}" if stamp else line))
    return rows


def entries(items: list, kind: str) -> list[tuple[str, str]]:
    rows = []
    for i in items:
        if not isinstance(i, dict):
            continue
        for d in i.get("data", []) if isinstance(i.get("data"), list) else []:
            if not isinstance(d, dict):
                continue
            inner = d.get("comment")
            body = (
                fix(inner.get("comment"))
                if isinstance(inner, dict) and kind == "comment"
                else fix(d.get("post"))
                if kind == "post"
                else ""
            )
            if body:
                stamp = when(i.get("timestamp"))
                rows.append(
                    (stamp, f"{stamp}  {kind}: {body}" if stamp else f"{kind}: {body}")
                )
    return rows


def convert(data: bytes) -> str | None:
    doc = json.loads(data.decode("utf-8-sig"))
    rows: list[tuple[str, str]] = []
    if (
        isinstance(doc, dict)
        and isinstance(doc.get("messages"), list)
        and isinstance(doc.get("participants"), list)
    ):
        rows = messages(doc)
    elif isinstance(doc, list) and any(
        isinstance(i, dict) and "timestamp" in i and "data" in i for i in doc
    ):
        rows = entries(doc, "post")
    elif isinstance(doc, dict):
        for key, value in doc.items():
            if key.startswith("comments") and isinstance(value, list):
                rows += entries(value, "comment")
    return (
        "\n".join(t for _s, t in sorted(rows, key=lambda r: r[0])) + "\n"
        if rows
        else None
    )


EXTS = (".json",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: meta_archive.py mirror --from FOLDER --to MIRROR"


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
