r"""joplin.py: Joplin's .jex export as plain text, note by note. Python 3.9+.

    python adapters/stdlib/joplin/joplin.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .jex files (hidden folders and files skipped) and reads each
as the tar archive it is, without unpacking it to disk. Every note in it is
written with its title, its notebook path and its dates, then its text:

    note: Tomato notes
    notebook: Garden/Veg
    created: 2024-03-02; updated: 2024-03-05

    Plant out after the last frost.

The notebook path is built from the notebooks' own parents. Notes in the trash,
the metadata Joplin writes under each note, tags, pictures and other resources
are left out. Notes come in the order of their names in the archive. A file
that is not a tar archive is skipped and counted. A member over 5 MB is left out.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import io
import re
import tarfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

BIGGEST = 5 * 1024 * 1024  # bytes of one member read
META = re.compile(r"^([a-z_]+): ?(.*)$")


def split(text: str) -> tuple[str, str, dict[str, str]]:
    """(title, body, metadata) of a Joplin item: the first line is the title, and
    the trailing block of `key: value` lines after the last blank line is metadata."""
    lines = text.replace("\r\n", "\n").split("\n")
    meta: dict[str, str] = {}
    end = len(lines)
    while end and not lines[end - 1].strip():
        end -= 1
    start = end
    while start and META.match(lines[start - 1]):
        start -= 1
        m = META.match(lines[start])
        meta.setdefault(m.group(1), m.group(2))
    body_lines = lines[:start]
    title = body_lines[0].strip() if body_lines else ""
    body = "\n".join(body_lines[1:]).strip()
    return title, body, meta


def day(stamp: str) -> str:
    return stamp[:10] if re.match(r"\d{4}-\d{2}-\d{2}", stamp) else ""


def path_of(folders: dict[str, tuple[str, str]], ref: str) -> str:
    names, seen = [], set()
    while ref in folders and ref not in seen:
        seen.add(ref)
        title, ref = folders[ref]
        names.append(title)
    return "/".join(reversed(names))


def convert(data: bytes) -> str | None:
    items = []
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        for member in sorted(
            (m for m in tar.getmembers() if m.isfile() and m.name.endswith(".md")),
            key=lambda m: m.name,
        ):
            if member.size > BIGGEST:
                continue
            raw = tar.extractfile(member)
            if raw is not None:
                items.append(split(raw.read().decode("utf-8", errors="replace")))
    folders = {
        m["id"]: (t, m.get("parent_id", ""))
        for t, _b, m in items
        if m.get("type_") == "2" and m.get("id")
    }
    blocks = []
    for title, body, meta in items:
        if meta.get("type_") != "1" or meta.get("deleted_time", "0") not in ("0", ""):
            continue
        head = [f"note: {title}"]
        where = path_of(folders, meta.get("parent_id", ""))
        if where:
            head.append(f"notebook: {where}")
        dates = [
            f"{k}: {day(meta.get(f'{k}_time', ''))}"
            for k in ("created", "updated")
            if day(meta.get(f"{k}_time", ""))
        ]
        if dates:
            head.append("; ".join(dates))
        blocks.append("\n".join(head) + ("\n\n" + body if body else ""))
    return "\n\n".join(blocks) + "\n" if blocks else None


EXTS = (".jex",)
ERRORS = (OSError, UnicodeDecodeError, ValueError, tarfile.TarError)

USAGE = "usage: joplin.py mirror --from FOLDER --to MIRROR"


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
