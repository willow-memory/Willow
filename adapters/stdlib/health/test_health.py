"""health: an Apple Health export as a table of daily numbers; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "health.py"
spec = importlib.util.spec_from_file_location("health", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'<?xml version="1.0"?><HealthData locale="en_GB"><Record type="HKQuantityTypeIdentifierStepCount" unit="count" startDate="2024-03-02 07:00:00 +0000" value="5000"/>'
    b'<Record type="HKQuantityTypeIdentifierStepCount" unit="count" startDate="2024-03-02 12:00:00 +0000" value="3123"/>'
    b'<Record type="HKQuantityTypeIdentifierDistanceWalkingRunning" unit="mi" startDate="2024-03-02 07:00:00 +0000" value="3.6"/>'
    b'<Record type="HKQuantityTypeIdentifierHeartRate" unit="count/min" startDate="2024-03-02 07:00:00 +0000" value="70"/>'
    b'<Record type="HKQuantityTypeIdentifierHeartRate" unit="count/min" startDate="2024-03-02 08:00:00 +0000" value="72"/>'
    b'<Record type="HKQuantityTypeIdentifierBodyMass" unit="lb" startDate="2024-03-02 06:00:00 +0000" value="160"/>'
    b'<Record type="HKQuantityTypeIdentifierBodyMass" unit="kg" startDate="2024-03-02 09:00:00 +0000" value="72.4"/>'
    b'<Record type="HKQuantityTypeIdentifierStepCount" unit="count" startDate="2024-03-03 07:00:00 +0000" value="10442"/>'
    b'<Record type="HKCategoryTypeIdentifierSleepAnalysis" startDate="2024-03-03 01:00:00 +0000" value="HKCategoryValueSleepAnalysisAsleep"/>'
    b'<Workout workoutActivityType="HKWorkoutActivityTypeRunning" startDate="2024-03-03 07:00:00 +0000"/></HealthData>'
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


def test_a_day_sums_steps_converts_miles_means_heart_rate_and_takes_the_last_weight():
    assert mod.convert(SAMPLE) == (
        "date,steps,walking km,heart rate,weight kg\n"
        "2024-03-02,8123,5.8,71,72.4\n"
        "2024-03-03,10442,,,\n"
    )


def test_units_are_converted_only_where_they_matter():
    n = mod.number
    assert (
        round(n("1", "mi", "walking km"), 4) == 1.6093
        and n("2", "km", "walking km") == 2
    )
    assert (
        round(n("160", "lb", "weight kg"), 2) == 72.57
        and n("72", "kg", "weight kg") == 72
    )
    assert (
        round(n("100", "kJ", "active kcal"), 3) == 23.901 and n("5", "mi", "steps") == 5
    )
    assert (
        n("x", "kg", "weight kg") is None
        and n(None, "kg", "weight kg") is None
        and n("", "", "steps") is None
    )


def test_numbers_are_shown_whole_where_a_count_and_to_a_tenth_where_a_measure():
    s = mod.shown
    assert (
        s(8123.4, "steps") == "8123"
        and s(71.5, "heart rate") == "72"
        and s(412.4, "active kcal") == "412"
    )
    assert (
        s(5.8, "walking km") == "5.8"
        and s(72.0, "weight kg") == "72"
        and s(72.04, "weight kg") == "72"
        and s(72.46, "weight kg") == "72.5"
    )


def test_a_last_reading_is_the_latest_by_time_not_by_position_in_the_file():
    doc = (
        b'<HealthData><Record type="HKQuantityTypeIdentifierBodyMass" unit="kg" startDate="2024-03-02 20:00:00 +0000" value="73"/>'
        b'<Record type="HKQuantityTypeIdentifierBodyMass" unit="kg" startDate="2024-03-02 06:00:00 +0000" value="72"/></HealthData>'
    )
    assert mod.convert(doc) == "date,weight kg\n2024-03-02,73\n"


def test_a_column_nothing_fills_is_left_out_and_a_record_with_no_date_or_number_is_skipped():
    doc = (
        b'<HealthData><Record type="HKQuantityTypeIdentifierStepCount" startDate="yesterday" value="5"/>'
        b'<Record type="HKQuantityTypeIdentifierStepCount" startDate="2024-03-02 07:00:00 +0000" value="oops"/>'
        b'<Record type="HKQuantityTypeIdentifierStepCount" startDate="2024-03-02 07:00:00 +0000" value="7"/></HealthData>'
    )
    assert mod.convert(doc) == "date,steps\n2024-03-02,7\n"


def test_other_xml_an_entity_bomb_and_an_export_with_nothing_to_table_are_not_results():
    assert mod.convert(b"<root/>") is None and mod.convert(b"") is None
    assert mod.convert(b'<!DOCTYPE HealthData [<!ENTITY a "x">]><HealthData/>') is None
    assert mod.convert(b"<HealthData/>") is None
    assert (
        mod.convert(
            b'<HealthData><Record type="HKCategoryTypeIdentifierSleepAnalysis" startDate="2024-03-02 01:00:00 +0000" value="x"/></HealthData>'
        )
        is None
    )


def test_an_export_over_the_limit_is_an_error_not_a_crash():
    big = b"<HealthData>" + b" " * (mod.BIGGEST + 1) + b"</HealthData>"
    try:
        mod.convert(big)
    except ValueError:
        pass
    else:
        raise AssertionError("too big")


def test_an_xml_file_that_is_no_export_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"export.xml": SAMPLE, "other.xml": b"<root/>"})
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"apple_health_export/export.xml": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "apple_health_export/export.xml.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "apple_health_export/export.xml": SAMPLE,
            ".hid/apple_health_export/export.xml": SAMPLE,
            ".apple_health_export/export.xml": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["apple_health_export/export.xml.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"apple_health_export/export.xml": SAMPLE})
    before = (tmp_path / "src" / "apple_health_export/export.xml").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "apple_health_export/export.xml.txt").read_bytes() == (
        out / "apple_health_export/export.xml.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "apple_health_export/export.xml").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path, {"good.xml": SAMPLE, "bad.xml": b"<HealthData><Record"}
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
        assert got.returncode == 2 and "health.py" in got.stderr
