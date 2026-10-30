r"""mediawiki.py: A MediaWiki XML dump as plain text, page by page. Python 3.9+.

    python adapters/stdlib/mediawiki/mediawiki.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .xml files that are a MediaWiki export (hidden folders and
files skipped; any other XML is skipped and counted) and writes each page as a
paragraph block: its title and the day of its latest revision, then its text
with the wiki markup taken off:

    page: Tomatoes (changed 2024-03-03)

    Tomatoes want six hours of sun.

    == Growing ==  becomes  Growing

Where a page has several revisions the last in the file is used. Links keep
their shown words ([[a|b]] is b), headings lose their equals signs, bold and
italic quotes, templates, comments, references, file and category links go, and
a table cell keeps its text. A redirect page is written as "redirect to X". A
file that declares entities (a way to make a small file expand to a huge one)
is not read.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import html
import re
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

BLOCKS = [
    (re.compile(r"<!--.*?-->", re.S), ""),
    (re.compile(r"<ref[^>]*?/>|<ref[^>]*>.*?</ref>", re.S | re.I), ""),
    (re.compile(r"<br\s*/?>", re.I), "\n"),
    (re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]"), r"\1"),
    (re.compile(r"\[(?:https?|ftp)://\S+ ([^\]]*)\]"), r"\1"),
    (re.compile(r"\[(?:https?|ftp)://\S+\]"), ""),
    (re.compile(r"'{2,5}"), ""),
    (re.compile(r"<[^>\n]+>"), ""),
]
TEMPLATE = re.compile(r"\{\{[^{}]*\}\}")
MEDIA = re.compile(r"\[\[(?:File|Image|Category):", re.I)


def without_media(text: str) -> str:
    """text with every [[File:...]], [[Image:...]] and [[Category:...]] link taken
    out, brackets matched, so a caption holding a link goes with it."""
    while True:
        m = MEDIA.search(text)
        if not m:
            return text
        depth, i = 0, m.start()
        while i < len(text):
            if text.startswith("[[", i):
                depth, i = depth + 1, i + 2
            elif text.startswith("]]", i):
                depth, i = depth - 1, i + 2
                if depth == 0:
                    break
            else:
                i += 1
        text = text[: m.start()] + text[i:]


def plain(wiki: str) -> str:
    """Wikitext as the text a reader sees, without links, templates and quotes."""
    redirect = re.match(r"\s*#REDIRECT\s*\[\[([^\]|#]+)", wiki, re.I)
    if redirect:
        return f"redirect to {redirect.group(1).strip()}"
    text = wiki
    for _ in range(8):  # innermost templates first
        text, n = TEMPLATE.subn("", text)
        if not n:
            break
    text = without_media(text)
    for rx, repl in BLOCKS:
        text = rx.sub(repl, text)
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(("{|", "|}", "|-", "|+")):
            continue
        s = re.sub(r"^[|!]\s*", "", s)
        s = re.sub(r"^=+\s*(.*?)\s*=+$", r"\1", s)
        s = re.sub(r"^[*#:;]+\s*", "", s)
        out.append(
            " ".join(html.unescape(s.replace("||", " ").replace("!!", " ")).split())
        )
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def convert(data: bytes) -> str | None:
    if b"<!ENTITY" in data or b"<mediawiki" not in data[:4000]:
        return None
    root = ET.fromstring(data)
    blocks = []
    for page in (e for e in root if local(e.tag) == "page"):
        title = next(
            (c.text or "" for c in page if local(c.tag) == "title"), ""
        ).strip()
        revs = [c for c in page if local(c.tag) == "revision"]
        if not title or not revs:
            continue
        rev = revs[-1]
        stamp = next((c.text or "" for c in rev if local(c.tag) == "timestamp"), "")[
            :10
        ]
        body = plain(next((c.text or "" for c in rev if local(c.tag) == "text"), ""))
        head = f"page: {title}" + (f" (changed {stamp})" if stamp else "")
        blocks.append(head + ("\n\n" + body if body else ""))
    return "\n\n".join(blocks) + "\n" if blocks else None


EXTS = (".xml",)
ERRORS = (OSError, UnicodeDecodeError, ValueError, ET.ParseError)

USAGE = "usage: mediawiki.py mirror --from FOLDER --to MIRROR"


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
