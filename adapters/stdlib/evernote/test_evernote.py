"""evernote: an Evernote export as its notes with notebook, dates, tags and text; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "evernote.py"
spec = importlib.util.spec_from_file_location("evernote", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE = (
    b'<?xml version="1.0" encoding="UTF-8"?><en-export export-date="20240306T000000Z"><note><title>Allotment plan</title>'
    b'<content><![CDATA[<?xml version="1.0" encoding="UTF-8"?><en-note><div>Plot 14 gets the beans.</div><div><en-todo checked="true"/>Order seed</div><div><en-todo/>Fix the gate</div></en-note>]]></content>'
    b"<created>20240303T101500Z</created><updated>20240305T080000Z</updated><tag>garden</tag><tag>plots</tag>"
    b"<note-attributes><author>Ada Example</author><source-url>https://example.org/plots</source-url></note-attributes>"
    b"<resource><resource-attributes><file-name>plan.pdf</file-name></resource-attributes></resource></note></en-export>"
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


def test_a_note_is_its_title_notebook_dates_tags_source_attachments_and_text():
    out = mod.convert(SAMPLE, "Garden")
    assert out == (
        "note: Allotment plan (notebook: Garden)\ncreated: 2024-03-03 10:15; updated: 2024-03-05 08:00\ntags: garden, plots\n"
        "from: Ada Example, https://example.org/plots\nattachments: plan.pdf\n\nPlot 14 gets the beans.\n[x] Order seed\n[ ] Fix the gate\n"
    )


def test_the_notebook_is_the_export_files_name(tmp_path):
    got, out = mirror_of(tmp_path, {"Garden.enex": SAMPLE})
    assert (
        "note: Allotment plan (notebook: Garden)"
        in (out / "Garden.enex.txt").read_text()
    )


def note(content: str, extra: str = "") -> bytes:
    return f"<en-export><note><title>T</title><content><![CDATA[<en-note>{content}</en-note>]]></content>{extra}</note></en-export>".encode()


def test_lists_line_breaks_tables_and_links_are_read_as_text():
    out = mod.convert(
        note(
            "<ul><li>one</li><li>two</li></ul><div>a<br/>b</div><table><tr><td>x</td><td>y</td></tr></table><a href='u'>link</a>"
        )
    )
    assert out == "note: T\n\n- one\n- two\na\nb\nx y\nlink\n"


def test_html_entities_in_the_body_are_read_as_the_characters_they_are():
    assert (
        mod.convert(note("Tom&nbsp;&amp;&nbsp;Jerry &lt;3 caf&eacute;"))
        == "note: T\n\nTom & Jerry <3 café\n"
    )


def test_several_notes_are_separate_paragraphs_in_the_files_order():
    two = b"<en-export><note><title>One</title><content>a</content></note><note><title>Two</title><content>b</content></note></en-export>"
    out = mod.convert(two)
    assert out.index("note: One") < out.index("note: Two") and "\n\nnote: Two" in out


def test_a_note_with_no_title_or_content_is_still_a_paragraph():
    assert mod.convert(b"<en-export><note></note></en-export>") == "note: (untitled)\n"


def test_something_that_is_not_enex_or_has_no_note_is_not_a_result():
    assert mod.convert(b"<other/>") is None
    try:
        mod.convert(b"not xml")
    except mod.ERRORS:
        return
    raise AssertionError


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"export/Garden.enex": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "export/Garden.enex.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "export/Garden.enex": SAMPLE,
            ".hid/export/Garden.enex": SAMPLE,
            ".export/Garden.enex": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["export/Garden.enex.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"export/Garden.enex": SAMPLE})
    before = (tmp_path / "src" / "export/Garden.enex").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "export/Garden.enex.txt").read_bytes() == (
        out / "export/Garden.enex.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "export/Garden.enex").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path, {"good.enex": SAMPLE, "bad.enex": b"<en-export><note>"}
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.enex.txt").is_file() and not (out / "bad.enex.txt").exists()


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
        assert got.returncode == 2 and "evernote.py" in got.stderr


def test_a_time_is_written_as_date_and_minute_and_anything_else_is_left_as_it_is():
    assert (
        mod.when("20240303T101500Z") == "2024-03-03 10:15"
        and mod.when("20240303T1015") == "2024-03-03 10:15"
    )
    assert (
        mod.when("20240303T10") == "20240303T10"
        and mod.when("20240303") == "20240303"
        and mod.when("") == ""
        and mod.when(None) == ""
    )
