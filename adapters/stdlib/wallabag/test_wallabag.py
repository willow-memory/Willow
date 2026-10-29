"""wallabag: a wallabag export entry by entry with tags and highlights; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "wallabag.py"
spec = importlib.util.spec_from_file_location("wallabag", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'[{"title":"Tomato growing guide","url":"https://example.org/tomatoes","created_at":"2024-03-02T10:00:00+0000","tags":["garden",{"label":"veg"},5],'
    b'"content":"<p>Plant   after <b>frost</b>.</p><script>x()</script><p>Stake early.</p>","annotations":[{"quote":"Stake early.","text":"do this in April"}]},'
    b'{"title":"","url":"https://example.org/older","created_at":"2024-01-01T00:00:00+0000","content":"<p>Old &amp; dusty.</p>"}, 7]'
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


def test_entries_come_oldest_first_with_url_tags_highlights_and_the_article_text():
    assert mod.convert(SAMPLE) == (
        "2024-01-01\nurl: https://example.org/older\n\nOld & dusty.\n\n"
        "2024-03-02  Tomato growing guide\nurl: https://example.org/tomatoes\ntags: garden, veg\n"
        'highlight: "Stake early." (note: do this in April)\n\nPlant after frost.\nStake early.\n'
    )


def test_a_tag_between_a_word_and_its_punctuation_leaves_no_gap_and_block_ends_break_lines():
    out = mod.convert(
        b'[{"url":"u","content":"<h1>Title</h1><p>a <i>b</i>, <b>c</b> (<u>d</u>)!</p><ul><li>one</li><li>two</li></ul>x<br>y"}]'
    )
    assert out == "u\nurl: u\n\nTitle\na b, c (d)!\none\ntwo\nx\ny\n"


def test_the_order_is_by_the_day_saved_with_undated_entries_first():
    doc = b'[{"title":"Alpha","url":"a","content":"","created_at":"2024-03-02T00:00:00+0000"},{"title":"Zed","url":"z","content":""}]'
    assert mod.convert(doc).splitlines()[0] == "Zed"


def test_a_highlight_may_have_only_a_quote_or_only_a_note():
    one = b'[{"url":"https://x.org","content":"","annotations":[{"quote":"q"},{"text":"n"},{},{"quote":" ","text":" "},5]}]'
    assert (
        mod.convert(one)
        == 'https://x.org\nurl: https://x.org\nhighlight: "q"\nhighlight: (note: n)\n'
    )


def test_an_entry_with_no_title_or_date_is_named_by_its_url_and_one_with_no_url_is_not_an_entry():
    assert (
        mod.convert(b'[{"url":"https://x.org","content":"hi"}]')
        == "https://x.org\nurl: https://x.org\n\nhi\n"
    )
    assert mod.convert(b'[{"title":"T","content":"hi"}]') is None
    assert mod.convert(b'[{"url":"https://x.org","content":7}]') is None


def test_json_that_is_not_an_export_is_not_a_result_and_bad_json_is_an_error():
    for other in (b"{}", b"[]", b"[1,2]", b'{"url":"x","content":"y"}'):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"[nope")
    except ValueError:
        pass
    else:
        raise AssertionError("bad json")


def test_a_json_file_that_is_no_export_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"a.json": SAMPLE, "b.json": b'{"other": 1}'})
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"export/wallabag.json": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "export/wallabag.json.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "export/wallabag.json": SAMPLE,
            ".hid/export/wallabag.json": SAMPLE,
            ".export/wallabag.json": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["export/wallabag.json.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"export/wallabag.json": SAMPLE})
    before = (tmp_path / "src" / "export/wallabag.json").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "export/wallabag.json.txt").read_bytes() == (
        out / "export/wallabag.json.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "export/wallabag.json").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(tmp_path, {"good.json": SAMPLE, "bad.json": b"[nope"})
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.json.txt").is_file() and not (out / "bad.json.txt").exists()


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
        assert got.returncode == 2 and "wallabag.py" in got.stderr
