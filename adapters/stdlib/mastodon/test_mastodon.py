"""mastodon: a Mastodon outbox as dated lines of your posts; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "mastodon.py"
spec = importlib.util.spec_from_file_location("mastodon", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'{"type":"OrderedCollection","orderedItems":['
    b'{"type":"Create","published":"2024-03-03T19:40:00Z","object":{"type":"Note","summary":"gardening","content":"<p>The slugs are <b>winning</b>.</p>","inReplyTo":"https://x/1",'
    b'"attachment":[{"type":"Document","mediaType":"image/jpeg","name":"slug on a leaf"},{"type":"Document","mediaType":"video/mp4","name":"clip"},{"mediaType":"image/png"}]}},'
    b'{"type":"Announce","published":"2024-03-02T10:00:00Z","object":"https://x/2"},'
    b'{"type":"Create","published":"2024-03-02T08:15:00Z","object":{"type":"Note","content":"<p>Planted out the tomatoes   today.</p>"}}]}'
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


def test_your_posts_come_oldest_first_with_warning_reply_and_attachment_descriptions():
    assert mod.convert(SAMPLE) == (
        "2024-03-02 08:15  Planted out the tomatoes today.\n"
        "2024-03-03 19:40  [cw: gardening] The slugs are winning. (reply)  [image: slug on a leaf]  [attachment: clip]\n"
    )


def test_boosts_and_likes_and_posts_with_nothing_in_them_are_left_out():
    doc = (
        b'{"orderedItems":[{"type":"Like","object":"x"},{"type":"Announce","object":"y"},5,{"type":"Create"},'
        b'{"type":"Create","object":{"content":""}},{"type":"Create","object":{"content":"<p></p>"}},'
        b'{"type":"Create","published":"2024-01-01","object":{"content":"kept"}}]}'
    )
    assert mod.convert(doc) == "2024-01-01  kept\n"


def test_a_post_with_no_date_is_still_written_and_the_object_may_carry_the_date():
    assert (
        mod.convert(
            b'{"orderedItems":[{"type":"Create","object":{"content":"no date"}}]}'
        )
        == "no date\n"
    )
    assert (
        mod.convert(
            b'{"orderedItems":[{"type":"Create","object":{"published":"2024-05-06T07:08:09Z","content":"inner"}}]}'
        )
        == "2024-05-06 07:08  inner\n"
    )
    assert (
        mod.when("2024-03-02") == "2024-03-02"
        and mod.when("soon") == ""
        and mod.when(None) == ""
    )


def test_the_order_is_by_the_day_with_undated_posts_first():
    doc = (
        b'{"orderedItems":[{"type":"Create","published":"2024-03-02T00:00:00Z","object":{"content":"Alpha"}},'
        b'{"type":"Create","object":{"content":"Zed"}}]}'
    )
    assert mod.convert(doc).splitlines() == ["Zed", "2024-03-02 00:00  Alpha"]


def test_a_post_that_is_only_a_warning_or_an_attachment_is_still_a_post():
    assert mod.post({"summary": "cw only"}) == "[cw: cw only]"
    assert (
        mod.post({"attachment": [{"mediaType": "image/png", "name": "alt"}]})
        == "[image: alt]"
    )
    assert mod.post({"content": "<p>a</p>", "attachment": 5}) == "a"


def test_json_that_is_not_an_outbox_is_not_a_result_and_bad_json_is_an_error():
    for other in (
        b"[]",
        b"{}",
        b'{"orderedItems":{}}',
        b'{"orderedItems":[]}',
        b'{"orderedItems":[{"type":"Announce"}]}',
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"{nope")
    except ValueError:
        pass
    else:
        raise AssertionError("bad json")


def test_a_json_file_that_is_no_outbox_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"a.json": SAMPLE, "b.json": b'{"other": 1}'})
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"archive/outbox.json": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "archive/outbox.json.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "archive/outbox.json": SAMPLE,
            ".hid/archive/outbox.json": SAMPLE,
            ".archive/outbox.json": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["archive/outbox.json.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"archive/outbox.json": SAMPLE})
    before = (tmp_path / "src" / "archive/outbox.json").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "archive/outbox.json.txt").read_bytes() == (
        out / "archive/outbox.json.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "archive/outbox.json").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(tmp_path, {"good.json": SAMPLE, "bad.json": b"{not json"})
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
        assert got.returncode == 2 and "mastodon.py" in got.stderr
