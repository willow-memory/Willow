"""webarchive: a Safari .webarchive's page read as web-pages reads the same
page saved as .html (address, title, blocks), then its frames under their
addresses; the archive's charset, then the page's, then UTF-8; what isn't a
web archive, or isn't text, skipped and counted; the same bytes twice;
hidden files skipped; the folder unchanged; MIRROR and FOLDER kept apart."""

from __future__ import annotations

import plistlib
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "web-pages"))
import web_pages  # noqa: E402
import webarchive  # noqa: E402

SCRIPT = HERE / "webarchive.py"
PAGE = (
    '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Roof repair</title>'
    "<style>p { color: red }</style><script>var x = '<p>not shown</p>';</script>"
    '<link rel="canonical" href="https://canonical.example/roof"></head><body>'
    "<h1>The roof</h1><p>The roofer comes on Thursday.</p>"
    "<ul><li>Bring the ladder</li><li>Pay &pound;600 on the day</li></ul>"
    '<iframe src="https://maps.example/embed"></iframe></body></html>'
)
FRAME = "<html><head><title>Map</title></head><body><p>12 Harbour Lane, Leeds.</p></body></html>"


def resource(
    data: bytes, mime: str, url: str, charset: str | None = "UTF-8", frame: str = ""
) -> dict:
    """A resource as Safari writes one: its bytes, type, address, frame name,
    and a text encoding only for text."""
    r = {"WebResourceData": data, "WebResourceFrameName": frame,
         "WebResourceMIMEType": mime, "WebResourceURL": url}  # fmt: skip
    if charset is not None:
        r["WebResourceTextEncodingName"] = charset
    return r


def archive(main: dict, frames: list[dict] | None = None) -> bytes:
    """A .webarchive as Safari saves one: a binary property list with the
    page, its pictures and styles, and its frames."""
    top = {
        "WebMainResource": main,
        "WebSubresources": [
            resource(b"\x89PNG\r\n\x1a\n", "image/png", "https://example.org/roof.png", None),
            resource(b"p { color: red }", "text/css", "https://example.org/site.css"),
        ],
    }  # fmt: skip
    if frames:
        top["WebSubframeArchives"] = frames
    return plistlib.dumps(top, fmt=plistlib.FMT_BINARY)


def saved(page: str = PAGE, url: str = "https://example.org/roof", **kw) -> bytes:
    frame = {"WebMainResource": resource(FRAME.encode(), "text/html", "https://maps.example/embed",
                                         frame="<!--framePath //<!--frame0-->-->")}  # fmt: skip
    return archive(resource(page.encode(), "text/html", url), kw.get("frames", [frame]))


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def mirror_of(tmp_path: Path, files: dict[str, bytes]):
    src = tmp_path / "src"
    for rel, data in files.items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_bytes(data)
    out = tmp_path / "out"
    return run("mirror", "--from", str(src), "--to", str(out)), out


def test_a_saved_page_is_its_address_title_and_blocks_then_its_frame(tmp_path):
    got, out = mirror_of(tmp_path, {"roof.webarchive": saved()})
    assert got.returncode == 0, got.stderr
    assert got.stdout.endswith("; skipped 0\n")
    assert (out / "roof.webarchive.txt").read_text(encoding="utf-8") == (
        "address: https://example.org/roof\n\nRoof repair\n\nThe roof\n\n"
        "The roofer comes on Thursday.\n\nBring the ladder\n\nPay £600 on the day\n\n"
        "https://maps.example/embed\n\nMap\n\n12 Harbour Lane, Leeds.\n"
    )


def test_the_page_reads_exactly_as_web_pages_reads_it_saved_as_html(tmp_path):
    """The same page, saved by Chrome as .html with its address noted, comes
    out of web-pages with the same bytes as the archive's page."""
    url = "https://example.org/roof"
    html = f"<!-- saved from url=({len(url):04d}){url} -->\n" + PAGE
    want = web_pages.as_text(html)
    got = webarchive.as_text(saved(frames=[]))
    assert got == want
    assert "not shown" not in got and "color" not in got


def test_the_archives_address_comes_before_the_canonical_link():
    assert webarchive.as_text(saved(frames=[])).startswith(
        "address: https://example.org/roof\n\n"
    )
    assert webarchive.as_text(saved(url="", frames=[])).startswith(
        "address: https://canonical.example/roof\n\n"
    )
    bare = archive(resource(b"<p>Hi.</p>", "text/html", ""))
    assert webarchive.as_text(bare) == "address: not in the file\n\nHi.\n"


