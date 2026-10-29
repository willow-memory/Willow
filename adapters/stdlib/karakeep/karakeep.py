r"""karakeep.py: Karakeep's JSON export: bookmarks, notes and tags as plain text. Python 3.9+.

    python adapters/stdlib/karakeep/karakeep.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .json files that are a Karakeep (formerly Hoarder) export, an
object with a `bookmarks` list (hidden folders and files skipped; other JSON
skipped and counted), and writes each bookmark, oldest first:

    2024-03-02  Tomato growing guide
    url: https://example.org/tomatoes
    tags: garden, veg
    note: Read the section on staking.
    summary: How to grow tomatoes in a small bed.

    The page's own description, or the text of a text bookmark.

The day is when the bookmark was created (a Unix time in seconds or
milliseconds, or an ISO date). A link keeps its URL, title and description; a
text bookmark keeps its text. The tags, your note and Karakeep's summary are
kept as words. Archived and favourite marks, images and the page's saved copy
are not.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import json
import re
from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


def day(value: object) -> str:
    """The UTC day of a created time: Unix seconds or milliseconds, or an ISO date."""
    if isinstance(value, str) and re.match(r"\d{4}-\d{2}-\d{2}", value):
        return value[:10]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return ""
    seconds = value / 1000 if value > 100_000_000_000 else value
    try:
        return datetime.fromtimestamp(seconds, tz=timezone.utc).strftime("%Y-%m-%d")
    except (OverflowError, OSError, ValueError):
        return ""


def words(v: object) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def convert(data: bytes) -> str | None:
    doc = json.loads(data.decode("utf-8-sig"))
    if not (isinstance(doc, dict) and isinstance(doc.get("bookmarks"), list)):
        return None
    rows = []
    for b in doc["bookmarks"]:
        if not isinstance(b, dict):
            continue
        content = b.get("content") if isinstance(b.get("content"), dict) else {}
        title = words(b.get("title")) or words(content.get("title"))
        url = words(content.get("url"))
        body = (
            words(content.get("text"))
            if content.get("type") == "text"
            else words(content.get("description"))
        )
        tags = [
            t
            if isinstance(t, str)
            else t.get("name", "")
            if isinstance(t, dict)
            else ""
            for t in (b.get("tags") if isinstance(b.get("tags"), list) else [])
        ]
        head = "  ".join(x for x in (day(b.get("createdAt")), title) if x)
        lines = [head or "(untitled bookmark)"]
        for label, value in (
            ("url", url),
            ("tags", ", ".join(t for t in tags if t)),
            ("note", words(b.get("note"))),
            ("summary", words(b.get("summary"))),
        ):
            if value:
                lines.append(f"{label}: {value}")
        if not (title or url or body):
            continue
        rows.append(
            (
                day(b.get("createdAt")),
                "\n".join(lines) + ("\n\n" + body if body else ""),
            )
        )
    return (
        "\n\n".join(t for _d, t in sorted(rows, key=lambda r: r[0])) + "\n"
        if rows
        else None
    )


EXTS = (".json",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: karakeep.py mirror --from FOLDER --to MIRROR"


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
