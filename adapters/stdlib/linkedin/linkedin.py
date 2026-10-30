r"""linkedin.py: LinkedIn's data export: messages, posts and connections as dated lines. Python 3.9+.

    python adapters/stdlib/linkedin/linkedin.py mirror --from FOLDER --to MIRROR

Walks FOLDER for the CSV files of a LinkedIn data export (hidden folders and
files skipped; any other CSV skipped and counted) and reads four of them,
telling each by its header:

    messages.csv      CONVERSATION ID, FROM, TO, DATE, SUBJECT, CONTENT
    Connections.csv   First Name, Last Name, Company, Position, Connected On
    Shares.csv        Date, ShareCommentary, SharedUrl
    Comments.csv      Date, Link, Message

and writes their rows, oldest first, as dated lines:

    2024-03-02 08:15  message Ana Lopez -> Ben Ruiz: [Garden talk] Are you coming on Saturday?
    2024-03-03  connected with Ana Lopez (Gardener, Garden Co)
    2024-03-04  post: Planted out the tomatoes. https://example.org/guide
    2024-03-05  comment: Congratulations!

Connections.csv starts with a few lines of notes before its header; they are
skipped. Dates are read as LinkedIn writes them (2024-03-02 08:15:30 UTC,
02 Mar 2024). Email addresses, profile addresses and the files' other columns
are not copied.

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
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

FIRST = {"CONVERSATION ID", "First Name", "Date"}


def words(v: object) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def day(v: object) -> str:
    s = words(v)
    m = re.match(r"(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}:\d{2}))?", s)
    if m:
        return m.group(1) + (f" {m.group(2)}" if m.group(2) else "")
    try:
        return datetime.strptime(s, "%d %b %Y").strftime("%Y-%m-%d")
    except ValueError:
        return ""


def table(text: str) -> list[dict[str, str]]:
    """The CSV from its header on: the header is the first line that starts with a column a LinkedIn file opens with."""
    lines = text.replace("\r\n", "\n").split("\n")
    start = next(
        (i for i, ln in enumerate(lines) if ln.split(",")[0].strip('"') in FIRST), None
    )
    if start is None:
        return []
    return list(csv.DictReader(io.StringIO("\n".join(lines[start:]))))


def convert(data: bytes) -> str | None:
    rows_ = table(data.decode("utf-8-sig"))
    if not rows_:
        return None
    head = set(rows_[0])
    rows = []
    for r in rows_:
        if {"CONVERSATION ID", "CONTENT"} <= head:
            when, body = day(r.get("DATE")), words(r.get("CONTENT"))
            who = (
                f"{words(r.get('FROM'))} -> {words(r.get('TO'))}"
                if words(r.get("FROM"))
                else ""
            )
            subject = f"[{words(r['SUBJECT'])}] " if words(r.get("SUBJECT")) else ""
            line = (
                f"message {who}: {subject}{body}".replace("message : ", "message: ")
                if body
                else ""
            )
        elif {"First Name", "Connected On"} <= head:
            when = day(r.get("Connected On"))
            name = words(f"{r.get('First Name', '')} {r.get('Last Name', '')}")
            job = ", ".join(
                x for x in (words(r.get("Position")), words(r.get("Company"))) if x
            )
            line = (
                f"connected with {name}" + (f" ({job})" if job else "") if name else ""
            )
        elif {"Date", "ShareCommentary"} <= head:
            when = day(r.get("Date"))
            line = " ".join(
                x
                for x in (words(r.get("ShareCommentary")), words(r.get("SharedUrl")))
                if x
            )
            line = f"post: {line}" if line else ""
        elif {"Date", "Message"} <= head:
            when, line = (
                day(r.get("Date")),
                (
                    f"comment: {words(r.get('Message'))}"
                    if words(r.get("Message"))
                    else ""
                ),
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

USAGE = "usage: linkedin.py mirror --from FOLDER --to MIRROR"


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
