"""webarchive.py: pages Safari saved as .webarchive, as their readable text,
with the address they came from, read the way web-pages reads a saved page.

    python adapters/stdlib/webarchive/webarchive.py mirror --from FOLDER --to MIRROR

A .webarchive is a property list: the page's own bytes, its address and its
charset under `WebMainResource`, each frame of it as an archive of the same
shape under `WebSubframeArchives`, and its pictures, styles and scripts
under `WebSubresources`. This writes, for each .webarchive under FOLDER,
`MIRROR/<same relative path>.txt`: what web-pages writes for the same page
(its address, then its blocks, the title first, one paragraph each), then
each frame's blocks under the frame's own address, alone on its line.

A page is read in the charset the archive names for it, else the one its
own `<meta charset>` names, else as UTF-8 with what isn't replaced. A file
that isn't a web archive, or whose page isn't HTML or plain text (a saved
PDF or picture), is skipped and counted. The contract every reader shares:
hidden files and folders are skipped; nothing is written inside FOLDER; the
same folder gives the same bytes. Exit codes: 0 wrote at least one file, 42
nothing to read, 2 refused.
"""

from __future__ import annotations

import codecs
import plistlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1] / "web-pages"))
import kernel  # noqa: E402
import web_pages  # noqa: E402

READS = (".webarchive",)
TEXT = ("text/html", "text/plain")


def inside(a: Path, b: Path) -> bool:
    return a == b or b in a.parents


def decode(raw: bytes, named: str) -> str:
    """A resource's text: in the charset the archive names, else the one the
    page's meta tag names, else UTF-8 with what isn't replaced."""
    for name in (named, *_meta(raw)):
        try:
            return raw.decode(codecs.lookup(name).name)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", errors="replace")


def _meta(raw: bytes) -> list[str]:
    m = web_pages.CHARSET.search(raw[:4096])
    return [m.group(1).decode("ascii")] if m else []


def resource(archive: object) -> tuple[str, str, str] | None:
    """An archive's main resource as (MIME type, address, text), or None
    when it isn't one: no WebMainResource, or no bytes in it."""
    main = archive.get("WebMainResource") if isinstance(archive, dict) else None
    if not isinstance(main, dict) or not isinstance(main.get("WebResourceData"), bytes):
        return None
    mime = str(main.get("WebResourceMIMEType", "")).strip().lower()
    url = str(main.get("WebResourceURL", "")).strip()
    named = str(main.get("WebResourceTextEncodingName", "")).strip()
    return mime, url, decode(main["WebResourceData"], named)


def blocks(mime: str, text: str) -> list[str]:
    """A page's blocks as web-pages reads them; plain text by its blank lines,
    each line kept, so a list stays a list."""
    if mime == "text/plain":
        paras = re.split(r"\n[ \t]*\n", text.replace("\r\n", "\n").replace("\r", "\n"))
        lines = [
            [" ".join(x.split()) for x in p.split("\n") if x.strip()] for p in paras
        ]
        return ["\n".join(p) for p in lines if p]
    return web_pages.as_text(text).split("\n\n")[1:]


def frames(archive: dict) -> list[str]:
    """Every frame's text under the main page, in the order the archive keeps
    them, a frame's own frames after it, each under its own address alone on
    its line (no label: a word written above every frame would answer any
    question holding it); one that isn't text gives its type instead."""
    out = []
    subs = archive.get("WebSubframeArchives")
    for sub in subs if isinstance(subs, list) else []:
        got = resource(sub)
        if got is None:
            continue
        mime, url, text = got
        if mime in TEXT:
            out += [url, *(b.strip() for b in blocks(mime, text))]
        else:
            out.append(f"{url} ({mime or '?'})".strip())
        out += frames(sub)
    return [s for s in out if s]


def as_text(raw: bytes) -> str | None:
    """A .webarchive's page as web-pages would write it, then its frames; None
    when it isn't a web archive or its page isn't HTML or plain text."""
    try:
        archive = plistlib.loads(raw)
    except Exception:  # plistlib raises several kinds on a broken file
        return None
    got = resource(archive)
    if got is None or got[0] not in TEXT:
        return None
    mime, url, text = got
    if mime == "text/html":
        page = web_pages.as_text(text, url).rstrip("\n").split("\n\n")
    else:
        page = [f"address: {url or 'not in the file'}", *blocks(mime, text)]
    return "\n\n".join([*page, *frames(archive)]) + "\n"


def mirror(src: Path, dst: Path) -> int:
    src, dst = src.resolve(), dst.resolve()
    if not src.is_dir():
        print(f"refused: {src} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    if inside(dst, src) or inside(src, dst):
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
        text = as_text(p.read_bytes())
        if text is None:
            skipped += 1
            continue
        out = dst / (str(rel) + ".txt")
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
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
