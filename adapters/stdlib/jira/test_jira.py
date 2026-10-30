"""jira: a Jira export issue by issue with comments; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "jira.py"
spec = importlib.util.spec_from_file_location("jira", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'<rss version="0.92"><channel><item><title>[GARDEN-12] Tomatoes want more sun</title><key id="1">GARDEN-12</key><summary>Tomatoes want more sun</summary>'
    b'<type>Bug</type><status>Open</status><reporter username="a">ana</reporter><assignee username="b">ben</assignee><created>Sat, 2 Mar 2024 08:15:00 +0000</created>'
    b"<description>&lt;p&gt;The bed by the  fence is shaded.&lt;/p&gt;</description><labels><label>garden</label><label>urgent</label></labels>"
    b'<comments><comment id="1" author="ben" created="Sun, 3 Mar 2024 10:00:00 +0000">Move them to bed 2.</comment></comments></item>'
    b'<item><title>[GARDEN-3] Order seed</title><key id="2">GARDEN-3</key><type>Task</type><status>Done</status><reporter>cy</reporter><assignee>Unassigned</assignee><created>Fri, 1 Mar 2024 09:00:00 +0000</created></item></channel></rss>'
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


def test_an_xml_export_gives_each_issue_oldest_first_with_who_labels_description_and_comments():
    assert mod.convert(SAMPLE) == (
        "GARDEN-3 (Done, Task) 2024-03-01 cy: Order seed\n\n"
        "GARDEN-12 (Open, Bug) 2024-03-02 ana -> ben: Tomatoes want more sun [garden, urgent]\n"
        "  The bed by the fence is shaded.\n  comment 2024-03-03 ben: Move them to bed 2.\n"
    )


CSV = (
    "Summary,Issue key,Issue Type,Status,Assignee,Reporter,Created,Labels,Labels,Description,Comment,Comment\n"
    'Tomatoes want more sun,GARDEN-12,Bug,Open,ben,ana,02/Mar/24 8:15 AM,garden,urgent,"The bed by the  fence\nis shaded.",03/Mar/24 10:00 AM;ben;Move them to bed 2.,\n'
    "Order seed,GARDEN-3,Task,Done,,cy,01/Mar/24 9:00 AM,,,,,\n"
)


def test_a_csv_export_gives_the_same_with_repeated_label_and_comment_columns():
    assert mod.convert(CSV.encode()) == (
        "GARDEN-3 (Done, Task) 2024-03-01 cy: Order seed\n\n"
        "GARDEN-12 (Open, Bug) 2024-03-02 ana -> ben: Tomatoes want more sun [garden, urgent]\n"
        "  The bed by the fence is shaded.\n  comment 2024-03-03 ben: Move them to bed 2.\n"
    )


def test_dates_in_both_forms():
    assert (
        mod.day_rfc("Sat, 2 Mar 2024 08:15:00 +0000") == "2024-03-02"
        and mod.day_rfc("garbage") == ""
        and mod.day_rfc(None) == ""
    )
    assert (
        mod.day_csv("02/Mar/24 8:15 AM") == "2024-03-02"
        and mod.day_csv("02/Mar/2024 8:15 PM") == "2024-03-02"
        and mod.day_csv("02/Mar/24 18:15") == "2024-03-02"
    )
    assert (
        mod.day_csv("") == "" and mod.day_csv("soon") == "" and mod.day_csv(None) == ""
    )


def test_an_issue_line_says_what_it_has():
    assert mod.line("K-1", "", "", "", "", "S", []) == "K-1 S"
    assert (
        mod.line("K-1", "Open", "", "2024-03-02", "ana", "S", ["a"])
        == "K-1 (Open) 2024-03-02 ana: S [a]"
    )
    assert (
        mod.line("K-1", "", "Bug", "", "ana -> ben", "S", [])
        == "K-1 (Bug) ana -> ben: S"
    )


def test_an_item_with_no_key_a_missing_summary_and_a_comment_with_no_date_still_read():
    xml = b'<rss><item><title>[K-2] From title</title></item><item><key>K-1</key><title>[K-1] Titled</title><comments><comment author="a">no date</comment><comment author="a"> </comment></comments></item></rss>'
    assert mod.convert(xml) == "K-1 Titled\n  comment a: no date\n"


def test_other_xml_other_csv_and_an_entity_bomb_are_not_results():
    for other in (
        b"<root/>",
        b"<rss><channel/></rss>",
        b'<!DOCTYPE r [<!ENTITY a "x">]><rss><item><key>K-1</key></item></rss>',
        b"a,b\n1,2\n",
        b"Summary,Issue key\n",
        b"Summary,Issue key\n,,\n",
        b"",
    ):
        assert mod.convert(other) is None, other


def test_a_bad_xml_file_is_an_error():
    try:
        mod.convert(b"<rss><item>")
    except mod.ET.ParseError:
        pass
    else:
        raise AssertionError("bad xml")


def test_a_file_that_is_no_export_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "export.xml": SAMPLE,
            "issues.csv": CSV.encode(),
            "other.xml": b"<root/>",
            "other.csv": b"a,b\n1,2\n",
        },
    )
    assert "wrote 2 files" in got.stdout and "skipped 2" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"jira/export.xml": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "jira/export.xml.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "jira/export.xml": SAMPLE,
            ".hid/jira/export.xml": SAMPLE,
            ".jira/export.xml": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["jira/export.xml.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"jira/export.xml": SAMPLE})
    before = (tmp_path / "src" / "jira/export.xml").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "jira/export.xml.txt").read_bytes() == (
        out / "jira/export.xml.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "jira/export.xml").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(tmp_path, {"good.xml": SAMPLE, "bad.xml": b"<rss><item>"})
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.xml.txt").is_file() and not (out / "bad.xml.txt").exists()


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
        assert got.returncode == 2 and "jira.py" in got.stderr
