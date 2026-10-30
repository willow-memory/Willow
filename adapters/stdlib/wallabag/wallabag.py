r"""wallabag.py: wallabag's JSON export: saved entries as plain text, with their tags. Python 3.9+.

    python adapters/stdlib/wallabag/wallabag.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .json files that are a wallabag export, a list of entries each
with a `url` and a `content` (hidden folders and files skipped; any other JSON
skipped and counted), and writes each entry, oldest first, by the day it was
saved:

    2024-03-02  Tomato growing guide
    url: https://example.org/tomatoes
    tags: garden, veg
    highlight: "Stake early." (note: do this in April)

    The article's text, with its tags and markup taken off.

The article is wallabag's saved HTML, read as the kernel reads a page (scripts,
styles and tags out, entities read). Your annotations are kept as highlights with
the note you wrote on them. The reading time, language and archived or starred
marks are not copied.

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

BLOCK = re.compile(r"</(?:p|div|li|h[1-6]|tr|blockquote|pre)>|<br\s*/?>", re.I)


TIGHT = re.compile(
    r" ([.,;:!?)])|(\() "
)  # a tag beside a full stop or a bracket leaves a space


def words(v: object) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def day(v: object) -> str:
    return v[:10] if isinstance(v, str) and re.match(r"\d{4}-\d{2}-\d{2}", v) else ""


def is_entry(e: object) -> bool:
    return (
        isinstance(e, dict)
        and isinstance(e.get("url"), str)
        and isinstance(e.get("content"), str)
    )


def convert(data: bytes) -> str | None:
    doc = json.loads(data.decode("utf-8-sig"))
    if not (isinstance(doc, list) and any(is_entry(e) for e in doc)):
        return None
    rows = []
    for e in doc:
        if not is_entry(e):
            continue
        head = "  ".join(
            x for x in (day(e.get("created_at")), words(e.get("title"))) if x
        ) or words(e["url"])
        tags = [
            t
            if isinstance(t, str)
            else t.get("label", "")
            if isinstance(t, dict)
            else ""
            for t in (e.get("tags") if isinstance(e.get("tags"), list) else [])
        ]
        lines = [head]
        if words(e["url"]):
            lines.append(f"url: {words(e['url'])}")
        if any(tags):
            lines.append("tags: " + ", ".join(t for t in tags if t))
        for a in (
            e.get("annotations", []) if isinstance(e.get("annotations"), list) else []
        ):
            if isinstance(a, dict) and (words(a.get("quote")) or words(a.get("text"))):
                quote = f'"{words(a.get("quote"))}"' if words(a.get("quote")) else ""
                note = f"(note: {words(a.get('text'))})" if words(a.get("text")) else ""
                lines.append("highlight: " + " ".join(x for x in (quote, note) if x))
        broken = BLOCK.sub(lambda m: m.group(0) + "\n", e["content"])
        text = re.sub(
            r"\n{3,}",
            "\n\n",
            "\n".join(
                TIGHT.sub(lambda m: m.group(1) or m.group(2), " ".join(x.split()))
                for x in kernel.html_text(broken).splitlines()
            ),
        ).strip()
        rows.append(
            (
                day(e.get("created_at")),
                "\n".join(lines) + ("\n\n" + text if text else ""),
            )
        )
    return "\n\n".join(t for _d, t in sorted(rows, key=lambda r: r[0])) + "\n"


EXTS = (".json",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: wallabag.py mirror --from FOLDER --to MIRROR"


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
