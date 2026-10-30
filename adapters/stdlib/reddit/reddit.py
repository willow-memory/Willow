r"""reddit.py: Reddit's data export: your posts, comments and saved items as dated lines. Python 3.9+.

    python adapters/stdlib/reddit/reddit.py mirror --from FOLDER --to MIRROR

Walks FOLDER for the CSV files of a Reddit data request (hidden folders and files
skipped; any other CSV skipped and counted) and reads three kinds, told by their
headers, writing their rows oldest first as dated lines:

    2024-03-02 08:15  r/gardening post: Tomatoes want more sun: The bed by the fence is shaded.
    2024-03-03 19:40  r/gardening comment: Move them to bed 2.
    saved https://www.reddit.com/r/gardening/comments/abc/tomatoes/

Posts (`posts.csv`: title and body), comments (`comments.csv`: body) and saved
posts and comments (`saved_posts.csv`, `saved_comments.csv`: a permalink only,
so without a date). Times are UTC as Reddit writes them. IP addresses, vote and
gilding data and the other files of the request are not copied.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import csv
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


def words(v: object) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def day(v: object) -> str:
    m = re.match(r"(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}:\d{2}))?", words(v))
    return m.group(1) + (f" {m.group(2)}" if m.group(2) else "") if m else ""


def convert(data: bytes) -> str | None:
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    head = set(reader.fieldnames or [])
    rows = []
    for r in reader:
        where = f"r/{words(r.get('subreddit'))} " if words(r.get("subreddit")) else ""
        if {"id", "permalink", "date", "title"} <= head:
            body = ": ".join(
                x for x in (words(r.get("title")), words(r.get("body"))) if x
            )
            line, when = f"{where}post: {body}" if body else "", day(r.get("date"))
        elif {"id", "permalink", "date", "body"} <= head:
            line, when = (
                (
                    f"{where}comment: {words(r.get('body'))}"
                    if words(r.get("body"))
                    else ""
                ),
                day(r.get("date")),
            )
        elif head == {"id", "permalink"}:
            line, when = (
                (
                    f"saved {words(r.get('permalink'))}"
                    if words(r.get("permalink"))
                    else ""
                ),
                "",
            )
        else:
            return None
        if line:
            rows.append((when, f"{when}  {line}" if when else line))
    return (
        "\n".join(t for _w, t in sorted(rows, key=lambda r: r[0])) + "\n"
        if rows
        else None
    )


EXTS = (".csv",)
ERRORS = (OSError, UnicodeDecodeError, ValueError, csv.Error)

USAGE = "usage: reddit.py mirror --from FOLDER --to MIRROR"


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
