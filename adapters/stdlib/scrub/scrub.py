"""scrub.py: a copy of a file without its hidden details, to share. Python 3.9+.

    python adapters/stdlib/scrub/scrub.py --from FILE --to FILE

A photo carries the camera, the time, and often the place it was taken. A
Word file carries who wrote it, who saved it last, and when. This writes a
copy of FILE with those details taken out and says what it took:

    removed  Exif (Make, Model, DateTime, GPS): 3,402 bytes
    removed  XMP packet: 1,180 bytes
    kept     the orientation, so the photo still shows the right way up
    wrote photo-clean.jpg: 2 removed

By kind of file, chosen by what is inside it and not by its name:

| Kind | Taken out | Kept |
|---|---|---|
| JPEG | Exif (camera, time, GPS), XMP, IPTC and Photoshop blocks, comments, thumbnails | the picture, the colour profile, and the orientation |
| PNG | text chunks (Author, Software, Comment, Creation Time), Exif, the time of last change | the picture and its colours |
| docx, xlsx, pptx | author, last saved by, created and modified times, revision, keywords, description, company, manager; the edit-session ids in a Word file; the names on comments and tracked changes; custom properties | the text, tables and slides, and the title |

Tracked changes themselves are not accepted or rejected: the changes stay and
their authors go. Text a person wrote (a comment, a revision) is theirs to
read before it is shared, and is said. A photo's thumbnail inside a Word file
is said, not removed.

Anything else is refused, not copied unchanged: a copy that claims to be
scrubbed and isn't is worse than none. PDFs and audio and video are not
handled yet. FILE is not changed. The copy is written once, readable only by
you, never over a file that exists, and the same bytes for the same file.

It strips what a file's format keeps in a known place. A name typed into the
text of a document, a face in a photo, and a street sign in the background are
not hidden details and stay.

Exit codes, the kernel's: 0 written; 2 refused (a bad command line, a kind of
file it doesn't handle, a file it can't read, an existing copy).
"""

from __future__ import annotations

import io
import os
import re
import struct
import sys
import zipfile
import zlib
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

PNG_SIG = b"\x89PNG\r\n\x1a\n"
PNG_DROP = {b"tEXt", b"zTXt", b"iTXt", b"eXIf", b"tIME"}
EXIF_TAGS = {0x010F: "Make", 0x0110: "Model", 0x0131: "Software", 0x0132: "DateTime", 0x013B: "Artist",
             0x8298: "Copyright", 0x8825: "GPS", 0x9003: "DateTimeOriginal", 0xA430: "OwnerName",
             0xA431: "BodySerialNumber", 0x010E: "ImageDescription", 0x9286: "UserComment"}  # fmt: skip
CORE_DROP = ("dc:creator", "cp:lastModifiedBy", "cp:lastPrinted", "dcterms:created", "dcterms:modified",
             "cp:revision", "dc:description", "cp:keywords", "dc:subject", "cp:category")  # fmt: skip
APP_DROP = ("Company", "Manager", "Template", "TotalTime")


class Refused(ValueError):
    pass


def size(n: int) -> str:
    return f"{n:,} bytes"


def exif_view(body: bytes) -> tuple[list[str], int]:
    """(names of the sensitive tags in an Exif block, its orientation or 1)."""
    names: list[str] = []
    orient = 1
    try:
        tiff = body[6:]
        end = "<" if tiff[:2] == b"II" else ">"
        ifd = struct.unpack(end + "I", tiff[4:8])[0]

        def walk(at: int, depth: int) -> None:
            nonlocal orient
            (count,) = struct.unpack(end + "H", tiff[at : at + 2])
            for i in range(min(count, 200)):
                tag, typ, n, val = struct.unpack(
                    end + "HHI4s", tiff[at + 2 + 12 * i : at + 14 + 12 * i]
                )
                if tag == 0x0112 and typ == 3:
                    orient = struct.unpack(end + "H", val[:2])[0]
                elif tag in EXIF_TAGS and EXIF_TAGS[tag] not in names:
                    names.append(EXIF_TAGS[tag])
                if tag == 0x8769 and depth < 2:  # the Exif sub-IFD
                    walk(struct.unpack(end + "I", val)[0], depth + 1)

        walk(ifd, 0)
    except (struct.error, IndexError):
        pass
    return names, orient if 1 <= orient <= 8 else 1


