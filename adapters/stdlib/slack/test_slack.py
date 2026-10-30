"""slack: a Slack export zip as dated lines of messages; hidden files and folders skipped, an unreadable file skipped
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
SCRIPT = HERE / "slack.py"
spec = importlib.util.spec_from_file_location("slack", SCRIPT)
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
        "users.json": '[{"id":"U1","name":"ana","real_name":"Ana Lopez","profile":{"display_name":"ana"}},{"id":"U2","name":"ben","real_name":"Ben Ruiz","profile":{"display_name":""}}]',
        "channels.json": '[{"id":"C1","name":"garden"}]',
        "garden/2024-03-02.json": '[{"type":"message","user":"U1","text":"Six hours of sun, <@U2>? &amp; <#C1|garden>","ts":"1709367300.000100"},'
        '{"type":"message","user":"U2","text":"See <https://example.org/guide|the guide> <!here>","ts":"1709367360.000200"},'
        '{"type":"message","subtype":"channel_join","user":"U2","text":"<@U2> has joined","ts":"1709367000.000000"},'
        '{"type":"message","user":"U3","text":"","ts":"1709367400.0"}]',
        "garden/2024-03-03.json": '[{"type":"message","subtype":"me_message","user":"U1","text":"waves","ts":"1709460000.0"}]',
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


def test_messages_come_oldest_first_with_the_channel_and_the_authors_display_name():
    assert mod.convert(SAMPLE) == (
        "2024-03-02 08:15  #garden  ana: Six hours of sun, @Ben Ruiz? & #garden\n"
        "2024-03-02 08:16  #garden  Ben Ruiz: See the guide @here\n"
        "2024-03-03 10:00  #garden  ana: waves\n"
    )


def test_a_slack_token_is_read_as_the_words_it_stands_for():
    users = {"U1": "ana"}
    c = mod.clean
    assert (
        c("hi <@U1> and <@U9>", users) == "hi @ana and @U9"
        and c("<@U1|bob>", users) == "@bob"
    )
    assert (
        c("<#C1|garden> <#C2>", users) == "#garden #C2"
        and c("<!here> <!channel> <!subteam^S1|devs>", users) == "@here @channel @devs"
    )
    assert (
        c("<https://x.org> <https://x.org|label> <mailto:a@b.org|mail me>", users)
        == "https://x.org label mail me"
    )
    assert (
        c("a &lt;b&gt; &amp; c", users) == "a <b> & c"
        and c("  a \n b  ", users) == "a b"
        and c("", users) == ""
    )


def test_user_names_prefer_the_display_name_then_the_real_name_then_the_name():
    got = mod.names_of(
        [
            {
                "id": "U1",
                "name": "n1",
                "real_name": "Real One",
                "profile": {"display_name": "disp"},
            },
            {"id": "U2", "name": "n2", "real_name": "Real Two", "profile": {}},
            {"id": "U3", "name": "n3"},
            {"id": "U4"},
            {"name": "no id"},
            5,
        ]
    )
    assert got == {"U1": "disp", "U2": "Real Two", "U3": "n3"}
    assert mod.names_of(None) == {} and mod.names_of({}) == {}


def test_a_time_is_utc_to_the_minute_and_a_message_with_no_time_takes_its_files_day():
    assert (
        mod.when("1709367300.000100") == "2024-03-02 08:15"
        and mod.when(1709367300) == "2024-03-02 08:15"
        and mod.when(None) == ""
        and mod.when("x") == ""
    )
    z = zipped(
        {
            "channels.json": "[]",
            "general/2024-05-06.json": '[{"user":"U1","text":"no time"}]',
        }
    )
    assert mod.convert(z) == "2024-05-06  #general  U1: no time\n"


def test_an_unknown_author_and_a_message_without_one_still_read():
    z = zipped(
        {
            "users.json": "[]",
            "c/2024-05-06.json": '[{"user":"U9","text":"x","ts":"60"},{"text":"y","ts":"120"}]',
        }
    )
    assert (
        mod.convert(z)
        == "1970-01-01 00:01  #c  U9: x\n1970-01-01 00:02  #c  (unknown): y\n"
    )


def test_the_order_is_by_time_and_the_same_minute_keeps_the_files_order():
    z = zipped(
        {
            "users.json": "[]",
            "c/2024-05-06.json": '[{"user":"Z","text":"x","ts":"60"},{"user":"A","text":"x","ts":"60"},{"user":"M","text":"x","ts":"0"}]',
        }
    )
    assert [x.split("  ")[-1] for x in mod.convert(z).splitlines()] == [
        "M: x",
        "Z: x",
        "A: x",
    ]


def test_a_zip_of_more_members_than_the_limit_is_not_read():
    filler = {f"pad/{i}.txt": "" for i in range(mod.MEMBERS - 2)}
    ok = zipped(
        {
            "users.json": "[]",
            "c/2024-05-06.json": '[{"user":"U","text":"x","ts":"60"}]',
            **filler,
        }
    )
    assert mod.convert(ok) is not None
    over = zipped(
        {
            "users.json": "[]",
            "c/2024-05-06.json": '[{"user":"U","text":"x","ts":"60"}]',
            **filler,
            "pad/one-more.txt": "",
        }
    )
    assert mod.convert(over) is None


def test_a_zip_that_is_no_slack_export_is_not_a_result_a_big_member_is_left_out_and_a_bad_zip_is_an_error():
    assert (
        mod.convert(zipped({"readme.txt": "hi"})) is None
        and mod.convert(zipped({})) is None
    )
    assert (
        mod.convert(zipped({"channels.json": "[]"})) is None
        and mod.convert(zipped({"users.json": "[]", "c/2024-05-06.json": "[]"})) is None
    )
    big = "[" + '{"user":"U","text":"' + "x" * (5 * 1024 * 1024) + '","ts":"1"}' + "]"
    assert mod.convert(zipped({"users.json": "[]", "c/2024-05-06.json": big})) is None
    try:
        mod.convert(b"not a zip")
    except mod.zipfile.BadZipFile:
        pass
    else:
        raise AssertionError("bad zip")


def test_a_zip_that_is_no_export_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(
        tmp_path, {"slack.zip": SAMPLE, "other.zip": zipped({"readme.txt": "hi"})}
    )
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"export/slack.zip": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "export/slack.zip.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "export/slack.zip": SAMPLE,
            ".hid/export/slack.zip": SAMPLE,
            ".export/slack.zip": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["export/slack.zip.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"export/slack.zip": SAMPLE})
    before = (tmp_path / "src" / "export/slack.zip").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "export/slack.zip.txt").read_bytes() == (
        out / "export/slack.zip.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "export/slack.zip").read_bytes() == before


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
        assert got.returncode == 2 and "slack.py" in got.stderr
