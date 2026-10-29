"""places: a KML, GeoJSON or GPX file as its places with note and where; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "places.py"
spec = importlib.util.spec_from_file_location("places", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE = (
    b'<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Leeds</name><Folder><name>Plots</name>'
    b"<Placemark><name>Allotment</name><description><![CDATA[<p>Plot 14, the <b>gate</b> sticks.</p>]]></description>"
    b"<Point><coordinates>-1.5491,53.8008,0</coordinates></Point></Placemark></Folder></Document></kml>"
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


def convert(text: str) -> str | None:
    return mod.convert(text.encode())


def test_a_kml_placemark_is_its_name_folders_note_and_where():
    assert (
        mod.convert(SAMPLE)
        == "place: Allotment (Leeds / Plots)\nnote: Plot 14, the gate sticks.\nat 53.80080, -1.54910\n"
    )


def test_geojson_features_are_named_by_name_title_or_label_and_a_note_is_kept():
    out = convert(
        '{"type":"FeatureCollection","features":[{"type":"Feature","properties":{"title":"Cafe","description":"Good <i>tea</i>"},"geometry":{"type":"Point","coordinates":[-1.5,53.8]}},'
        '{"type":"Feature","properties":{"label":"Pier","note":"Closed"},"geometry":{"type":"Point","coordinates":[1.25,51.5]}}]}'
    )
    assert (
        out
        == "place: Cafe\nnote: Good tea\nat 53.80000, -1.50000\n\nplace: Pier\nnote: Closed\nat 51.50000, 1.25000\n"
    )


def test_a_line_and_an_area_are_written_as_their_kind_and_first_point():
    out = convert(
        '{"type":"FeatureCollection","features":[{"type":"Feature","properties":{"name":"Path"},"geometry":{"type":"LineString","coordinates":[[1,2],[3,4],[5,6]]}},'
        '{"type":"Feature","properties":{"name":"Park"},"geometry":{"type":"Polygon","coordinates":[[[1,2],[3,4],[5,6],[1,2]]]}}]}'
    )
    assert (
        "place: Path\nline of 3 points from 2.00000, 1.00000" in out
        and "place: Park\narea of 4 points from 2.00000, 1.00000" in out
    )


def test_a_single_feature_a_multipoint_and_an_unnamed_place():
    assert (
        convert(
            '{"type":"Feature","properties":{},"geometry":{"type":"Point","coordinates":[2,1]}}'
        )
        == "place: unnamed place\nat 1.00000, 2.00000\n"
    )
    assert "line of 2 points" in convert(
        '{"type":"Feature","properties":{"name":"M"},"geometry":{"type":"MultiPoint","coordinates":[[1,2],[3,4]]}}'
    )


def test_gpx_waypoints_routes_and_tracks():
    gpx = (
        '<gpx xmlns="http://www.topografix.com/GPX/1/1"><wpt lat="53.8" lon="-1.5"><name>Car park</name><desc>Pay &amp; display</desc></wpt>'
        '<rte><name>Route</name><rtept lat="1" lon="2"/><rtept lat="3" lon="4"/></rte>'
        '<trk><name>Walk</name><cmt>Muddy</cmt><trkseg><trkpt lat="5" lon="6"/><trkpt lat="7" lon="8"/><trkpt lat="9" lon="10"/></trkseg></trk></gpx>'
    )
    out = convert(gpx)
    assert "place: Car park\nnote: Pay & display\nat 53.80000, -1.50000" in out
    assert (
        "place: Route\nline of 2 points from 1.00000, 2.00000" in out
        and "place: Walk\nnote: Muddy\nline of 3 points from 5.00000, 6.00000" in out
    )


def test_a_kml_line_and_polygon_and_a_placemark_with_no_name():
    kml = (
        "<kml><Placemark><name>Lane</name><LineString><coordinates>1,2,0 3,4,0</coordinates></LineString></Placemark>"
        "<Placemark><Polygon><outerBoundaryIs><LinearRing><coordinates>1,2 3,4 5,6 1,2</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></kml>"
    )
    out = convert(kml)
    assert (
        "place: Lane\nline of 2 points from 2.00000, 1.00000" in out
        and "place: unnamed place\narea of 4 points from 2.00000, 1.00000" in out
    )


def test_a_long_comment_before_the_root_does_not_hide_the_kind_of_file():
    pad = "<!-- " + "x" * 30000 + " -->"
    assert "place: Far" in convert(
        '<?xml version="1.0"?>'
        + pad
        + "<kml><Placemark><name>Far</name><Point><coordinates>1,2</coordinates></Point></Placemark></kml>"
    )


def test_something_that_is_not_a_places_file_is_unreadable_and_an_empty_one_is_no_result():
    for bad in (b"plain text", b"<html></html>", b"{not json"):
        try:
            mod.convert(bad)
        except mod.ERRORS:
            continue
        raise AssertionError(bad)
    assert (
        mod.convert(b'{"type":"FeatureCollection","features":[]}') is None
        and mod.convert(b"<kml></kml>") is None
    )


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"maps/leeds.kml": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "maps/leeds.kml.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "maps/leeds.kml": SAMPLE,
            ".hid/maps/leeds.kml": SAMPLE,
            ".maps/leeds.kml": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["maps/leeds.kml.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"maps/leeds.kml": SAMPLE})
    before = (tmp_path / "src" / "maps/leeds.kml").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "maps/leeds.kml.txt").read_bytes() == (
        out / "maps/leeds.kml.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "maps/leeds.kml").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(tmp_path, {"good.kml": SAMPLE, "bad.kml": b"<kml><broken"})
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.kml.txt").is_file() and not (out / "bad.kml.txt").exists()


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
        assert got.returncode == 2 and "places.py" in got.stderr
