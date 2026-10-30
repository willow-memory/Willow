"""linkedin: a LinkedIn export's messages, posts, comments and connections as dated lines; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "linkedin.py"
spec = importlib.util.spec_from_file_location("linkedin", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b"CONVERSATION ID,CONVERSATION TITLE,FROM,SENDER PROFILE URL,TO,RECIPIENT PROFILE URLS,DATE,SUBJECT,CONTENT,FOLDER\n"
    b"c1,,Ana Lopez,https://x/a,Ben Ruiz,https://x/b,2024-03-02 08:15:30 UTC,Garden talk,Are you   coming on Saturday?,INBOX\n"
    b"c1,,Ben Ruiz,https://x/b,Ana Lopez,https://x/a,2024-03-02 08:20:00 UTC,,Yes!,SENT\n"
    b"c2,,Cy,https://x/c,Ben Ruiz,https://x/b,2024-03-01 09:00:00 UTC,,,INBOX\n"
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


def test_messages_come_oldest_first_with_who_to_whom_the_subject_and_the_text():
    assert mod.convert(SAMPLE) == (
        "2024-03-02 08:15  message Ana Lopez -> Ben Ruiz: [Garden talk] Are you coming on Saturday?\n"
        "2024-03-02 08:20  message Ben Ruiz -> Ana Lopez: Yes!\n"
    )


def test_connections_skip_the_notes_before_their_header():
    conn = (
        b'Notes:\n"When exporting your connection data, you may notice that some email addresses are missing."\n\n'
        b"First Name,Last Name,URL,Email Address,Company,Position,Connected On\n"
        b"Ana,Lopez,https://x/a,ana@example.org,Garden Co,Gardener,03 Mar 2024\n"
        b"Ben,Ruiz,https://x/b,,,,02 Mar 2024\n,,,,,,01 Mar 2024\n"
    )
    assert (
        mod.convert(conn)
        == "2024-03-02  connected with Ben Ruiz\n2024-03-03  connected with Ana Lopez (Gardener, Garden Co)\n"
    )
    assert "ana@example.org" not in mod.convert(conn)


def test_shares_and_comments_are_posts_and_comments():
    shares = b"Date,ShareLink,ShareCommentary,SharedUrl,MediaUrl,Visibility\n2024-03-04 09:00:00,l,Planted out the tomatoes.,https://example.org/guide,,MEMBER_NETWORK\n2024-03-05 09:00:00,l,,,,\n"
    assert (
        mod.convert(shares)
        == "2024-03-04 09:00  post: Planted out the tomatoes. https://example.org/guide\n"
    )
    comments = b"Date,Link,Message\n2024-03-05 10:00:00,l,Congratulations!\n2024-03-06 10:00:00,l,\n"
    assert mod.convert(comments) == "2024-03-05 10:00  comment: Congratulations!\n"


def test_dates_in_both_forms_and_a_bad_one_is_left_out():
    d = mod.day
    assert (
        d("2024-03-02 08:15:30 UTC") == "2024-03-02 08:15"
        and d("2024-03-02") == "2024-03-02"
        and d("2024-03-02T08:15:30Z") == "2024-03-02 08:15"
    )
    assert (
        d("02 Mar 2024") == "2024-03-02"
        and d("") == ""
        and d("soon") == ""
        and d(None) == ""
    )
    assert mod.convert(b"Date,Link,Message\nsoon,l,undated\n") == "comment: undated\n"


def test_a_message_with_no_sender_and_the_order_for_undated_and_same_minute_rows():
    msg = b"CONVERSATION ID,FROM,TO,DATE,SUBJECT,CONTENT\nc,,Ben,2024-03-02 08:15:30 UTC,,anonymous\n"
    assert mod.convert(msg) == "2024-03-02 08:15  message: anonymous\n"
    ordered = b"Date,Link,Message\n2024-03-02 08:15:00,l,zed\n2024-03-02 08:15:30,l,alpha\n,l,undated\n"
    assert mod.convert(ordered).splitlines() == [
        "comment: undated",
        "2024-03-02 08:15  comment: zed",
        "2024-03-02 08:15  comment: alpha",
    ]


def test_a_csv_that_is_not_one_of_the_four_is_not_a_result_and_bad_encoding_is_an_error():
    for other in (
        b"",
        b"a,b\n1,2\n",
        b"Date,Other\n2024-03-02,x\n",
        b"First Name,Other\nAna,x\n",
        b"Date,Link,Message\n",
        b"Notes:\nonly notes\n",
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"\xff\xfe\x00 bad")
    except UnicodeDecodeError:
        pass
    else:
        raise AssertionError("bad bytes")


def test_a_csv_that_is_no_export_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"messages.csv": SAMPLE, "other.csv": b"a,b\n1,2\n"})
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"linkedin/messages.csv": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "linkedin/messages.csv.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "linkedin/messages.csv": SAMPLE,
            ".hid/linkedin/messages.csv": SAMPLE,
            ".linkedin/messages.csv": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["linkedin/messages.csv.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"linkedin/messages.csv": SAMPLE})
    before = (tmp_path / "src" / "linkedin/messages.csv").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "linkedin/messages.csv.txt").read_bytes() == (
        out / "linkedin/messages.csv.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "linkedin/messages.csv").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path, {"good.csv": SAMPLE, "bad.csv": b"\xff\xfe\x00 not csv"}
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.csv.txt").is_file() and not (out / "bad.csv.txt").exists()


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
        assert got.returncode == 2 and "linkedin.py" in got.stderr
