"""Tests for books.py. Every sample is built here: made-up books, no fixture files."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOKS = HERE / "books.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]

CLIPPINGS = (
    "Made-Up Harbour (Ada Example)\n"
    "- Your Highlight on page 12 | Location 180-182 | "
    "Added on Sunday, 3 March 2024 10:15:22\n"
    "\n"
    "The tide keeps its own calendar.\n"
    "\n"
    "==========\n"
    "Made-Up Harbour (Ada Example)\n"
    "- Your Bookmark on page 13 | Location 200 | "
    "Added on Monday, 4 March 2024 09:00:00\n"
    "\n"
    "\n"
    "==========\n"
    "Another Shore (Bo Sample)\n"
    "- Your Note on page 4 | Location 60 | "
    "Added on Sunday, March 3, 2024 10:15:22 PM\n"
    "\n"
    "Remember the second pier.\n"
    "\n"
    "==========\n"
    "Made-Up Harbour (Ada Example)\n"
    "- Your Highlight on page 40 | Location 610 | "
    "Added on Tuesday, 5 March 2024 07:30:00\n"
    "\n"
    "Salt keeps the lamps burning.\n"
    "\n"
    "==========\n"
)

EXPECTED_MIRROR = (
    "2024-03-03  Another Shore (Bo Sample), page 4\n"
    "Remember the second pier.\n"
    "\n"
    "2024-03-03  Made-Up Harbour (Ada Example), page 12\n"
    "The tide keeps its own calendar.\n"
    "\n"
    "2024-03-05  Made-Up Harbour (Ada Example), page 40\n"
    "Salt keeps the lamps burning.\n"
    "\n"
)

CONTAINER = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

OPF = """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Made-Up Almanac</dc:title>
    <dc:creator>Cy Sample</dc:creator>
  </metadata>
  <manifest>
    <item id="c1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="c2" href="ch2.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="c2"/>
    <itemref idref="c1"/>
  </spine>
