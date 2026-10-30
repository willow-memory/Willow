"""readwise: a Readwise export as dated lines of highlights; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "readwise.py"
spec = importlib.util.spec_from_file_location("readwise", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b"Highlight,Book Title,Book Author,Amazon Book ID,Note,Color,Tags,Location Type,Location,Highlighted at\n"
    b'"In a hole in the ground there lived a hobbit.",The Hobbit,J.R.R. Tolkien,B1,the best   opening,yellow,fantasy,location,120,2024-03-02 08:15:00\n'
    b"Tie the stem loosely.,Staking tomatoes,Ana Lopez,,,,,,,2024-03-04T10:00:00Z\n"
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


def test_highlights_come_oldest_first_with_title_author_location_note_and_tags():
    assert mod.convert(SAMPLE) == (
        '2024-03-02  The Hobbit by J.R.R. Tolkien, location 120: "In a hole in the ground there lived a hobbit."  (note: the best opening)  [fantasy]\n'
        '2024-03-04  Staking tomatoes by Ana Lopez: "Tie the stem loosely."\n'
    )


def test_a_location_with_no_type_is_loc_and_a_note_alone_is_written_bare():
    csv = b"Highlight,Book Title,Book Author,Note,Location Type,Location,Highlighted at\nText,T,,,,42,2024-03-02\n,T,A,Just a note,page,7,2024-03-03\n"
    out = mod.convert(csv).splitlines()
    assert out[0] == '2024-03-02  T, loc 42: "Text"'
    assert out[1] == "2024-03-03  T by A, page 7  Just a note"


def test_a_row_with_neither_text_nor_note_is_skipped_and_an_undated_one_is_written_first():
    csv = b"Highlight,Book Title,Note,Highlighted at\n,T,,2024-03-02\nZed,T,,2024-03-02\nAlpha,T,,2024-03-02\nUndated,T,,\n"
    assert mod.convert(csv).splitlines() == [
        'T: "Undated"',
        '2024-03-02  T: "Zed"',
        '2024-03-02  T: "Alpha"',
    ]


def test_a_highlight_with_no_title_is_just_the_quotation():
    assert mod.convert(b"Highlight,Book Title\nJust text,\n") == '"Just text"\n'


def test_a_csv_that_is_not_a_readwise_export_is_not_a_result_and_bad_encoding_is_an_error():
    for other in (
        b"",
        b"a,b\n1,2\n",
        b"Highlight,Note\nx,y\n",
        b"Book Title,Note\nx,y\n",
        b"Highlight,Book Title\n",
        b"Highlight,Book Title\n,\n",
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"\xff\xfe\x00 bad")
    except UnicodeDecodeError:
        pass
    else:
        raise AssertionError("bad bytes")


def test_a_csv_that_is_no_export_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(
        tmp_path, {"readwise-data.csv": SAMPLE, "other.csv": b"a,b\n1,2\n"}
    )
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"readwise/readwise-data.csv": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "readwise/readwise-data.csv.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "readwise/readwise-data.csv": SAMPLE,
            ".hid/readwise/readwise-data.csv": SAMPLE,
            ".readwise/readwise-data.csv": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["readwise/readwise-data.csv.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"readwise/readwise-data.csv": SAMPLE})
    before = (tmp_path / "src" / "readwise/readwise-data.csv").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "readwise/readwise-data.csv.txt").read_bytes() == (
        out / "readwise/readwise-data.csv.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "readwise/readwise-data.csv").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path, {"good.csv": SAMPLE, "bad.csv": b"\xff\xfe\x00 not csv"}
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.csv.txt").is_file() and not (out / "bad.csv.txt").exists()


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
        assert got.returncode == 2 and "readwise.py" in got.stderr
