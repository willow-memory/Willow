"""logs: a system or web server log as dated lines; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "logs.py"
spec = importlib.util.spec_from_file_location("logs", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b"Mar  2 08:15:30 host sshd[1234]: Accepted publickey for ana from 10.0.0.2\nMar  2 08:16:01 host cron: (root) CMD (run-parts /etc/cron.hourly)\n"
    b"    at stack frame\n2024-03-02T08:17:00.123456+00:00 host app[7]: started\n"
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


def test_syslog_lines_keep_their_month_and_day_and_lose_their_process_ids():
    assert mod.convert(SAMPLE) == (
        "Mar 02 08:15  host sshd: Accepted publickey for ana from 10.0.0.2\n"
        "Mar 02 08:16  host cron: (root) CMD (run-parts /etc/cron.hourly)\n"
        "2024-03-02 08:17  host app: started\n"
    )


def test_an_iso_timestamp_line_and_an_access_log_line():
    e = mod.entry
    assert (
        e("2024-03-02T08:15:30Z host app[7]: started")
        == "2024-03-02 08:15  host app: started"
    )
    assert (
        e("2024-03-02 08:15:30 host app: started")
        == "2024-03-02 08:15  host app: started"
    )
    assert e("2024-03-02T08:15:30-05:00 host app: x") == "2024-03-02 08:15  host app: x"
    line = '192.0.2.7 - - [02/Mar/2024:08:17:05 +0000] "GET /garden HTTP/1.1" 200 1234 "-" "curl/8"'
    assert e(line) == "2024-03-02 08:17  192.0.2.7 GET /garden 200 1234"
    assert (
        e('192.0.2.7 - bob [02/Mar/2024:08:17:05 +0000] "-" 408 0')
        == "2024-03-02 08:17  192.0.2.7 - 408 0"
    )


def test_a_line_that_is_not_an_entry_is_empty():
    for line in (
        "",
        "    at stack frame",
        "Traceback (most recent call last):",
        "Foo  2 08:15:30 host sshd: x",
        "random text: with colon",
    ):
        assert mod.entry(line) == "", line


def test_a_syslog_line_with_no_message_has_no_trailing_colon_and_the_day_is_padded():
    assert mod.entry("Mar  2 08:15:30 host cron:") == "Mar 02 08:15  host cron"
    assert mod.entry("Mar 12 08:15:30 host cron: x") == "Mar 12 08:15  host cron: x"


def test_journalds_export_format_is_read_by_its_blocks():
    export = (
        b"__CURSOR=s=1\n__REALTIME_TIMESTAMP=1709367330123456\n_HOSTNAME=host\nSYSLOG_IDENTIFIER=sshd\nMESSAGE=Accepted publickey for ana\n\n"
        b"__REALTIME_TIMESTAMP=1709367400000000\nMESSAGE=no identifier\n\n__REALTIME_TIMESTAMP=oops\nMESSAGE=bad time\n\n__REALTIME_TIMESTAMP=1709367500000000\nMESSAGE=\n"
    )
    assert (
        mod.convert(export)
        == "2024-03-02 08:15  host sshd: Accepted publickey for ana\n2024-03-02 08:16  no identifier\n"
    )


def test_most_of_the_first_twenty_lines_must_be_entries_and_other_text_is_not_a_result():
    mixed = b"Mar  2 08:15:30 host a: x\n" + b"plain line\n" * 3
    assert mod.convert(mixed) is None
    half = b"Mar  2 08:15:30 host a: x\nplain line\n"
    assert mod.convert(half) == "Mar 02 08:15  host a: x\n"
    for other in (
        b"",
        b"just some text\nwith lines\n",
        b"\n\n",
        b"2024-03-02 08:15:30 no host or process\n",
    ):
        assert mod.convert(other) is None, other


def test_a_log_over_the_limit_is_an_error_not_a_crash():
    try:
        mod.convert(b"x" * (mod.BIGGEST + 1))
    except ValueError:
        pass
    else:
        raise AssertionError("too big")


def test_a_log_of_something_else_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"syslog.log": SAMPLE, "other.log": b"just text\n"})
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"var/log/syslog.log": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "var/log/syslog.log.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def _journal(n: int) -> bytes:
    """`n` entries of journald's export, each message about 200 characters."""
    block = (
        "__REALTIME_TIMESTAMP={t}\nSYSLOG_IDENTIFIER=steward\n_HOSTNAME=box\n"
        "MESSAGE=tick {i} " + "x" * 200 + "\n\n"
    )
    return "".join(
        block.format(t=1793426400000000 + i * 1000000, i=i) for i in range(n)
    ).encode()


def test_a_mirror_bigger_than_the_kernel_reads_is_cut_into_parts_it_can(tmp_path):
    """2026-10-31: one day of a steward's journal mirrored to 5.9 MB, and the
    kernel, which reads at most `kernel.MAX_FILE` from a file, left it all out."""
    got, out = mirror_of(tmp_path, {"steward.log": _journal(12000)})
    assert got.returncode == 0, got.stderr
    made = sorted(p.name for p in out.iterdir())
    assert made[0] == "steward.log.part2.txt" and "steward.log.txt" in made
    assert len(made) >= 3
    assert all((out / m).stat().st_size <= mod.kernel.MAX_FILE for m in made)
    text = "".join(
        (out / mod._part_name("steward.log", n)).read_text()
        for n in range(1, len(made) + 1)
    )
    assert text == mod.convert(_journal(12000))
    assert all((out / m).read_text().endswith("\n") for m in made)


def test_a_shorter_run_removes_the_parts_a_longer_one_left(tmp_path):
    got, out = mirror_of(tmp_path, {"steward.log": _journal(12000)})
    assert (out / "steward.log.part2.txt").is_file()
    (tmp_path / "src" / "steward.log").write_bytes(_journal(10))
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(out))
    assert sorted(p.name for p in out.iterdir()) == ["steward.log.txt"]


def test_a_line_longer_than_a_part_is_shortened_to_fit():
    got = mod.parts("a\n" + "é" * 40 + "\nb\n", limit=20)
    assert all(len(p.encode()) <= 20 for p in got)
    assert got[0] == "a\n" and got[-1].endswith("b\n") and got[1].endswith("\n")


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "var/log/syslog.log": SAMPLE,
            ".hid/var/log/syslog.log": SAMPLE,
            ".var/log/syslog.log": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["var/log/syslog.log.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"var/log/syslog.log": SAMPLE})
    before = (tmp_path / "src" / "var/log/syslog.log").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "var/log/syslog.log.txt").read_bytes() == (
        out / "var/log/syslog.log.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "var/log/syslog.log").read_bytes() == before


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
        assert got.returncode == 2 and "logs.py" in got.stderr
