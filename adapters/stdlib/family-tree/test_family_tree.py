"""family-tree: a GEDCOM family tree as one paragraph for each person; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "family_tree.py"
spec = importlib.util.spec_from_file_location("family_tree", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE = (
    b"0 HEAD\n1 CHAR UTF-8\n0 @I1@ INDI\n1 NAME John /Smith/\n1 BIRT\n2 DATE 2 Mar 1850\n2 PLAC Leeds\n1 DEAT\n2 DATE 1920\n2 PLAC York\n"
    b"1 FAMC @F1@\n1 FAMS @F2@\n1 NOTE A weaver\n2 CONC  and a singer.\n2 CONT Second line.\n"
    b"0 @I2@ INDI\n1 NAME Mary /Brown/\n1 FAMS @F2@\n0 @I4@ INDI\n1 NAME Arthur /Smith/\n0 @I5@ INDI\n1 NAME Ann /Jones/\n"
    b"0 @F1@ FAM\n1 HUSB @I4@\n1 WIFE @I5@\n1 CHIL @I1@\n0 @F2@ FAM\n1 HUSB @I1@\n1 WIFE @I2@\n1 MARR\n2 DATE 1875\n2 PLAC Hull\n0 TRLR\n"
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


def ged(text: str) -> str | None:
    return mod.convert(("0 HEAD\n" + text).encode())


def test_a_person_is_born_died_with_parents_spouse_and_note():
    out = mod.convert(SAMPLE)
    first = out.split("\n\n")[0]
    assert first == (
        "John Smith (@I1@): born 2 Mar 1850 in Leeds; died 1920 in York; father Arthur Smith (@I4@); "
        "mother Ann Jones (@I5@); married Mary Brown (@I2@) 1875 in Hull; note: A weaver and a singer. Second line."
    )


def test_every_person_is_a_paragraph_in_file_order_with_their_own_id():
    out = mod.convert(SAMPLE)
    assert [p.split(":")[0].rstrip(".") for p in out.strip().split("\n\n")] == [
        "John Smith (@I1@)", "Mary Brown (@I2@)", "Arthur Smith (@I4@)", "Ann Jones (@I5@)"]  # fmt: skip
    assert "Mary Brown (@I2@): married John Smith (@I1@) 1875 in Hull." in out


def test_the_slashes_round_a_surname_go_and_a_person_with_no_facts_is_still_named():
    out = ged("0 @I1@ INDI\n1 NAME Ana /Lopez de la Cruz/\n")
    assert out == "Ana Lopez de la Cruz (@I1@).\n"
    assert ged("0 @I1@ INDI\n1 NAME //\n") == "(no name) (@I1@).\n"
    assert ged("0 @I1@ INDI\n") == "(no name) (@I1@).\n"


def test_dates_and_places_are_kept_as_written_and_a_bare_event_is_said():
    out = ged(
        "0 @I1@ INDI\n1 NAME A /B/\n1 BIRT\n2 DATE ABT 1850\n1 DEAT Y\n1 BURI\n2 PLAC Hull\n1 CHR\n2 DATE BEF 1851\n"
    )
    assert (
        out == "A B (@I1@): born ABT 1850; christened BEF 1851; died; buried in Hull.\n"
    )


def test_a_family_member_who_is_not_in_the_file_is_named_by_id():
    out = ged("0 @I1@ INDI\n1 NAME A /B/\n1 FAMC @F1@\n0 @F1@ FAM\n1 HUSB @I9@\n")
    assert "father @I9@" in out


def test_lines_with_odd_endings_and_a_byte_order_mark_are_read():
    out = mod.convert(
        b"\xef\xbb\xbf0 HEAD\r\n0 @I1@ INDI\r\n1 NAME A /B/\r\n1 BIRT\r\n2 DATE 1900\r\n"
    )
    assert out == "A B (@I1@): born 1900.\n"


def test_a_file_with_no_person_is_not_a_result_and_a_file_that_is_no_gedcom_is_an_error():
    assert mod.convert(b"0 HEAD\n0 TRLR\n") is None
    for not_gedcom in (b"", b"just some text\n", b"1 NAME A /B/\n"):
        try:
            mod.convert(not_gedcom)
        except ValueError:
            pass
        else:
            raise AssertionError(not_gedcom)


def test_a_record_that_is_not_a_family_is_not_one():
    out = ged("0 @I1@ INDI\n1 NAME A /B/\n1 FAMC @S1@\n0 @S1@ SOUR\n1 HUSB @I9@\n")
    assert "father" not in out


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"tree/family.ged": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "tree/family.ged.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "tree/family.ged": SAMPLE,
            ".hid/tree/family.ged": SAMPLE,
            ".tree/family.ged": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["tree/family.ged.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"tree/family.ged": SAMPLE})
    before = (tmp_path / "src" / "tree/family.ged").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "tree/family.ged.txt").read_bytes() == (
        out / "tree/family.ged.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "tree/family.ged").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(tmp_path, {"good.ged": SAMPLE, "bad.ged": b"\xff\xfe\x00"})
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.ged.txt").is_file() and not (out / "bad.ged.txt").exists()


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
        assert got.returncode == 2 and "family_tree.py" in got.stderr
