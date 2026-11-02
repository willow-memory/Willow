"""warc.py: WARC web archives as the pages they captured, each with its
address and the time it was captured. Python 3.9+.

    python adapters/stdlib/warc/warc.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .warc, .warc.gz and .wacz files (hidden folders and files
skipped) and reads each without unpacking it: a .warc.gz is read through
gzip, one member per record or one for the whole file, and a .wacz
(Webrecorder's zip) through zipfile, its archive/*.warc and *.warc.gz in
name order. Records are read by their Content-Length, never by looking for
the blank line after them.

Each captured page (a `response` record holding an HTTP response with a 2xx
status, or a `resource` record, which Webrecorder writes, with no HTTP
envelope) whose type is HTML or plain text becomes one passage:

    2024-03-02 08:15 https://example.org/roof
    The roof - Example Street
    The roof was fixed on Tuesday.

    The gutters are next.

the capture's time from WARC-Date (UTC, to the minute), its address from
WARC-Target-URI and the page's <title> on the lines above its first
paragraph, then its paragraphs with a blank line between. A paragraph does
not carry the address again: the kernel cuts a long page into many passages,
and the page's heading is above them in the same file, where the kernel's
dates already look. A tag on every paragraph would make every paragraph of
a site hold the site's words, so a question naming the site and one other
word would be held by all of them.

HTTP bodies sent chunked are joined, and gzip and deflate are undone; one
sent as br (Brotli) can't be read with the standard library and is left
out and counted. The charset is the one Content-Type names, else the page's
own meta tag, else UTF-8, with what can't be decoded replaced. A page's text
is the kernel's `html_text`, with each block tag (a paragraph, a heading, a
list item, a cell) a paragraph of its own, each tag's attributes taken off
first, and a first heading that only repeats the title left out. warcinfo, request, metadata,
revisit and conversion records are not pages and are passed over, as are
images, scripts, styles, and responses that aren't 2xx; what was left out of
each file is said on the line printed for it.

Each file is written to MIRROR at the same relative path with .txt added;
one that would pass the kernel's MAX_FILE goes on in .2.txt, .3.txt and so
on, a page never split across two. A page's text past MAX_PAGE characters is
left out, and the file's printed line counts it as cut short. A file is
skipped only when no page in it can be read. Nothing the record doesn't hold
is written into the mirror: no stand-in for a missing title, address or date.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import codecs
import gzip
import os
import re
import sys
import textwrap
import zipfile
import zlib
from pathlib import Path
from typing import IO, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

EXTS = (".warc", ".warc.gz", ".wacz")
PAGES = ("response", "resource")  # the record types that hold a page
HTML = ("text/html", "application/xhtml+xml")
MAX_RECORD = 16_000_000  # bytes of one record read; a bigger one is passed over
MAX_PAGE = 20_000  # characters of one page's text written
WIDTH = 200  # a long paragraph is wrapped at this, so the kernel can cut it
BLOCK = re.compile(
    r"</?(?:p|div|li|ul|ol|h[1-6]|br|tr|td|th|table|section|article|header|"
    r"footer|blockquote|main|nav|figure|figcaption|dd|dt|dl|aside|pre|hr)\b[^>]*>",
    re.I,
)
#: a tag with its attributes, quoted values whole: a value may hold ">" or
#: "<!--" (Wikipedia's data-mw does), which would end the tag, or start a
#: comment, for a reader that doesn't look at quotes
ATTRS = re.compile(r"""<(/?[A-Za-z][\w:-]*)(?:"[^"]*"|'[^']*'|[^'">])*>""")
TITLE = re.compile(r"<title\b[^>]*>(.*?)</title\s*>", re.I | re.S)
META = re.compile(rb"<meta[^>]+charset\s*=\s*[\"']?([A-Za-z0-9_.:\-]+)", re.I)
WHEN = re.compile(r"(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})")
ERRORS = (OSError, EOFError, ValueError, zlib.error, zipfile.BadZipFile)

USAGE = "usage: warc.py mirror --from FOLDER --to MIRROR"


class Unreadable(Exception):
    """A record whose body can't be read (not HTTP, a broken gzip)."""


# ── records ─────────────────────────────────────────────────────────────────
def headers(lines: list[bytes]) -> dict[str, str]:
    """`Name: value` lines as a dict, names lowercased; a line that starts
    with a space or a tab goes on the one before it."""
    out: dict[str, str] = {}
    last = ""
    for raw in lines:
        line = raw.decode("utf-8", "replace").rstrip("\r\n")
        if line[:1] in (" ", "\t") and last:
            out[last] += " " + line.strip()
        elif ":" in line:
            name, value = line.split(":", 1)
            last = name.strip().lower()
            out[last] = value.strip()
    return out


