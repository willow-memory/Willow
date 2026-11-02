r"""pocket.py: Pocket's export as one dated line per saved article. Python 3.9+.

    python adapters/stdlib/pocket/pocket.py mirror --from FOLDER --to MIRROR

Pocket closed in 2025; what is left of it is the export. This reads both of
its shapes, recognised by what they hold, never by their names:

- the older `ril_export.html`: an `<h1>Unread</h1>` and an `<h1>Read
  Archive</h1>`, each over a list of `<a href=... time_added=... tags=...>`;
- the 2025 CSV (`part_000000.csv` and on), whose header is exactly
  `title,url,time_added,tags,status`, tags joined by `|`.

Each saved article is one line, the day it was saved (UTC) first:

    2024-03-02 saved: How to keep a sourdough starter <https://example.org/s> [baking, bread] (archived)

A title that is blank or is the address itself is written as just the address.
Tags are left out when there are none, the status (unread, or archived for
Pocket's "archive", "read" and "Read Archive") when the export gives none, and
an article with no time_added is "(no date) saved:".

Each line is a paragraph of its own, a blank line between, so the kernel's
`chunks` makes each article one passage: "when did I save that article about
sourdough" is held by that one line (its "saved" and "sourdough"), served with
its own date, never in a run of other articles' titles. The lines go oldest
first, undated ones at the top, because the kernel dates a passage by the
latest date at or above it in its file: newest first, every article would wear
the newest one's date.

A .zip (Pocket emailed `pocket.zip`) is read without unpacking it: every Pocket
CSV or HTML file in it, hidden members and `__MACOSX` left out, goes into one
mirror, `<zip path>.txt`, so there is still one .txt per file read. Loose .csv
and .html files are read too. Pocket's annotations file in the zip is left
alone: its shape is not documented anywhere this could check.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file that is not Pocket's is left alone and not
counted; one that cannot be read, or is Pocket's with no articles, is skipped
and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import csv
import io
import os
import sys
import zipfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

HEADER = ["title", "url", "time_added", "tags", "status"]
STATUS = {"unread": "unread", "archive": "archived", "read": "archived"}
SECTIONS = {"unread": "unread", "read archive": "archived"}
BIGGEST = 64 * 1024 * 1024  # bytes of one zip member read


class NotPocket(Exception):
    """A file that is not Pocket's export: left alone, not counted."""


def day(stamp: str) -> str:
    """The UTC day of a Unix time, or "" when it isn't one."""
    try:
        t = int(stamp.strip())
        return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d")
    except (ValueError, OverflowError, OSError):
        return ""


def line(title: str, url: str, stamp: str, tags: list[str], status: str) -> str:
    title, url = " ".join(title.split()), url.strip()
    what = url if not title or title == url else f"{title} <{url}>" if url else title
    out = f"{day(stamp) or '(no date)'} saved: {what}"
    kept = [t for t in (" ".join(t.split()) for t in tags) if t]
    if kept:
        out += f" [{', '.join(kept)}]"
    return out + (f" ({status})" if status else "")


def from_csv(text: str) -> list[tuple[str, str]]:
    """(day, line) for each row of a 2025 export CSV."""
    rows = csv.reader(io.StringIO(text.lstrip("﻿"), newline=""))
    if next(rows, None) != HEADER:
        raise NotPocket
    out = []
    for row in rows:
        title, url, stamp, tags, status = (row + [""] * 5)[:5]
        if not (title.strip() or url.strip()):
            continue
        s = status.strip()
        out.append(
            (
                day(stamp),
                line(title, url, stamp, tags.split("|"), STATUS.get(s.lower(), s)),
            )
        )
    return out


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.items: list[tuple[str, str]] = []
        self.sections: set[str] = set()
        self.status = ""
        self.h1: list[str] | None = None
        self.a: tuple[dict, list[str]] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "h1":
            self.h1 = []
        elif tag == "a":
            self.a = ({k: v or "" for k, v in attrs}, [])

    def handle_endtag(self, tag):
        if tag == "h1" and self.h1 is not None:
            name = " ".join("".join(self.h1).split()).lower()
            self.h1 = None
            self.status = SECTIONS.get(name, "")
            if name in SECTIONS:
                self.sections.add(name)
        elif tag == "a" and self.a is not None:
            attrs, text = self.a
            self.a = None
            if "time_added" in attrs and self.sections:
                url, stamp = attrs.get("href", ""), attrs["time_added"]
                tags = attrs.get("tags", "").split(",")
                title = "".join(text)
                if title.strip() or url.strip():
                    self.items.append(
                        (day(stamp), line(title, url, stamp, tags, self.status))
                    )

    def handle_data(self, data):
        if self.h1 is not None:
            self.h1.append(data)
        if self.a is not None:
            self.a[1].append(data)


def from_html(text: str) -> list[tuple[str, str]]:
    """(day, line) for each link of a ril_export.html."""
    parser = _Links()
    parser.feed(text)
    parser.close()
    if not parser.sections or "time_added=" not in text:
        raise NotPocket
    return parser.items


def read_one(name: str, data: bytes) -> list[tuple[str, str]]:
    text = data.decode("utf-8-sig")
    if name.lower().endswith(".csv"):
        return from_csv(text)
    return from_html(text)


def hidden(member: str) -> bool:
    return any(p.startswith(".") or p == "__MACOSX" for p in member.split("/"))


def read_zip(data: bytes) -> list[tuple[str, str]]:
    out, found = [], False
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in sorted(z.infolist(), key=lambda i: i.filename):
            name = info.filename
            if info.is_dir() or hidden(name) or not name.lower().endswith(MEMBERS):
                continue
            if info.file_size > BIGGEST:
                continue
            try:
                out += read_one(name, z.read(info))
                found = True
            except (NotPocket, UnicodeDecodeError, csv.Error):
                continue
    if not found:
        raise NotPocket
    return out


def convert(name: str, data: bytes) -> str | None:
    """The mirror of one file: its articles oldest first, a blank line between,
    or None for a Pocket export with none. Raises NotPocket for another file."""
    items = read_zip(data) if name.lower().endswith(".zip") else read_one(name, data)
    if not items:
        return None
    items = sorted(items, key=lambda it: it[0])  # stable: same day, export order
    return "\n\n".join(text for _, text in items) + "\n"


MEMBERS = (".csv", ".html", ".htm")
EXTS = MEMBERS + (".zip",)
ERRORS = (OSError, UnicodeDecodeError, ValueError, csv.Error, zipfile.BadZipFile)

USAGE = "usage: pocket.py mirror --from FOLDER --to MIRROR"


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
            text = convert(path.name, path.read_bytes())
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except NotPocket:
            continue
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
