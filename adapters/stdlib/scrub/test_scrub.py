"""scrub: the hidden details taken out of a JPEG, PNG, docx, xlsx or pptx and
listed; the picture, text and orientation kept; a kind it doesn't handle
refused rather than copied; the original unchanged; the copy written once,
private, the same bytes twice; a bad command line refused."""

from __future__ import annotations

import io
import os
import stat
import struct
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "scrub.py"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def seg(marker: int, body: bytes) -> bytes:
    return b"\xff" + bytes([marker]) + struct.pack(">H", len(body) + 2) + body


def exif(orientation: int | None = 6) -> bytes:
    """A big-endian Exif block with Make, DateTime, a GPS pointer and, if given, the orientation."""
    entries = [(0x010F, 2, 6, b"Canon\0"), (0x0132, 2, 20, b"2024:05:01 10:00:00\0")]
    # values longer than four bytes live after the IFD
    n = 3 + (orientation is not None)
    data_at = 8 + 2 + 12 * n + 4
    blob, ifd = b"", b""
    for tag, typ, cnt, val in entries:
        ifd += struct.pack(">HHII", tag, typ, cnt, data_at + len(blob))
        blob += val
    if orientation is not None:
        ifd += (
            struct.pack(">HHI", 0x0112, 3, 1) + struct.pack(">H", orientation) + b"\0\0"
        )
    ifd += struct.pack(">HHII", 0x8825, 4, 1, 0)
    tiff = (
        b"MM\0*"
        + struct.pack(">I", 8)
        + struct.pack(">H", n)
        + ifd
        + struct.pack(">I", 0)
        + blob
    )
    return b"Exif\0\0" + tiff


PICTURE = (
    seg(0xDB, b"\0" + bytes(range(64)))
    + seg(0xC0, b"\x08\0\x10\0\x10\x01\x01\x11\0")
    + seg(0xDA, b"\x01\x01\0\0?\0")
    + b"\x12\x34\x56\xff\xd9"
)


def jpeg(*segments: bytes) -> bytes:
    return b"\xff\xd8" + b"".join(segments) + PICTURE


def chunk(kind: bytes, body: bytes) -> bytes:
    return (
        struct.pack(">I", len(body))
        + kind
        + body
        + struct.pack(">I", zlib.crc32(kind + body))
    )


def png(*extra: bytes) -> bytes:
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\0\xff\0\0"))
    return b"\x89PNG\r\n\x1a\n" + ihdr + b"".join(extra) + idat + chunk(b"IEND", b"")


CORE = ('<?xml version="1.0"?><cp:coreProperties xmlns:cp="c" xmlns:dc="d" xmlns:dcterms="t">'
        "<dc:title>Quarterly plan</dc:title><dc:creator>Jane Doe</dc:creator><cp:lastModifiedBy>Bob</cp:lastModifiedBy>"
        "<cp:revision>7</cp:revision><dcterms:created>2024-01-01T00:00:00Z</dcterms:created>"
        "<dcterms:modified>2024-02-02T00:00:00Z</dcterms:modified><dc:description/></cp:coreProperties>")  # fmt: skip
APP = "<Properties><Application>Word</Application><Company>Acme</Company><Manager>Pat</Manager><TotalTime>99</TotalTime></Properties>"
DOC = ('<w:document xmlns:w="w"><w:body><w:p w:rsidR="00AB12CD" w:rsidRDefault="00AB12CD"><w:ins w:id="1" w:author="Bob Lee" w:date="2024-02-02T00:00:00Z">'
       "<w:r><w:t>Hello</w:t></w:r></w:ins></w:p></w:body></w:document>")  # fmt: skip
COMMENTS = '<w:comments xmlns:w="w"><w:comment w:id="0" w:author="Jane Doe" w:initials="JD"><w:p/></w:comment></w:comments>'
CUSTOM = '<Properties><property fmtid="x" pid="2" name="Client"><vt:lpwstr>Acme</vt:lpwstr></property></Properties>'


def office(**extra: str) -> bytes:
    files = {"[Content_Types].xml": "<Types/>", "word/document.xml": DOC, "word/comments.xml": COMMENTS,
             "docProps/core.xml": CORE, "docProps/app.xml": APP, "docProps/custom.xml": CUSTOM, **extra}  # fmt: skip
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, text in files.items():
            z.writestr(zipfile.ZipInfo(name, (2024, 3, 3, 12, 0, 0)), text)
    return buf.getvalue()


def scrubbed(
    tmp_path: Path, data: bytes, name: str = "in.bin"
) -> tuple[subprocess.CompletedProcess, bytes]:
    src, to = tmp_path / name, tmp_path / "out.bin"
    src.write_bytes(data)
    to.unlink(missing_ok=True)
    got = run("--from", str(src), "--to", str(to))
    return got, to.read_bytes() if to.exists() else b""


