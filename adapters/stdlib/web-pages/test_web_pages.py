"""web-pages: a saved page's blocks as paragraphs, headed by the address it
came from (a browser's note, an .mhtml's header, the canonical link, og:url,
or said to be absent); its own charset; what can't be read skipped."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import web_pages  # noqa: E402

SCRIPT = HERE / "web_pages.py"
BODY = "<h1>Terms</h1><p>We keep data.</p><ul><li>One item</li></ul>"
MHTML = (
    "From: <Saved by Blink>\r\n"
    "Snapshot-Content-Location: https://example.org/terms\r\n"
    "Subject: Terms\r\n"
    "MIME-Version: 1.0\r\n"
    'Content-Type: multipart/related; type="text/html"; boundary="B"\r\n\r\n'
    "--B\r\n"
    "Content-Type: text/html; charset=utf-8\r\n"
    "Content-Transfer-Encoding: quoted-printable\r\n"
    "Content-Location: https://example.org/terms-part\r\n\r\n"
    "<p>We don=E2=80=99t sell data.</p><p>A long line that the encoder breaks=\r\n"
    " in two.</p>\r\n"
    "--B\r\n"
    "Content-Type: text/css\r\n\r\n"
    "p { color: red }\r\n"
    "--B--\r\n"
)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def test_a_saved_page_is_its_blocks_under_its_address(tmp_path):
    src = tmp_path / "saved"
    src.mkdir()
    (src / "terms.html").write_text(
        "<!-- saved from url=(0025)https://example.org/terms -->\n"
        f'<html><head><link rel="canonical" href="https://other.example/"></head>{BODY}</html>'
    )
    got = run("mirror", "--from", str(src), "--to", str(tmp_path / "m"))
    assert got.returncode == 0 and got.stdout.endswith("; skipped 0\n")
    assert (tmp_path / "m" / "terms.html.txt").read_text() == (
        "address: https://example.org/terms\n\nTerms\n\nWe keep data.\n\nOne item\n"
    )


def test_an_mhtml_page_is_read_from_its_part():
    page, said = web_pages.mhtml(MHTML.encode())
    assert said == "https://example.org/terms"  # the snapshot's, not the part's
    assert web_pages.as_text(page, said) == (
        "address: https://example.org/terms\n\nWe don’t sell data.\n\n"
        "A long line that the encoder breaks in two.\n"
    )
    bare = MHTML.replace("Snapshot-Content-Location: https://example.org/terms\r\n", "")
    assert web_pages.mhtml(bare.encode())[1] == "https://example.org/terms-part"
    assert web_pages.mhtml(b"Subject: no page\r\n\r\nplain text") is None


def test_the_address_comes_from_the_first_thing_that_says_it():
    canon = '<link href="https://a.example/" rel="canonical">'
    og = '<meta property="og:url" content="https://b.example/">'
    assert web_pages.address(f"<head>{og}{canon}</head>") == "https://a.example/"
    assert web_pages.address(f"<head>{og}</head>") == "https://b.example/"
    assert web_pages.address(
        '<meta content="https://c.example/" property="og:url">'
    ) == ("https://c.example/")
    assert web_pages.address(f"<head>{og}</head>", "https://said.example/") == (
        "https://said.example/"
    )
    assert web_pages.as_text("<p>Hi.</p>").startswith("address: not in the file\n\n")


def test_a_page_in_its_own_charset_and_one_that_cant_be_read(tmp_path):
    src = tmp_path / "saved"
    src.mkdir()
    (src / "old.htm").write_bytes(b'<meta charset="iso-8859-1"><p>Caf\xe9 hours.</p>')
    (src / "bad.html").write_bytes(b"<p>\xff\xfe no charset said</p>")
    (src / "odd.html").write_bytes(b'<meta charset="no-such"><p>\xff</p>')
    (src / "notes.txt").write_text("not a page")
    got = run("mirror", "--from", str(src), "--to", str(tmp_path / "m"))
    assert got.returncode == 0 and got.stdout.endswith("wrote 1 files to "
                                                       f"{(tmp_path / 'm').resolve()}; skipped 2\n")  # fmt: skip
    assert (tmp_path / "m" / "old.htm.txt").read_text().endswith("Café hours.\n")
    assert sorted(p.name for p in (tmp_path / "m").iterdir()) == ["old.htm.txt"]


def test_a_charset_is_read_only_from_the_first_4096_bytes():
    head = b'<meta charset="cp1252'  # cut one byte short, "cp125" is no codec
    pad = b" " * (4096 - len(head))
    page = b'"><p>Caf\xe9</p>'
    assert web_pages.decode(pad + head + page).endswith("<p>Café</p>")  # all within
    assert web_pages.decode(b" " + pad + head + page) is None  # its last byte past


#: the shape Chrome 154 wrote for live.py's check: no charset on the page's
#: part, only in the page's own meta tag (shortened; the boundary is Chrome's)
CHROME = (
    "From: <Saved by Blink>\r\n"
    "Snapshot-Content-Location: file:///tmp/with%20space/pages/terms.html\r\n"
    "Subject: Terms\r\n"
    "MIME-Version: 1.0\r\n"
    "Content-Type: multipart/related;\r\n"
    '\ttype="text/html";\r\n'
    '\tboundary="----MultipartBoundary--3sOx----"\r\n\r\n\r\n'
    "------MultipartBoundary--3sOx----\r\n"
    "Content-Type: text/html\r\n"
    "Content-Transfer-Encoding: quoted-printable\r\n"
    "Content-Location: file:///tmp/with%20space/pages/terms.html\r\n\r\n"
    '<!DOCTYPE html><html><head><meta http-equiv=3D"Content-Type" content=3D"tex=\r\n'
    't/html; charset=3DUTF-8"><title>Terms</title></head>\r\n'
    "<body><p>We don=E2=80=99t sell data.</p></body></html>\r\n"
    "------MultipartBoundary--3sOx------\r\n"
)


def test_a_chrome_mhtml_whose_part_names_no_charset_is_read_as_its_page_says():
    page, said = web_pages.mhtml(CHROME.encode())
    assert said == "file:///tmp/with%20space/pages/terms.html"
    assert web_pages.as_text(page, said).endswith("Terms\n\nWe don’t sell data.\n")
    latin = CHROME.replace("=E2=80=99", "=92").replace("UTF-8", "windows-1252")
    assert "don’t" in web_pages.mhtml(latin.encode())[0]
    bad = CHROME.replace(
        "Content-Type: text/html\r\n", "Content-Type: text/html; charset=nope\r\n"
    )
    assert web_pages.mhtml(bad.encode()) is None


def test_the_mark_of_the_webs_zone_marker_is_not_an_address():
    marked = "<!-- saved from url=(0014)about:internet -->\n"
    canon = '<link rel="canonical" href="https://a.example/">'
    assert web_pages.address(marked + canon) == "https://a.example/"
    assert web_pages.address(marked + "<p>Hi.</p>") == ""
    assert web_pages.address("<!-- saved from url=(0018)https://b.example/ -->") == (
        "https://b.example/"
    )


PAGE = (
    "<html><body>\n"
    "<header><h1>The Mill</h1></header>\n"
    '<nav><ul><li><a href="/a">Departments</a></li></ul></nav>\n'
    "<p>The mill opened in 1880.</p>\n"
    "<aside><p>Related links</p></aside>\n"
    "<p>It closed in 1921.</p>\n"
    "<footer><p>Copyright</p></footer>\n"
    "</body></html>\n"
)


def test_body_only_leaves_out_menus_and_keeps_the_page():
    kept = web_pages.as_text(PAGE, body_only=True)
    assert kept == (
        "address: not in the file\n\nThe Mill\n\n"
        "The mill opened in 1880.\n\nIt closed in 1921.\n"
    )  # the header's title stays; nav, aside and footer words do not
    assert "Departments" in web_pages.as_text(PAGE)  # without it, nothing is cut
    assert web_pages.as_text(PAGE) == web_pages.as_text(PAGE, "", False)


def test_an_element_that_says_its_role_is_a_menu_is_one():
    page = (
        '<div role="navigation"><p>Menu words</p></div><p>Kept.</p>'
        '<div role="Complementary"><p>Side words</p></div>'
        '<div role="foo contentinfo"><p>Foot words</p></div>'
        '<div role="banner"><p>Banner words</p></div>'
        '<div role="main"><p>Main words</p></div>'
    )
    got = web_pages.as_text(page, body_only=True)
    assert got == (
        "address: not in the file\n\nKept.\n\nBanner words\n\nMain words\n"
    )  # the role may sit among others, in any case; banner and main stay


def test_a_menu_inside_a_menu_ends_with_its_own_end_tag():
    page = "<nav><p>A</p><nav><p>B</p></nav><p>C</p></nav><p>After.</p>"
    assert web_pages.as_text(page, body_only=True).endswith("\n\nAfter.\n")
    assert "C" not in web_pages.as_text(page, body_only=True).split("\n\n")[1:]
    two = "<nav>one</nav><p>Mid.</p><nav>two</nav><p>End.</p>"
    assert web_pages.as_text(two, body_only=True) == (
        "address: not in the file\n\nMid.\n\nEnd.\n"
    )  # both menus go, and what lies between them stays


def test_a_menu_that_never_closes_is_kept_not_guessed_at():
    page = "<p>Before.</p><nav><p>Left open.</p><p>After.</p>"
    got = web_pages.as_text(page, body_only=True)
    assert got == web_pages.as_text(page)
    assert "Left open." in got and "After." in got


def test_a_menu_named_in_a_comment_or_an_attribute_is_not_a_menu():
    page = (
        '<!-- <nav><p>Hidden</p></nav> --><p>Kept.</p><p title="<nav>">Also kept.</p>'
    )
    got = web_pages.as_text(page, body_only=True)
    assert "Kept." in got and "Also kept." in got


def test_the_cut_is_found_on_the_right_line_and_column():
    page = "<p>One.</p>\r\n<p>Two.</p>\r\n  <nav>\r\n<p>Gone.</p>\r\n</nav>\r\n<p>Three.</p>"
    assert (
        web_pages.without_chrome(page)
        == "<p>One.</p>\r\n<p>Two.</p>\r\n  \n\r\n<p>Three.</p>"
    )
    one = "<nav>x</nav>tail"
    assert web_pages.without_chrome(one) == "\ntail"  # a menu at the very start


def test_body_only_is_a_flag_of_mirror_and_nothing_else_is(tmp_path):
    src = tmp_path / "saved"
    src.mkdir()
    (src / "p.html").write_text(PAGE)
    plain = run("mirror", "--from", str(src), "--to", str(tmp_path / "a"))
    body = run("mirror", "--from", str(src), "--to", str(tmp_path / "b"), "--body-only")
    assert plain.returncode == 0 and body.returncode == 0
    assert "Departments" in (tmp_path / "a" / "p.html.txt").read_text()
    assert "Departments" not in (tmp_path / "b" / "p.html.txt").read_text()
    for extra in ("--body", "--all", "body-only"):
        got = run("mirror", "--from", str(src), "--to", str(tmp_path / "c"), extra)
        assert got.returncode == 2 and not (tmp_path / "c").exists()
    assert run("--body-only").returncode == 2
