r"""notion.py: Notion's export zip, Markdown and CSV, as plain text with each page's title and path. Python 3.9+.

    python adapters/stdlib/notion/notion.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .zip files that are a Notion export (a zip whose pages are
named `Title <32 hex digits>.md`; hidden folders and files skipped; any other
zip skipped and counted) and writes each page and each database:

    page: Garden / Veg / Tomato notes

    Created: March 2, 2024 8:15 AM
    Plant out after the last frost.

    table: Garden / Seed orders
    Name | Qty | Supplier
    Basil | 3 | Seeds Ltd

The export is read as the zip it is, without unpacking it to disk, and a zip
nested inside it (large exports come in parts) is read too. The path is the
page's folders and title with Notion's 32-digit ids taken off, joined with
" / ". A page's first heading is its title and is not repeated; the Markdown
is otherwise kept as written. A database CSV keeps its header and rows, cells
joined with " | ". Images and other files are not copied. A member over 5 MB
is left out.

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
import zipfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

BIGGEST = 5 * 1024 * 1024
NESTED = 50 * 1024 * 1024
MEMBERS = 20_000
ID = re.compile(r" ?[0-9a-f]{32}(?=\.|/|_all|$)")
PAGE = re.compile(r"[0-9a-f]{32}\.(?:md|csv)$", re.I)


def title_path(name: str) -> str:
    """A member's path without Notion's ids and extension, parts joined with ' / '."""
    parts = [ID.sub("", p) for p in name.split("/") if p]
    if parts:
        parts[-1] = re.sub(r"\.(?:md|csv)$", "", parts[-1])
        if parts[-1].endswith("_all"):
            parts[-1] = parts[-1][: -len("_all")]
    return (
        " / ".join(p for p in parts[1:] if p)
        if len(parts) > 1 and parts[0].startswith("Export-")
        else " / ".join(p for p in parts if p)
    )


def page(path: str, body: str) -> str:
    lines = body.replace("\r\n", "\n").split("\n")
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    text = "\n".join(lines).strip("\n")
    return f"page: {title_path(path)}" + ("\n\n" + text if text.strip() else "")


def table(path: str, body: str) -> str:
    rows = [
        " | ".join(" ".join(c.split()) for c in r)
        for r in csv.reader(io.StringIO(body))
        if any(c.strip() for c in r)
    ]
    return f"table: {title_path(path)}" + ("\n" + "\n".join(rows) if rows else "")


def walk(z: zipfile.ZipFile, depth: int = 0) -> list[tuple[str, str]]:
    out = []
    infos = z.infolist()
    if len(infos) > MEMBERS:
        return out
    for info in sorted(infos, key=lambda i: i.filename):
        name = info.filename
        if name.lower().endswith(".zip") and depth == 0 and info.file_size <= NESTED:
            with zipfile.ZipFile(io.BytesIO(z.read(info))) as inner:
                out += walk(inner, 1)
        elif PAGE.search(name) and info.file_size <= BIGGEST:
            body = z.read(info).decode("utf-8-sig", errors="replace")
            out.append(
                (
                    name,
                    table(name, body)
                    if name.lower().endswith(".csv")
                    else page(name, body),
                )
            )
    return out


def convert(data: bytes) -> str | None:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        items = walk(z)
    return "\n\n".join(t for _n, t in items) + "\n" if items else None


EXTS = (".zip",)
ERRORS = (
    OSError,
    UnicodeDecodeError,
    ValueError,
    zipfile.BadZipFile,
    RuntimeError,
    csv.Error,
)

USAGE = "usage: notion.py mirror --from FOLDER --to MIRROR"


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
