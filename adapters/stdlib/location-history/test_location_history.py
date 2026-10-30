"""location-history: a Timeline export as dated lines of places and trips; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "location_history.py"
spec = importlib.util.spec_from_file_location("location_history", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'{"timelineObjects":[{"activitySegment":{"activityType":"WALKING","distance":1500,"duration":{"startTimestamp":"2024-03-02T09:10:00Z","endTimestamp":"2024-03-02T09:40:00Z"}}},'
    b'{"placeVisit":{"location":{"name":"Kitchen Cafe","address":"1 High St, Leeds"},"duration":{"startTimestamp":"2024-03-02T08:15:00.000Z","endTimestamp":"2024-03-02T09:10:00.000Z"}}},'
    b'{"placeVisit":{"location":{},"duration":{"startTimestamp":"2024-03-02T23:00:00Z","endTimestamp":"2024-03-03T07:00:00Z"}}},{"placeVisit":{"duration":{}}}]}'
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


def test_visits_and_trips_come_oldest_first_with_the_hours_they_cover():
    assert mod.convert(SAMPLE) == (
        "2024-03-02 08:15-09:10  Kitchen Cafe, 1 High St, Leeds\n"
        "2024-03-02 09:10-09:40  walking 1.5 km\n"
        "2024-03-02 23:00 to 2024-03-03 07:00  (unnamed place)\n"
    )


def test_the_newer_timeline_export_is_read_too():
    doc = (
        b'{"semanticSegments":[{"startTime":"2024-03-02T12:00:00.000+00:00","endTime":"2024-03-02T17:30:00.000+00:00","visit":{"topCandidate":{"semanticType":"HOME","placeLocation":{"latLng":"45.123\\u00b0, 7.456\\u00b0"}}}},'
        b'{"startTime":"2024-03-02T09:10:00Z","endTime":"2024-03-02T09:40:00Z","activity":{"topCandidate":{"type":"IN_PASSENGER_VEHICLE"},"distanceMeters":12345}},'
        b'{"startTime":"2024-03-02T10:00:00Z","endTime":"2024-03-02T10:30:00Z","visit":{"topCandidate":{"placeLocation":{"latLng":"1\\u00b0, 2\\u00b0"}}}},'
        b'{"startTime":"2024-03-02T11:00:00Z","visit":{}},{"timelinePath":[]}]}'
    )
    assert mod.convert(doc) == (
        "2024-03-02 09:10-09:40  in passenger vehicle 12.3 km\n2024-03-02 10:00-10:30  1, 2\n"
        "2024-03-02 11:00  (unnamed place)\n2024-03-02 12:00-17:30  HOME (45.123, 7.456)\n"
    )


def test_a_span_is_to_the_minute_and_crosses_midnight_in_words():
    sp = mod.span
    assert sp("2024-03-02T08:15:30Z", "2024-03-02T09:10:00Z") == (
        "2024-03-02T08:15:30Z",
        "2024-03-02 08:15-09:10",
    )
    assert (
        sp("2024-03-02T08:15:30Z", "2024-03-03T01:00:00Z")[1]
        == "2024-03-02 08:15 to 2024-03-03 01:00"
    )
    assert (
        sp("2024-03-02T08:15:30Z", None)[1] == "2024-03-02 08:15"
        and sp("2024-03-02T08:15:30Z", "soon")[1] == "2024-03-02 08:15"
    )
    assert (
        sp(None, "2024-03-02T08:15:30Z") == ("", "")
        and sp("yesterday", None) == ("", "")
        and sp("2024-03-02", None) == ("", "")
    )


def test_distances_are_kilometres_to_a_tenth_and_a_trip_without_a_type_is_a_trip():
    assert (
        mod.km(1500) == "1.5 km"
        and mod.km(1549.9) == "1.5 km"
        and mod.km(50) == "0.1 km"
        and mod.km(1) == "0.0 km"
    )
    assert (
        mod.km(0) == ""
        and mod.km(-5) == ""
        and mod.km(None) == ""
        and mod.km(True) == ""
        and mod.km("12") == ""
    )
    assert (
        mod.trip(None, None) == "trip"
        and mod.trip("ON_BICYCLE", 2000) == "on bicycle 2.0 km"
        and mod.trip("WALKING", None) == "walking"
    )


def test_the_order_is_by_start_and_trips_at_the_same_minute_keep_the_files_order():
    def seg(who, t):
        return {
            "activitySegment": {
                "activityType": who,
                "duration": {"startTimestamp": t, "endTimestamp": t},
            }
        }

    rows = mod.old(
        [
            seg("ZED", "2024-03-02T08:00:00Z"),
            seg("ALPHA", "2024-03-02T08:00:00Z"),
            seg("EARLY", "2024-03-01T08:00:00Z"),
        ]
    )
    assert [r[1].split("  ")[1] for r in sorted(rows, key=lambda r: r[0])] == [
        "early",
        "zed",
        "alpha",
    ]


def test_convert_orders_by_start_and_keeps_the_files_order_for_trips_that_start_together():
    def seg(kind, t):
        return (
            '{"activitySegment":{"activityType":"%s","duration":{"startTimestamp":"%s","endTimestamp":"%s"}}}'
            % (kind, t, t)
        )

    doc = (
        '{"timelineObjects":['
        + ",".join(
            [
                seg("ZED", "2024-03-02T08:00:00Z"),
                seg("ALPHA", "2024-03-02T08:00:00Z"),
                seg("EARLY", "2024-03-01T08:00:00Z"),
            ]
        )
        + "]}"
    )
    assert [x.split("  ")[1] for x in mod.convert(doc.encode()).splitlines()] == [
        "early",
        "zed",
        "alpha",
    ]


def test_json_that_is_not_a_timeline_is_not_a_result_and_bad_json_is_an_error():
    for other in (
        b"[]",
        b"5",
        b"null",
        b"{}",
        b'{"timelineObjects":{}}',
        b'{"timelineObjects":[]}',
        b'{"timelineObjects":[5,{}]}',
        b'{"semanticSegments":[{"visit":{}}]}',
        b'{"locations":[{"latitudeE7":1}]}',
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"{nope")
    except ValueError:
        pass
    else:
        raise AssertionError("bad json")


def test_a_json_file_that_is_no_timeline_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"a.json": SAMPLE, "b.json": b'{"other": 1}'})
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"Takeout/2024_MARCH.json": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "Takeout/2024_MARCH.json.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "Takeout/2024_MARCH.json": SAMPLE,
            ".hid/Takeout/2024_MARCH.json": SAMPLE,
            ".Takeout/2024_MARCH.json": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["Takeout/2024_MARCH.json.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"Takeout/2024_MARCH.json": SAMPLE})
    before = (tmp_path / "src" / "Takeout/2024_MARCH.json").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "Takeout/2024_MARCH.json.txt").read_bytes() == (
        out / "Takeout/2024_MARCH.json.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "Takeout/2024_MARCH.json").read_bytes() == before


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
        assert got.returncode == 2 and "location_history.py" in got.stderr
