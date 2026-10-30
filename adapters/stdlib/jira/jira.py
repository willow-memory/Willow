r"""jira.py: Jira's issue export, CSV or XML: each issue and its comments as a dated passage. Python 3.9+.

    python adapters/stdlib/jira/jira.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .xml and .csv files that are a Jira issue export (the XML
export is an RSS file of `item`s with a `key`; the CSV export has `Summary` and
`Issue key` columns; hidden folders and files skipped; any other XML or CSV
skipped and counted) and writes each issue, oldest first:

    GARDEN-12 (Open, Bug) 2024-03-02 ana -> ben: Tomatoes want more sun [garden, urgent]
      The bed by the fence is shaded after noon.
      comment 2024-03-03 ben: Move them to bed 2.

An issue's line has its key, its status and type, the day it was created, who
reported it and who it is assigned to (when it says), its summary and its labels.
The description follows, whitespace collapsed and, in the XML, with its HTML
taken off as the kernel reads a page. Comments follow in the order the export
gives them. Dates are read from the XML's RFC 2822 form and the CSV's
`02/Mar/24 8:15 AM`. Attachments, links, sprints and custom fields are not
copied. A file that declares entities is not read.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import csv
import io
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

STAMP_CSV = ("%d/%b/%y %I:%M %p", "%d/%b/%Y %I:%M %p", "%d/%b/%y %H:%M")


def words(v: object) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def day_rfc(v: object) -> str:
    try:
        return parsedate_to_datetime(v).strftime("%Y-%m-%d")  # type: ignore[arg-type]
    except (TypeError, ValueError, IndexError):
        return ""


def day_csv(v: object) -> str:
    for fmt in STAMP_CSV:
        try:
            return datetime.strptime(words(v), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


def text_of(el: ET.Element | None) -> str:
    return words(kernel.html_text("".join(el.itertext()))) if el is not None else ""


def line(
    key: str,
    status: str,
    kind: str,
    day: str,
    who: str,
    summary: str,
    labels: list[str],
) -> str:
    inside = ", ".join(x for x in (status, kind) if x)
    out = key + (f" ({inside})" if inside else "")
    out += "".join(" " + x for x in (day, who + ":" if who else "") if x)
    return out + " " + summary + (f" [{', '.join(labels)}]" if labels else "")


def from_xml(data: bytes) -> list[tuple[str, str]]:
    root = ET.fromstring(data)
    rows = []
    for item in root.iter("item"):
        key = words(item.findtext("key"))
        if not key:
            continue
        reporter, assignee = (
            words(item.findtext("reporter")),
            words(item.findtext("assignee")),
        )
        who = reporter + (
            f" -> {assignee}" if assignee and assignee.lower() != "unassigned" else ""
        )
        day = day_rfc(item.findtext("created"))
        summary = (
            words(item.findtext("summary"))
            or words(item.findtext("title")).split("] ", 1)[-1]
        )
        labels = [words(lab.text) for lab in item.iter("label") if words(lab.text)]
        lines = [
            line(
                key,
                words(item.findtext("status")),
                words(item.findtext("type")),
                day,
                who,
                summary,
                labels,
            )
        ]
        if text_of(item.find("description")):
            lines.append("  " + text_of(item.find("description")))
        for c in item.iter("comment"):
            if text_of(c):
                lines.append(
                    f"  comment {day_rfc(c.get('created'))} {words(c.get('author'))}: {text_of(c)}".replace(
                        "comment  ", "comment "
                    )
                )
        rows.append((day, "\n".join(lines)))
    return rows


def from_csv(text: str) -> list[tuple[str, str]]:
    table = list(csv.reader(io.StringIO(text)))
    if not table or "Issue key" not in table[0] or "Summary" not in table[0]:
        return []
    head, rows = table[0], []

    def col(r: list[str], name: str) -> str:
        return (
            words(r[head.index(name)])
            if name in head and head.index(name) < len(r)
            else ""
        )

    for r in table[1:]:
        key = col(r, "Issue key")
        if not key:
            continue
        day = day_csv(col(r, "Created"))
        who = col(r, "Reporter") + (
            f" -> {col(r, 'Assignee')}" if col(r, "Assignee") else ""
        )
        labels = [
            words(r[i])
            for i, h in enumerate(head)
            if h == "Labels" and i < len(r) and words(r[i])
        ]
        lines = [
            line(
                key,
                col(r, "Status"),
                col(r, "Issue Type"),
                day,
                who,
                col(r, "Summary"),
                labels,
            )
        ]
        if col(r, "Description"):
            lines.append("  " + col(r, "Description"))
        for i, h in enumerate(head):
            if h == "Comment" and i < len(r) and r[i].strip():
                when, _, rest = r[i].partition(";")
                who_c, _, body = rest.partition(";")
                lines.append(
                    f"  comment {day_csv(when)} {words(who_c)}: {words(body)}".replace(
                        "comment  ", "comment "
                    )
                )
        rows.append((day, "\n".join(lines)))
    return rows


def convert(data: bytes) -> str | None:
    if b"<!ENTITY" in data[:100_000]:
        return None
    head = data[:2000].lstrip()
    rows = (
        from_xml(data) if head.startswith(b"<") else from_csv(data.decode("utf-8-sig"))
    )
    return (
        "\n\n".join(t for _d, t in sorted(rows, key=lambda r: r[0])) + "\n"
        if rows
        else None
    )


EXTS = (".xml", ".csv")
ERRORS = (OSError, UnicodeDecodeError, ValueError, ET.ParseError, csv.Error)

USAGE = "usage: jira.py mirror --from FOLDER --to MIRROR"


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
