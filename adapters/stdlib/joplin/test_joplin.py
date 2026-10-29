"""joplin: a Joplin export note by note with its notebook path and dates; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import io
import tarfile
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "joplin.py"
spec = importlib.util.spec_from_file_location("joplin", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def jex(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for name, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


SAMPLE = jex(
    {
        "aaa.md": "Garden\n\nid: aaa\nparent_id: \ncreated_time: 2024-01-01T00:00:00.000Z\ntype_: 2",
        "bbb.md": "Veg\n\nid: bbb\nparent_id: aaa\ntype_: 2",
        "n1.md": "Tomato notes\n\nPlant out after the last frost.\nSecond line.\n\nid: n1\nparent_id: bbb\ncreated_time: 2024-03-02T08:00:00.000Z\nupdated_time: 2024-03-05T09:30:00.000Z\ndeleted_time: 0\ntype_: 1",
        "n2.md": "Bin day\n\nid: n2\nparent_id: \ncreated_time: 2024-04-01T00:00:00.000Z\ntype_: 1",
        "gone.md": "Old\n\nrubbish\n\nid: g\nparent_id: bbb\ndeleted_time: 1710000000000\ntype_: 1",
        "tag.md": "mytag\n\nid: t\ntype_: 5",
        "resources/pic.png": "not markdown",
    }
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


def test_a_note_is_its_title_notebook_path_dates_and_text():
    out = mod.convert(SAMPLE)
    assert out == (
        "note: Tomato notes\nnotebook: Garden/Veg\ncreated: 2024-03-02; updated: 2024-03-05\n\n"
        "Plant out after the last frost.\nSecond line.\n\n"
        "note: Bin day\ncreated: 2024-04-01\n"
    )


def test_the_trash_tags_folders_and_pictures_are_left_out():
    out = mod.convert(SAMPLE)
    for left_out in ("Old", "rubbish", "mytag", "not markdown"):
        assert left_out not in out
    assert out.count("note: ") == 2


def test_split_takes_the_title_the_body_and_the_trailing_metadata():
    title, body, meta = mod.split(
        "T\n\nline one\nkey: not meta in the body\n\nmore\n\nid: x\ntype_: 1\n"
    )
    assert (title, meta) == ("T", {"id": "x", "type_": "1"})
    assert body == "line one\nkey: not meta in the body\n\nmore"
    assert mod.split("") == ("", "", {})
    assert mod.split("Only a title") == ("Only a title", "", {})
    assert mod.split("id: x\ntype_: 1")[2] == {"id": "x", "type_": "1"}


def test_a_notebook_path_follows_parents_and_survives_a_loop():
    folders = {"a": ("A", ""), "b": ("B", "a"), "c": ("C", "b")}
    assert (
        mod.path_of(folders, "c") == "A/B/C"
        and mod.path_of(folders, "") == ""
        and mod.path_of(folders, "zz") == ""
    )
    loop = {"a": ("A", "b"), "b": ("B", "a")}
    assert mod.path_of(loop, "a") == "B/A"


def test_days_are_the_first_ten_characters_of_a_timestamp():
    assert (
        mod.day("2024-03-02T08:00:00.000Z") == "2024-03-02"
        and mod.day("") == ""
        and mod.day("1710000000000") == ""
    )


def test_a_note_with_no_dates_or_notebook_is_just_its_title_and_text():
    assert (
        mod.convert(jex({"n.md": "T\n\nbody\n\nid: n\ntype_: 1"}))
        == "note: T\n\nbody\n"
    )
    assert mod.convert(jex({"n.md": "T\n\nid: n\ntype_: 1"})) == "note: T\n"


def test_an_archive_with_no_note_is_no_result_and_a_file_that_is_no_archive_is_an_error():
    assert mod.convert(jex({"f.md": "F\n\nid: f\ntype_: 2"})) is None
    assert mod.convert(jex({})) is None
    try:
        mod.convert(b"not a tar")
    except mod.tarfile.TarError:
        pass
    else:
        raise AssertionError("not an archive")


def test_a_member_over_five_megabytes_is_left_out():
    big = "T\n\n" + "x" * (5 * 1024 * 1024 + 1) + "\n\nid: n\ntype_: 1"
    assert mod.convert(jex({"n.md": big})) is None
    exactly = "T\n\n" + "x" * 100 + "\n\nid: n\ntype_: 1"
    assert mod.convert(jex({"n.md": exactly})).startswith("note: T")


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"export/notes.jex": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "export/notes.jex.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "export/notes.jex": SAMPLE,
            ".hid/export/notes.jex": SAMPLE,
            ".export/notes.jex": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["export/notes.jex.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"export/notes.jex": SAMPLE})
    before = (tmp_path / "src" / "export/notes.jex").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "export/notes.jex.txt").read_bytes() == (
        out / "export/notes.jex.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "export/notes.jex").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(tmp_path, {"good.jex": SAMPLE, "bad.jex": b"not a tar"})
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.jex.txt").is_file() and not (out / "bad.jex.txt").exists()


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
        assert got.returncode == 2 and "joplin.py" in got.stderr
