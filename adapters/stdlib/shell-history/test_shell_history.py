"""shell-history: a history is known by its file's name, each command mirrors
as one line with the time its shell recorded it in UTC, a day is one
paragraph, and a command with no time is never given one."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "shell_history", HERE / "shell_history.py"
)
sh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sh)

BASH = (
    b"cd before-any-stamp\n"
    b"#1709460900\n"
    b"git push\n"
    b"#1709461000\n"
    b"for f in *; do\n"
    b"\n"
    b"  echo $f\n"
    b"done\n"
    b"#1709560000\n"
    b"ls\n"
)
ZSH = (
    b": 1709460900:0;git push\n"
    b": 1709460950:3;echo one\\\n"
    b"two\n"
    b"plain line\n"
    b": 1709460960:0;\n"
)
FISH = (
    b"- cmd: echo a\\\\nb\\nc\n"
    b"  when: 1709460900\n"
    b"  paths:\n"
    b"    - when: 1\n"
    b"- cmd: ls\n"
    b"- cmd: pwd\n"
    b"  when: 1709560000\n"
    b"  when: 1\n"
)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "shell_history.py"), *argv],
        capture_output=True,
        text=True,
    )


def test_the_shell_is_known_by_the_name_alone():
    assert sh.shell_of("bash_history") == "bash"
    assert sh.shell_of("Bash_History.old") == "bash"
    assert sh.shell_of("zsh_history") == "zsh"
    assert sh.shell_of("histfile") == "zsh"
    assert sh.shell_of("fish_history") == "fish"
    assert sh.shell_of("history") is None
    assert sh.shell_of("my_bash_history") is None


def test_bash_stamps_date_the_lines_under_them_and_a_day_is_a_paragraph():
    assert sh.history_text(BASH, "bash") == (
        "cd before-any-stamp\n"
        "\n"
        "2024-03-03 10:15:00 UTC  git push\n"
        "2024-03-03 10:16:40 UTC  for f in *; do\n"
        "  echo $f\n"
        "done\n"
        "\n"
        "2024-03-04 13:46:40 UTC  ls\n"
        "\n"
    )


def test_bash_with_no_stamps_is_one_undated_command_a_line():
    assert sh.bash("ls\n\n  \ngit status\n") == [(None, "ls"), (None, "git status")]
    assert sh.history_text(b"ls\ngit status\n", "bash") == "ls\ngit status\n\n"
    assert sh.bash("#comment\nls\n") == [(None, "#comment"), (None, "ls")]


def test_zsh_extended_lines_go_on_past_a_backslash_and_plain_ones_are_bare():
    assert sh.zsh(ZSH.decode()) == [
        (1709460900, "git push"),
        (1709460950, "echo one\ntwo"),
        (None, "plain line"),
    ]
    assert sh.zsh(": 1:0;last\\") == [(1, "last\\")], "nothing after: kept"
    assert sh.zsh(":  1709460900:0;spaced") == [(1709460900, "spaced")]
    assert sh.history_text(ZSH, "zsh") == (
        "2024-03-03 10:15:00 UTC  git push\n"
        "2024-03-03 10:15:50 UTC  echo one\n"
        "two\n"
        "\n"
        "plain line\n"
        "\n"
    )


def test_zsh_bytes_are_unmetafied_before_they_are_read():
    assert sh.unmetafy(b"plain") == b"plain"
    assert sh.unmetafy(bytes([0x61, 0x83, 0xA3 ^ 32, 0x62])) == bytes(
        [0x61, 0xA3, 0x62]
    )
    assert sh.unmetafy(bytes([0x83, 0x83 ^ 32, 0x83 ^ 32])) == bytes([0x83, 0xA3])
    assert sh.unmetafy(b"end\x83") == b"end\x83", "a META with nothing after stays"
    pound = ": 1709460900:0;echo \xa3".encode()  # £ is c2 a3; a3 is zsh's own
    meta = pound.replace(b"\xa3", bytes([0x83, 0xA3 ^ 32]))
    assert sh.history_text(meta, "zsh") == "2024-03-03 10:15:00 UTC  echo £\n\n"
    assert sh.history_text(meta, "bash") != sh.history_text(meta, "zsh")


def test_fish_commands_take_their_own_when_and_are_unescaped():
    assert sh.fish(FISH.decode()) == [
        (1709460900, "echo a\\nb\nc"),
        (None, "ls"),
        (1709560000, "pwd"),
    ]
    assert sh.fish("  when: 5\n- cmd:\n- cmd: x\\y\\\n") == [(None, "x\\y\\")]
    assert sh.history_text(FISH, "fish") == (
        "2024-03-03 10:15:00 UTC  echo a\\nb\n"
        "c\n"
        "\n"
        "ls\n"
        "\n"
        "2024-03-04 13:46:40 UTC  pwd\n"
        "\n"
    )


def test_a_time_past_any_calendar_is_no_time_and_empty_is_none():
    assert sh._stamp(None) == ""
    assert sh._stamp(0) == "1970-01-01 00:00:00 UTC"
    assert sh._stamp(10**20) == ""
    assert sh.history_text(b": 99999999999999999999:0;ls\n", "zsh") == "ls\n\n"
    assert sh.history_text(b"", "bash") is None
    assert sh.history_text(b"\n  \n", "zsh") is None
    assert sh.history_text(b"#1709460900\n", "bash") is None
    assert sh.history_text(b"\xef\xbb\xbfls\n", "bash") == "ls\n\n", "BOM off"
    assert sh.history_text(b"ls \xff\n", "bash") == "ls �\n\n"


def test_mirror_writes_histories_skips_the_rest_and_never_touches_from(tmp_path):
    src = tmp_path / "from"
    (src / "laptop").mkdir(parents=True)
    (src / "laptop" / "bash_history").write_bytes(BASH)
    (src / "zsh_history").write_bytes(ZSH)
    (src / "fish_history").write_bytes(b"")
    (src / "notes.txt").write_text("not a history\n")
    (src / ".bash_history").write_bytes(BASH)
    before = {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}
    dst = tmp_path / "mirror"
    got = run("mirror", "--from", str(src), "--to", str(dst))
    assert got.returncode == 0
    assert got.stdout.strip() == f"wrote 2 files to {dst}; skipped 1"
    assert sorted(p for p in dst.rglob("*") if p.is_file()) == [
        dst / "laptop" / "bash_history.txt",
        dst / "zsh_history.txt",
    ]
    assert (dst / "zsh_history.txt").read_text() == sh.history_text(ZSH, "zsh")
    assert before == {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}


def test_the_kernel_dates_a_mirrored_history():
    sys.path.insert(0, str(HERE.parents[2]))
    import kernel

    assert kernel.newest(sh.history_text(BASH, "bash")) == "20240304"


def test_nothing_readable_is_42_and_bad_places_are_refused(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    got = run("mirror", "--from", str(empty), "--to", str(tmp_path / "m"))
    assert got.returncode == 42 and "wrote 0 files" in got.stdout
    got = run()
    assert got.returncode == 2 and "shell_history.py" in got.stderr
    got = run("mirror", "--from", str(empty), "--too", str(tmp_path / "m"))
    assert got.returncode == 2 and "usage" in got.stderr
    got = run("mirror", "--from", str(tmp_path / "gone"), "--to", str(tmp_path / "m2"))
    assert got.returncode == 2 and got.stderr.startswith("refused")
    got = run("mirror", "--from", str(empty), "--to", str(empty / "inside"))
    assert got.returncode == 2 and "inside one another" in got.stderr
    got = run("mirror", "--from", str(empty / "x" / ".."), "--to", str(tmp_path))
    assert got.returncode == 2
