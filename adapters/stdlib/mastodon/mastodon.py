r"""mastodon.py: A Mastodon or Pixelfed account archive's outbox: your posts as dated lines. Python 3.9+.

    python adapters/stdlib/mastodon/mastodon.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .json files that are an ActivityPub outbox, an object with a
list of `orderedItems` (a Mastodon or Pixelfed archive's outbox.json; hidden
folders and files skipped; other JSON skipped and counted), and writes each post
you made, oldest first, as a dated line:

    2024-03-02 08:15  Planted out the tomatoes today.
    2024-03-03 19:40  [cw: gardening] The slugs are winning. (reply)  [image: slug on a leaf]

The post's HTML is read as the kernel reads a page (tags out, entities read).
A content warning is kept in front, in brackets; a reply is marked; an
attachment's description (its alt text) is kept as [image: ...] or
[attachment: ...]. Boosts and likes (Announce and Like) are not your words and
are left out, as are polls' votes and the media files.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


def text(v: object) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def when(stamp: object) -> str:
    return (
        f"{stamp[:10]} {stamp[11:16]}".rstrip()
        if isinstance(stamp, str) and re.match(r"\d{4}-\d{2}-\d{2}", stamp)
        else ""
    )


def post(obj: dict) -> str:
    body = (
        text(kernel.html_text(obj["content"]))
        if isinstance(obj.get("content"), str)
        else ""
    )
    body = re.sub(r" ([.,;:!?)])", r"\1", body)
    warning = text(obj.get("summary"))
    parts = [
        f"[cw: {warning}]" if warning else "",
        body,
        "(reply)" if obj.get("inReplyTo") else "",
    ]
    for a in obj.get("attachment") if isinstance(obj.get("attachment"), list) else []:
        if isinstance(a, dict) and text(a.get("name")):
            kind = (
                "image"
                if text(a.get("mediaType")).startswith("image/")
                else "attachment"
            )
            parts.append(f"[{kind}: {text(a['name'])}]")
    return (
        " ".join(p for p in parts[:3] if p) + "".join("  " + p for p in parts[3:])
    ).strip()


def convert(data: bytes) -> str | None:
    doc = json.loads(data.decode("utf-8-sig"))
    if not (isinstance(doc, dict) and isinstance(doc.get("orderedItems"), list)):
        return None
    rows = []
    for item in doc["orderedItems"]:
        obj = item.get("object") if isinstance(item, dict) else None
        if not (
            isinstance(item, dict)
            and item.get("type") == "Create"
            and isinstance(obj, dict)
        ):
            continue
        line = post(obj)
        if line:
            stamp = item.get("published") or obj.get("published")
            rows.append(
                (when(stamp), f"{when(stamp)}  {line}" if when(stamp) else line)
            )
    return (
        "\n".join(t for _d, t in sorted(rows, key=lambda r: r[0])) + "\n"
        if rows
        else None
    )


EXTS = (".json",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: mastodon.py mirror --from FOLDER --to MIRROR"


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
