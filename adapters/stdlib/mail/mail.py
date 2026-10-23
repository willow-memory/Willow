"""mail.py: your .eml and .mbox mail, as plain text the kernel can read.

    python adapters/stdlib/mail/mail.py mirror --from FOLDER --to MIRROR

Walks FOLDER (sorted; a folder or file whose name starts with "." is skipped)
and writes, into MIRROR, one text file for each .eml or .mbox it can read, at
the same relative path with ".txt" added: inbox/a.eml becomes
MIRROR/inbox/a.eml.txt. Then point the kernel at MIRROR:

    python kernel.py init --box BOX --pile MIRROR --key KEY

Each message becomes a header block, a blank line, the body, and then the
attachments, listed by name only:

    From: Ada Example <ada@example.org>
    To: Ben Example <ben@example.org>
    Date: 2026-10-23 09:15
    Subject: Estimate for the roof

    The estimate is attached as a PDF; the total is in the second table.

    Attachment: estimate.pdf

The body is the first text/plain part, else the text/html part with its tags
stripped. Quoted-printable and base64 are decoded, and encoded headers
(RFC 2047) are read. Date is the sender's clock time as their message wrote
it, with no time zone conversion, so the same bytes always give the same line.
An .mbox holds several messages: each starts with a line `== message N` and a
blank line, and they are separated by a blank line.

FOLDER is only read, and no original is modified. A file that can't be read
as a message is skipped and counted. A file with no message in it is not
written. Only files ending .eml or .mbox are read; others are not counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (a bad
command line, FOLDER not a folder, or MIRROR and FOLDER inside each other).
"""

from __future__ import annotations

import email
import email.header
import email.utils
import io
import mailbox
import os
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "refused: usage: mail.py mirror --from FOLDER --to MIRROR"
BLOCK = {
    "p",
    "div",
    "br",
    "tr",
    "li",
    "hr",
    "blockquote",
    "table",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
}
SKIP = {"script", "style", "head"}


class _Tags(HTMLParser):
    """The text a page shows: block tags become line breaks, scripts go."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in SKIP:
            self.hidden += 1
        elif tag in BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP:
            self.hidden = max(0, self.hidden - 1)
        elif tag in BLOCK:
            self.out.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.out.append(data)


def _lines(text: str) -> str:
    """Each line's runs of spaces made one; at most one blank line in a row."""
    out: list[str] = []
    for line in (" ".join(ln.split()) for ln in text.split("\n")):
        if line or (out and out[-1]):
            out.append(line)
    return "\n".join(out).strip("\n")


def html_to_text(page: str) -> str:
    parser = _Tags()
    parser.feed(page)
    parser.close()
    return _lines("".join(parser.out))


def _text_of(s: str) -> str:
    """A header as it came in: 8-bit bytes read as UTF-8, not as escapes."""
    try:
        return s.encode("ascii", "surrogateescape").decode("utf-8", "replace")
    except UnicodeEncodeError:
        return s


def _header(value: object) -> str:
    """A header value, RFC 2047 words decoded, folds and runs of spaces made one."""
    if value is None:
        return ""
    s = " ".join(_text_of(str(value)).split())
    out = []
    for chunk, charset in email.header.decode_header(s):
        if isinstance(chunk, bytes):
            try:
                chunk = chunk.decode(charset or "utf-8", "replace")
            except LookupError:
                chunk = chunk.decode("utf-8", "replace")
        out.append(chunk)
    return " ".join("".join(out).split())


def _date(value: object) -> str:
    raw = _header(value)
    try:
        return email.utils.parsedate_to_datetime(raw).strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError, IndexError, OverflowError):
        return raw or "none"


def _text(part: email.message.Message) -> str:
    raw = part.get_payload(decode=True) or b""
    try:
        text = raw.decode(part.get_content_charset() or "utf-8", "replace")
    except LookupError:
        text = raw.decode("utf-8", "replace")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _visit(part, plain: list, page: list, files: list) -> None:
    """Sort a message's parts into plain bodies, HTML bodies and attachments.
    Nested multipart parts are opened; a forwarded message is an attachment."""
    if part.get_content_maintype() == "multipart":
        for sub in part.get_payload():
            _visit(sub, plain, page, files)
        return
    name = _header(part.get_filename())
    ctype = part.get_content_type()
    inline = part.get_content_disposition() != "attachment" and not name
    if inline and ctype == "text/plain":
        plain.append(_text(part))
    elif inline and ctype == "text/html":
        page.append(_text(part))
    else:  # listed by name; the content is never read
        files.append(name or f"(unnamed {ctype})")


