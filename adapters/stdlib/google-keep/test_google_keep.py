"""google-keep: a Google Keep note or list with its day and labels; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "google_keep.py"
spec = importlib.util.spec_from_file_location("google_keep", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'{"color":"DEFAULT","isTrashed":false,"isPinned":true,"title":"Shopping","userEditedTimestampUsec":1710000000000000,"createdTimestampUsec":1709380000000000,'
    b'"labels":[{"name":"home"},{"name":"food"}],"listContent":[{"text":"milk","isChecked":false},{"text":"eggs","isChecked":true},{"text":" ","isChecked":false}]}'
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


def test_a_list_note_is_its_title_day_labels_and_ticked_items():
    assert (
        mod.convert(SAMPLE)
        == "note: Shopping (2024-03-02)\nlabels: home, food\n\n[ ] milk\n[x] eggs\n"
    )


def test_a_label_must_be_a_named_object():
    note = b'{"userEditedTimestampUsec":1710000000000000,"title":"T","textContent":"x","labels":[{"name":""},{"name":3},"home",{"name":"ok"},{}]}'
    assert mod.convert(note) == "note: T (2024-03-09)\nlabels: ok\n\nx\n"


def test_a_text_note_keeps_its_text_and_a_note_with_both_keeps_both():
    text = b'{"userEditedTimestampUsec":1710000000000000,"title":"Idea","textContent":"  Try basil.\\nWater it.  "}'
    assert mod.convert(text) == "note: Idea (2024-03-09)\n\nTry basil.\nWater it.\n"
    both = b'{"userEditedTimestampUsec":1710000000000000,"title":"T","textContent":"intro","listContent":[{"text":"a"}]}'
    assert mod.convert(both).endswith("\n\nintro\n[ ] a\n")


def test_the_day_is_the_created_day_else_the_edited_day_else_none():
    assert mod.day(1709380000000000) == "2024-03-02" and mod.day(0) == "1970-01-01"
    assert (
        mod.day("1709380000000000") == ""
        and mod.day(None) == ""
        and mod.day(True) == ""
        and mod.day(10**30) == ""
    )
    edited = (
        b'{"userEditedTimestampUsec":1710000000000000,"title":"T","textContent":"x"}'
    )
    assert mod.convert(edited).startswith("note: T (2024-03-09)")
    none = b'{"userEditedTimestampUsec":"x","title":"T","textContent":"x"}'
    assert mod.convert(none).startswith("note: T\n")


def test_an_untitled_note_is_named_so_and_an_empty_untitled_one_is_not_a_result():
    assert mod.convert(b'{"userEditedTimestampUsec":1,"textContent":"x"}').startswith(
        "note: (untitled) (1970-01-01)"
    )
    assert mod.convert(
        b'{"userEditedTimestampUsec":1,"title":"  ","textContent":"x"}'
    ).startswith("note: (untitled)")
    assert mod.convert(b'{"userEditedTimestampUsec":1,"textContent":"  "}') is None
    assert (
        mod.convert(
            b'{"userEditedTimestampUsec":1,"title":"Only a title","textContent":""}'
        )
        == "note: Only a title (1970-01-01)\n"
    )


def test_a_note_in_the_bin_and_other_json_are_not_results_and_bad_json_is_an_error():
    assert (
        mod.convert(
            b'{"userEditedTimestampUsec":1,"isTrashed":true,"title":"T","textContent":"x"}'
        )
        is None
    )
    for other in (
        b"[]",
        b"{}",
        b'{"title":"T","textContent":"x"}',
        b'{"userEditedTimestampUsec":1,"title":"T"}',
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"{nope")
    except ValueError:
        pass
    else:
        raise AssertionError("bad json")


def test_a_json_file_that_is_no_note_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"a.json": SAMPLE, "b.json": b'{"other": 1}'})
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"Takeout/Keep/Shopping.json": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "Takeout/Keep/Shopping.json.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "Takeout/Keep/Shopping.json": SAMPLE,
            ".hid/Takeout/Keep/Shopping.json": SAMPLE,
            ".Takeout/Keep/Shopping.json": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["Takeout/Keep/Shopping.json.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"Takeout/Keep/Shopping.json": SAMPLE})
    before = (tmp_path / "src" / "Takeout/Keep/Shopping.json").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "Takeout/Keep/Shopping.json.txt").read_bytes() == (
        out / "Takeout/Keep/Shopping.json.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "Takeout/Keep/Shopping.json").read_bytes() == before


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
        assert got.returncode == 2 and "google_keep.py" in got.stderr
