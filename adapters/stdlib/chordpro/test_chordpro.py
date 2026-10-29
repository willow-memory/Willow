"""chordpro: a ChordPro song as its title, chords and lyrics; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "chordpro.py"
spec = importlib.util.spec_from_file_location("chordpro", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE = (
    b"{title: Down by the Estuary}\n{artist: Ada Example}\n{key: G}\n{capo: 2}\n# a comment\n\n{start_of_verse}\n"
    b"[G]Down by the [C]estuary the [D]tide comes [Em]in\n{end_of_verse}\n{soc}\nOh, the [G]water, the [D]water\n{eoc}\n"
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


def cho(text: str) -> str | None:
    return mod.convert(text.encode())


def test_a_song_is_its_title_artist_key_and_capo_then_its_chords_and_lyrics():
    out = mod.convert(SAMPLE)
    assert out == (
        "song: Down by the Estuary, by Ada Example (key G, capo 2)\nchords: G, C, D, Em\n\n"
        "Verse:\nDown by the estuary the tide comes in\nChorus:\nOh, the water, the water\n"
    )


def test_the_short_directive_names_are_read():
    out = cho("{t: Short}\n{st: A sub}\n{a: Cy}\n{k: Am}\n[Am]La [E]la\n")
    assert out.startswith("song: Short, by Cy (key Am)\nA sub\nchords: Am, E\n\nLa la")


def test_a_tab_section_is_dropped_and_a_comment_is_kept_as_a_lyric():
    out = cho(
        "{title: T}\n{start_of_tab}\ne|--0--|\n{end_of_tab}\n{c: Repeat twice}\nSing [C]this\n"
    )
    assert "e|--0--|" not in out and "Repeat twice\nSing this" in out


def test_a_line_of_only_chords_is_no_lyric():
    out = cho("{title: T}\n[Am] [G] [C]\nWords [F]here\n")
    assert out.endswith("Words here\n") and "chords: Am, G, C, F" in out


def test_several_songs_are_separate_paragraphs():
    out = cho("{title: One}\nla\n{new_song}\n{title: Two}\nlo\n")
    assert out.count("song: ") == 2 and "\n\nsong: Two" in out


def test_lyricist_composer_album_and_year_are_kept():
    out = cho(
        "{title: T}\n{lyricist: L}\n{composer: C}\n{album: Al}\n{year: 1999}\nla\n"
    )
    assert out.startswith("song: T, words L, music C (1999)\nalbum: Al")


def test_a_custom_section_is_labelled_by_its_name_or_argument():
    out = cho(
        "{title: T}\n{start_of_chorus: Refrain}\nla\n{end_of_chorus}\n{start_of_intro}\nx\n{end_of_intro}\n"
    )
    assert "Refrain:\nla" in out and "Intro:\nx" in out


def test_a_file_with_no_song_text_is_not_a_result():
    assert mod.convert(b"# only a comment\n") is None and mod.convert(b"") is None


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"songs/estuary.cho": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "songs/estuary.cho.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "songs/estuary.cho": SAMPLE,
            ".hid/songs/estuary.cho": SAMPLE,
            ".songs/estuary.cho": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["songs/estuary.cho.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"songs/estuary.cho": SAMPLE})
    before = (tmp_path / "src" / "songs/estuary.cho").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "songs/estuary.cho.txt").read_bytes() == (
        out / "songs/estuary.cho.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "songs/estuary.cho").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path, {"good.cho": SAMPLE, "bad.cho": b"\xff\xfe\x00 not utf8"}
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.cho.txt").is_file() and not (out / "bad.cho.txt").exists()


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
        assert got.returncode == 2 and "chordpro.py" in got.stderr


def test_a_song_with_no_title_is_kept_when_it_has_words_and_not_when_it_has_none():
    assert mod.convert(b"{key: G}\n") is None
    assert mod.convert(b"{key: G}\nla la\n") == "song: (untitled) (key G)\n\nla la\n"
