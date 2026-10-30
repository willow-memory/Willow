r"""google_keep.py: Google Keep notes from Takeout: notes, lists and labels. Python 3.9+.

    python adapters/stdlib/google-keep/google_keep.py mirror --from FOLDER --to MIRROR

Takeout gives one JSON file for each note. This walks FOLDER for .json files
that are a Keep note (hidden folders and files skipped; any other JSON, and a
note in the bin, skipped and counted) and writes each as:

    note: Shopping (2024-03-02)
    labels: home, food

    [ ] milk
    [x] eggs

The day is when the note was created (in UTC). A text note keeps its text; a
list keeps each item with a tick for the ones done. A note's title is its
`title`, or "(untitled)". Pinned, archived and colour are not copied, nor are
attachments.

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


def day(usec: object) -> str:
    """The UTC day of a Keep timestamp in microseconds, or "" when it isn't one."""
    if isinstance(usec, bool) or not isinstance(usec, int):
        return ""
    try:
        return datetime.fromtimestamp(usec / 1_000_000, tz=timezone.utc).strftime(
            "%Y-%m-%d"
        )
    except (OverflowError, OSError, ValueError):
        return ""


def convert(data: bytes) -> str | None:
    note = json.loads(data.decode("utf-8-sig"))
    if not (
        isinstance(note, dict)
        and "userEditedTimestampUsec" in note
        and ("textContent" in note or "listContent" in note)
    ):
        return None
    if note.get("isTrashed") is True:
        return None
    title = (
        note.get("title")
        if isinstance(note.get("title"), str) and note["title"].strip()
        else "(untitled)"
    )
    when = day(note.get("createdTimestampUsec")) or day(
        note.get("userEditedTimestampUsec")
    )
    lines = [f"note: {title.strip()}" + (f" ({when})" if when else "")]
    labels = [
        lab["name"]
        for lab in note.get("labels", [])
        if isinstance(lab, dict) and isinstance(lab.get("name"), str) and lab["name"]
    ]
    if labels:
        lines.append("labels: " + ", ".join(labels))
    body = []
    if isinstance(note.get("textContent"), str) and note["textContent"].strip():
        body.append(note["textContent"].strip())
    for item in (
        note.get("listContent", []) if isinstance(note.get("listContent"), list) else []
    ):
        if (
            isinstance(item, dict)
            and isinstance(item.get("text"), str)
            and item["text"].strip()
        ):
            body.append(
                f"[{'x' if item.get('isChecked') is True else ' '}] {item['text'].strip()}"
            )
    if not body and title == "(untitled)":
        return None
    return "\n".join(lines) + ("\n\n" + "\n".join(body) if body else "") + "\n"


EXTS = (".json",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: google_keep.py mirror --from FOLDER --to MIRROR"


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
