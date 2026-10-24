"""hook-replay: each hook answer a row of hashes, its input kept by hash,
and check running every one again."""

from __future__ import annotations

import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "hook_replay.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T09:00:00Z"]


def make(tmp_path: Path) -> tuple[Path, Path, Path]:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.txt").write_text("x\n")
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), *NOW], check=True, capture_output=True)  # fmt: skip
    hook = tmp_path / "hook.py"
    hook.write_text("import sys\nd = sys.stdin.read()\nsys.stdout.write(d.upper())\n"
                    "sys.stderr.write('n=' + str(len(d)))\nsys.exit(2 if 'no' in d else 0)\n")  # fmt: skip
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    return b, hook, inputs


def run(*argv: str, data: str = "") -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv], input=data,
                          capture_output=True, text=True)  # fmt: skip


def record(b: Path, hook: Path, inputs: Path, data: str) -> subprocess.CompletedProcess:
    cmd = f"{shlex.quote(sys.executable)} {shlex.quote(str(hook))}"
    return run(
        "--box", str(b), "--to", str(inputs), "run", "--hook", cmd, *NOW, data=data
    )


def h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def test_run_passes_the_hook_through_and_writes_hashes_not_words(tmp_path):
    b, hook, inputs = make(tmp_path)
    got = record(b, hook, inputs, "bees")
    assert (got.returncode, got.stdout, got.stderr) == (0, "BEES", "n=4")
    row = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    assert (row["kind"], row["who"], row["input"]) == (
        "hook-replay",
        "hook-replay",
        h("bees"),
    )
    assert row["command"] == [sys.executable, str(hook)] and row["ts"] == NOW[1]
    assert row["said"] == {"output": h("BEES"), "errors": h("n=4"), "exit": 0}
    assert "bees" not in (b / "record.jsonl").read_text().lower().replace(
        str(hook).lower(), ""
    )
    assert (inputs / f"{h('bees')}.in").read_text() == "bees"
    no = record(b, hook, inputs, "no")
    assert (no.returncode, no.stdout) == (2, "NO")


def test_check_runs_every_answer_again(tmp_path):
    b, hook, inputs = make(tmp_path)
    for data in ("bees", "calm", "bees", "no"):
        record(b, hook, inputs, data)
    assert len(list(inputs.iterdir())) == 3  # bees kept once
    got = run("--box", str(b), "--from", str(inputs), "check")
    assert (got.returncode, got.stdout) == (0, "4 of 4 hook answers held\n")


def test_a_hook_that_answers_differently_is_named(tmp_path):
    b, hook, inputs = make(tmp_path)
    record(b, hook, inputs, "bees")
    record(b, hook, inputs, "calm")
    hook.write_text("import sys\nd = sys.stdin.read()\nsys.stdout.write(d.upper())\n"
                    "sys.stderr.write('n=' + str(len(d)))\nsys.exit(1 if d == 'calm' else 0)\n")  # fmt: skip
    got = run("--box", str(b), "--from", str(inputs), "check")
    assert got.returncode == 42
    assert got.stdout == "differs   row 2: its exit\n1 of 2 hook answers held\n"
    hook.write_text("import sys\nsys.stdout.write('?')\n")
    got = run("--box", str(b), "--from", str(inputs), "check")
    assert got.stdout.splitlines()[0] == "differs   row 1: its output and errors"


def test_an_input_not_kept_is_said_never_skipped(tmp_path):
    b, hook, inputs = make(tmp_path)
    record(b, hook, inputs, "bees")
    record(b, hook, inputs, "calm")
    (inputs / f"{h('bees')}.in").unlink()
    (inputs / f"{h('calm')}.in").write_text("tampered")
    got = run("--box", str(b), "--from", str(inputs), "check")
    assert got.returncode == 42
    assert got.stdout.splitlines() == [f"not kept  row 1: its input isn't in {inputs}",
                                       f"not kept  row 2: its input isn't in {inputs}",
                                       "0 of 2 hook answers held"]  # fmt: skip


def test_a_hook_that_wont_start_is_answered_and_recorded(tmp_path):
    b, _, inputs = make(tmp_path)
    got = run(
        "--box", str(b), "--to", str(inputs), "run", "--hook", "/no/such/hook", data="x"
    )
    assert got.returncode == 127 and "won't start" in got.stderr
    row = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    assert row["said"]["exit"] == 127


def test_it_refuses_what_it_cant_hold(tmp_path):
    b, hook, inputs = make(tmp_path)
    got = run("--box", str(b), "--to", str(tmp_path / "nope"), "run", "--hook", "x")
    assert got.returncode == 2 and "make it first" in got.stderr
    assert run("--box", str(tmp_path), "--from", str(inputs), "check").returncode == 2
    lines = (b / "record.jsonl").read_text().splitlines()
    (b / "record.jsonl").write_text(lines[0].replace("boot", "bootx") + "\n")
    broken = run("--box", str(b), "--from", str(inputs), "check")
    assert broken.returncode == 2 and "doesn't verify" in broken.stderr


def test_a_bad_command_line_is_refused(tmp_path):
    b, _, inputs = make(tmp_path)
    box, to, frm = ["--box", str(b)], ["--to", str(inputs)], ["--from", str(inputs)]
    for argv in ([], [*box, "run"], [*box, *to, "run"], [*box, "run", "--hook", "x"],
                 [*box, *frm, "run", "--hook", "x"], [*box, "check"],
                 [*box, *frm, *to, "check"], [*box, *frm, "check", "--hook", "x"],
                 [*box, *frm, "check", "--stray", "more"], [*to, "run", "--hook", "x"],
                 [*box, *to, "run", "--hook", "'unclosed"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "hook_replay.py" in got.stderr, argv
