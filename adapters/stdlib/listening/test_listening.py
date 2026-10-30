"""listening: a Spotify streaming history as dated lines of plays; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "listening.py"
spec = importlib.util.spec_from_file_location("listening", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'[{"endTime":"2024-03-02 09:02","artistName":"Nina Simone","trackName":"Sinnerman","msPlayed":620000},'
    b'{"endTime":"2024-03-02 08:15","artistName":"X","trackName":"Skipped","msPlayed":29999},'
    b'{"ts":"2024-03-02T07:30:00Z","master_metadata_track_name":"Feeling Good","master_metadata_album_artist_name":"Nina Simone","ms_played":175500},'
    b'{"ts":"2024-03-03T10:00:00Z","episode_name":"Staking tomatoes","episode_show_name":"Garden Radio","ms_played":1450000},'
    b'{"ts":"2024-03-03T11:00:00Z","ms_played":60000}]'
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


def test_plays_come_oldest_first_in_both_shapes_with_podcasts_and_lengths():
    assert mod.convert(SAMPLE) == (
        "2024-03-02 07:30  Nina Simone - Feeling Good (2:55)\n"
        "2024-03-02 09:02  Nina Simone - Sinnerman (10:20)\n"
        "2024-03-03 10:00  Garden Radio: Staking tomatoes (24:10)\n"
    )


def test_thirty_seconds_is_a_play_and_less_is_a_skip():
    assert (
        mod.play({"msPlayed": 29_999, "trackName": "t", "endTime": "2024-03-02 08:15"})
        is None
    )
    assert mod.play(
        {"msPlayed": 30_000, "trackName": "t", "endTime": "2024-03-02 08:15"}
    ) == ("2024-03-02 08:15", "2024-03-02 08:15  t (0:30)")
    assert (
        mod.play({"msPlayed": True, "trackName": "t"}) is None
        and mod.play({"msPlayed": "40000", "trackName": "t"}) is None
    )


def test_a_track_with_no_artist_a_play_with_no_time_and_an_episode_with_no_show_still_read():
    assert mod.play({"msPlayed": 60_000, "trackName": "Solo"}) == ("", "Solo (1:00)")
    assert mod.play(
        {"ms_played": 61_000, "episode_name": "Ep", "ts": "2024-03-02"}
    ) == ("2024-03-02", "2024-03-02  Ep (1:01)")
    assert mod.play({"msPlayed": 60_000}) is None and mod.play({}) is None


def test_lengths_are_minutes_and_seconds():
    assert (
        mod.length(0) == "0:00"
        and mod.length(59_999) == "0:59"
        and mod.length(60_000) == "1:00"
        and mod.length(3_725_000) == "62:05"
    )


def test_json_that_is_not_a_history_is_not_a_result_and_bad_json_is_an_error():
    for other in (
        b"{}",
        b"[]",
        b"5",
        b"null",
        b'"text"',
        b"[1, 2]",
        b'[{"other": 1}]',
        b'[{"msPlayed": 10, "trackName": "short"}]',
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"[nope")
    except ValueError:
        pass
    else:
        raise AssertionError("bad json")


def test_a_json_file_that_is_no_history_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"a.json": SAMPLE, "b.json": b'{"other": 1}'})
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"Spotify/StreamingHistory0.json": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "Spotify/StreamingHistory0.json.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "Spotify/StreamingHistory0.json": SAMPLE,
            ".hid/Spotify/StreamingHistory0.json": SAMPLE,
            ".Spotify/StreamingHistory0.json": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["Spotify/StreamingHistory0.json.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"Spotify/StreamingHistory0.json": SAMPLE})
    before = (tmp_path / "src" / "Spotify/StreamingHistory0.json").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "Spotify/StreamingHistory0.json.txt").read_bytes() == (
        out / "Spotify/StreamingHistory0.json.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "Spotify/StreamingHistory0.json").read_bytes() == before


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
        assert got.returncode == 2 and "listening.py" in got.stderr
