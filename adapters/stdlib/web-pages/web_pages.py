"""web_pages.py: saved web pages as their readable text, with the address
they came from.

    python adapters/stdlib/web-pages/web_pages.py mirror --from FOLDER --to MIRROR

The kernel reads a web page as the words it shows, but a page saved from a
browser is one long line of markup, and a .mhtml file is a whole message of
parts. This writes, for each .html, .htm, .mhtml or .mht under FOLDER,
`MIRROR/<same relative path>.txt`: a first line saying where the page came
from, then the page's blocks (paragraphs, headings, list items), one
paragraph each, so an answer lands on the paragraph that says it.

    address: https://example.org/terms

The address is the first of: the `saved from url=` note a browser writes in
an .html it saves; an .mhtml's `Snapshot-Content-Location` or its page's
`Content-Location`; the page's canonical link; its `og:url`. A page that
says none of them gets `address: not in the file`, never a guess.

A page is read as UTF-8, or as the charset its own `<meta charset>` names
in its first 4,096 bytes;
an .mhtml's page as its part says. The contract every reader shares: hidden
files and folders are skipped; nothing is written inside FOLDER; the same
folder gives the same bytes; a file it can't read is skipped and counted.
Exit codes: 0 wrote at least one file, 42 nothing to read, 2 refused.
"""

from __future__ import annotations

import codecs
import email
import email.policy
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1] / "clauses"))
import clauses  # noqa: E402
import kernel  # noqa: E402

READS = (".html", ".htm", ".mhtml", ".mht")
SAVED = re.compile(r"<!--\s*saved from url=\(\d+\)(\S+?)\s*-->", re.I)
CHARSET = re.compile(rb"<meta[^>]+charset=[\"']?([A-Za-z0-9_\-]+)", re.I)
CANONICAL = (
    re.compile(r"<link[^>]+rel=[\"']?canonical[\"']?[^>]*href=[\"']([^\"']+)", re.I),
    re.compile(r"<link[^>]+href=[\"']([^\"']+)[\"'][^>]*rel=[\"']?canonical", re.I),
    re.compile(r"<meta[^>]+property=[\"']og:url[\"'][^>]*content=[\"']([^\"']+)", re.I),
    re.compile(r"<meta[^>]+content=[\"']([^\"']+)[\"'][^>]*property=[\"']og:url", re.I),
)


def decode(raw: bytes) -> str | None:
    """A saved page's text: UTF-8, or the charset its own meta tag names."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    m = CHARSET.search(raw[:4096])
    if not m:
        return None
    try:
        return raw.decode(codecs.lookup(m.group(1).decode("ascii")).name)
    except (LookupError, UnicodeDecodeError):
        return None


def mhtml(raw: bytes) -> tuple[str, str] | None:
    """An .mhtml's page and the address it says, or None."""
    msg = email.message_from_bytes(raw, policy=email.policy.default)
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            try:
                page = part.get_content()
            except (LookupError, UnicodeDecodeError):
                return None
            where = (
                msg.get("Snapshot-Content-Location")
                or part.get("Content-Location")
                or ""
            )
            return page, str(where).strip()
    return None


def address(page: str, said: str = "") -> str:
    """Where the page came from, by the first thing that says so."""
    m = SAVED.search(page[:4096])
    if m:
        return m.group(1)
    if said:
        return said
    for pat in CANONICAL:
        if m := pat.search(page):
            return m.group(1)
    return ""


def as_text(page: str, said: str = "") -> str:
    where = address(page, said) or "not in the file"
    blocks = [b for _, b in clauses.blocks_of_html(page)]
    return (
        "".join(s + "\n\n" for s in [f"address: {where}", *blocks]).rstrip("\n") + "\n"
    )


def mirror(src: Path, dst: Path) -> int:
    src, dst = src.resolve(), dst.resolve()
    if not src.is_dir():
        print(f"refused: {src} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    if clauses.inside(dst, src) or clauses.inside(src, dst):
        print("refused: the mirror and the folder can't be inside each other",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    wrote = skipped = 0
    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src)
        if not p.is_file() or p.suffix.lower() not in READS:
            continue
        if any(part.startswith(".") for part in rel.parts):
            continue
        raw = p.read_bytes()
        if p.suffix.lower() in (".mhtml", ".mht"):
            got = mhtml(raw)
        else:
            page = decode(raw)
            got = (page, "") if page is not None else None
        if got is None:
            skipped += 1
            continue
        out = dst / (str(rel) + ".txt")
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(as_text(*got))
        wrote += 1
    print(f"wrote {wrote} files to {dst}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


def main(argv: list[str]) -> int:
    if (
        len(argv) == 5
        and argv[0] == "mirror"
        and argv[1] == "--from"
        and argv[3] == "--to"
    ):
        return mirror(Path(argv[2]), Path(argv[4]))
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
