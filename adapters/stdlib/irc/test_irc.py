"""irc: IRC logs from WeeChat, irssi or ZNC as dated lines of messages; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "irc.py"
spec = importlib.util.spec_from_file_location("irc", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b"2024-03-02 08:15:30\tana\tSix hours of sun, I read.\n2024-03-02 08:15:50\t--> \tben (~b@host) has joined #garden\n"
    b"2024-03-02 08:16:01\t *\tben waves\n2024-03-03 19:40:00\tben\tThe slugs are winning.\n"
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


def test_weechat_lines_are_dated_messages_with_the_channel_from_the_file_name():
    assert mod.convert(SAMPLE, "irc.libera.#garden.weechatlog") == (
        "2024-03-02 08:15  #garden  ana: Six hours of sun, I read.\n"
        "2024-03-02 08:16  #garden  * ben waves\n"
        "2024-03-03 19:40  #garden  ben: The slugs are winning.\n"
    )


def test_irssi_takes_its_dates_from_the_log_opened_and_day_changed_lines_and_keeps_actions():
    log = (
        b"--- Log opened Sat Mar 02 08:00:00 2024\n08:15 < ana> Six hours of sun.\n08:16 -!- ben [~b@host] has joined #garden\n"
        b"08:17  * ben waves\n--- Day changed Sun Mar 03 2024\n19:40 <@ben> The slugs are winning.\n--- Log closed Sun Mar 03 20:00:00 2024\n"
    )
    assert mod.convert(log, "#garden.log") == (
        "2024-03-02 08:15  #garden  ana: Six hours of sun.\n"
        "2024-03-02 08:17  #garden  * ben waves\n"
        "2024-03-03 19:40  #garden  @ben: The slugs are winning.\n"
    )


def test_znc_takes_its_date_from_the_file_name():
    log = b"[08:15:30] <ana> Six hours of sun.\n[08:16:00] *** Joins: ben (~b@host)\n[08:17:00] * ben waves\n[08:18:00] <ben> \n"
    assert mod.convert(log, "#garden_20240302.log") == (
        "2024-03-02 08:15  #garden  ana: Six hours of sun.\n2024-03-02 08:17  #garden  * ben waves\n"
    )
    assert mod.convert(log, "#garden.log") is None, "no date, no line"


def test_the_channel_is_read_from_the_file_name():
    c = mod.channel_of
    assert (
        c("irc.libera.#garden.weechatlog") == "#garden"
        and c("#garden.log") == "#garden"
        and c("#garden_20240302.log") == "#garden"
    )
    assert (
        c("irc.libera.#a.b.weechatlog") == "#a.b"
        and c("&local.log") == "&local"
        and c("server.log") == "server"
    )
    assert c("") == ""


def test_joins_parts_modes_and_blank_messages_are_left_out_and_other_logs_are_no_result():
    only = b"2024-03-02 08:15:30\t<--\tben has left #garden\n2024-03-02 08:15:30\t--\tMode #garden [+o ana]\n2024-03-02 08:16:00\tana\t \n"
    assert mod.convert(only, "x.weechatlog") is None
    for other in (
        b"",
        b"Mar  2 08:15:30 host sshd[1]: accepted\n",
        b"just some text\n",
    ):
        assert mod.convert(other, "syslog.log") is None, other


def test_a_log_that_is_not_irc_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "irc.libera.#garden.weechatlog": SAMPLE,
            "syslog.log": b"Mar  2 08:15:30 host sshd[1]: accepted\n",
        },
    )
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"logs/irc.libera.#garden.weechatlog": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "logs/irc.libera.#garden.weechatlog.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "logs/irc.libera.#garden.weechatlog": SAMPLE,
            ".hid/logs/irc.libera.#garden.weechatlog": SAMPLE,
            ".logs/irc.libera.#garden.weechatlog": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["logs/irc.libera.#garden.weechatlog.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"logs/irc.libera.#garden.weechatlog": SAMPLE})
    before = (tmp_path / "src" / "logs/irc.libera.#garden.weechatlog").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "logs/irc.libera.#garden.weechatlog.txt").read_bytes() == (
        out / "logs/irc.libera.#garden.weechatlog.txt"
    ).read_bytes()
    assert (
        tmp_path / "src" / "logs/irc.libera.#garden.weechatlog"
    ).read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path, {"good.log": SAMPLE, "bad.log": b"\xff\xfe\x00 not a log"}
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.log.txt").is_file() and not (out / "bad.log.txt").exists()


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
        assert got.returncode == 2 and "irc.py" in got.stderr
