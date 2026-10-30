"""goodreads: a Goodreads or StoryGraph library as dated lines of books; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "goodreads.py"
spec = importlib.util.spec_from_file_location("goodreads", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b"Book Id,Title,Author,My Rating,Date Read,Date Added,Bookshelves,Exclusive Shelf,My Review,Private Notes\n"
    b'1,The Hobbit,J.R.R. Tolkien,4,2024/03/02,2023/01/05,"fantasy, favourites",read,A comfort   read.,secret\n'
    b"2,Dune,Frank Herbert,0,,2024/03/09,,currently-reading,,\n"
    b"3,Piranesi,Susanna Clarke,0,,2023/12/01,,to-read,,\n"
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


def test_books_come_oldest_first_by_the_day_finished_or_added_with_the_shelf_as_the_verb():
    assert mod.convert(SAMPLE) == (
        "2023-12-01  to read Piranesi by Susanna Clarke\n"
        "2024-03-02  read The Hobbit by J.R.R. Tolkien  4/5  A comfort read.  [fantasy, favourites]\n"
        "2024-03-09  reading Dune by Frank Herbert\n"
    )
    assert "secret" not in mod.convert(SAMPLE)


def test_a_storygraph_export_is_read_too():
    sg = (
        b"Title,Authors,Read Status,Date Added,Last Date Read,Star Rating,Review,Tags\n"
        b'Piranesi,Susanna Clarke,read,2024/01/02,2024-02-03,4.5,Strange and lovely.,"mystery, fantasy"\n'
        b"Hyperion,Dan Simmons,did-not-finish,2024-01-05,2024/01/20,,,\n"
    )
    assert mod.convert(sg) == (
        "2024-01-20  gave up on Hyperion by Dan Simmons\n"
        "2024-02-03  read Piranesi by Susanna Clarke  4.5/5  Strange and lovely.  [mystery, fantasy]\n"
    )


def test_a_book_read_with_no_finish_date_takes_the_day_added_and_an_unknown_shelf_is_named_as_written():
    csv = b"Title,Exclusive Shelf,Date Added\nA,read,2024/01/02\nB,favourites,2024/01/03\nC,,2024/01/04\n"
    assert mod.convert(csv).splitlines() == [
        "2024-01-02  read A",
        "2024-01-03  favourites B",
        "2024-01-04  listed C",
    ]


def test_dates_and_ratings():
    d, s = mod.day, mod.stars
    assert (
        d("2024/03/02") == "2024-03-02"
        and d("2024-03-02") == "2024-03-02"
        and d("2024/03/02 10:00") == "2024-03-02"
        and d("") == ""
        and d("soon") == ""
        and d(None) == ""
    )
    assert (
        s("1") == "1/5"
        and s("0.5") == "0.5/5"
        and s("4") == "4/5"
        and s("4.5") == "4.5/5"
        and s("5") == "5/5"
        and s("0") == ""
        and s("6") == ""
        and s("x") == ""
        and s(None) == ""
    )


def test_the_order_is_by_day_with_undated_first_and_the_same_day_keeps_the_files_order():
    csv = b"Title,Exclusive Shelf,Date Added\nZed,to-read,2024/01/02\nAlpha,to-read,2024/01/02\nUndated,to-read,\n"
    assert mod.convert(csv).splitlines() == [
        "to read Undated",
        "2024-01-02  to read Zed",
        "2024-01-02  to read Alpha",
    ]


def test_a_csv_that_is_not_a_library_export_is_not_a_result_and_bad_encoding_is_an_error():
    for other in (
        b"",
        b"a,b\n1,2\n",
        b"Title,Author\nDune,Frank\n",
        b"Title,Exclusive Shelf\n",
        b"Title,Exclusive Shelf\n,read\n",
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
        tmp_path, {"goodreads_library_export.csv": SAMPLE, "other.csv": b"a,b\n1,2\n"}
    )
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"goodreads/goodreads_library_export.csv": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "goodreads/goodreads_library_export.csv.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "goodreads/goodreads_library_export.csv": SAMPLE,
            ".hid/goodreads/goodreads_library_export.csv": SAMPLE,
            ".goodreads/goodreads_library_export.csv": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["goodreads/goodreads_library_export.csv.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"goodreads/goodreads_library_export.csv": SAMPLE})
    before = (tmp_path / "src" / "goodreads/goodreads_library_export.csv").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "goodreads/goodreads_library_export.csv.txt").read_bytes() == (
        out / "goodreads/goodreads_library_export.csv.txt"
    ).read_bytes()
    assert (
        tmp_path / "src" / "goodreads/goodreads_library_export.csv"
    ).read_bytes() == before


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
        assert got.returncode == 2 and "goodreads.py" in got.stderr
