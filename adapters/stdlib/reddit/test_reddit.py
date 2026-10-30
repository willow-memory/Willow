"""reddit: a Reddit export's posts, comments and saved items as dated lines; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "reddit.py"
spec = importlib.util.spec_from_file_location("reddit", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b"id,permalink,date,ip,subreddit,gildings,title,url,body\n"
    b"abc,https://www.reddit.com/r/gardening/comments/abc/,2024-03-02 08:15:30 UTC,1.2.3.4,gardening,0,Tomatoes want more sun,,The bed by the   fence is shaded.\n"
    b"def,https://www.reddit.com/r/gardening/comments/def/,2024-03-01 09:00:00 UTC,1.2.3.4,gardening,0,Link only,https://example.org,\n"
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


def test_posts_come_oldest_first_with_the_subreddit_title_and_body_and_no_ip():
    out = mod.convert(SAMPLE)
    assert out == (
        "2024-03-01 09:00  r/gardening post: Link only\n"
        "2024-03-02 08:15  r/gardening post: Tomatoes want more sun: The bed by the fence is shaded.\n"
    )
    assert "1.2.3.4" not in out


def test_comments_and_saved_items():
    comments = b"id,permalink,date,ip,subreddit,gildings,link,parent,body,media\nx,p,2024-03-03 19:40:00 UTC,1.2.3.4,gardening,0,l,,Move them to bed 2.,\ny,p,2024-03-04 19:40:00 UTC,1.2.3.4,,0,l,,,\n"
    assert (
        mod.convert(comments)
        == "2024-03-03 19:40  r/gardening comment: Move them to bed 2.\n"
    )
    saved = b"id,permalink\nabc,https://www.reddit.com/r/g/comments/abc/\ndef,\n"
    assert mod.convert(saved) == "saved https://www.reddit.com/r/g/comments/abc/\n"


def test_a_row_with_no_subreddit_or_date_is_written_bare():
    posts = b"id,permalink,date,title,body\nabc,p,,Just a title,\n"
    assert mod.convert(posts) == "post: Just a title\n"


def test_times_are_the_day_and_minute_and_a_bad_one_is_left_out():
    assert (
        mod.day("2024-03-02 08:15:30 UTC") == "2024-03-02 08:15"
        and mod.day("2024-03-02") == "2024-03-02"
        and mod.day("soon") == ""
        and mod.day(None) == ""
    )


def test_the_order_is_by_time_with_undated_first_and_the_same_minute_keeps_the_files_order():
    posts = b"id,permalink,date,title,body\na,p,2024-03-02 08:15:50 UTC,Zed,\nb,p,2024-03-02 08:15:10 UTC,Alpha,\nc,p,,Undated,\n"
    assert mod.convert(posts).splitlines() == [
        "post: Undated",
        "2024-03-02 08:15  post: Zed",
        "2024-03-02 08:15  post: Alpha",
    ]


def test_a_csv_that_is_not_a_reddit_file_is_not_a_result_and_bad_encoding_is_an_error():
    for other in (
        b"",
        b"a,b\n1,2\n",
        b"id,permalink,other\n1,p,x\n",
        b"id,permalink,date\n1,p,2024-03-02\n",
        b"id,permalink\n",
        b"id,permalink,date,title,body\n,,,,\n",
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"\xff\xfe\x00 bad")
    except UnicodeDecodeError:
        pass
    else:
        raise AssertionError("bad bytes")


def test_a_csv_that_is_no_export_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"posts.csv": SAMPLE, "other.csv": b"a,b\n1,2\n"})
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"reddit/posts.csv": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "reddit/posts.csv.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "reddit/posts.csv": SAMPLE,
            ".hid/reddit/posts.csv": SAMPLE,
            ".reddit/posts.csv": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["reddit/posts.csv.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"reddit/posts.csv": SAMPLE})
    before = (tmp_path / "src" / "reddit/posts.csv").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "reddit/posts.csv.txt").read_bytes() == (
        out / "reddit/posts.csv.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "reddit/posts.csv").read_bytes() == before


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
        assert got.returncode == 2 and "reddit.py" in got.stderr
