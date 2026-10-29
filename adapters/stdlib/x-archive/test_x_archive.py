"""x-archive: an X archive's posts and direct messages as dated lines; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "x_archive.py"
spec = importlib.util.spec_from_file_location("x_archive", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'window.YTD.tweets.part0 = [ {"tweet": {"created_at": "Wed Mar 02 08:15:00 +0000 2022", "full_text": "Planted out the tomatoes. https://t.co/abc &amp; more",'
    b' "entities": {"urls": [{"url": "https://t.co/abc", "expanded_url": "https://example.org/guide"}]}}},'
    b' {"tweet": {"created_at": "Thu Mar 03 19:40:00 -0500 2022", "full_text": "@ana the slugs are winning.", "in_reply_to_status_id_str": "123"}} ]'
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


def test_posts_come_oldest_first_in_utc_with_links_expanded_entities_read_and_replies_marked():
    assert mod.convert(SAMPLE) == (
        "2022-03-02 08:15  Planted out the tomatoes. https://example.org/guide & more\n"
        "2022-03-04 00:40  @ana the slugs are winning. (reply)\n"
    )


def test_direct_messages_name_the_conversation_and_the_sender():
    dms = (
        b'window.YTD.direct_messages.part0 = [{"dmConversation": {"conversationId": "12-34", "messages": ['
        b'{"messageCreate": {"senderId": "12", "createdAt": "2022-03-04T09:00:00.000Z", "text": "are you  coming &amp; when?"}},'
        b'{"messageCreate": {"senderId": "34", "createdAt": "2022-03-04T09:05:00.000Z", "text": ""}}, 5]}}]'
    )
    assert (
        mod.convert(dms) == "2022-03-04 09:00  dm 12-34: 12: are you coming & when?\n"
    )


def test_times_are_parsed_to_the_minute_and_a_bad_one_is_left_out_not_fatal():
    assert mod.tweet_time("Wed Mar 02 08:15:59 +0000 2022") == "2022-03-02 08:15"
    assert mod.tweet_time("Wed Mar 02 23:30:00 -0200 2022") == "2022-03-03 01:30"
    assert mod.tweet_time("yesterday") == "" and mod.tweet_time(None) == ""
    assert (
        mod.iso_time("2022-03-04T09:05:06Z") == "2022-03-04 09:05"
        and mod.iso_time("2022-03-04") == "2022-03-04"
        and mod.iso_time(7) == ""
    )
    undated = b'window.YTD.tweets.part0 = [{"tweet": {"full_text": "no date"}}]'
    assert mod.convert(undated) == "no date\n"


def test_a_semicolon_after_the_array_and_other_part_numbers_are_fine():
    assert (
        mod.convert(b'window.YTD.tweets.part3 = [{"tweet": {"full_text": "x"}}];\n')
        == "x\n"
    )
    assert (
        mod.convert(b'  window.YTD.tweet.part0=[{"tweet":{"text":"older shape"}}]')
        == "older shape\n"
    )


def test_other_archive_files_other_js_and_empty_data_are_not_results_and_bad_json_is_an_error():
    for other in (
        b'window.YTD.like.part0 = [{"like": {"tweetId": "1", "fullText": "x"}}]',
        b"var x = 1;",
        b"",
        b"window.YTD.tweets.part0 = {}",
        b"window.YTD.tweets.part0 = []",
        b'window.YTD.tweets.part0 = [{"tweet": {"full_text": "  "}}, 5, {}]',
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"window.YTD.tweets.part0 = [nope")
    except ValueError:
        pass
    else:
        raise AssertionError("bad json")


def test_a_js_file_that_is_no_archive_data_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "data/tweets.js": SAMPLE,
            "data/like.js": b"window.YTD.like.part0 = []",
            "app.js": b"console.log(1)",
        },
    )
    assert "wrote 1 files" in got.stdout and "skipped 2" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"data/tweets.js": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "data/tweets.js.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "data/tweets.js": SAMPLE,
            ".hid/data/tweets.js": SAMPLE,
            ".data/tweets.js": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["data/tweets.js.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"data/tweets.js": SAMPLE})
    before = (tmp_path / "src" / "data/tweets.js").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "data/tweets.js.txt").read_bytes() == (
        out / "data/tweets.js.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "data/tweets.js").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path, {"good.js": SAMPLE, "bad.js": b"window.YTD.tweets.part0 = [nope"}
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.js.txt").is_file() and not (out / "bad.js.txt").exists()


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
        assert got.returncode == 2 and "x_archive.py" in got.stderr
