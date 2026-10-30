"""discord: a Discord data package as dated lines of your messages; hidden files and folders skipped, an unreadable file skipped
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
SCRIPT = HERE / "discord.py"
spec = importlib.util.spec_from_file_location("discord", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def zipped(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, text in files.items():
            z.writestr(name, text)
    return buf.getvalue()


SAMPLE = zipped(
    {
        "Messages/index.json": '{"123": "Direct Message with ben", "456": "garden"}',
        "Messages/c123/channel.json": '{"id":"123","type":1}',
        "Messages/c123/messages.json": '[{"ID":"1","Timestamp":"2024-03-02 08:16:00","Contents":"See you  Saturday.","Attachments":""},{"ID":"2","Timestamp":"2024-03-02 08:20:00","Contents":"","Attachments":"https://cdn/x.png"},{"ID":"3","Timestamp":"2024-03-02 08:21:00","Contents":"","Attachments":""}]',
        "Messages/c456/channel.json": '{"id":"456","type":0,"name":"garden","guild":{"id":"9","name":"Garden Club"}}',
        "Messages/c456/messages.csv": 'ID,Timestamp,Contents,Attachments\n7,2024-03-02 08:15:30,"Six hours of sun.",\n',
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


def test_messages_come_oldest_first_with_the_server_channel_and_attachments_said():
    assert mod.convert(SAMPLE) == (
        "2024-03-02 08:15  Garden Club #garden  Six hours of sun.\n"
        "2024-03-02 08:16  Direct Message with ben  See you Saturday.\n"
        "2024-03-02 08:20  Direct Message with ben  [attachment]\n"
    )


def test_a_channel_is_named_by_its_channel_json_else_the_index_else_its_id():
    n = mod.channel_name
    assert (
        n({"name": "garden", "guild": {"name": "Garden Club"}}, "x", "c1")
        == "Garden Club #garden"
    )
    assert (
        n({"name": "garden"}, "x", "c1") == "#garden"
        and n({"id": "1", "type": 1}, "Direct Message with ben", "c1")
        == "Direct Message with ben"
    )
    assert (
        n(None, "", "c42") == "channel 42"
        and n({}, "", "99") == "channel 99"
        and n(None, "listed", "c1") == "listed"
    )


def test_a_time_is_the_day_and_minute_as_given_and_a_missing_one_is_left_out():
    assert (
        mod.stamp("2024-03-02 08:15:30") == "2024-03-02 08:15"
        and mod.stamp("2024-03-02T08:15:30+00:00") == "2024-03-02 08:15"
        and mod.stamp("2024-03-02") == "2024-03-02"
    )
    assert mod.stamp(None) == "" and mod.stamp("soon") == "" and mod.stamp(5) == ""
    z = zipped({"messages/c1/messages.json": '[{"Contents":"no time"},5]'})
    assert mod.convert(z) == "channel 1  no time\n"


def test_the_order_is_by_time_and_the_same_minute_keeps_the_files_order():
    z = zipped(
        {
            "messages/c1/messages.json": '[{"Timestamp":"2024-03-02 08:00:30","Contents":"zed"},{"Timestamp":"2024-03-02 08:00:10","Contents":"alpha"},{"Contents":"undated"}]'
        }
    )
    assert mod.convert(z).splitlines() == [
        "channel 1  undated",
        "2024-03-02 08:00  channel 1  zed",
        "2024-03-02 08:00  channel 1  alpha",
    ]


def test_a_zip_of_more_members_than_the_limit_is_not_read():
    filler = {f"pad/{i}.txt": "" for i in range(mod.MEMBERS - 1)}
    ok = zipped(
        {
            "messages/c1/messages.json": '[{"Timestamp":"2024-03-02 08:00:00","Contents":"x"}]',
            **filler,
        }
    )
    assert mod.convert(ok) is not None
    over = zipped(
        {
            "messages/c1/messages.json": '[{"Timestamp":"2024-03-02 08:00:00","Contents":"x"}]',
            **filler,
            "pad/one-more.txt": "",
        }
    )
    assert mod.convert(over) is None


def test_a_zip_that_is_no_package_is_not_a_result_a_big_member_is_left_out_and_a_bad_zip_is_an_error():
    assert (
        mod.convert(zipped({"readme.txt": "hi"})) is None
        and mod.convert(zipped({})) is None
    )
    assert (
        mod.convert(zipped({"messages/c1/messages.json": "[]"})) is None
        and mod.convert(zipped({"messages/c1/messages.json": "{}"})) is None
    )
    big = (
        '[{"Timestamp":"2024-03-02 08:00:00","Contents":"'
        + "x" * (5 * 1024 * 1024)
        + '"}]'
    )
    assert mod.convert(zipped({"messages/c1/messages.json": big})) is None
    try:
        mod.convert(b"not a zip")
    except mod.zipfile.BadZipFile:
        pass
    else:
        raise AssertionError("bad zip")


def test_a_zip_that_is_no_package_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(
        tmp_path, {"discord.zip": SAMPLE, "other.zip": zipped({"readme.txt": "hi"})}
    )
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"package/discord.zip": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "package/discord.zip.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "package/discord.zip": SAMPLE,
            ".hid/package/discord.zip": SAMPLE,
            ".package/discord.zip": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["package/discord.zip.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"package/discord.zip": SAMPLE})
    before = (tmp_path / "src" / "package/discord.zip").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "package/discord.zip.txt").read_bytes() == (
        out / "package/discord.zip.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "package/discord.zip").read_bytes() == before


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
        assert got.returncode == 2 and "discord.py" in got.stderr
