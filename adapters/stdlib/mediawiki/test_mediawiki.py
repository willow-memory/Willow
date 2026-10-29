"""mediawiki: a MediaWiki dump page by page, markup off; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "mediawiki.py"
spec = importlib.util.spec_from_file_location("mediawiki", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE = (
    b'<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.10/" version="0.10"><siteinfo><sitename>Garden</sitename></siteinfo>'
    b'<page><title>Tomatoes</title><ns>0</ns><id>1</id><revision><timestamp>2024-01-01T10:00:00Z</timestamp><text xml:space="preserve">old text</text></revision>'
    b"<revision><timestamp>2024-03-03T10:00:00Z</timestamp><text xml:space=\"preserve\">'''Tomatoes''' want [[sun|six hours of sun]].{{cite|x}}&lt;ref&gt;n&lt;/ref&gt;\n== Growing ==\n* plant in [[Bed 2]]\n[[Category:Veg]]</text></revision></page>"
    b"<page><title>Maters</title><ns>0</ns><id>2</id><revision><timestamp>2024-02-02T00:00:00Z</timestamp><text>#REDIRECT [[Tomatoes]]</text></revision></page></mediawiki>"
)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def mirror_of(
    tmp_path: Path, files: dict[str, bytes]
) -> tuple[subprocess.CompletedProcess, Path]:
    src = tmp_path / "src"
    for rel, data in files.items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_bytes(data)
    out = tmp_path / "out"
    return run("mirror", "--from", str(src), "--to", str(out)), out


def test_a_page_is_its_title_the_day_of_its_last_revision_and_its_text():
    out = mod.convert(SAMPLE)
    assert out.startswith(
        "page: Tomatoes (changed 2024-03-03)\n\nTomatoes want six hours of sun.\nGrowing\nplant in Bed 2\n"
    )
    assert "old text" not in out


def test_a_redirect_is_said_and_pages_are_separate_blocks():
    out = mod.convert(SAMPLE)
    assert out.endswith("page: Maters (changed 2024-02-02)\n\nredirect to Tomatoes\n")
    assert out.count("page: ") == 2


def test_markup_comes_off():
    p = mod.plain
    assert (
        p("'''bold''' and ''italic'' and '''''both'''''") == "bold and italic and both"
    )
    assert p("[[a|b]] [[c]] [[Category:x]] [[File:y.png|thumb|[[z]] cap]]") == "b c"
    assert p("[http://x.org a link] and [http://x.org] and") == "a link and and"
    assert p("a{{t|{{u}}}}b") == "ab" and p("a<!-- hidden -->b") == "ab"
    assert p("x<ref name=a>cite</ref>y<ref name=b />z") == "xyz"
    assert (
        p("== H2 ==\n=== H3 ===\n* item\n# num\n: indent")
        == "H2\nH3\nitem\nnum\nindent"
    )
    assert p("{|\n|-\n! head !! two\n|-\n| cell || other\n|}") == "head two\ncell other"
    assert p("a<br/>b<br>c") == "a\nb\nc"
    assert p("fish &amp; chips &nbsp;x") == "fish & chips x"
    assert p("a\n\n\n\nb") == "a\n\nb"
    assert p("#redirect [[Target#Section|shown]]") == "redirect to Target"
    assert p("") == ""


def test_other_xml_and_an_entity_bomb_are_not_read():
    assert mod.convert(b"<root><page/></root>") is None
    bomb = b'<!DOCTYPE mediawiki [<!ENTITY a "aaaa">]><mediawiki><page><title>x</title><revision><text>&a;&a;</text></revision></page></mediawiki>'
    assert mod.convert(bomb) is None
    assert mod.convert(b"<mediawiki><siteinfo/></mediawiki>") is None, "no pages"
    assert (
        mod.convert(
            b"<mediawiki><page><title></title><revision><text>x</text></revision></page></mediawiki>"
        )
        is None
    )


def test_a_page_without_text_or_date_is_still_listed():
    out = mod.convert(
        b"<mediawiki><page><title>Empty</title><revision><text></text></revision></page></mediawiki>"
    )
    assert out == "page: Empty\n"


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"wiki/dump.xml": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "wiki/dump.xml.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "wiki/dump.xml": SAMPLE,
            ".hid/wiki/dump.xml": SAMPLE,
            ".wiki/dump.xml": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["wiki/dump.xml.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"wiki/dump.xml": SAMPLE})
    before = (tmp_path / "src" / "wiki/dump.xml").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "wiki/dump.xml.txt").read_bytes() == (
        out / "wiki/dump.xml.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "wiki/dump.xml").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path, {"good.xml": SAMPLE, "bad.xml": b"<mediawiki><page>"}
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.xml.txt").is_file() and not (out / "bad.xml.txt").exists()


def test_a_folder_with_nothing_to_read_waits_on_you(tmp_path):
    got, _ = mirror_of(tmp_path, {"notes.md": b"nothing here\n"})
    assert got.returncode == 42 and "wrote 0 files" in got.stdout


def test_a_mirror_inside_the_folder_or_the_folder_inside_it_is_refused(tmp_path):
    (tmp_path / "src").mkdir()
    for to in (tmp_path / "src" / "m", tmp_path):
        got = run("mirror", "--from", str(tmp_path / "src"), "--to", str(to))
        assert got.returncode == 2 and got.stderr.startswith("refused")
    assert (
        run(
            "mirror", "--from", str(tmp_path / "missing"), "--to", str(tmp_path / "m")
        ).returncode
        == 2
    )


def test_a_bad_command_line_says_how_to_run_it():
    for argv in (
        [],
        ["mirror"],
        ["mirror", "--from", "a"],
        ["nope", "--from", "a", "--to", "b"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "mediawiki.py" in got.stderr
