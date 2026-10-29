"""notion: a Notion export as pages and databases with their paths; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import io
import zipfile
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "notion.py"
spec = importlib.util.spec_from_file_location("notion", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def zipped(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, text in files.items():
            z.writestr(name, text)
    return buf.getvalue()


def zipped_raw(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue()


SAMPLE = zipped(
    {
        "Garden 0123456789abcdef0123456789abcdef.md": "# Garden\n\nIntro.\n",
        "Garden/Veg 11111111111111111111111111111111/Tomato notes 22222222222222222222222222222222.md": "# Tomato notes\n\nCreated: March 2, 2024 8:15 AM\nPlant out after the last frost.\n",
        "Garden/Seed orders 33333333333333333333333333333333.csv": "Name,Qty,Supplier\nBasil,3,Seeds Ltd\n,,\n",
        "Garden/photo.png": "not text",
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


def test_pages_and_databases_come_in_path_order_with_ids_off_and_the_first_heading_not_repeated():
    assert mod.convert(SAMPLE) == (
        "page: Garden\n\nIntro.\n\n"
        "table: Garden / Seed orders\nName | Qty | Supplier\nBasil | 3 | Seeds Ltd\n\n"
        "page: Garden / Veg / Tomato notes\n\nCreated: March 2, 2024 8:15 AM\nPlant out after the last frost.\n"
    )


def test_a_title_path_drops_ids_the_extension_the_export_folder_and_all():
    t = mod.title_path
    h = "0123456789abcdef0123456789abcdef"
    assert (
        t(f"Export-{h}/A {h}/B {h}.md") == "A / B"
        and t(f"A {h}/B {h}.csv") == "A / B"
        and t(f"Database {h}_all.csv") == "Database"
    )
    assert (
        t(f"Export-{h}/Solo {h}.md") == "Solo"
        and t("plain.md") == "plain"
        and t("") == ""
    )
    assert t("A/B C/D.md") == "A / B C / D" and t(f"x {h}y.md") == f"x {h}y"


def test_a_page_with_only_a_heading_is_its_title_and_other_text_is_kept_whole():
    assert mod.page("T 0123456789abcdef0123456789abcdef.md", "# T\n") == "page: T"
    assert (
        mod.page("T 0123456789abcdef0123456789abcdef.md", "No heading\nsecond\n")
        == "page: T\n\nNo heading\nsecond"
    )
    assert (
        mod.page("T 0123456789abcdef0123456789abcdef.md", "## Not first level\ntext")
        == "page: T\n\n## Not first level\ntext"
    )


def test_a_table_joins_cells_drops_empty_rows_and_an_empty_one_is_just_its_title():
    assert (
        mod.table("D 0123456789abcdef0123456789abcdef.csv", 'a,"b\n c",d\n,,\n1,2,3\n')
        == "table: D\na | b c | d\n1 | 2 | 3"
    )
    assert mod.table("D 0123456789abcdef0123456789abcdef.csv", "") == "table: D"


def test_a_zip_inside_the_export_is_read_too_and_only_one_level_deep():
    inner = zipped({"P 0123456789abcdef0123456789abcdef.md": "# P\nbody"})
    assert (
        mod.convert(zipped_raw({"Export-1-Part-1.zip": inner})) == "page: P\n\nbody\n"
    )
    deeper = zipped_raw({"a.zip": zipped_raw({"b.zip": inner})})
    assert mod.convert(deeper) is None


def test_a_zip_of_more_members_than_the_limit_is_not_read():
    filler = {f"pad/{i}.txt": "" for i in range(mod.MEMBERS - 1)}
    ok = zipped({"T 0123456789abcdef0123456789abcdef.md": "# T\nx", **filler})
    assert mod.convert(ok) is not None
    over = zipped(
        {
            "T 0123456789abcdef0123456789abcdef.md": "# T\nx",
            **filler,
            "pad/one-more.txt": "",
        }
    )
    assert mod.convert(over) is None


def test_a_zip_that_is_no_notion_export_is_not_a_result_a_big_member_is_left_out_and_a_bad_zip_is_an_error():
    assert (
        mod.convert(zipped({"readme.txt": "hi", "notes.md": "no id"})) is None
        and mod.convert(zipped({})) is None
    )
    big = "# T\n" + "x" * (5 * 1024 * 1024)
    assert mod.convert(zipped({"T 0123456789abcdef0123456789abcdef.md": big})) is None
    try:
        mod.convert(b"not a zip")
    except mod.zipfile.BadZipFile:
        pass
    else:
        raise AssertionError("bad zip")


def test_a_zip_that_is_no_export_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(
        tmp_path, {"notion.zip": SAMPLE, "other.zip": zipped({"readme.txt": "hi"})}
    )
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"export/notion.zip": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "export/notion.zip.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "export/notion.zip": SAMPLE,
            ".hid/export/notion.zip": SAMPLE,
            ".export/notion.zip": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["export/notion.zip.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"export/notion.zip": SAMPLE})
    before = (tmp_path / "src" / "export/notion.zip").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "export/notion.zip.txt").read_bytes() == (
        out / "export/notion.zip.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "export/notion.zip").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(tmp_path, {"good.zip": SAMPLE, "bad.zip": b"not a zip"})
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.zip.txt").is_file() and not (out / "bad.zip.txt").exists()


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
        assert got.returncode == 2 and "notion.py" in got.stderr