</package>
"""

CH1 = """<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>One</title><style>p { color: red; }</style></head>
<body>
<h1>Chapter one</h1>
<p>The first <em>chapter</em> of the almanac.</p>
<script>var secret = 1;</script>
</body>
</html>
"""

CH2 = """<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><script>alert("x")</script></head>
<body>
<p>Second chapter, read first.</p>
<div>Line &amp; more</div>
</body>
</html>
"""


def make_epub(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", CONTAINER)
        z.writestr("OEBPS/content.opf", OPF)
        z.writestr("OEBPS/ch1.xhtml", CH1)
        z.writestr("OEBPS/ch2.xhtml", CH2)


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *map(str, argv)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def mirror(folder: Path, to: Path) -> subprocess.CompletedProcess:
    return run(BOOKS, "mirror", "--from", folder, "--to", to)


def snapshot(folder: Path) -> dict[str, bytes]:
    return {
        p.relative_to(folder).as_posix(): p.read_bytes()
        for p in sorted(folder.rglob("*"))
        if p.is_file()
    }


def make_library(folder: Path) -> None:
    (folder / "kindle").mkdir(parents=True)
    (folder / "kindle" / "My Clippings.txt").write_text(CLIPPINGS, encoding="utf-8")
    (folder / "books").mkdir()
    make_epub(folder / "books" / "almanac.epub")


def test_highlight_has_iso_date_and_page_and_note_is_kept(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    make_library(folder)
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    text = (to / "kindle" / "My Clippings.txt.txt").read_text(encoding="utf-8")
    assert "2024-03-03  Made-Up Harbour (Ada Example), page 12\n" in text
    assert "The tide keeps its own calendar.\n" in text
    assert "Remember the second pier.\n" in text  # a note is kept


def test_both_added_on_formats_read_to_the_same_iso_day(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    (folder / "kindle").mkdir(parents=True)
    (folder / "kindle" / "My Clippings.txt").write_text(CLIPPINGS, encoding="utf-8")
    assert mirror(folder, to).returncode == 0
    text = (to / "kindle" / "My Clippings.txt.txt").read_text(encoding="utf-8")
    # "3 March 2024" (day first) and "March 3, 2024 ... PM" (month first) both give 03-03.
    assert text.count("2024-03-03  ") == 2
    assert "2024-03-05  Made-Up Harbour (Ada Example), page 40\n" in text


def test_bookmark_is_skipped_and_books_grouped_by_title(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    (folder / "kindle").mkdir(parents=True)
    (folder / "kindle" / "My Clippings.txt").write_text(CLIPPINGS, encoding="utf-8")
    assert mirror(folder, to).returncode == 0
    text = (to / "kindle" / "My Clippings.txt.txt").read_text(encoding="utf-8")
    assert "Monday" not in text and "page 13" not in text  # the bookmark
    assert text == EXPECTED_MIRROR  # grouped, sorted by title, file order kept


def test_bom_is_stripped(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    (folder / "kindle").mkdir(parents=True)
    (folder / "kindle" / "My Clippings.txt").write_bytes(
        b"\xef\xbb\xbf" + CLIPPINGS.encode("utf-8")
    )
    assert mirror(folder, to).returncode == 0
    text = (to / "kindle" / "My Clippings.txt.txt").read_text(encoding="utf-8")
    assert text == EXPECTED_MIRROR
    assert not text.startswith("﻿")


def test_epub_text_in_spine_order_with_book_line_and_no_script_or_style(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    (folder / "books").mkdir(parents=True)
    make_epub(folder / "books" / "almanac.epub")
    assert mirror(folder, to).returncode == 0
    text = (to / "books" / "almanac.epub.txt").read_text(encoding="utf-8")
    assert text.startswith("book: Made-Up Almanac by Cy Sample\n\n")
    assert "Second chapter, read first." in text
    assert "Line & more" in text
    assert "The first chapter of the almanac." in text
    # spine lists ch2 before ch1, so ch2's text comes first
    assert text.index("Second chapter") < text.index("The first chapter")
    for dropped in ("alert", "secret", "color"):
        assert dropped not in text
    assert text.endswith("\n")


def test_mirror_naming_and_hidden_parts_skipped(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    make_library(folder)
    (folder / ".hidden").mkdir()
    (folder / ".hidden" / "My Clippings.txt").write_text(CLIPPINGS, encoding="utf-8")
    (folder / "my clippings.TXT").write_text(CLIPPINGS, encoding="utf-8")
    assert mirror(folder, to).returncode == 0
    made = sorted(p.relative_to(to).as_posix() for p in to.rglob("*") if p.is_file())
    assert made == [
        "books/almanac.epub.txt",
        "kindle/My Clippings.txt.txt",
        "my clippings.TXT.txt",
    ]


def test_corrupt_epub_is_skipped_and_counted(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    make_library(folder)
    (folder / "broken.epub").write_bytes(b"this is not a zip file")
    got = mirror(folder, to)
    assert got.returncode == 0
    assert got.stdout.strip() == f"wrote 2 files to {to}; skipped 1"
    assert not (to / "broken.epub.txt").exists()


def test_mirror_inside_folder_is_refused(tmp_path):
    folder = tmp_path / "f"
    folder.mkdir()
    make_library(folder)
    before = snapshot(folder)
    got = mirror(folder, folder / "out")
    assert got.returncode == 2
    assert got.stderr.startswith("refused:")
    assert snapshot(folder) == before


def test_folder_inside_mirror_is_refused(tmp_path):
    to = tmp_path / "m"
    folder = to / "src"
    folder.mkdir(parents=True)
    make_library(folder)
    got = mirror(folder, to)
    assert got.returncode == 2
    assert got.stderr.startswith("refused:")


def test_folder_that_is_not_a_folder_is_refused(tmp_path):
    got = mirror(tmp_path / "missing", tmp_path / "m")
    assert got.returncode == 2
    assert got.stderr.startswith("refused:")


def test_nothing_readable_exits_42(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    (folder / "notes.txt").write_text("Nothing to read here.\n", encoding="utf-8")
    (folder / "broken.epub").write_bytes(b"not a zip")
    (folder / "My Clippings.txt").write_bytes(b"\xff\xfe not utf-8 \x80")
    got = mirror(folder, to)
    assert got.returncode == 42
    assert got.stdout.strip() == f"wrote 0 files to {to}; skipped 2"


def test_originals_are_unchanged(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    make_library(folder)
    before = snapshot(folder)
    assert mirror(folder, to).returncode == 0
    assert snapshot(folder) == before  # same files, same bytes: nothing added


def test_two_runs_give_identical_bytes(tmp_path):
    folder = tmp_path / "f"
    folder.mkdir()
    make_library(folder)
    first, second = tmp_path / "m1", tmp_path / "m2"
    assert mirror(folder, first).returncode == 0
    assert mirror(folder, second).returncode == 0

    def digests(root: Path) -> dict[str, str]:
        return {
            p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*"))
            if p.is_file()
        }

    assert digests(first) == digests(second)
    assert all(v.read_bytes().endswith(b"\n") for v in first.rglob("*") if v.is_file())


def test_kernel_serves_a_highlight_from_the_mirror(tmp_path):
    folder, to, box, key = (
        tmp_path / "f",
        tmp_path / "m",
        tmp_path / "box",
        tmp_path / "key",
    )
    folder.mkdir()
    make_library(folder)
    assert mirror(folder, to).returncode == 0
    init = run(KERNEL, "init", "--box", box, "--pile", to, "--key", key, *NOW)
    assert init.returncode == 0, init.stderr
    got = run(KERNEL, "bite", "--box", box, *NOW, "salt lamps burning")
    assert got.returncode == 0, got.stderr
    assert "Salt keeps the lamps burning." in got.stdout
