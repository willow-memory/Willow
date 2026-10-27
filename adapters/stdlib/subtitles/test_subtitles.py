"""subtitles: each cue one line with its start, voices named, tags off, and
a file that isn't what its name says skipped, never guessed at."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("subtitles", HERE / "subtitles.py")
st = importlib.util.module_from_spec(spec)
spec.loader.exec_module(st)

SRT = (
    "1\n00:00:01,000 --> 00:00:04,000\nThe tide keeps\nits own calendar.\n\n"
    "2\n01:02:03,500 --> 01:02:05,000\n<i>And the harbour</i> keeps the tide's.\n"
)
VTT = (
    "WEBVTT\n\nNOTE made by hand\n\nintro\n00:01.000 --> 00:04.000\n"
    "<v Ada>Welcome back.</v>\n\nSTYLE\n::cue { color: red }\n\n"
    "00:05.000 --> 00:06.000\nposition:none here\n"
)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "subtitles.py"), *argv],
        capture_output=True, text=True,
    )  # fmt: skip


def test_each_cue_is_one_line_with_its_start():
    assert st.cues(SRT.encode(), vtt=False) == (
        "00:00:01  The tide keeps its own calendar.\n"
        "01:02:03  And the harbour keeps the tide's.\n"
    ), "lines joined, tags off, the fraction dropped"


def test_a_vtt_names_its_voices_and_its_notes_say_nothing():
    assert st.cues(VTT.encode(), vtt=True) == (
        "00:00:01  Ada: Welcome back.\n00:00:05  position:none here\n"
    ), "hours added where left off; NOTE and STYLE blocks left out"


def test_a_file_that_is_not_what_its_name_says_is_none():
    assert st.cues(b"just some text\n", vtt=False) is None, "a .srt with no cue"
    assert st.cues(VTT.encode(), vtt=False) is not None, "cues are cues"
    assert st.cues(SRT.encode(), vtt=True) is None, "a .vtt opens with WEBVTT"
    assert st.cues(b"WEBVTT\n\nno cues follow\n", vtt=True) is None
    assert st.cues(b"", vtt=False) is None
    header = b"WEBVTT - with a note\n\n00:01.000 --> 00:02.000\nstill read\n"
    assert st.cues(header, vtt=True) == "00:00:01  still read\n", (
        "the WEBVTT line may carry a note after it"
    )


def test_the_times_are_read_exactly():
    assert st.start_of("00:00:01,000 --> 00:00:04,000") == "00:00:01"
    assert st.start_of("00:01.000 --> 00:04.000") == "00:00:01"
    assert st.start_of("1:02:03.500 --> 1:02:05.000") == "01:02:03"
    assert st.start_of("not a timing") is None
    assert st.start_of("00:00:01 --> 00:00:04") is None, "a timing has its fraction"


def test_mirror_writes_both_kinds_skips_the_rest_never_touches_from(tmp_path):
    src = tmp_path / "from"
    (src / "talks").mkdir(parents=True)
    (src / "talks" / "ep1.srt").write_text(SRT)
    (src / "pod.vtt").write_text(VTT)
    (src / "fake.vtt").write_text("no header\n")
    (src / "notes.txt").write_text("00:00:01,000 --> 00:00:02,000\nnot walked\n")
    before = {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}
    dst = tmp_path / "mirror"
    got = run("mirror", "--from", str(src), "--to", str(dst))
    assert got.returncode == 0
    assert got.stdout.strip() == f"wrote 2 files to {dst}; skipped 1"
    assert sorted(p.relative_to(dst).as_posix() for p in dst.rglob("*") if p.is_file()) == [
        "pod.vtt.txt", "talks/ep1.srt.txt"]  # fmt: skip
    assert before == {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}
    again = tmp_path / "again"
    run("mirror", "--from", str(src), "--to", str(again))
    assert (again / "pod.vtt.txt").read_bytes() == (dst / "pod.vtt.txt").read_bytes()


def test_nothing_readable_is_42_and_bad_places_are_refused(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    got = run("mirror", "--from", str(empty), "--to", str(tmp_path / "m"))
    assert got.returncode == 42 and "wrote 0 files" in got.stdout
    got = run()
    assert got.returncode == 2 and "subtitles.py" in got.stderr
    got = run("mirror", "--from", str(tmp_path / "gone"), "--to", str(tmp_path / "m2"))
    assert got.returncode == 2 and got.stderr.startswith("refused")
    got = run("mirror", "--from", str(empty), "--to", str(empty / "in"))
    assert got.returncode == 2 and "inside one another" in got.stderr