def records(stream: IO[bytes]) -> Iterator[tuple[dict[str, str], bytes | None]]:
    """Each record's WARC headers and its block (None when it is over
    MAX_RECORD, and so passed over unread), read by its Content-Length."""
    while True:
        line = stream.readline()
        while line in (b"\r\n", b"\n"):  # the blank lines after a record
            line = stream.readline()
        if not line:
            return
        if not line.startswith(b"WARC/"):
            raise ValueError("not a WARC record")
        lines = []
        while (line := stream.readline()) not in (b"\r\n", b"\n", b""):
            lines.append(line)
        head = headers(lines)
        size = int(head.get("content-length", ""))
        if size > MAX_RECORD:
            while size:
                skip = stream.read(min(size, 1 << 20))
                if not skip:
                    raise EOFError("the file ends inside a record")
                size -= len(skip)
            yield head, None
            continue
        block = stream.read(size)
        if len(block) != size:
            raise EOFError("the file ends inside a record")
        yield head, block


def dechunk(body: bytes) -> bytes:
    """A body sent with Transfer-Encoding: chunked, joined. A capture cut off
    mid-body keeps the chunks that arrived; a body that doesn't start with a
    chunk is read as stored, since some crawlers store it joined already and
    keep the header."""
    out, i = [], 0
    while (end := body.find(b"\n", i)) >= 0:
        try:
            size = int(body[i:end].split(b";")[0].strip(), 16)
        except ValueError:
            break
        if size == 0:
            break
        out.append(body[end + 1 : end + 1 + size])
        i = end + 1 + size
        i += 2 if body[i : i + 2] == b"\r\n" else 1 if body[i : i + 1] == b"\n" else 0
    return b"".join(out) if out else body


def undo(body: bytes, coding: str) -> bytes:
    """A body with its Content-Encoding taken off."""
    try:
        if coding in ("gzip", "x-gzip"):
            return zlib.decompress(body, 47)  # a gzip or zlib header, either
        if coding == "deflate":
            try:
                return zlib.decompress(body)
            except zlib.error:
                return zlib.decompress(body, -15)  # raw deflate, as some send
    except zlib.error:
        raise Unreadable("encoding") from None
    return body


def http(block: bytes) -> tuple[int, dict[str, str], bytes]:
    """An HTTP response's status, headers and body."""
    cut = block.find(b"\r\n\r\n")
    head, body = (block[:cut], block[cut + 4 :]) if cut >= 0 else (block, b"")
    if cut < 0 and (cut := block.find(b"\n\n")) >= 0:
        head, body = block[:cut], block[cut + 2 :]
    first, *rest = head.split(b"\n")
    parts = first.split()
    if len(parts) < 2 or not parts[0].startswith(b"HTTP/") or not parts[1].isdigit():
        raise Unreadable("not http")
    return int(parts[1]), headers(rest), body


# ── a page's text ───────────────────────────────────────────────────────────
def charset(ctype: str, body: bytes) -> str:
    """The charset Content-Type names, else the page's meta tag, else UTF-8."""
    for found in (re.search(r"charset\s*=\s*[\"']?([^\s;\"']+)", ctype, re.I),
                  META.search(body[:4096])):  # fmt: skip
        if found:
            name = found.group(1)
            name = name.decode("ascii", "replace") if isinstance(name, bytes) else name
            try:
                return codecs.lookup(name).name
            except LookupError:
                continue
    return "utf-8"


def wrapped(para: str) -> list[str]:
    return textwrap.wrap(para, WIDTH, break_long_words=False, break_on_hyphens=False)


def page_text(body: bytes, ctype: str) -> tuple[str, list[str]]:
    """A page's title ("" for none) and its paragraphs, each a list of lines."""
    text = body.decode(charset(ctype, body), "replace").lstrip("﻿")
    if ctype.split(";")[0].strip().lower() not in HTML:
        paras = re.split(r"\n\s*\n", text.replace("\r\n", "\n").replace("\r", "\n"))
        return "", [
            "\n".join(
                w for line in p.split("\n") if line.strip() for w in wrapped(line)
            )
            for p in paras
            if p.strip()
        ]
    text = ATTRS.sub(r"<\1>", text)
    found = TITLE.search(text)
    title = " ".join(kernel.html_text(found.group(1)).split()) if found else ""
    text = TITLE.sub(" ", text)
    text = kernel.html_text(BLOCK.sub("\n\n", text))
    paras = [" ".join(p.split()) for p in re.split(r"\n\s*\n", text)]
    paras = [p for p in paras if p]
    if paras and paras[0] == title:  # a heading that repeats the title
        paras = paras[1:]
    return title, ["\n".join(wrapped(p)) for p in paras]