def test_a_jpegs_exif_xmp_iptc_and_comment_are_removed_and_the_picture_is_kept(
    tmp_path,
):
    data = jpeg(seg(0xE0, b"JFIF\0\1\1\0\0\1\0\1\0\0"), seg(0xE1, exif(None)), seg(0xE1, b"http://ns.adobe.com/xap/1.0/\0<x/>"),
                seg(0xED, b"Photoshop 3.0\0"), seg(0xFE, b"made by Jane"), seg(0xE5, b"junk"))  # fmt: skip
    got, clean = scrubbed(tmp_path, data)
    assert got.returncode == 0, got.stderr
    assert (
        b"Exif" not in clean
        and b"xap" not in clean
        and b"Photoshop" not in clean
        and b"Jane" not in clean
        and b"Canon" not in clean
    )
    assert clean.startswith(b"\xff\xd8\xff\xe0") and clean.endswith(PICTURE), (
        "the JFIF header and the picture stay"
    )
    assert "removed  Exif (Make, DateTime, GPS):" in got.stdout
    assert (
        "removed  XMP packet" in got.stdout
        and "removed  Photoshop/IPTC block" in got.stdout
    )
    assert "removed  comment" in got.stdout and "removed  APP5 block" in got.stdout
    assert got.stdout.splitlines()[-1].endswith(": 5 removed")


def test_the_orientation_is_kept_so_a_photo_does_not_turn_on_its_side(tmp_path):
    got, clean = scrubbed(tmp_path, jpeg(seg(0xE1, exif(6))))
    assert b"Canon" not in clean and b"2024:05" not in clean
    assert clean[2:4] == b"\xff\xe1" and clean[6:12] == b"Exif\0\0"
    tiff = clean[12 : 4 + 2 + struct.unpack(">H", clean[4:6])[0]]
    assert struct.unpack(">HHIH", tiff[10:20]) == (0x0112, 3, 1, 6)
    assert "kept     the orientation" in got.stdout
    plain, clean2 = scrubbed(tmp_path, jpeg(seg(0xE1, exif(1))))
    assert b"Exif" not in clean2 and "kept     the orientation" not in plain.stdout


def test_a_colour_profile_stays_and_other_second_blocks_go(tmp_path):
    data = jpeg(seg(0xE2, b"ICC_PROFILE\0\1\1profile"), seg(0xE2, b"MPF\0multi"))
    _, clean = scrubbed(tmp_path, data)
    assert b"ICC_PROFILE" in clean and b"MPF" not in clean


def test_a_jpeg_with_nothing_hidden_comes_back_the_same_and_says_so(tmp_path):
    data = jpeg(seg(0xE0, b"JFIF\0\1\1\0\0\1\0\1\0\0"))
    got, clean = scrubbed(tmp_path, data)
    assert clean == data and "nothing hidden found" in got.stdout


def test_a_pngs_text_exif_and_time_chunks_are_removed_and_the_rest_kept(tmp_path):
    data = png(chunk(b"tEXt", b"Author\0Jane Doe"), chunk(b"eXIf", b"MM\0*"), chunk(b"tIME", b"\x07\xe8\x05\x01\0\0\0"),
               chunk(b"iTXt", b"Comment\0\0\0\0\0hello"), chunk(b"gAMA", struct.pack(">I", 45455)))  # fmt: skip
    got, clean = scrubbed(tmp_path, data)
    assert got.returncode == 0, got.stderr
    assert (
        b"Jane" not in clean
        and b"eXIf" not in clean
        and b"tIME" not in clean
        and b"hello" not in clean
    )
    assert b"gAMA" in clean and b"IDAT" in clean and clean.endswith(chunk(b"IEND", b""))
    assert (
        "removed  text chunk 'Author'" in got.stdout
        and "removed  eXIf chunk" in got.stdout
    )
    assert got.stdout.splitlines()[-1].endswith(": 4 removed")


def test_a_png_with_a_bad_checksum_is_refused(tmp_path):
    data = bytearray(png(chunk(b"tEXt", b"Author\0Jane")))
    data[data.index(b"Jane")] ^= 1
    got, clean = scrubbed(tmp_path, bytes(data))
    assert got.returncode == 2 and "chunks don't read" in got.stderr and clean == b""


def test_an_office_files_author_times_revision_company_and_custom_properties_are_removed(
    tmp_path,
):
    got, clean = scrubbed(tmp_path, office())
    assert got.returncode == 0, got.stderr
    z = zipfile.ZipFile(io.BytesIO(clean))
    core, app, custom = (
        z.read(f"docProps/{n}.xml").decode() for n in ("core", "app", "custom")
    )
    assert (
        "Jane Doe" not in core
        and "Bob" not in core
        and "2024-01-01" not in core
        and "revision" not in core
    )
    assert "<dc:title>Quarterly plan</dc:title>" in core
    assert (
        "Acme" not in app
        and "Pat" not in app
        and "TotalTime" not in app
        and "<Application>Word</Application>" in app
    )
    assert "Acme" not in custom and "<property" not in custom
    assert (
        "removed  core properties (creator, lastModifiedBy, created, modified, revision, description)"
        in got.stdout
    )
    assert "removed  application properties (Company, Manager, TotalTime)" in got.stdout
    assert "removed  1 custom property" in got.stdout


