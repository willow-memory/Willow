"""karakeep: a Karakeep export bookmark by bookmark with tags and notes; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "karakeep.py"
spec = importlib.util.spec_from_file_location("karakeep", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'{"bookmarks":[{"createdAt":1710000000,"title":"Tomato growing guide","tags":["garden",{"name":"veg"}],"note":"Read the  staking section.","summary":"How to grow tomatoes.",'
    b'"content":{"type":"link","url":"https://example.org/tomatoes","description":"A guide\\nto tomatoes."}},'
    b'{"createdAt":"2024-02-01T10:00:00Z","title":"","content":{"type":"text","text":"Remember   the basil."}}]}'
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


def test_bookmarks_come_oldest_first_with_url_tags_note_summary_and_text():
    assert mod.convert(SAMPLE) == (
        "2024-02-01\n\nRemember the basil.\n\n"
        "2024-03-09  Tomato growing guide\nurl: https://example.org/tomatoes\ntags: garden, veg\n"
        "note: Read the staking section.\nsummary: How to grow tomatoes.\n\nA guide to tomatoes.\n"
    )


def test_a_created_time_is_unix_seconds_or_milliseconds_or_an_iso_date():
    assert (
        mod.day(1710000000) == "2024-03-09"
        and mod.day(1710000000000) == "2024-03-09"
        and mod.day(1710000000.5) == "2024-03-09"
    )
    assert (
        mod.day(100_000_000_000) == "5138-11-16"
        and mod.day(100_000_000_001) == "1973-03-03"
    )
    assert (
        mod.day("2024-03-02T08:00:00Z") == "2024-03-02" and mod.day("yesterday") == ""
    )
    assert mod.day(None) == "" and mod.day(True) == "" and mod.day(10**30) == ""


def test_a_bookmark_with_nothing_to_say_is_left_out_and_one_with_no_date_is_still_written():
    none = b'{"bookmarks":[5,{"createdAt":1710000000,"content":{}},{"title":"Only a title"}]}'
    assert mod.convert(none) == "Only a title\n"
    assert (
        mod.convert(
            b'{"bookmarks":[{"createdAt":1710000000,"content":{"url":"https://x.org"}}]}'
        )
        == "2024-03-09\nurl: https://x.org\n"
    )


def test_json_that_is_not_an_export_is_not_a_result_and_bad_json_is_an_error():
    for other in (
        b"[]",
        b"{}",
        b'{"bookmarks":{}}',
        b'{"bookmarks":[]}',
        b'{"bookmarks":[{}]}',
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"{nope")
    except ValueError:
        pass
    else:
        raise AssertionError("bad json")


def test_a_json_file_that_is_no_export_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"a.json": SAMPLE, "b.json": b'{"other": 1}'})
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"export/karakeep.json": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "export/karakeep.json.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "export/karakeep.json": SAMPLE,
            ".hid/export/karakeep.json": SAMPLE,
            ".export/karakeep.json": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["export/karakeep.json.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"export/karakeep.json": SAMPLE})
    before = (tmp_path / "src" / "export/karakeep.json").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "export/karakeep.json.txt").read_bytes() == (
        out / "export/karakeep.json.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "export/karakeep.json").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(tmp_path, {"good.json": SAMPLE, "bad.json": b"{not json"})
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
        assert got.returncode == 2 and "karakeep.py" in got.stderr
