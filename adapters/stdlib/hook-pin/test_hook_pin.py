"""hook-pin: a hook's bytes approved on the record, checked, and the gate
that runs it only while they still match."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "hook_pin.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T09:00:00Z"]


def make(tmp_path: Path) -> tuple[Path, Path]:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.txt").write_text("x\n")
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), *NOW], check=True, capture_output=True)  # fmt: skip
    hook = tmp_path / "hook.py"
    hook.write_text("import sys\nsys.stdout.write('saw:' + sys.stdin.read())\n")
    return b, hook


def run(*argv: str, data: str = "") -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv], input=data,
                          capture_output=True, text=True)  # fmt: skip


def gate(b: Path, hook: Path, data: str = "bees") -> subprocess.CompletedProcess:
    cmd = f"{shlex.quote(sys.executable)} {shlex.quote(str(hook))}"
    return run("--box", str(b), "run", "--file", str(hook), "--hook", cmd, data=data)


def test_an_approved_hook_is_pinned_and_runs(tmp_path):
    b, hook = make(tmp_path)
    got = run("--box", str(b), "approve", str(hook), *NOW)
    assert got.returncode == 0 and got.stdout == f"pinned        {hook} (row 1)\n"
    row = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    assert (row["kind"], row["who"], row["path"]) == (
        "hook-pin",
        "hook-pin",
        str(hook.resolve()),
    )
    assert len(row["sha256"]) == 64 and row["ts"] == NOW[1]
    assert (
        run("--box", str(b), "check", str(hook)).stdout
        == f"pinned        {hook} (row 1)\n"
    )
    ran = gate(b, hook)
    assert (ran.returncode, ran.stdout) == (0, "saw:bees")


def test_a_changed_hook_is_named_and_blocked(tmp_path):
    b, hook = make(tmp_path)
    run("--box", str(b), "approve", str(hook), *NOW)
    hook.write_text("import sys\nsys.stdout.write('changed')\n")
    got = run("--box", str(b), "check", str(hook))
    assert (
        got.returncode == 42
        and got.stdout == f"changed       {hook} (pinned at row 1)\n"
    )
    ran = gate(b, hook)
    assert ran.returncode == 2 and ran.stdout == ""
    assert ran.stderr == f"blocked: changed       {hook} (pinned at row 1)\n"
    run("--box", str(b), "approve", str(hook), *NOW)  # approved again: a new row
    assert gate(b, hook).stdout == "changed"
    assert len((b / "record.jsonl").read_text().splitlines()) == 3


def test_a_hook_never_pinned_is_named_and_blocked(tmp_path):
    b, hook = make(tmp_path)
    other = tmp_path / "other.py"
    other.write_text("pass\n")
    run("--box", str(b), "approve", str(other), *NOW)
    got = run("--box", str(b), "check", str(other), str(hook))
    assert got.returncode == 42
    assert got.stdout.splitlines() == [f"pinned        {other} (row 1)",
                                       f"never pinned  {hook}"]  # fmt: skip
    ran = gate(b, hook)
    assert ran.returncode == 2 and ran.stderr == f"blocked: never pinned  {hook}\n"


def test_the_hooks_own_exit_and_errors_pass_through(tmp_path):
    b, hook = make(tmp_path)
    hook.write_text("import sys\nsys.stderr.write('no')\nsys.exit(2)\n")
    run("--box", str(b), "approve", str(hook), *NOW)
    ran = gate(b, hook)
    assert (ran.returncode, ran.stderr) == (2, "no")
    missing = run(
        "--box", str(b), "run", "--file", str(hook), "--hook", "/no/such/hook"
    )
    assert missing.returncode == 2
    assert (
        missing.stderr == "blocked: the hook won't start: No such file or directory\n"
    )
    gone = run(
        "--box", str(b), "run", "--file", str(tmp_path / "gone.py"), "--hook", "x"
    )
    assert gone.returncode == 2 and gone.stderr.startswith("blocked: not a file")


def test_it_refuses_what_it_cant_hold(tmp_path):
    b, hook = make(tmp_path)
    got = run("--box", str(b), "approve", str(tmp_path / "nope.py"))
    assert got.returncode == 2 and "not a file" in got.stderr
    assert run("--box", str(tmp_path), "check", str(hook)).returncode == 2
    lines = (b / "record.jsonl").read_text().splitlines()
    (b / "record.jsonl").write_text(lines[0].replace("boot", "bootx") + "\n")
    broken = run("--box", str(b), "check", str(hook))
    assert broken.returncode == 2 and "doesn't verify" in broken.stderr


def test_a_bad_command_line_is_refused(tmp_path):
    b, hook = make(tmp_path)
    for argv in ([], ["--box", str(b)], ["--box", str(b), "approve"],
                 ["--box", str(b), "check"], ["--box", str(b), "run", "--hook", "x"],
                 ["--box", str(b), "run", "--file", str(hook)],
                 ["--box", str(b), "approve", str(hook), "--hook", "x"],
                 ["--box", str(b), "check", str(hook), "--stray", "more"],
                 ["--box", str(b), "run", "--file", str(hook), "--hook", "'unclosed"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "hook_pin.py" in got.stderr, argv
