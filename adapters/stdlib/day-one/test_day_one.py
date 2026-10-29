"""day-one: a Day One export entry by entry with place, weather and tags; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "day_one.py"
spec = importlib.util.spec_from_file_location("day_one", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'{"metadata":{"version":"1.0"},"entries":['
    b'{"creationDate":"2024-03-03T09:00:00Z","text":"Second entry\\\\.","tags":["garden","spring"],"starred":true,"location":{"placeName":"Kitchen","localityName":"Leeds","country":"United Kingdom"},"weather":{"conditionsDescription":"Cloudy","temperatureCelsius":7.6}},'
    b'{"creationDate":"2024-03-02T08:15:00Z","text":"Planted out the tomatoes. It was 5\\\\-6 degrees\\\\!"},'
    b'{"creationDate":"2024-03-01T00:00:00Z","text":"  "}]}'
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


def test_entries_come_oldest_first_with_place_weather_tags_and_the_star():
    assert mod.convert(SAMPLE) == (
        "2024-03-02 08:15\n\nPlanted out the tomatoes. It was 5-6 degrees!\n\n"
        "2024-03-03 09:00  Kitchen, Leeds, United Kingdom  cloudy 8°C  #garden #spring  starred\n\nSecond entry.\n"
    )


def test_day_ones_markdown_escapes_are_undone_and_other_backslashes_stay():
    assert (
        mod.ESCAPED.sub(r"\1", r"5\-6 \. \! \# \* \_ \( \) \[ \] \> \\ \q")
        == r"5-6 . ! # * _ ( ) [ ] > \ \q"
    )


def test_a_tag_must_be_a_non_empty_string():
    out = mod.convert(
        b'{"metadata":{},"entries":[{"creationDate":"2024-03-02T08:00:00Z","text":"x","tags":[5,"","ok",null]}]}'
    )
    assert out == "2024-03-02 08:00  #ok\n\nx\n"


def test_a_place_drops_repeats_and_blanks_and_weather_needs_words_or_degrees():
    assert (
        mod.place({"placeName": "Leeds", "localityName": "Leeds", "country": " "})
        == "Leeds"
    )
    assert (
        mod.place(
            {
                "placeName": "A",
                "localityName": "B",
                "administrativeArea": "C",
                "country": "D",
            }
        )
        == "A, B, C, D"
    )
    assert (
        mod.place(None) == ""
        and mod.place({}) == ""
        and mod.place({"placeName": 3}) == ""
    )
    assert (
        mod.weather({"conditionsDescription": "Rain", "temperatureCelsius": 12})
        == "rain 12°C"
    )
    assert (
        mod.weather({"temperatureCelsius": 12.4}) == "12°C"
        and mod.weather({"conditionsDescription": "Snow"}) == "snow"
    )
    assert (
        mod.weather({"temperatureCelsius": True}) == ""
        and mod.weather(None) == ""
        and mod.weather({}) == ""
    )


def test_a_date_is_the_day_and_the_minute_and_a_missing_one_is_left_out():
    assert (
        mod.when("2024-03-02T08:15:30Z") == "2024-03-02 08:15"
        and mod.when("2024-03-02") == "2024-03-02"
    )
    assert mod.when(None) == "" and mod.when("short") == ""
    out = mod.convert(b'{"metadata":{},"entries":[{"text":"no date"}]}')
    assert out == "\n\nno date\n"


def test_json_that_is_not_an_export_is_not_a_result_and_bad_json_is_an_error():
    for other in (
        b"[]",
        b"{}",
        b'{"entries":[]}',
        b'{"metadata":{},"entries":{}}',
        b'{"metadata":{},"entries":[]}',
        b'{"metadata":{},"entries":[{"text":""}, 5]}',
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"{not json")
    except ValueError:
        pass
    else:
        raise AssertionError("bad json")


def test_a_json_file_that_is_no_export_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"a.json": SAMPLE, "b.json": b'{"other": 1}'})
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"journal/Journal.json": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "journal/Journal.json.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "journal/Journal.json": SAMPLE,
            ".hid/journal/Journal.json": SAMPLE,
            ".journal/Journal.json": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["journal/Journal.json.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"journal/Journal.json": SAMPLE})
    before = (tmp_path / "src" / "journal/Journal.json").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "journal/Journal.json.txt").read_bytes() == (
        out / "journal/Journal.json.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "journal/Journal.json").read_bytes() == before


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
        assert got.returncode == 2 and "day_one.py" in got.stderr
