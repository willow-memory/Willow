"""stack-row: each step that has ended goes on the record with its marks,
its exit and the hash of what it printed; a step not ended is left out;
asked twice it writes once; and no output or argument is on the row."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRIPT = HERE / "stack_row.py"
EXAMPLE = HERE / "example-run"
NOW = "2026-11-11T12:00:00Z"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
import kernel  # noqa: E402
import stack_row  # noqa: E402


def box_in(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "note.txt").write_text("a note\n")
    box = tmp_path / "box"
    got = subprocess.run(
        [sys.executable, str(ROOT / "kernel.py"), "init", "--box", str(box), "--pile", str(pile),
         "--key", str(tmp_path / "k.key")], capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return box


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, text=True)  # fmt: skip


def a_run(tmp_path: Path, log: str, files: dict[str, str]) -> Path:
    folder = tmp_path / "run"
    folder.mkdir(exist_ok=True)
    (folder / "00-stack.txt").write_text(log)
    for name, text in files.items():
        (folder / name).write_text(text)
    return folder


def rows_of(box: Path) -> list[dict]:
    rows, breaks = kernel.read(box / "record.jsonl")
    assert not breaks
    return rows


def test_each_ended_step_goes_on_the_record_and_one_not_ended_is_left_out(tmp_path):
    box = box_in(tmp_path)
    got = run("--box", str(box), "--run", str(EXAMPLE), "--now", NOW)
    assert got.returncode == 0, got.stderr
    assert (
        got.stdout == "put on the record: row 1, 2 steps (1 clean, 1 ended otherwise)\n"
    )
    row = rows_of(box)[-1]
    assert row["kind"] == "stack-row" and row["who"] == "stack-row" and row["ts"] == NOW
    assert row["steps"] == [
        {"n": 1, "addon": "todo", "mark": "3f9a2c1b", "fed": None, "exit": 0, "lines": 2,
         "sha256": hashlib.sha256((EXAMPLE / "01-todo.txt").read_bytes()).hexdigest()},
        {"n": 2, "addon": "scan", "mark": "a04e77d2", "fed": "1c0e44aa", "exit": 42, "lines": 3,
         "sha256": hashlib.sha256((EXAMPLE / "02-scan.txt").read_bytes()).hexdigest()},
    ]  # fmt: skip
    assert row["of"] == stack_row.of(row["steps"]) and len(row["of"]) == 64
    assert row["standing"] == "unattested", "a row a script wrote is never sealed"


def test_no_output_and_no_argument_is_on_the_row(tmp_path):
    box = box_in(tmp_path)
    log = "01 claim-check: started (aaaaaaaa)\n01 claim-check: exit 0, 1 line\n"
    folder = a_run(
        tmp_path,
        log,
        {"01-claim-check.txt": "all parts  secret-diary.md:3  a private thing\n"},
    )
    assert run("--box", str(box), "--run", str(folder)).returncode == 0
    line = (box / "record.jsonl").read_text().splitlines()[-1]
    for word in ("secret", "private", "diary", str(folder), "claim-check.txt"):
        assert word not in line, word
    assert set(json.loads(line)["steps"][0]) == {
        "n",
        "addon",
        "mark",
        "fed",
        "exit",
        "lines",
        "sha256",
    }


def test_asked_twice_it_writes_once_and_a_run_gone_on_with_gets_a_row(tmp_path):
    box = box_in(tmp_path)
    log = "01 todo: started (aaaaaaaa)\n01 todo: exit 0, 1 line\n02 scan: started (bbbbbbbb)\n"
    folder = a_run(tmp_path, log, {"01-todo.txt": "x\n"})
    assert "put on the record: row 1, 1 step (1 clean, 0 ended otherwise)" in run("--box", str(box), "--run", str(folder)).stdout  # fmt: skip
    again = run("--box", str(box), "--run", str(folder))
    assert again.returncode == 0 and again.stdout.startswith(
        "already on the record: row 1 holds this run"
    )
    assert len(rows_of(box)) == 2
    a_run(tmp_path, log + "02 scan: exit 0, 2 lines\n", {"02-scan.txt": "a\nb\n"})
    more = run("--box", str(box), "--run", str(folder))
    assert (
        more.stdout
        == "put on the record: row 2, 2 steps (2 clean, 0 ended otherwise)\n"
    )
    assert [r["kind"] for r in rows_of(box)] == ["boot", "stack-row", "stack-row"]
    (folder / "02-scan.txt").write_text("a\nchanged\n")
    assert run("--box", str(box), "--run", str(folder)).stdout.startswith(
        "put on the record: row 3"
    )
    assert run("--box", str(box), "--run", str(folder)).stdout.startswith(
        "already on the record: row 3"
    )


def test_the_log_is_read_as_stack_writes_it():
    def of_log(tmp, log, files=()):
        folder = tmp / "r"
        folder.mkdir()
        (folder / "00-stack.txt").write_text(log)
        for name in files:
            (folder / name).write_text("x\n")
        return stack_row.steps_of(folder)

    import tempfile

    with tempfile.TemporaryDirectory() as d:
        log = (
            "01 a: started (11111111)\n01 a: exit 0, 1 line\n"
            "resumed: 1 of 3 steps had finished\n01 a: kept from before\n"
            "02 b: not run: step 1 (a) kept nothing to hand on\n"
            "03 c: started (33333333, fed 44444444)\n03 c: exit 2, 1 line, exit 2, flagged\n"
            "03 c: started (55555555)\n"
            "04 d: started (66666666)\n04 d: exit 0, 12 lines, mass 9, populated\n"
            "done: 1 of 4 steps flagged\n"
        )
        steps = of_log(Path(d), log, ["01-a.txt", "04-d.txt"])
    assert [(s["n"], s["addon"], s["exit"], s["lines"]) for s in steps] == [
        (1, "a", 0, 1), (2, "b", None, 0), (4, "d", 0, 12)]  # fmt: skip
    assert (
        steps[0]["mark"] == "11111111"
        and steps[1]["mark"] is None
        and steps[1]["sha256"] is None
    )
    assert steps[2]["sha256"] == hashlib.sha256(b"x\n").hexdigest()
    assert 3 not in [s["n"] for s in steps], (
        "started again and not ended: half a step is not a step"
    )
    assert stack_row.said(steps) == "3 steps (2 clean, 0 ended otherwise, 1 not run)"


def test_a_run_with_no_step_ended_writes_nothing_and_ends_42(tmp_path):
    box = box_in(tmp_path)
    folder = a_run(tmp_path, "01 todo: started (aaaaaaaa)\n", {})
    got = run("--box", str(box), "--run", str(folder))
    assert got.returncode == 42 and "no step of this run has ended" in got.stdout
    assert len(rows_of(box)) == 1


def test_what_is_not_a_box_a_run_or_a_command_line_is_refused(tmp_path):
    box = box_in(tmp_path)
    empty = tmp_path / "empty"
    empty.mkdir()
    cases = [
        ([], "stack_row.py"),
        (["--box", str(box)], "stack_row.py"),
        (["--run", str(EXAMPLE)], "stack_row.py"),
        (["--box", str(box), "--run", str(EXAMPLE), "extra"], "stack_row.py"),
        (["--box", str(box), "--box", str(box), "--run", str(EXAMPLE)], "stack_row.py"),
        (["--box", str(empty), "--run", str(EXAMPLE)], "not a kernel box"),
        (["--box", str(box), "--run", str(empty)], "is not a kept run"),
        (["--box", str(box), "--run", str(tmp_path / "absent")], "is not a kept run"),
    ]
    for argv, why in cases:
        got = run(*argv)
        assert got.returncode == 2 and why in got.stderr and got.stdout == "", argv
    assert len(rows_of(box)) == 1


def test_a_record_that_does_not_verify_is_refused_and_left_as_it_is(tmp_path):
    box = box_in(tmp_path)
    record = box / "record.jsonl"
    record.write_text(record.read_text().replace('"kind":"boot"', '"kind":"boat"'))
    before = record.read_bytes()
    got = run("--box", str(box), "--run", str(EXAMPLE))
    assert got.returncode == 2 and "doesn't verify" in got.stderr
    assert record.read_bytes() == before


def test_it_writes_the_record_and_nothing_else(tmp_path):
    box = box_in(tmp_path)
    folder = a_run(
        tmp_path,
        "01 todo: started (aaaaaaaa)\n01 todo: exit 0, 1 line\n",
        {"01-todo.txt": "x\n"},
    )
    before = {
        p: p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file() and p.name != "record.jsonl"
    }
    assert run("--box", str(box), "--run", str(folder)).returncode == 0
    after = {
        p: p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file() and p.name != "record.jsonl"
    }
    assert after == before
    got = subprocess.run([sys.executable, str(ROOT / "kernel.py"), "verify", "--box", str(box)],
                         capture_output=True, text=True)  # fmt: skip
    assert got.stdout.strip() == "the chain holds: 2 rows, 0 sealed"
