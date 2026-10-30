"""matrix: an Element room export as dated lines of messages; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "matrix.py"
spec = importlib.util.spec_from_file_location("matrix", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'{"room_name":"Garden Club","topic":"Plants","messages":['
    b'{"type":"m.room.message","sender":"@ben:example.org","origin_server_ts":1709367360000,"content":{"msgtype":"m.emote","body":"waves"}},'
    b'{"type":"m.room.message","sender":"@ana:example.org","origin_server_ts":1709367300000,"content":{"msgtype":"m.text","body":"Six  hours of sun."}},'
    b'{"type":"m.room.member","sender":"@ben:example.org","origin_server_ts":1709367000000,"content":{"membership":"join"}},'
    b'{"type":"m.room.message","sender":"@ana:example.org","origin_server_ts":1709367400000,"content":{"msgtype":"m.image","body":"tomato.png"}},'
    b'{"type":"m.room.message","sender":"@ana:example.org","origin_server_ts":1709367500000,"content":{"msgtype":"m.text","body":""}}]}'
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


def test_messages_come_oldest_first_with_the_room_the_time_and_who_said_it():
    assert mod.convert(SAMPLE) == (
        "2024-03-02 08:15  Garden Club  @ana:example.org: Six hours of sun.\n"
        "2024-03-02 08:16  Garden Club  * @ben:example.org waves\n"
        "2024-03-02 08:16  Garden Club  @ana:example.org: [image] tomato.png\n"
    )


def test_a_room_with_no_name_is_named_by_its_topic_else_unnamed():
    msg = b'"messages":[{"type":"m.room.message","sender":"@a:b","origin_server_ts":0,"content":{"msgtype":"m.text","body":"hi"}}]'
    assert mod.convert(b'{"room_name":"","topic":"Plants",' + msg + b"}").startswith(
        "1970-01-01 00:00  Plants  "
    )
    assert mod.convert(b'{"room_name":null,' + msg + b"}").startswith(
        "1970-01-01 00:00  (unnamed room)  "
    )


def test_a_time_is_utc_to_the_minute_and_a_missing_one_is_left_out():
    assert (
        mod.when(1709367300000) == "2024-03-02 08:15"
        and mod.when(1709367300000.9) == "2024-03-02 08:15"
        and mod.when(0) == "1970-01-01 00:00"
    )
    assert (
        mod.when(None) == ""
        and mod.when("x") == ""
        and mod.when(True) == ""
        and mod.when(10**30) == ""
    )
    out = mod.convert(
        b'{"room_name":"R","messages":[{"type":"m.room.message","sender":"@a:b","content":{"msgtype":"m.text","body":"no time"}}]}'
    )
    assert out == "R  @a:b: no time\n"


def test_the_order_is_by_time_undated_first_and_the_same_minute_keeps_the_files_order():
    def one(who, ts):
        return (
            b'{"type":"m.room.message","sender":"%s","content":{"msgtype":"m.text","body":"x"}%s}'
            % (who, ts)
        )

    doc = (
        b'{"room_name":"R","messages":['
        + b",".join(
            [
                one(b"@z:b", b',"origin_server_ts":60000'),
                one(b"@a:b", b',"origin_server_ts":60000'),
                one(b"@m:b", b""),
            ]
        )
        + b"]}"
    )
    assert [x.split("  ")[-1] for x in mod.convert(doc).splitlines()] == [
        "@m:b: x",
        "@z:b: x",
        "@a:b: x",
    ]


def test_a_message_with_no_sender_and_other_message_kinds():
    assert (
        mod.line(
            {"type": "m.room.message", "content": {"msgtype": "m.text", "body": "x"}}
        )
        == "(unknown): x"
    )
    assert (
        mod.line(
            {
                "type": "m.room.message",
                "sender": "@a:b",
                "content": {"msgtype": "m.notice", "body": "n"},
            }
        )
        == "@a:b: n"
    )
    for kind in ("m.file", "m.video", "m.audio"):
        assert (
            mod.line(
                {
                    "type": "m.room.message",
                    "sender": "@a:b",
                    "content": {"msgtype": kind, "body": "f"},
                }
            )
            == f"@a:b: [{kind[2:]}] f"
        )
    assert (
        mod.line({"type": "m.reaction", "content": {"body": "x"}}) == ""
        and mod.line({"type": "m.room.message", "content": {}}) == ""
    )


def test_json_that_is_not_a_room_export_is_not_a_result_and_bad_json_is_an_error():
    for other in (
        b"[]",
        b"5",
        b"null",
        b"{}",
        b'{"room_name":"R"}',
        b'{"messages":[]}',
        b'{"room_name":"R","messages":{}}',
        b'{"room_name":"R","messages":[]}',
        b'{"room_name":"R","messages":[5]}',
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
    got, out = mirror_of(tmp_path, {"export/room.json": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "export/room.json.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "export/room.json": SAMPLE,
            ".hid/export/room.json": SAMPLE,
            ".export/room.json": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["export/room.json.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"export/room.json": SAMPLE})
    before = (tmp_path / "src" / "export/room.json").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "export/room.json.txt").read_bytes() == (
        out / "export/room.json.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "export/room.json").read_bytes() == before


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
        assert got.returncode == 2 and "matrix.py" in got.stderr