def orientation_block(orient: int) -> bytes:
    """A tiny Exif block holding only the orientation."""
    ifd = (
        struct.pack(">H", 1)
        + struct.pack(">HHI", 0x0112, 3, 1)
        + struct.pack(">H", orient)
        + b"\0\0"
        + struct.pack(">I", 0)
    )
    body = b"Exif\0\0MM\0*" + struct.pack(">I", 8) + ifd
    return b"\xff\xe1" + struct.pack(">H", len(body) + 2) + body


def jpeg(data: bytes) -> tuple[bytes, list[str]]:
    if data[:2] != b"\xff\xd8":
        raise Refused("not a JPEG")
    out, said, i, orient = [data[:2]], [], 2, 1
    while i < len(data):
        if data[i] != 0xFF:
            raise Refused("the JPEG's markers don't read")
        marker = data[i + 1]
        if marker == 0xFF:
            i += 1
            continue
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            out.append(data[i : i + 2])
            i += 2
            continue
        if marker == 0xD9:
            out.append(data[i:])
            break
        (length,) = struct.unpack(">H", data[i + 2 : i + 4])
        if length < 2 or i + 2 + length > len(data):
            raise Refused("the JPEG is cut short")
        seg = data[i : i + 2 + length]
        body = seg[4:]
        if marker == 0xDA:  # the scan: everything after is picture
            out.append(data[i:])
            break
        drop = False
        if marker == 0xE1 and body[:6] == b"Exif\0\0":
            names, orient = exif_view(body)
            said.append(
                f"removed  Exif ({', '.join(names) or 'no named tags'}): {size(len(seg))}"
            )
            drop = True
        elif marker == 0xE1:
            said.append(f"removed  XMP packet: {size(len(seg))}")
            drop = True
        elif marker == 0xED:
            said.append(f"removed  Photoshop/IPTC block: {size(len(seg))}")
            drop = True
        elif marker == 0xFE:
            said.append(f"removed  comment: {size(len(seg))}")
            drop = True
        elif marker == 0xE2 and not body.startswith(b"ICC_PROFILE\0"):
            said.append(
                f"removed  APP2 block ({body[:4].decode('latin-1')!r}): {size(len(seg))}"
            )
            drop = True
        elif 0xE3 <= marker <= 0xEC or marker == 0xEF:
            said.append(f"removed  APP{marker - 0xE0} block: {size(len(seg))}")
            drop = True
        if not drop:
            out.append(seg)
        i += 2 + length
    result = b"".join(out)
    if orient != 1:
        # the orientation goes right after the file's first marker, as Exif is allowed to
        result = result[:2] + orientation_block(orient) + result[2:]
        said.append(
            "kept     the orientation, so the photo still shows the right way up"
        )
    return result, said


def png(data: bytes) -> tuple[bytes, list[str]]:
    if data[:8] != PNG_SIG:
        raise Refused("not a PNG")
    out, said, i = [PNG_SIG], [], 8
    while i + 8 <= len(data):
        (length,) = struct.unpack(">I", data[i : i + 4])
        kind, body, crc = (
            data[i + 4 : i + 8],
            data[i + 8 : i + 8 + length],
            data[i + 8 + length : i + 12 + length],
        )
        if (
            len(body) != length
            or len(crc) != 4
            or zlib.crc32(kind + body) != struct.unpack(">I", crc)[0]
        ):
            raise Refused("the PNG's chunks don't read")
        if kind in PNG_DROP:
            what = kind.decode()
            if kind in (b"tEXt", b"zTXt", b"iTXt"):
                key = body.split(b"\0", 1)[0].decode("latin-1")[:40]
                said.append(f"removed  text chunk {key!r}: {size(length + 12)}")
            else:
                said.append(f"removed  {what} chunk: {size(length + 12)}")
        else:
            out.append(data[i : i + 12 + length])
        i += 12 + length
        if kind == b"IEND":
            break
    return b"".join(out), said


