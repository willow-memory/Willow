"""musicxml: a MusicXML score as titles, credits, key, tempo, markings and lyrics; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "musicxml.py"
spec = importlib.util.spec_from_file_location("musicxml", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'<?xml version="1.0"?><score-partwise version="3.1"><work><work-title>Evening Song</work-title></work>'
    b'<identification><creator type="composer">Ana Example</creator><creator type="lyricist">Ben Sample</creator></identification>'
    b'<part-list><score-part id="P1"><part-name>Soprano</part-name></score-part></part-list>'
    b'<part id="P1"><measure number="1"><attributes><key><fifths>1</fifths><mode>major</mode></key><time><beats>3</beats><beat-type>4</beat-type></time></attributes>'
    b'<direction><direction-type><words>Andante</words></direction-type><sound tempo="72"/></direction>'
    b"<direction><direction-type><dynamics><p/></dynamics></direction-type></direction>"
    b'<note><pitch><step>G</step><octave>4</octave></pitch><lyric number="1"><syllabic>begin</syllabic><text>Ev</text></lyric></note>'
    b'<note><pitch><step>A</step><octave>4</octave></pitch><lyric number="1"><syllabic>end</syllabic><text>ening</text></lyric></note>'
    b'<note><pitch><step>B</step><octave>4</octave></pitch><lyric number="1"><syllabic>single</syllabic><text>comes</text></lyric><lyric number="2"><syllabic>single</syllabic><text>Morn</text></lyric></note></measure></part></score-partwise>'
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


def test_a_score_is_titles_credits_parts_key_time_tempo_markings_and_lyrics():
    assert mod.convert(SAMPLE) == (
        "title: Evening Song\ncomposer: Ana Example; lyricist: Ben Sample\nparts: Soprano\n"
        "key: G major; time: 3/4; tempo: 72\nmarkings: m.1 Andante; m.1 p\n"
        "lyrics (Soprano): Evening comes\nlyrics (Soprano, verse 2): Morn\n"
    )


def test_key_names_from_the_circle_of_fifths():
    k = mod.key_name
    assert (
        k("0", "major") == "C major"
        and k("0", "minor") == "A minor"
        and k("0", "") == "C major"
    )
    assert k("-7", "major") == "Cb major" and k("7", "major") == "C# major"
    assert (
        k("-3", "minor") == "C minor"
        and k("3", "minor") == "F# minor"
        and k("-7", "minor") == "Ab minor"
        and k("7", "minor") == "A# minor"
    )
    assert (
        k("2", "MINOR") == "B minor"
        and k("8", "major") == ""
        and k("-8", "major") == ""
        and k("x", "major") == ""
    )


def test_a_movement_title_is_added_only_when_it_differs():
    two = b"<score-partwise><work><work-title>Suite</work-title></work><movement-title>Prelude</movement-title></score-partwise>"
    assert mod.convert(two) == "title: Suite\nmovement: Prelude\n"
    same = b"<score-partwise><work><work-title>Suite</work-title></work><movement-title>Suite</movement-title></score-partwise>"
    assert mod.convert(same) == "title: Suite\n"


def test_lyrics_join_hyphenated_syllables_and_keep_verses_apart():
    part = mod.ET.fromstring(
        "<part><note><lyric><syllabic>begin</syllabic><text>a</text></lyric></note>"
        "<note><lyric><syllabic>middle</syllabic><text>ga</text></lyric></note>"
        "<note><lyric><syllabic>end</syllabic><text>in</text></lyric></note>"
        '<note><lyric><text>now</text></lyric></note><note><lyric number="2"><text>two</text></lyric></note>'
        "<note><lyric><text></text></lyric></note><note/></part>"
    )
    assert mod.lyrics_of(part) == {"1": "again now", "2": "two"}


def test_markings_and_dynamics_are_in_order_with_their_measures():
    xml = (
        b'<score-partwise><part-list><score-part id="P1"><part-name>A</part-name></score-part></part-list><part id="P1">'
        b'<measure number="1"><direction><direction-type><words>Andante</words></direction-type></direction></measure>'
        b'<measure number="9"><direction><direction-type><words>cresc.</words></direction-type></direction></measure>'
        b'<measure number="17"><direction><direction-type><dynamics><f/></dynamics></direction-type></direction></measure></part></score-partwise>'
    )
    assert "markings: m.1 Andante; m.9 cresc.; m.17 f\n" in mod.convert(xml)


def test_a_score_whose_key_cannot_be_named_gives_no_key():
    xml = b"<score-partwise><work><work-title>T</work-title></work><part><measure><attributes><key><fifths>9</fifths></key></attributes></measure></part></score-partwise>"
    assert mod.convert(xml) == "title: T\n"


def test_an_xml_file_that_is_no_score_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"a.xml": SAMPLE, "b.xml": b"<root/>"})
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "a.xml.txt").is_file() and not (out / "b.xml.txt").exists()


def test_other_xml_a_timewise_score_and_entity_bombs_are_not_read():
    assert mod.convert(b"<root/>") is None and mod.convert(b"<score-timewise/>") is None
    assert (
        mod.convert(
            b'<!DOCTYPE s [<!ENTITY a "x">]><score-partwise><work><work-title>&a;</work-title></work></score-partwise>'
        )
        is None
    )
    assert mod.convert(b"<score-partwise></score-partwise>") is None


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"scores/song.musicxml": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "scores/song.musicxml.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "scores/song.musicxml": SAMPLE,
            ".hid/scores/song.musicxml": SAMPLE,
            ".scores/song.musicxml": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["scores/song.musicxml.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"scores/song.musicxml": SAMPLE})
    before = (tmp_path / "src" / "scores/song.musicxml").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "scores/song.musicxml.txt").read_bytes() == (
        out / "scores/song.musicxml.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "scores/song.musicxml").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path, {"good.musicxml": SAMPLE, "bad.musicxml": b"<score-partwise><part>"}
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.musicxml.txt").is_file() and not (
        out / "bad.musicxml.txt"
    ).exists()


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
        assert got.returncode == 2 and "musicxml.py" in got.stderr