def test_frames_follow_the_page_in_order_with_their_own_frames_after_them():
    def frame(url: str, text: str, inner: list | None = None) -> dict:
        a = {"WebMainResource": resource(f"<p>{text}</p>".encode(), "text/html", url)}
        if inner:
            a["WebSubframeArchives"] = inner
        return a

    pdf = {
        "WebMainResource": resource(
            b"%PDF-1.4", "application/pdf", "https://f.example/c.pdf", None
        )
    }
    frames = [frame("https://f.example/a", "First", [frame("https://f.example/a1", "Inside")]),
              pdf, frame("https://f.example/b", "Second")]  # fmt: skip
    got = webarchive.as_text(archive(resource(b"<p>Main.</p>", "text/html", "https://m.example/"), frames))  # fmt: skip
    assert got == (
        "address: https://m.example/\n\nMain.\n\n"
        "https://f.example/a\n\nFirst\n\nhttps://f.example/a1\n\nInside\n\n"
        "https://f.example/c.pdf (application/pdf)\n\n"
        "https://f.example/b\n\nSecond\n"
    )
    empty = {"WebMainResource": resource(b"", "text/html", "")}
    bare = {"WebMainResource": resource(b"<p>No address.</p>", "text/html", "")}
    gif = {"WebMainResource": resource(b"GIF89a", "image/gif", "", None)}
    assert webarchive.as_text(archive(resource(b"<p>M.</p>", "text/html", "u"), [empty, "junk", bare, gif])) == (
        "address: u\n\nM.\n\nNo address.\n\n(image/gif)\n"
    )  # fmt: skip


def test_the_archives_charset_comes_first_then_the_pages_then_utf8():
    latin = "<p>Café prices</p>".encode("latin-1")
    assert "Café prices" in webarchive.as_text(
        archive(resource(latin, "text/html", "u", "ISO-8859-1"))
    )
    meta = b'<meta charset="windows-1252"><p>Caf\xe9 prices</p>'
    assert "Café prices" in webarchive.as_text(
        archive(resource(meta, "text/html", "u", None))
    )
    assert "Café prices" in webarchive.as_text(
        archive(resource(meta, "text/html", "u", "no-such-codec"))
    )
    # the archive's name wins over the page's own meta tag
    sjis = '<meta charset="utf-8"><p>東京</p>'.encode("shift_jis")
    assert "東京" in webarchive.as_text(
        archive(resource(sjis, "text/html", "u", "Shift_JIS"))
    )
    broken = b"<p>Caf\xe9 \xff prices</p>"
    assert "Caf� � prices" in webarchive.as_text(archive(resource(broken, "text/html", "u", None)))  # fmt: skip


def test_a_plain_text_page_is_its_paragraphs_with_no_markup_read_into_it():
    text = b"Notes on the roof\r\n\r\nThe <ladder> is\r\nin  the shed.\r\n\r\n\r\n- pay on Thursday\n- lock the gate  "
    got = webarchive.as_text(
        archive(resource(text, "text/plain", "https://example.org/notes.txt"))
    )
    assert got == (
        "address: https://example.org/notes.txt\n\nNotes on the roof\n\n"
        "The <ladder> is\nin the shed.\n\n- pay on Thursday\n- lock the gate\n"
    )
    frame = {
        "WebMainResource": resource(b"One\n \nTwo", "text/plain", "https://f.example/t")
    }
    got = webarchive.as_text(archive(resource(b"<p>M.</p>", "text/html", "u"), [frame]))
    assert got == "address: u\n\nM.\n\nhttps://f.example/t\n\nOne\n\nTwo\n"


def test_what_isnt_a_web_archive_or_isnt_text_is_skipped_and_counted(tmp_path):
    pdf = archive(
        resource(b"%PDF-1.4", "application/pdf", "https://example.org/a.pdf", None)
    )
    png = archive(resource(b"\x89PNG", "image/png", "https://example.org/a.png", None))
    other = plistlib.dumps({"CFBundleName": "Not an archive"}, fmt=plistlib.FMT_BINARY)
    nodata = plistlib.dumps({"WebMainResource": {"WebResourceMIMEType": "text/html"}})
    got, out = mirror_of(tmp_path, {
        "page.webarchive": saved(), "a.webarchive": pdf, "b.webarchive": png,
        "c.webarchive": other, "d.webarchive": b"<html>not a plist</html>",
        "e.webarchive": nodata, "f.webarchive": plistlib.dumps(["a list"]),
        "page.html": b"<p>another reader's</p>",
    })  # fmt: skip
    assert got.returncode == 0
    assert got.stdout.endswith(
        "wrote 1 files to " + str(out.resolve()) + "; skipped 6\n"
    )
    assert sorted(p.name for p in out.rglob("*")) == ["page.webarchive.txt"]


