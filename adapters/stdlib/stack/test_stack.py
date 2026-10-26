"""stack: one document from a stack of add-on steps over a box. It groups the
steps into pools, runs each, composes their output peaks-first (tallest pool,
and tallest step within, come first), substitutes the box into a step's args,
flags a step that doesn't run clean, writes nothing, and refuses a malformed
stack or command line."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STACK = HERE / "stack.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(STACK), *argv],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )


def a_box(tmp: Path) -> Path:
    """A box over a two-file pile; no bite needed (the steps only read it)."""
    pile = tmp / "pile"
    pile.mkdir()
    (pile / "roof.md").write_text("2026-03-01 The roof estimate came in at 4200.\n")
    (pile / "mould.md").write_text("2026-03-02 Reported the mould in the bedroom.\n")
    box = tmp / "box"
    subprocess.run(
        [sys.executable, str(KERNEL), "init", "--box", str(box), "--pile",
         str(pile), "--key", str(tmp / "key"), *NOW],
        check=True, capture_output=True,
    )  # fmt: skip
    return box


def a_stack(tmp: Path, text: str) -> Path:
    path = tmp / "stack.md"
    path.write_text(text, encoding="utf-8")
    return path


def snapshot(root: Path) -> dict:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*")) if p.is_file()
    }  # fmt: skip


def test_a_stack_composes_its_pools_with_peaks_first(tmp_path):
    box = a_box(tmp_path)
    # mmm is the heaviest (digest); aaa and zzz are equal light pools (one
    # export each). File order is zzz, mmm, aaa, so the right order -- by mass,
    # then heading for a tie -- is mmm, aaa, zzz, which is neither the file
    # order nor grouped by the steps, so only mass-then-heading gives it.
    stack = a_stack(tmp_path, "## zzz\n- export -- --box {box}\n## mmm\n"
                    "- digest -- --box {box}\n## aaa\n- export -- --box {box}\n")  # fmt: skip
    got = run("--box", str(box), "--stack", str(stack))
    assert got.returncode == 0, got.stdout + got.stderr
    page = got.stdout
    assert "peaks first" in page
    assert page.index("## mmm") < page.index("## aaa"), "tallest pool first"
    assert page.index("## aaa") < page.index("## zzz"), "a tie breaks by heading"


def test_the_box_is_substituted_into_a_steps_args(tmp_path):
    box = a_box(tmp_path)
    stack = a_stack(tmp_path, "## p\n- export -- --box {box}\n")
    got = run("--box", str(box), "--stack", str(stack))
    assert got.returncode == 0, got.stderr
    # export ran against the real box: its own output, not a not-a-box refusal
    assert "# Approved answers" in got.stdout
    assert "not a kernel box" not in got.stdout
    assert "1 step in 1 pool," in got.stdout  # counted, and singular


def test_a_step_before_any_pool_is_refused(tmp_path):
    box = a_box(tmp_path)
    stack = a_stack(tmp_path, "- export -- --box {box}\n")
    got = run("--box", str(box), "--stack", str(stack))
    assert got.returncode == 2 and "before any ## pool" in got.stderr


def test_an_unknown_add_on_is_refused_and_names_it(tmp_path):
    box = a_box(tmp_path)
    stack = a_stack(tmp_path, "## p\n- nope -- --box {box}\n")
    got = run("--box", str(box), "--stack", str(stack))
    assert got.returncode == 2 and "nope add-on isn't here" in got.stderr


def test_a_flagged_step_makes_the_stack_exit_42(tmp_path):
    box = a_box(tmp_path)
    # the box is real, but the step points one level below it, which is not one
    stack = a_stack(tmp_path, "## p\n- export -- --box {box}/nope\n")
    got = run("--box", str(box), "--stack", str(stack))
    assert got.returncode == 42, got.stdout + got.stderr
    assert "(exit 2)" in got.stdout  # the step's own refusal, surfaced and flagged


def test_not_a_kernel_box_is_refused(tmp_path):
    (tmp_path / "b").mkdir()
    stack = a_stack(tmp_path, "## p\n- export -- --box {box}\n")
    got = run("--box", str(tmp_path / "b"), "--stack", str(stack))
    assert got.returncode == 2 and "not a kernel box" in got.stderr


def test_an_unreadable_stack_is_refused(tmp_path):
    box = a_box(tmp_path)
    got = run("--box", str(box), "--stack", str(tmp_path / "missing.md"))
    assert got.returncode == 2 and "can't read the stack" in got.stderr


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    box = a_box(tmp_path)
    stack = a_stack(tmp_path, "## p\n- export -- --box {box}\n")
    for argv in (
        [],  # nothing
        ["--box", str(box)],  # no --stack
        ["--stack", str(stack)],  # no --box
        ["--box", str(box), "--stack", str(stack), "--stray", "more"],  # extra
    ):
        got = run(*argv)
        assert got.returncode == 2 and "stack.py" in got.stderr, (argv, got.stderr)


def test_the_stack_writes_nothing_to_the_box(tmp_path):
    box = a_box(tmp_path)
    stack = a_stack(
        tmp_path, "## p\n- digest -- --box {box}\n- export -- --box {box}\n"
    )
    before = snapshot(box)
    got = run("--box", str(box), "--stack", str(stack))
    assert got.returncode == 0, got.stderr
    assert snapshot(box) == before, "stack reads and composes; it writes no box"
