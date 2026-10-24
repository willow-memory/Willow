"""hook-fuzz: a fixed list of bad inputs, and each one that breaks a hook
named, by exit code, crash, timeout or traceback."""

from __future__ import annotations

import importlib.util
import json
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "hook_fuzz.py"
PY = shlex.quote(sys.executable)
spec = importlib.util.spec_from_file_location("hook_fuzz", SCRIPT)
hf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hf)


def hook(code: str) -> str:
    return f"{PY} -c {shlex.quote(code)}"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True,
                          text=True)  # fmt: skip


#: a careful hook: reads its input as bytes, and says no to anything odd
CAREFUL = hook(
    "import json, sys\n"
    "try:\n"
    "    d = json.loads(sys.stdin.buffer.read() or b'{}')\n"
    "except (ValueError, RecursionError):\n"
    "    sys.exit(2)\n"
    "sys.exit(0 if isinstance(d, dict) else 2)\n"
)


def test_a_careful_hook_holds_on_every_input():
    got = run("--hook", CAREFUL)
    assert got.returncode == 0, got.stdout
    assert got.stdout == f"{len(hf.CASES)} of {len(hf.CASES)} inputs held\n"


def test_a_careless_hook_is_named_on_each_input_that_breaks_it():
    careless = hook("import json, sys; json.load(sys.stdin)['prompt']")
    got = run("--hook", careless)
    assert got.returncode == 42
    lines = got.stdout.splitlines()
    broke = {line.split()[1] for line in lines[:-1]}
    assert {"empty", "null", "list", "number", "truncated", "deep"} <= broke
    assert "wrong-type" not in broke and "huge" not in broke
    assert all("with a traceback" in line for line in lines[:-1])
    assert lines[-1] == f"{len(hf.CASES) - len(broke)} of {len(hf.CASES)} inputs held"


def test_an_exit_code_a_crash_and_a_hang_each_break():
    assert hf.verdict(shlex.split(hook("raise SystemExit(1)")), b"", 5) == "exited 1"
    assert hf.verdict(shlex.split(hook("import os,signal; os.kill(os.getpid(), signal.SIGKILL)")),
                      b"", 5) == "was killed"  # fmt: skip
    assert (
        hf.verdict(shlex.split(hook("import time; time.sleep(5)")), b"", 0.5)
        == "ran past 0.5s"
    )
    assert hf.verdict(["/no/such/hook"], b"", 5).startswith("won't start")
    assert hf.verdict(shlex.split(hook("raise SystemExit(2)")), b"", 5) == ""


def test_a_traceback_under_exit_zero_still_breaks():
    lucky = hook(
        "import sys, traceback\ntry:\n    1/0\nexcept Exception:\n    traceback.print_exc()\n"
    )
    got = hf.verdict(shlex.split(lucky), b"", 5)
    assert got == "exited 0 with a traceback: ZeroDivisionError: division by zero"


def test_the_inputs_are_fixed_and_what_they_say():
    names = [n for n, _ in hf.CASES]
    assert names == ["empty", "blank", "null", "list", "number", "object", "truncated",
                     "wrong-type", "huge", "not-utf8", "nul", "surrogate", "deep"]  # fmt: skip
    data = dict(hf.CASES)
    assert data["empty"] == b"" and len(data["huge"]) > 1_000_000
    assert data["deep"].count(b"[") == 10_000
    assert json.loads(data["wrong-type"])["prompt"] == 5
    assert hf.TIMEOUT == 10.0


def test_a_timeout_under_a_second_is_a_timeout():
    got = run("--hook", hook("import time; time.sleep(5)"), "--timeout", "0.5")
    assert got.returncode == 42 and "ran past 0.5s" in got.stdout


def test_a_bad_command_line_is_refused():
    for argv in ([], ["--hook", ""], ["--hook", "x", "--timeout", "0"],
                 ["--hook", "x", "--timeout", "soon"], ["--hook", "x", "--stray"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "hook_fuzz.py" in got.stderr, argv