def test_an_xml_property_list_is_read_too():
    top = {
        "WebMainResource": resource(
            b"<p>Kept.</p>", "text/html", "https://example.org/"
        )
    }
    assert webarchive.as_text(plistlib.dumps(top, fmt=plistlib.FMT_XML)) == (
        "address: https://example.org/\n\nKept.\n"
    )


def test_hidden_skipped_folders_kept_same_bytes_and_the_folder_unchanged(tmp_path):
    files = {"Saved/2024/roof.webarchive": saved(), ".hidden/x.webarchive": saved(),
             "Saved/.y.webarchive": saved(), "UPPER.WEBARCHIVE": saved()}  # fmt: skip
    got, out = mirror_of(tmp_path, files)
    assert got.returncode == 0
    names = sorted(str(p.relative_to(out)) for p in out.rglob("*.txt"))
    assert names == ["Saved/2024/roof.webarchive.txt", "UPPER.WEBARCHIVE.txt"]
    first = (out / "Saved/2024/roof.webarchive.txt").read_bytes()
    src = tmp_path / "src"
    assert sorted(
        str(p.relative_to(src)) for p in src.rglob("*") if p.is_file()
    ) == sorted(files)
    again = tmp_path / "again"
    assert run("mirror", "--from", str(src), "--to", str(again)).returncode == 0
    assert (again / "Saved/2024/roof.webarchive.txt").read_bytes() == first
    for rel, data in files.items():
        assert (src / rel).read_bytes() == data


def test_nothing_to_read_is_42_and_a_bad_command_is_refused(tmp_path):
    got, out = mirror_of(tmp_path, {"notes.txt": b"hello"})
    assert got.returncode == 42 and "wrote 0 files" in got.stdout
    assert not out.exists()
    assert run().returncode == 2 and "mirror --from FOLDER --to MIRROR" in run().stderr
    assert (
        run("mirror", "--from", str(tmp_path / "nope"), "--to", str(out)).returncode
        == 2
    )
    src = tmp_path / "src"
    inner = run("mirror", "--from", str(src), "--to", str(src / "m"))
    assert inner.returncode == 2 and "inside each other" in inner.stderr
    assert run("mirror", "--from", str(src / "x"), "--to", str(src)).returncode == 2
    assert run("mirror", "--from", str(src), "--to", str(src)).returncode == 2
    assert not (src / "m").exists()
    assert webarchive.main(["mirror", "--from", str(src)]) == 2


def test_no_word_it_adds_answers_a_question_about_something_the_folder_lacks(tmp_path):
    """No word the reader writes sits in most passages, so pairing one with a
    word the folder lacks is served nothing; real questions still land."""
    sys.path.insert(0, str(HERE.parents[2]))
    import kernel

    garden = "<title>Garden</title><p>Plant the tomatoes in May.</p><p>Water them at dusk.</p>"
    got, out = mirror_of(tmp_path, {"Saved/roof.webarchive": saved(),
                                    "Saved/notes.webarchive": saved(page=garden, url="https://example.org/garden")})  # fmt: skip
    assert got.returncode == 0
    pile = kernel.chunks(out)
    for path in {c["path"] for c in pile}:
        mine = [c for c in pile if c["path"] == path]
        seen: dict[str, int] = {}
        for c in mine:
            for w in set(kernel.words(c["text"])) - kernel.FUNCTION:
                seen[w] = seen.get(w, 0) + 1
        common = [w for w, n in seen.items() if n * 2 > len(mine)]
        assert common == [], f"{path}: {common} in most passages"
    for added in ("frame", "marathon"):
        assert kernel.rank(pile, f"volcano {added}") == [], added
    # the one label it writes, once a file, as web-pages does: "address" is
    # served only the address line, which is what a person asking it wants
    assert {c["text"].split(":")[0] for c in kernel.rank(pile, "volcano address")} == {
        "address"
    }
    where = kernel.rank(pile, "address of the garden page")[0]["text"]
    assert where == "address: https://example.org/garden"
    for q, want in (("when does the roofer come", "Thursday"),
                    ("when to plant the tomatoes", "May"),
                    ("Harbour Lane map", "Harbour Lane")):  # fmt: skip
        assert want in kernel.rank(pile, q)[0]["text"], q