def when(date: str) -> str:
    """WARC-Date to the minute, `YYYY-MM-DD HH:MM`; anything else as written."""
    m = WHEN.match(date)
    return f"{m.group(1)} {m.group(2)}" if m else date


def passage(head: dict[str, str], title: str, paras: list[str]) -> tuple[str, bool]:
    """A page's passage, and whether its text was cut at MAX_PAGE. Nothing
    the record doesn't hold is written: no stand-in for a missing title,
    address or date, and the cut is said on the file's printed line, since a
    word written into passage after passage would hold questions about
    something the archive never had."""
    url = head.get("warc-target-uri", "").strip().strip("<>")
    top = " ".join(x for x in (when(head.get("warc-date", "").strip()), url) if x)
    body, size, cut = [], 0, False
    for p in paras:
        if size + len(p) > MAX_PAGE:
            cut = True
            break
        body.append(p)
        size += len(p)
    lines = [x for x in (top, title) if x]
    return "\n".join(lines) + "\n" + "\n\n".join(body) + "\n", cut


def page(head: dict[str, str], block: bytes) -> tuple[str | None, str]:
    """A record's passage, or None and why it was left out ("cut short"
    with a passage whose text stopped at MAX_PAGE)."""
    kind = head.get("warc-type", "").lower()
    if kind not in PAGES:
        return None, kind or "no type"
    ctype = head.get("content-type", "")
    body = block
    if kind == "response":
        if "application/http" not in ctype.lower():
            return None, "not http"
        status, hhead, body = http(block)
        if not 200 <= status < 300:
            return None, "not 2xx"
        ctype = hhead.get("content-type", "")
        if hhead.get("content-encoding", "").lower() == "br":
            return None, "br"
        if "chunked" in hhead.get("transfer-encoding", "").lower():
            body = dechunk(body)
        body = undo(body, hhead.get("content-encoding", "").lower().strip())
    mime = ctype.split(";")[0].strip().lower()
    if mime not in HTML and mime != "text/plain":
        return None, "not text"
    title, paras = page_text(body, ctype)
    if not title and not paras:
        return None, "no text"
    text, cut = passage(head, title, paras)
    return text, "cut short" if cut else ""


# ── a file ──────────────────────────────────────────────────────────────────
def opened(raw) -> IO[bytes]:
    """The stream itself, or through gzip when it starts with gzip's bytes."""
    if raw.peek(2)[:2] == b"\x1f\x8b":
        return gzip.GzipFile(fileobj=raw)
    return raw


def streams(path: Path) -> Iterator[IO[bytes]]:
    """The WARC streams in a file: the file, or each WARC inside a .wacz."""
    if path.name.lower().endswith(".wacz"):
        with zipfile.ZipFile(path) as zf:
            names = sorted(n for n in zf.namelist()
                           if n.lower().endswith((".warc", ".warc.gz")))  # fmt: skip
            for name in names:
                with zf.open(name) as member:
                    yield opened(member)
        return
    with open(path, "rb") as f:
        yield opened(f)


def read(path: Path) -> tuple[list[str], dict[str, int]]:
    """A file's passages, and what was left out of it, by reason."""
    found: list[str] = []
    left: dict[str, int] = {}
    for stream in streams(path):
        try:
            for head, block in records(stream):
                if block is None:
                    why = "too big"
                    text = None
                else:
                    try:
                        text, why = page(head, block)
                    except Unreadable as e:
                        text, why = None, str(e)
                if text is not None:
                    found.append(text)
                if why:  # left out, or (with a text) cut short
                    left[why] = left.get(why, 0) + 1
        except ERRORS:
            left["unreadable rest"] = left.get("unreadable rest", 0) + 1
    return found, left


def parts(found: list[str]) -> list[str]:
    """The passages as files the kernel reads whole: under MAX_FILE bytes."""
    out, cur = [], ""
    for text in found:
        piece = ("\n" if cur else "") + text
        if cur and len((cur + piece).encode("utf-8")) > kernel.MAX_FILE:
            out.append(cur)
            cur, piece = "", text
        cur += piece
    return out + [cur] if cur else out


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
            found, left = read(path)
        except ERRORS:
            found, left = [], {"unreadable": 1}
        said = ", ".join(f"{n} {why}" for why, n in sorted(left.items()))
        print(
            f"{rel.as_posix()}: {len(found)} pages"
            + (f"; left out {said}" if said else "")
        )
        if not found:
            skipped += 1
            continue
        for i, text in enumerate(parts(found), 1):
            name = rel.name + (f".{i}" if i > 1 else "") + ".txt"
            target = dst.joinpath(rel.parent, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
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
