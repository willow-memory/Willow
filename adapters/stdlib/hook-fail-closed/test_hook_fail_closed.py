"""hook-fail-closed: a hook that says yes is passed through; anything else
blocks, with the reason, including a hook that crashes or hangs."""

from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "hook_fail_closed.py"
PY = shlex.quote(sys.executable)


def hook(code: str) -> str:
    """A hook written in Python, as one command string."""
    return f"{PY} -c {shlex.quote(code)}"


def run(*argv: str, data: bytes = b"") -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv], input=data,
                          capture_output=True)  # fmt: skip


def test_a_hook_that_says_yes_is_passed_through_with_what_it_read():
    echo = hook("import sys; sys.stdout.write('ok:' + sys.stdin.read())")
    got = run("--hook", echo, data=b"bees")
    assert (got.returncode, got.stdout, got.stderr) == (0, b"ok:bees", b"")


def test_a_hook_that_blocks_on_purpose_keeps_its_reason():
    no = hook("import sys; sys.stderr.write('no: rm -rf'); sys.exit(2)")
    got = run("--hook", no)
    assert (got.returncode, got.stdout, got.stderr) == (2, b"", b"no: rm -rf")


def test_a_hook_that_breaks_blocks_and_says_how():
    crash = hook("raise SystemExit(1)")
    got = run("--hook", crash)
    assert got.returncode == 2 and got.stdout == b""
    assert got.stderr.endswith(b"blocked: the hook broke, it exited 1\n")
    traceback = run("--hook", hook("1/0"))
    assert traceback.returncode == 2 and b"ZeroDivisionError" in traceback.stderr
    killed = run(
        "--hook", hook("import os, signal; os.kill(os.getpid(), signal.SIGKILL)")
    )
    assert killed.returncode == 2 and b"it was killed" in killed.stderr


def test_a_hook_that_hangs_or_wont_start_blocks():
    slow = run("--hook", hook("import time; time.sleep(5)"), "--timeout", "0.5")
    assert slow.returncode == 2 and b"ran past 0.5s" in slow.stderr
    gone = run("--hook", "/no/such/hook")
    assert gone.returncode == 2 and b"won't start" in gone.stderr


def test_json_a_hook_owes_is_held_to_json():
    words = hook("print('not json')")
    assert run("--hook", words).returncode == 0
    got = run("--hook", words, "--json")
    assert got.returncode == 2 and b"isn't JSON" in got.stderr and got.stdout == b""
    good = run("--hook", hook('print(\'{"decision": "allow"}\')'), "--json")
    assert good.returncode == 0 and good.stdout == b'{"decision": "allow"}\n'
    assert run("--hook", hook("pass"), "--json").returncode == 0  # empty is fine


def test_the_default_timeout_is_thirty_seconds():
    spec = __import__("importlib.util").util.spec_from_file_location("fc", SCRIPT)
    fc = __import__("importlib.util").util.module_from_spec(spec)
    spec.loader.exec_module(fc)
    assert fc.TIMEOUT == 30.0


def test_a_bad_command_line_is_refused():
    for argv in ([], ["--hook", ""], ["--hook", "x", "--timeout", "0"],
                 ["--hook", "x", "--timeout", "soon"], ["--hook", "'unclosed"],
                 ["--hook", "x", "--stray"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and b"hook_fail_closed.py" in got.stderr, argv
