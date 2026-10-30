"""letterboxd: a Letterboxd export as dated lines of films; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "letterboxd.py"
spec = importlib.util.spec_from_file_location("letterboxd", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b"Date,Name,Year,Letterboxd URI,Rating,Rewatch,Review,Tags,Watched Date\n"
    b'2024-03-05,Heat,1995,https://boxd.it/1,4.5,Yes,,"crime, night",2024-03-02\n'
    b"2024-03-10,Paddington 2,2017,https://boxd.it/2,4,,Funnier than it has   any right to be.,,2024-03-09\n"
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


def test_rows_come_oldest_first_by_the_day_watched_with_rating_rewatch_review_and_tags():
    assert mod.convert(SAMPLE) == (
        "2024-03-02  watched Heat (1995)  4.5/5  rewatch  [crime, night]\n"
        "2024-03-09  watched Paddington 2 (2017)  4/5  Funnier than it has any right to be.\n"
    )


def test_a_ratings_file_and_a_watchlist_say_rated_and_listed_with_the_day_logged():
    ratings = b"Date,Name,Year,Letterboxd URI,Rating\n2024-03-04,Alien,1979,u,5\n2024-03-03,Zed,,u,0.5\n"
    assert (
        mod.convert(ratings)
        == "2024-03-03  rated Zed  0.5/5\n2024-03-04  rated Alien (1979)  5/5\n"
    )
    watchlist = b"Date,Name,Year,Letterboxd URI\n2024-03-04,Alien,1979,u\n"
    assert mod.convert(watchlist) == "2024-03-04  listed Alien (1979)\n"


def test_a_diary_row_with_no_watched_date_takes_the_day_logged_and_is_not_called_watched():
    diary = b"Date,Name,Year,Letterboxd URI,Rating,Watched Date\n2024-03-04,Alien,1979,u,,\n"
    assert mod.convert(diary) == "2024-03-04  listed Alien (1979)\n"


def test_ratings_are_out_of_five_and_nothing_else_is_a_rating():
    s = mod.stars
    assert (
        s("4.5") == "4.5/5"
        and s("5") == "5/5"
        and s("0.5") == "0.5/5"
        and s("4.0") == "4/5"
    )
    assert (
        s("0") == ""
        and s("5.5") == ""
        and s("-1") == ""
        and s("") == ""
        and s("great") == ""
        and s(None) == ""
    )


def test_a_row_with_no_name_is_skipped_and_a_row_with_no_dates_is_written_bare():
    csv = b"Date,Name,Year,Letterboxd URI\n2024-03-04,,1979,u\n,Alien,,u\n"
    assert mod.convert(csv) == "listed Alien\n"


def test_the_order_is_by_day_with_undated_first_and_the_same_day_keeps_the_files_order():
    csv = b"Date,Name,Year,Letterboxd URI\n2024-03-04,Zed,,u\n2024-03-04,Alpha,,u\n,Undated,,u\n"
    assert mod.convert(csv).splitlines() == [
        "listed Undated",
        "2024-03-04  listed Zed",
        "2024-03-04  listed Alpha",
    ]


def test_a_csv_that_is_not_a_letterboxd_export_is_not_a_result_and_bad_encoding_is_an_error():
    for other in (
        b"",
        b"a,b\n1,2\n",
        b"Name,Year\nHeat,1995\n",
        b"Date,Name,Year,Letterboxd URI\n",
        b"Date,Name,Year,Letterboxd URI\n,,,\n",
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"\xff\xfe\x00 bad")
    except UnicodeDecodeError:
        pass
    else:
        raise AssertionError("bad bytes")


def test_a_csv_that_is_no_export_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"diary.csv": SAMPLE, "other.csv": b"a,b\n1,2\n"})
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"letterboxd/diary.csv": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "letterboxd/diary.csv.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "letterboxd/diary.csv": SAMPLE,
            ".hid/letterboxd/diary.csv": SAMPLE,
            ".letterboxd/diary.csv": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["letterboxd/diary.csv.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"letterboxd/diary.csv": SAMPLE})
    before = (tmp_path / "src" / "letterboxd/diary.csv").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "letterboxd/diary.csv.txt").read_bytes() == (
        out / "letterboxd/diary.csv.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "letterboxd/diary.csv").read_bytes() == before


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
        assert got.returncode == 2 and "letterboxd.py" in got.stderr
