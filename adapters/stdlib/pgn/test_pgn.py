"""pgn: a PGN game as who, when, where, the result, the opening and the comments; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "pgn.py"
spec = importlib.util.spec_from_file_location("pgn", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE = (
    b'[Event "Club Championship"]\n[Site "Leeds"]\n[Date "2024.03.03"]\n[White "Ada Example"]\n[Black "Cy Sample"]\n[Result "1-0"]\n[ECO "B20"]\n[Opening "Sicilian Defense"]\n\n'
    b"1. e4 {My usual start.} c5 2. Nf3 d6 (2... Nc6 {Also fine}) 3. d4 cxd4 4. Nxd4 Nf6 14. Qd7 {I missed the fork here.} 1-0\n"
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


def pgn(text: str) -> str | None:
    return mod.convert(text.encode())


def test_a_game_is_its_players_date_event_site_result_and_opening():
    out = mod.convert(SAMPLE)
    assert out.startswith(
        "game: Ada Example vs Cy Sample, 2024-03-03, Club Championship, Leeds\nresult: 1-0 (Sicilian Defense, B20)\n"
    )


def test_each_comment_is_kept_whole_with_the_move_it_follows():
    out = mod.convert(SAMPLE)
    assert "note after 1.e4: My usual start." in out
    assert "note after 14.Qd7: I missed the fork here." in out


def test_black_s_move_is_marked_with_three_dots():
    out = pgn(
        '[White "A"]\n[Black "B"]\n\n1. e4 e5 {Open game} 2. Nf3 Nc6 3. Bb5 a6 {Morphy}\n'
    )
    assert "note after 1...e5: Open game" in out
    assert "note after 3...a6: Morphy" in out


def test_a_move_number_and_the_dots_come_from_the_movetext():
    out = pgn(
        '[White "A"]\n[Black "B"]\n\n1. e4 {first} 1... e5 {second} 2. Nf3 {third}\n'
    )
    assert out.splitlines()[1:] == [
        "note after 1.e4: first",
        "note after 1...e5: second",
        "note after 2.Nf3: third",
    ]


def test_comments_in_variations_are_kept_and_the_variation_moves_are_not_notes_anchors():
    out = pgn(
        '[White "A"]\n[Black "B"]\n\n1. e4 e5 (1... c5 {Sicilian}) 2. Nf3 {After Nf3}\n'
    )
    assert "note after 1...e5: Sicilian" in out
    assert "note after 2.Nf3: After Nf3" in out


def test_a_semicolon_comment_runs_to_the_end_of_the_line():
    out = pgn('[White "A"]\n[Black "B"]\n\n1. e4 ; a line comment\ne5 2. Nf3\n')
    assert "note after 1.e4: a line comment" in out


def test_an_unknown_date_player_and_site_are_left_out_or_marked():
    out = pgn(
        '[Event "?"]\n[Site "?"]\n[Date "????.??.??"]\n[White "Ada"]\n[Black "?"]\n[Result "*"]\n\n1. e4 {hi} *\n'
    )
    assert (
        out.splitlines()[0] == "game: Ada vs ?" and out.splitlines()[1] == "result: *"
    )


def test_several_games_are_separate_paragraphs_and_the_annotator_is_kept():
    two = '[White "A"]\n[Black "B"]\n[Annotator "Coach"]\n\n1. e4 {x} *\n\n[White "C"]\n[Black "D"]\n\n1. d4 {y} *\n'
    out = pgn(two)
    assert (
        out.count("game: ") == 2
        and "annotator: Coach" in out
        and "\n\ngame: C vs D" in out
    )


def test_a_tag_value_with_quotes_and_unicode():
    assert 'game: Zoë "Z" Quinn vs B' in pgn(
        '[White "Zoë \\"Z\\" Quinn"]\n[Black "B"]\n\n1. e4 {x} *\n'
    )


def test_a_file_with_no_game_is_not_a_result():
    assert mod.convert(b"") is None and mod.convert(b"\n\n") is None


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"games/club.pgn": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "games/club.pgn.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "games/club.pgn": SAMPLE,
            ".hid/games/club.pgn": SAMPLE,
            ".games/club.pgn": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["games/club.pgn.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"games/club.pgn": SAMPLE})
    before = (tmp_path / "src" / "games/club.pgn").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "games/club.pgn.txt").read_bytes() == (
        out / "games/club.pgn.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "games/club.pgn").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(tmp_path, {"good.pgn": SAMPLE, "bad.pgn": b"\xff\xfe\x00"})
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.pgn.txt").is_file() and not (out / "bad.pgn.txt").exists()


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
        assert got.returncode == 2 and "pgn.py" in got.stderr