def test_a_word_files_edit_session_ids_and_the_names_on_comments_and_changes_are_removed(
    tmp_path,
):
    _, clean = scrubbed(tmp_path, office())
    z = zipfile.ZipFile(io.BytesIO(clean))
    doc, comments = (
        z.read("word/document.xml").decode(),
        z.read("word/comments.xml").decode(),
    )
    assert (
        "rsid" not in doc
        and "Bob Lee" not in doc
        and 'w:author=""' in doc
        and "<w:t>Hello</w:t>" in doc
    )
    assert (
        "Jane Doe" not in comments
        and 'w:initials=""' in comments
        and "<w:comment " in comments
    )
    got, _ = scrubbed(tmp_path, office())
    assert "removed  2 edit-session ids in word/document.xml" in got.stdout
    assert (
        "removed  1 author name in word/comments.xml" not in got.stdout
        and "2 author names in word/comments.xml" in got.stdout
    )


def test_an_office_copy_has_no_file_times_or_comment_and_is_the_same_bytes_twice(
    tmp_path,
):
    got, clean = scrubbed(tmp_path, office())
    z = zipfile.ZipFile(io.BytesIO(clean))
    assert (
        all(i.date_time == (1980, 1, 1, 0, 0, 0) for i in z.infolist())
        and z.comment == b""
    )
    assert z.namelist()[0] == "[Content_Types].xml"
    assert scrubbed(tmp_path, office())[1] == clean


def test_a_thumbnail_is_said_and_kept(tmp_path):
    got, clean = scrubbed(tmp_path, office(**{"docProps/thumbnail.jpeg": "x"}))
    assert (
        "note     docProps/thumbnail.jpeg" in got.stdout
        and "docProps/thumbnail.jpeg" in zipfile.ZipFile(io.BytesIO(clean)).namelist()
    )


def test_a_kind_it_does_not_handle_is_refused_not_copied(tmp_path):
    for data in (b"plain text\n", b"%PDF-1.4\n", b"", b"PK\x03\x04junk"):
        got, clean = scrubbed(tmp_path, data)
        assert got.returncode == 2 and clean == b"", data
    zipped = io.BytesIO()
    with zipfile.ZipFile(zipped, "w") as z:
        z.writestr("a.txt", "hello")
    got, _ = scrubbed(tmp_path, zipped.getvalue())
    assert got.returncode == 2 and "not a docx, xlsx or pptx" in got.stderr


def test_a_cut_short_jpeg_is_refused(tmp_path):
    for data in (
        b"\xff\xd8\xff\xe1\x00\x10Exif",
        b"\xff\xd8\xff",
        b"\xff\xd8\xff\xe1\x00\x01",
        b"\xff\xd8\x00\x00",
    ):
        got, clean = scrubbed(tmp_path, data)
        assert got.returncode == 2 and clean == b"", data


def test_the_original_is_unchanged_and_the_copy_is_written_once_private(tmp_path):
    src, to = tmp_path / "in.jpg", tmp_path / "out.jpg"
    data = jpeg(seg(0xE1, exif(6)))
    src.write_bytes(data)
    assert run("--from", str(src), "--to", str(to)).returncode == 0
    assert src.read_bytes() == data and stat.S_IMODE(os.stat(to).st_mode) == 0o600
    again = run("--from", str(src), "--to", str(to))
    assert again.returncode == 2 and "could not write" in again.stderr
    assert (
        run("--from", str(src), "--to", str(tmp_path / "nope" / "o.jpg")).returncode
        == 2
    )


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    f = tmp_path / "a.jpg"
    f.write_bytes(jpeg())
    for argv in ([], ["--from", str(f)], ["--to", str(tmp_path / "o")], ["--from", str(f), "--to", str(tmp_path / "o"), "stray"],
                 ["--from", str(tmp_path / "missing"), "--to", str(tmp_path / "o")]):  # fmt: skip
        assert run(*argv).returncode == 2, argv
    assert "scrub.py" in run().stderr


def test_every_kind_of_tag_that_names_a_person_or_a_device_is_listed(tmp_path):
    tags = {
        0x010E: b"A holiday\0",
        0x0131: b"Gimp\0",
        0x013B: b"Jane\0",
        0x8298: b"(c) Jane\0",
        0x9286: b"hello\0",
        0xA430: b"Jane Doe\0",
        0xA431: b"SN12345\0",
    }
    data_at = 8 + 2 + 12 * len(tags) + 4
    ifd, blob = b"", b""
    for tag, val in sorted(tags.items()):
        ifd += struct.pack(">HHII", tag, 2, len(val), data_at + len(blob))
        blob += val
    tiff = (
        b"MM\0*"
        + struct.pack(">I", 8)
        + struct.pack(">H", len(tags))
        + ifd
        + struct.pack(">I", 0)
        + blob
    )
    got, clean = scrubbed(tmp_path, jpeg(seg(0xE1, b"Exif\0\0" + tiff)))
    assert (
        "removed  Exif (ImageDescription, Software, Artist, Copyright, UserComment, OwnerName, BodySerialNumber):"
        in got.stdout
    )
    assert b"Jane" not in clean and b"SN12345" not in clean
