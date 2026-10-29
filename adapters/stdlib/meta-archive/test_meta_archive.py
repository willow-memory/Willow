"""meta-archive: a Facebook or Instagram export's messages, posts and comments as dated lines; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "meta_archive.py"
spec = importlib.util.spec_from_file_location("meta_archive", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'{"participants":[{"name":"Ana"},{"name":"Ben"}],"title":"Garden chat","messages":['
    b'{"sender_name":"Ben","timestamp_ms":1709370000000,"content":"Caf\xc3\x83\xc2\xa9 later?"},'
    b'{"sender_name":"Ana","timestamp_ms":1709367300000,"content":"Six  hours of sun."},{"sender_name":"Ana","timestamp_ms":1709367400000,"photos":[{}]}]}'
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


def test_messages_come_oldest_first_with_the_conversation_and_sender_and_the_garbling_undone():
    assert mod.convert(SAMPLE) == (
        "2024-03-02 08:15  Garden chat (Ana, Ben)  Ana: Six hours of sun.\n"
        "2024-03-02 09:00  Garden chat (Ana, Ben)  Ben: Café later?\n"
    )


def test_a_conversation_with_no_title_is_named_by_its_participants_and_a_sender_may_be_missing():
    doc = b'{"participants":[{"name":"Ana"},{"name":"Ben"}],"messages":[{"timestamp_ms":0,"content":"hi"}]}'
    assert mod.convert(doc) == "1970-01-01 00:00  Ana, Ben  (unknown): hi\n"
    alone = b'{"participants":[],"messages":[{"timestamp_ms":0,"sender_name":"A","content":"hi"}]}'
    assert mod.convert(alone) == "1970-01-01 00:00  A: hi\n"


def test_posts_and_comments_are_dated_lines():
    posts = b'[{"timestamp":1709370000,"data":[{"post":"Planted out the tomatoes."},{"other":1}]},{"timestamp":1709367300,"data":[{"post":"Earlier."}]},{"timestamp":5,"data":[]}]'
    assert (
        mod.convert(posts)
        == "2024-03-02 08:15  post: Earlier.\n2024-03-02 09:00  post: Planted out the tomatoes.\n"
    )
    comments = b'{"comments_v2":[{"timestamp":1709370000,"data":[{"comment":{"comment":"The slugs are winning."}}]}],"other":[1]}'
    assert (
        mod.convert(comments) == "2024-03-02 09:00  comment: The slugs are winning.\n"
    )
    assert (
        mod.convert(
            b'{"comments":[{"timestamp":0,"data":[{"comment":{"comment":"x"}}]}]}'
        )
        == "1970-01-01 00:00  comment: x\n"
    )


def test_garbled_text_is_put_right_only_when_it_can_be():
    assert (
        mod.fix("CafÃ©") == "Café"
        and mod.fix("plain") == "plain"
        and mod.fix("Café") == "Café"
    )
    assert (
        mod.fix("â\u0080\u0099") == "’"
        and mod.fix("a \n b") == "a b"
        and mod.fix(None) == ""
        and mod.fix(5) == ""
    )


def test_a_time_is_utc_to_the_minute_in_seconds_or_milliseconds_and_a_bad_one_is_left_out():
    assert (
        mod.when(1709367300) == "2024-03-02 08:15"
        and mod.when(1709367300000, ms=True) == "2024-03-02 08:15"
    )
    assert (
        mod.when(None) == ""
        and mod.when("x") == ""
        and mod.when(True) == ""
        and mod.when(10**30) == ""
    )
    assert (
        mod.convert(b'[{"timestamp":"x","data":[{"post":"no time"}]}]')
        == "post: no time\n"
    )


def test_the_order_is_by_time_undated_first_and_the_same_minute_keeps_the_files_order():
    doc = (
        b'{"participants":[{"name":"A"}],"title":"T","messages":[{"sender_name":"Z","timestamp_ms":60000,"content":"x"},'
        b'{"sender_name":"A","timestamp_ms":60000,"content":"x"},{"sender_name":"M","content":"x"}]}'
    )
    assert [x.split("  ")[-1] for x in mod.convert(doc).splitlines()] == [
        "M: x",
        "Z: x",
        "A: x",
    ]


def test_json_that_is_not_an_export_is_not_a_result_and_bad_json_is_an_error():
    for other in (
        b"{}",
        b"[]",
        b"5",
        b"null",
        b'{"messages":[]}',
        b'{"participants":[],"messages":[]}',
        b'[{"other":1}]',
        b'{"comments":{}}',
        b'{"x":[1]}',
        b'{"participants":[],"messages":[{"content":""},5]}',
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"{nope")
    except ValueError:
        pass
    else:
        raise AssertionError("bad json")


def test_a_json_file_that_is_no_export_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"a.json": SAMPLE, "b.json": b'{"other": 1}'})
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"messages/inbox/chat/message_1.json": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "messages/inbox/chat/message_1.json.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "messages/inbox/chat/message_1.json": SAMPLE,
            ".hid/messages/inbox/chat/message_1.json": SAMPLE,
            ".messages/inbox/chat/message_1.json": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["messages/inbox/chat/message_1.json.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"messages/inbox/chat/message_1.json": SAMPLE})
    before = (tmp_path / "src" / "messages/inbox/chat/message_1.json").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "messages/inbox/chat/message_1.json.txt").read_bytes() == (
        out / "messages/inbox/chat/message_1.json.txt"
    ).read_bytes()
    assert (
        tmp_path / "src" / "messages/inbox/chat/message_1.json"
    ).read_bytes() == before


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
        assert got.returncode == 2 and "meta_archive.py" in got.stderr
