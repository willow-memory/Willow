"""home-sensors: a Home Assistant history as a table of daily numbers; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "home_sensors.py"
spec = importlib.util.spec_from_file_location("home_sensors", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'[[{"entity_id":"sensor.kitchen_temp","state":"21.0","last_changed":"2024-03-02T08:00:00+00:00","attributes":{"unit_of_measurement":"C","friendly_name":"Kitchen temperature"}},'
    b'{"entity_id":"sensor.kitchen_temp","state":"21.8","last_changed":"2024-03-02T20:00:00+00:00","attributes":{}},'
    b'{"entity_id":"sensor.kitchen_temp","state":"unavailable","last_changed":"2024-03-02T21:00:00+00:00"},'
    b'{"entity_id":"sensor.kitchen_temp","state":"20.9","last_changed":"2024-03-03T08:00:00+00:00"}],'
    b'[{"entity_id":"sensor.hall_humidity","state":"48.5","last_changed":"2024-03-02T09:00:00+00:00","attributes":{"unit_of_measurement":"%","friendly_name":"Hall, humidity"}}],'
    b'[{"entity_id":"light.hall","state":"on","last_changed":"2024-03-02T09:00:00+00:00"}]]'
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


def test_each_entity_with_numbers_is_a_column_and_each_day_a_row_of_means():
    assert mod.convert(SAMPLE) == (
        "date,Kitchen temperature (C),Hall humidity (%)\n"
        "2024-03-02,21.4,48.5\n"
        "2024-03-03,20.9,\n"
    )


def test_a_column_is_headed_by_the_friendly_name_else_the_id_with_its_unit_and_commas_taken_out():
    c = mod.column
    assert (
        c(
            [
                {
                    "entity_id": "sensor.a",
                    "attributes": {
                        "friendly_name": "Name, with comma",
                        "unit_of_measurement": "kWh",
                    },
                }
            ]
        )
        == "Name with comma (kWh)"
    )
    assert (
        c([{"entity_id": "sensor.a"}]) == "sensor.a"
        and c([{"entity_id": "sensor.a", "attributes": {"unit_of_measurement": "W"}}])
        == "sensor.a (W)"
    )
    assert (
        c(
            [
                {"entity_id": "sensor.a"},
                {"entity_id": "sensor.a", "attributes": {"friendly_name": "Later"}},
            ]
        )
        == "Later"
    )
    assert c([]) == "sensor" and c([5]) == "sensor"


def test_means_are_shown_to_a_tenth_without_a_pointless_zero():
    assert (
        mod.tenth(21.0) == "21"
        and mod.tenth(21.04) == "21"
        and mod.tenth(21.05) == "21.1"
        and mod.tenth(-3.25) == "-3.2"
        and mod.tenth(0.0) == "0"
    )


def test_two_entities_with_the_same_name_keep_their_own_columns_and_odd_numbers_are_ignored():
    a = '{"entity_id":"sensor.a","state":"1","last_changed":"2024-03-02T00:00:00Z","attributes":{"friendly_name":"Temp"}}'
    b = '{"entity_id":"sensor.b","state":"3","last_changed":"2024-03-02T00:00:00Z","attributes":{"friendly_name":"Temp"}}'
    nan = '{"entity_id":"sensor.a","state":"nan","last_changed":"2024-03-02T00:00:00Z"}'
    undated = '{"entity_id":"sensor.a","state":"9","last_changed":"later"}'
    assert (
        mod.convert(f"[[{a},{nan},{undated}],[{b}]]".encode())
        == "date,Temp,Temp*\n2024-03-02,1,3\n"
    )


def test_json_that_is_not_a_history_or_has_no_number_is_not_a_result_and_bad_json_is_an_error():
    for other in (
        b"[]",
        b"{}",
        b"[[5]]",
        b'[["entity_id"]]',
        b"5",
        b"null",
        b"[1]",
        b"[[]]",
        b'[[{"other":1}]]',
        b'[[{"entity_id":"light.a","state":"on","last_changed":"2024-03-02T00:00:00Z"}]]',
        b'{"a":[]}',
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"[nope")
    except ValueError:
        pass
    else:
        raise AssertionError("bad json")


def test_a_json_file_that_is_no_history_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(
        tmp_path, {"history.json": SAMPLE, "other.json": b'{"other": 1}'}
    )
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"ha/history.json": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "ha/history.json.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "ha/history.json": SAMPLE,
            ".hid/ha/history.json": SAMPLE,
            ".ha/history.json": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["ha/history.json.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"ha/history.json": SAMPLE})
    before = (tmp_path / "src" / "ha/history.json").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "ha/history.json.txt").read_bytes() == (
        out / "ha/history.json.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "ha/history.json").read_bytes() == before


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
        assert got.returncode == 2 and "home_sensors.py" in got.stderr