def blank(xml: str, names: tuple[str, ...]) -> tuple[str, list[str]]:
    gone = []
    for name in names:
        rx = re.compile(rf"<{name}\b[^>]*?/>|<{name}\b[^>]*>.*?</{name}>", re.S)
        xml, n = rx.subn("", xml)
        if n:
            gone.append(name.split(":")[-1])
    return xml, gone


def ooxml(data: bytes) -> tuple[bytes, list[str]]:
    try:
        src = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise Refused("not an Office file") from None
    names = src.namelist()
    if "[Content_Types].xml" not in names or not any(
        n.startswith(("word/", "xl/", "ppt/")) for n in names
    ):
        raise Refused("a zip, but not a docx, xlsx or pptx")
    out, said = io.BytesIO(), []
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            body = src.read(info)
            name = info.filename
            if name == "docProps/core.xml":
                xml, gone = blank(body.decode("utf-8"), CORE_DROP)
                body = xml.encode("utf-8")
                if gone:
                    said.append(f"removed  core properties ({', '.join(gone)})")
            elif name == "docProps/app.xml":
                xml, gone = blank(body.decode("utf-8"), APP_DROP)
                body = xml.encode("utf-8")
                if gone:
                    said.append(f"removed  application properties ({', '.join(gone)})")
            elif name == "docProps/custom.xml":
                xml, n = re.subn(
                    r"<property\b.*?</property>", "", body.decode("utf-8"), flags=re.S
                )
                body = xml.encode("utf-8")
                if n:
                    said.append(
                        f"removed  {n} custom propert{'ies' if n != 1 else 'y'}"
                    )
            elif name.endswith(".xml") and name.startswith(
                ("word/", "xl/comments", "ppt/comments")
            ):
                xml = body.decode("utf-8")
                xml, rs = re.subn(r'\sw:rsid\w*="[0-9A-Fa-f]+"', "", xml)
                xml, who = re.subn(r'(\sw:(?:author|initials))="[^"]*"', r'\1=""', xml)
                xml, authors = re.subn(
                    r"<author>[^<]*</author>", "<author></author>", xml
                )
                body = xml.encode("utf-8")
                if rs:
                    said.append(
                        f"removed  {rs} edit-session id{'s' if rs != 1 else ''} in {name}"
                    )
                if who or authors:
                    said.append(
                        f"removed  {who + authors} author name{'s' if who + authors != 1 else ''} in {name}"
                    )
            elif name.startswith("docProps/thumbnail"):
                said.append(
                    f"note     {name} is a picture of the first page and is kept; remove it by hand if that matters"
                )
            dst.writestr(
                zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0)), body, zipfile.ZIP_DEFLATED
            )
    return out.getvalue(), said


def scrub(data: bytes) -> tuple[bytes, list[str]]:
    if data[:2] == b"\xff\xd8":
        return jpeg(data)
    if data[:8] == PNG_SIG:
        return png(data)
    if data[:4] == b"PK\x03\x04":
        return ooxml(data)
    raise Refused(
        "a kind of file this doesn't handle (JPEG, PNG, docx, xlsx and pptx are)"
    )


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--from", "--to"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--from") or not opts.get("--to") or args:
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    src, to = Path(opts["--from"]), Path(opts["--to"])
    if not src.is_file():
        print(f"refused: {src} isn't a file", file=sys.stderr)
        return kernel.REFUSED
    try:
        clean, said = scrub(src.read_bytes())
    except (OSError, Refused, UnicodeDecodeError, struct.error, IndexError) as e:
        print(
            f"refused: {e if isinstance(e, Refused) else 'could not read ' + str(src)}",
            file=sys.stderr,
        )
        return kernel.REFUSED
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as e:
        print(f"refused: could not write {to}: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    with os.fdopen(fd, "wb") as f:
        f.write(clean)
    for line in said:
        print(line)
    removed = sum(1 for s in said if s.startswith("removed"))
    print(
        f"wrote {to}: {removed} removed"
        if removed
        else f"wrote {to}: nothing hidden found"
    )
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