def render(msg: email.message.Message) -> str:
    """One message as its header block, body and attachment names."""
    plain: list[str] = []
    page: list[str] = []
    files: list[str] = []
    _visit(msg, plain, page, files)
    body = next((b for b in plain if b.strip()), None)
    if body is None:  # no plain part: the HTML part, its tags stripped
        body = next((t for t in (html_to_text(h) for h in page) if t), "")
    else:  # plain text keeps its indentation; only trailing spaces go
        body = "\n".join(ln.rstrip() for ln in body.split("\n")).strip("\n")
    lines = [
        f"From: {_header(msg.get('From')) or 'none'}",
        f"To: {_header(', '.join(str(v) for v in msg.get_all('To') or [])) or 'none'}",
        f"Date: {_date(msg.get('Date'))}",
        f"Subject: {_header(msg.get('Subject')) or 'none'}",
        "",
    ]
    lines += body.split("\n") if body else ["(no text body)"]
    if files:
        lines += [""] + [f"Attachment: {name}" for name in files]
    return "\n".join(lines) + "\n"


def is_message(msg: email.message.Message) -> bool:
    return any(msg.get(h) for h in ("From", "To", "Subject", "Date"))


def _split_mbox(raw: bytes) -> list[bytes]:
    """The messages of an mbox: a line starting "From " opens each one, and that
    line is not kept. Read as bytes, so a read-only file is never opened for
    writing (mailbox.mbox() would open it rb+)."""
    chunks: list[bytes] = []
    cur: list[bytes] = []
    for line in io.BytesIO(raw):
        if line.startswith(b"From "):
            if cur:
                chunks.append(b"".join(cur))
            cur = []
        else:
            cur.append(line)
    if cur:
        chunks.append(b"".join(cur))
    return chunks


def read_file(path: Path) -> str | None:
    """The text a file mirrors to, or None when it holds no message."""
    try:
        raw = path.read_bytes()
        if b"\0" in raw:
            return None
        if path.name.lower().endswith(".eml"):
            msg = email.message_from_bytes(raw)
            return render(msg) if is_message(msg) else None
        msgs = [mailbox.mboxMessage(c) for c in _split_mbox(raw)]
        texts = [render(m) for m in msgs if is_message(m)]
    except Exception:  # any file that won't parse is skipped and counted
        return None
    if not texts:
        return None
    return "\n".join(f"== message {n}\n\n{t}" for n, t in enumerate(texts, 1))


def sources(folder: Path):
    """(path, relative path) of each .eml or .mbox under folder, sorted."""
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            if name.startswith(".") or not name.lower().endswith((".eml", ".mbox")):
                continue
            path = Path(dirpath) / name
            yield path, path.relative_to(folder)


def mirror(folder: Path, dest: Path) -> int:
    if not folder.is_dir():
        print(f"refused: {folder} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    if dest.exists() and not dest.is_dir():
        print(f"refused: {dest} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    src, out = folder.resolve(), dest.resolve()
    if out == src or out.is_relative_to(src) or src.is_relative_to(out):
        print(
            "refused: MIRROR and FOLDER must not be inside each other", file=sys.stderr
        )
        return kernel.REFUSED
    wrote = skipped = 0
    for path, rel in sources(src):
        text = read_file(path)
        if text is None:
            skipped += 1
            continue
        target = out / rel.parent / (rel.name + ".txt")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8", "replace"))
        except OSError as err:
            print(f"refused: cannot write {target}: {err}", file=sys.stderr)
            return kernel.REFUSED
        wrote += 1
    print(f"wrote {wrote} files to {dest}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


def main(argv: list[str]) -> int:
    if (
        len(argv) != 5
        or argv[0] != "mirror"
        or argv[1] != "--from"
        or argv[3] != "--to"
    ):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    return mirror(Path(argv[2]), Path(argv[4]))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
