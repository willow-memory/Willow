"""strava: Strava's activities.csv, GPX and TCX files, each activity as a dated
line with its distance and time; .fit skipped and counted, hidden files and
folders skipped, an unreadable file skipped and counted, the same bytes twice,
originals unchanged, and MIRROR and FOLDER kept apart."""

from __future__ import annotations

import gzip
import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "strava.py"
spec = importlib.util.spec_from_file_location("strava", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# the header of a Strava bulk export's activities.csv, its columns in their
# order: "Elapsed Time", "Distance", "Max Heart Rate", "Relative Effort" and
# "Commute" each appear twice
HEADER = (
    "Activity ID,Activity Date,Activity Name,Activity Type,Activity Description,"
    "Elapsed Time,Distance,Max Heart Rate,Relative Effort,Commute,"
    "Activity Private Note,Activity Gear,Filename,Athlete Weight,Bike Weight,"
    "Elapsed Time,Moving Time,Distance,Max Speed,Average Speed,Elevation Gain,"
    "Elevation Loss,Elevation Low,Elevation High,Max Grade,Average Grade,"
    "Average Positive Grade,Average Negative Grade,Max Cadence,Average Cadence,"
    "Max Heart Rate,Average Heart Rate,Max Watts,Average Watts,Calories,"
    "Max Temperature,Average Temperature,Relative Effort,Total Work,"
    "Number of Runs,Uphill Time,Downhill Time,Other Time,Perceived Exertion,"
    "Type,Start Time,Weighted Average Power,Power Count,"
    "Prefer Perceived Exertion,Perceived Relative Effort,Commute,"
    "Total Weight Lifted,From Upload,Grade Adjusted Distance\n"
)


def row(id_, date, name, type_, desc, elapsed, km, note, gear, file_, elapsed2,
        moving, metres) -> str:  # fmt: skip
    first = [id_, date, name, type_, desc, elapsed, km, "", "", "false", note,
             gear, file_, "", "", elapsed2, moving, metres]  # fmt: skip
    cells = first + [""] * (HEADER.count(",") + 1 - len(first))
    return ",".join(f'"{c}"' if "," in c else c for c in cells) + "\n"


CSV = (
    HEADER
    + row("10865432101", "Mar 3, 2024, 7:15:22 AM", "Harbour Loop", "Run",
          "Easy, legs fresh", "1694", "5.23", "", "Pegasus 40",
          "activities/11234.gpx.gz", "1694.0", "1630.0", "5230.5")
    + row("10865432102", "Mar 4, 2024, 5:40:00 PM", "Lunch Swim", "Swim", "",
          "2100", "1,500", "felt slow", "", "activities/11235.fit.gz", "2100.0",
          "1980.0", "1500.0")
    + row("10865432103", "Mar 9, 2024, 9:02:10 AM", "Dales loop", "Virtual Ride",
          "", "7322", "61.07", "", "", "", "7322.0", "7010.0", "61070.2")
)  # fmt: skip

# GPX 1.1 as Strava writes it, with Garmin's point extensions
GPX = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx creator="StravaGPX" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd http://www.garmin.com/xmlschemas/GpxExtensions/v3 http://www.garmin.com/xmlschemas/GpxExtensionsv3.xsd http://www.garmin.com/xmlschemas/TrackPointExtension/v1 http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd" version="1.1" xmlns="http://www.topografix.com/GPX/1/1" xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1" xmlns:gpxx="http://www.garmin.com/xmlschemas/GpxExtensions/v3">
 <metadata>
  <time>2024-03-03T07:15:22Z</time>
 </metadata>
 <trk>
  <name>Harbour Loop</name>
  <type>running</type>
  <trkseg>
   <trkpt lat="0.0000000" lon="0.0000000">
    <ele>12.4</ele>
    <time>2024-03-03T07:15:22Z</time>
    <extensions><gpxtpx:TrackPointExtension><gpxtpx:hr>131</gpxtpx:hr></gpxtpx:TrackPointExtension></extensions>
   </trkpt>
   <trkpt lat="0.0250000" lon="0.0000000">
    <ele>13.0</ele>
    <time>2024-03-03T07:30:00Z</time>
   </trkpt>
   <trkpt lat="0.0500000" lon="0.0000000">
    <ele>12.8</ele>
    <time>2024-03-03T07:43:36Z</time>
   </trkpt>
  </trkseg>
 </trk>
</gpx>
"""

# TCX as a Garmin device writes it, blank space before the declaration and all
TCX = b"""          <?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase xsi:schemaLocation="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd" xmlns:ns5="http://www.garmin.com/xmlschemas/ActivityGoals/v1" xmlns:ns3="http://www.garmin.com/xmlschemas/ActivityExtension/v2" xmlns:ns2="http://www.garmin.com/xmlschemas/UserProfile/v2" xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Activities>
    <Activity Sport="Biking">
      <Id>2024-03-05T16:20:00.000Z</Id>
      <Lap StartTime="2024-03-05T16:20:00.000Z">
        <TotalTimeSeconds>1800.0</TotalTimeSeconds>
        <DistanceMeters>12000.0</DistanceMeters>
        <MaximumSpeed>11.2</MaximumSpeed>
        <Calories>310</Calories>
        <Intensity>Active</Intensity>
        <TriggerMethod>Manual</TriggerMethod>
        <Track>
          <Trackpoint><Time>2024-03-05T16:20:00.000Z</Time><DistanceMeters>0.0</DistanceMeters></Trackpoint>
        </Track>
      </Lap>
      <Lap StartTime="2024-03-05T16:50:00.000Z">
        <TotalTimeSeconds>1514.0</TotalTimeSeconds>
        <DistanceMeters>9400.5</DistanceMeters>
        <Calories>250</Calories>
        <Intensity>Active</Intensity>
        <TriggerMethod>Manual</TriggerMethod>
      </Lap>
      <Notes>Commute home, headwind</Notes>
      <Creator xsi:type="Device_t"><Name>Edge 530</Name></Creator>
    </Activity>
  </Activities>
</TrainingCenterDatabase>
"""


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


def test_haversine_matches_a_known_distance():
    # Nashville (BNA) to Los Angeles (LAX): 2886.44 km on a 6371 km sphere
    assert round(mod.haversine_km((36.12, -86.67), (33.94, -118.40)), 2) == 2886.44
    # a degree of latitude along a meridian: 111.19 km
    assert round(mod.haversine_km((0, 0), (1, 0)), 2) == 111.19
    assert round(mod.haversine_km((10, 20), (10, 21)), 2) == round(
        mod.haversine_km((10, 21), (10, 20)), 2
    )
    assert mod.haversine_km((51.5, -0.1), (51.5, -0.1)) == 0


def test_each_csv_row_is_a_dated_line_with_the_metres_column_and_the_utc_start():
    out = mod.convert(CSV.encode(), "activities.csv")
    assert out.split("\n\n") == [
        "2024-03-03 07:15Z Harbour Loop, 5.2, 0:28:14\nEasy, legs fresh\nPegasus 40",
        # the summary column says "1,500" for a swim; the metres column says 1500.0
        "2024-03-04 17:40Z Lunch Swim, 1.5, 0:35:00\nfelt slow",
        "2024-03-09 09:02Z Dales loop, 61.1, 2:02:02\n",
    ]


def test_a_csv_that_is_not_stravas_is_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "activities.csv": CSV.encode(),
            "comments.csv": b"Comment Date,Comment\n1,hi\n",
        },
    )
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip().endswith("wrote 1 files to " + str(out) + "; skipped 0")
    assert not (out / "comments.csv.txt").exists()


def test_a_date_strava_did_not_write_its_way_is_kept_as_written_and_a_missing_value_is_a_question_mark():
    text = HEADER + row("1", "3. März 2024, 07:15:22", "", "Workout", "", "", "",
                        "", "", "", "", "", "")  # fmt: skip
    assert mod.convert(text.encode(), "a.csv") == "3. März 2024, 07:15:22, ?, ?\n"
    text = HEADER + row("1", "Mar 3, 2024, 12:05:00 AM", "Night", "Run", "", "",
                        "", "", "", "", "600", "", "")  # fmt: skip
    assert (
        mod.convert(text.encode(), "a.csv") == "2024-03-03 00:05Z Night, ?, 0:10:00\n"
    )
    text = HEADER + row("1", "Mar 3, 2024, 12:05:00 PM", "Noon", "Walk", "", "",
                        "", "", "", "", "", "", "640.4")  # fmt: skip
    assert mod.convert(text.encode(), "a.csv") == "2024-03-03 12:05Z Noon, 0.64, ?\n"
    text = HEADER + row("1", "", "Lost", "Walk", "", "60", "", "", "", "", "", "", "")
    assert mod.convert(text.encode(), "a.csv") == "? Lost, ?, 0:01:00\n"


def test_a_csv_with_one_distance_column_writes_no_distance_rather_than_guess_its_unit():
    text = (
        "Activity ID,Activity Date,Activity Name,Activity Type,Elapsed Time,Distance\n"
        '1,"Mar 3, 2024, 7:15:22 AM",Harbour Loop,Run,1694,5.23\n'
    )
    assert mod.convert(text.encode(), "activities.csv") == (
        "2024-03-03 07:15Z Harbour Loop, ?, 0:28:14\n"
    )


def test_a_gpx_track_is_its_haversine_distance_and_its_elapsed_time():
    assert mod.convert(GPX, "Harbour_Loop.gpx") == (
        "2024-03-03 07:15Z Harbour Loop, 5.6, 0:28:14\n"
    )


def test_a_gpx_gz_is_read_through_gzip_and_written_with_txt_added(tmp_path):
    got, out = mirror_of(
        tmp_path, {"activities/11234.gpx.gz": gzip.compress(GPX, mtime=0)}
    )
    assert got.returncode == 0, got.stderr
    assert (out / "activities/11234.gpx.gz.txt").read_text(encoding="utf-8") == (
        "2024-03-03 07:15Z Harbour Loop, 5.6, 0:28:14\n"
    )


def test_gpx_10_its_offset_kept_and_its_segments_not_joined():
    data = b"""<?xml version="1.0"?>
<gpx version="1.0" creator="x" xmlns="http://www.topografix.com/GPX/1/0"><name>Old file</name>
<trk><type>9</type><trkseg>
<trkpt lat="0" lon="0"><time>2024-03-03T08:15:00+01:00</time></trkpt>
<trkpt lat="0.01" lon="0"><time>2024-03-03T08:20:00+01:00</time></trkpt></trkseg>
<trkseg><trkpt lat="5" lon="5"><time>2024-03-03T09:15:00+01:00</time></trkpt>
<trkpt lat="5.01" lon="5"><time>2024-03-03T09:20:00+01:00</time></trkpt></trkseg></trk></gpx>"""
    # two segments of 1.11 km each; the 785 km between them is not walked
    assert mod.convert(data, "old.gpx") == (
        "2024-03-03 08:15+01:00 Old file, 2.2, 1:05:00\n"
    )


def test_a_time_with_no_zone_is_shown_as_written_and_no_zone_is_guessed():
    data = b"""<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1"><trk><name>Walk</name><type>walking</type><trkseg>
<trkpt lat="0" lon="0"><time>2024-03-03T23:50:00</time></trkpt>
<trkpt lat="0.001" lon="0"><time>2024-03-04T00:10:30</time></trkpt></trkseg></trk></gpx>"""
    assert mod.convert(data, "w.gpx") == "2024-03-03 23:50 Walk, 0.11, 0:20:30\n"


def test_a_gpx_of_waypoints_only_has_no_activity_and_a_track_with_no_times_says_so():
    assert (
        mod.convert(
            b'<gpx version="1.1"><wpt lat="1" lon="2"><name>Gate</name></wpt></gpx>',
            "p.gpx",
        )
        is None
    )
    data = b'<gpx version="1.1"><metadata><time>2024-05-01T10:00:00Z</time></metadata><trk><name>Hill</name><type>hiking</type><trkseg><trkpt lat="0" lon="0"/><trkpt lat="0.02" lon="0"/></trkseg></trk></gpx>'
    assert mod.convert(data, "h.gpx") == "? Hill, 2.2, ?\n"


def test_a_tcx_activity_is_its_laps_added_up_with_its_notes():
    assert mod.convert(TCX, "ride.tcx") == (
        "2024-03-05 16:20Z, 21.4, 0:55:14\nCommute home, headwind\n"
    )
    assert mod.convert(gzip.compress(TCX, mtime=0), "ride.tcx.gz") == mod.convert(
        TCX, "ride.tcx"
    )


def test_distances_and_times_are_rounded_as_a_person_reads_them():
    assert [mod.distance(m) for m in (None, 0, 4.9, 999.4, 999.6, 1000, 1051, 5230.5, 42195)] == [
        "?", "0.00", "0.00", "1.00", "1.00", "1.0", "1.1", "5.2", "42.2"]  # fmt: skip
    assert [mod.duration(s) for s in (None, -1, 0, 59.6, 3599, 3600, 90061)] == [
        "?", "?", "0:00:00", "0:01:00", "0:59:59", "1:00:00", "25:01:01"]  # fmt: skip


def test_no_word_of_the_readers_own_answers_a_question_the_folder_cannot():
    """A word the reader wrote into every passage ("run", "km", "UTC", a
    weekday) would let a question about something the folder doesn't hold be
    answered by any activity. Pair each word most passages hold with one the
    folder doesn't: nothing is served. The real questions still land."""
    texts = {
        "activities.csv.txt": mod.convert(CSV.encode(), "activities.csv"),
        "activities/11234.gpx.gz.txt": mod.convert(GPX, "11234.gpx"),
        "activities/11236.tcx.txt": mod.convert(TCX, "11236.tcx"),
    }
    pile = [
        {"path": path, "line": i, "text": t, "id": mod.kernel.h256(t)}
        for path, text in texts.items()
        for i, t in enumerate(text.strip().split("\n\n"), 1)
    ]
    # the reader adds no word of its own: every word a passage holds is one
    # the files hold, or a date, a clock or a number
    source = set(mod.kernel.words(CSV + GPX.decode() + TCX.decode()))
    added = {w for c in pile for w in mod.kernel.words(c["text"])} - source
    assert not [w for w in added if not any(ch.isdigit() for ch in w)], added
    # and the words it used to add hold nothing alone (paths as Strava's export
    # names them, whose own folder is "activities")
    for w in ("run", "ride", "km", "utc", "march", "sunday", "started", "given"):
        assert mod.kernel.rank(pile, f"{w} volcano") == [], w
    assert mod.kernel.rank(pile, "when did I run a marathon") == []
    for question, starts in (
        ("how far was the harbour loop", "2024-03-03 07:15Z Harbour Loop"),
        ("when was the lunch swim", "2024-03-04 17:40Z Lunch Swim"),
        ("the commute home in a headwind", "2024-03-05 16:20Z, 21.4"),
        ("which shoes, Pegasus 40?", "2024-03-03 07:15Z Harbour Loop"),
        ("dales loop", "2024-03-09 09:02Z Dales loop"),
    ):
        got = mod.kernel.rank(pile, question)
        assert got and got[0]["text"].startswith(starts), question


def test_a_fit_file_is_skipped_counted_and_named(tmp_path):
    got, out = mirror_of(
        tmp_path, {"ride.tcx": TCX, "activities/9.fit.gz": b"\x0e\x10binary"}
    )
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip().endswith("wrote 1 files to " + str(out) + "; skipped 1")
    assert "activities/9.fit.gz" in got.stderr and "binary" in got.stderr
    assert not (out / "activities/9.fit.gz.txt").exists()


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(
        tmp_path, {"export/activities.csv": CSV.encode(), "a/ride.tcx": TCX}
    )
    assert got.returncode == 0, got.stderr
    assert (out / "export/activities.csv.txt").is_file() and (
        out / "a/ride.tcx.txt"
    ).is_file()
    assert got.stdout.strip().endswith("wrote 2 files to " + str(out) + "; skipped 0")


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path, {"run.gpx": GPX, ".hid/run.gpx": GPX, ".run.gpx": GPX}
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["run.gpx.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"activities.csv": CSV.encode(), "run.gpx": GPX})
    before = {p.name: p.read_bytes() for p in (tmp_path / "src").iterdir()}
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    for name in ("activities.csv.txt", "run.gpx.txt"):
        assert (again / name).read_bytes() == (out / name).read_bytes()
    assert {p.name: p.read_bytes() for p in (tmp_path / "src").iterdir()} == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {"good.gpx": GPX, "bad.gpx": b"<gpx><trk>", "bad.tcx.gz": b"not gzip",
         "notgpx.gpx": b"<kml></kml>", "empty.tcx": b"<TrainingCenterDatabase><Courses/></TrainingCenterDatabase>"},
    )  # fmt: skip
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip().endswith("wrote 1 files to " + str(out) + "; skipped 4")
    assert (out / "good.gpx.txt").is_file() and not (out / "bad.gpx.txt").exists()


def test_a_gz_that_opens_too_big_is_skipped(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "GZ_LIMIT", len(GPX) - 1)
    try:
        mod.convert(gzip.compress(GPX), "x.gpx.gz")
    except ValueError:
        pass
    else:
        raise AssertionError("a .gz bigger than the limit is refused")
    monkeypatch.setattr(mod, "GZ_LIMIT", len(GPX))
    assert mod.convert(gzip.compress(GPX), "x.gpx.gz").startswith(
        "2024-03-03 07:15Z Harbour Loop"
    )


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
        assert got.returncode == 2 and "strava.py" in got.stderr


def test_fractions_of_a_second_count_toward_the_elapsed_time():
    data = b"""<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1"><trk><type>running</type><trkseg>
<trkpt lat="0" lon="0"><time>2015-12-11T15:43:13.000+01:00</time></trkpt>
<trkpt lat="0" lon="0.0001"><time>2015-12-11T15:43:13.994+01:00</time></trkpt></trkseg></trk></gpx>"""
    assert mod.convert(data, "x.gpx") == ("2015-12-11 15:43+01:00, 0.01, 0:00:01\n")


def test_a_short_track_is_in_km_to_two_places_and_a_single_point_has_no_distance():
    data = b"""<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1"><trk><name>Pool</name><type>walking</type><trkseg>
<trkpt lat="0" lon="0"><time>2024-03-03T10:00:00Z</time></trkpt>
<trkpt lat="0.00454" lon="0"><time>2024-03-03T10:08:00Z</time></trkpt></trkseg></trk></gpx>"""
    # 0.00454 degrees of latitude is 504.8 m: 0.50 km, not 0.51
    assert mod.convert(data, "w.gpx") == "2024-03-03 10:00Z Pool, 0.50, 0:08:00\n"
    one = b"""<gpx version="1.1"><trk><name>Start</name><trkseg>
<trkpt lat="0" lon="0"><time>2024-03-03T10:00:00Z</time></trkpt></trkseg></trk></gpx>"""
    assert mod.convert(one, "o.gpx") == "2024-03-03 10:00Z Start, ?, ?\n"


def test_the_gz_limit_is_the_one_the_card_promises():
    card = (HERE / "README.md").read_text(encoding="utf-8")
    assert "opens to more than 256 MB is skipped" in card
    assert mod.GZ_LIMIT == 256 * 1024 * 1024
