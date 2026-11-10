"""stack: one document from a stack of add-on steps over a box. It groups the
steps into pools, runs each, composes their output peaks-first (tallest pool,
and tallest step within, come first), substitutes the box into a step's args,
flags a step that doesn't run clean, writes nothing, and refuses a malformed
stack or command line.

Its steps here are stand-ins, written into a scratch copy beside this
stack.py and the kernel: `heavy` prints five lines, `light` one, and
`amounts` finds nothing, the way the real amounts does on a folder with no
sums. So these tests hold wherever stack.py is, whichever add-ons are beside
it, and test stack, not the add-ons it runs."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
sys.path.insert(0, str(HERE))
import stack as st  # noqa: E402

STANDIN = """import sys
from pathlib import Path

argv = sys.argv[1:]
box = Path(argv[argv.index("--box") + 1]) if "--box" in argv else None
if box is None or not (box / "kernel.json").is_file():
    print("refused: not a kernel box", file=sys.stderr)
    sys.exit(2)
rows = (box / "record.jsonl").read_text(encoding="utf-8").count("\\n")
for i in range({lines}):
    print(f"{name} line {{i + 1}}, over a box of {{rows}} rows")
if __name__ == "__main__":
    sys.exit({code})
"""
STACK = None  # the scratch copy's stack.py, set for each test


@pytest.fixture(autouse=True)
def scratch(tmp_path, monkeypatch):
    root = tmp_path / "willow"
    (root / "adapters" / "stdlib" / "stack").mkdir(parents=True)
    shutil.copy2(KERNEL, root / "kernel.py")
    shutil.copy2(HERE / "stack.py", root / "adapters" / "stdlib" / "stack" / "stack.py")
    for name, lines, code in (("heavy", 5, 0), ("light", 1, 0), ("amounts", 0, 42)):
        folder = root / "adapters" / "stdlib" / name
        folder.mkdir()
        (folder / f"{name}.py").write_text(
            STANDIN.format(name=name, lines=lines, code=code)
        )
    monkeypatch.setitem(
        globals(), "STACK", root / "adapters" / "stdlib" / "stack" / "stack.py"
    )


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
    # mmm is the heaviest (heavy); aaa and zzz are equal light pools (one
    # light each). File order is zzz, mmm, aaa, so the right order -- by mass,
    # then heading for a tie -- is mmm, aaa, zzz, which is neither the file
    # order nor grouped by the steps, so only mass-then-heading gives it.
    stack = a_stack(tmp_path, "## zzz\n- light -- --box {box}\n## mmm\n"
                    "- heavy -- --box {box}\n## aaa\n- light -- --box {box}\n")  # fmt: skip
    got = run("--box", str(box), "--stack", str(stack))
    assert got.returncode == 0, got.stdout + got.stderr
    page = got.stdout
    assert "peaks first" in page
    assert page.index("## mmm") < page.index("## aaa"), "tallest pool first"
    assert page.index("## aaa") < page.index("## zzz"), "a tie breaks by heading"


def test_the_box_is_substituted_into_a_steps_args(tmp_path):
    box = a_box(tmp_path)
    stack = a_stack(tmp_path, "## p\n- light -- --box {box}\n")
    got = run("--box", str(box), "--stack", str(stack))
    assert got.returncode == 0, got.stderr
    # light ran against the real box: its own output, not a not-a-box refusal
    assert "light line 1, over a box of 1 rows" in got.stdout
    assert "not a kernel box" not in got.stdout
    assert "1 step in 1 pool," in got.stdout  # counted, and singular


def test_a_step_before_any_pool_is_refused(tmp_path):
    box = a_box(tmp_path)
    stack = a_stack(tmp_path, "- light -- --box {box}\n")
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
    stack = a_stack(tmp_path, "## p\n- light -- --box {box}/nope\n")
    got = run("--box", str(box), "--stack", str(stack))
    assert got.returncode == 42, got.stdout + got.stderr
    assert "(exit 2)" in got.stdout  # the step's own refusal, surfaced and flagged


def test_step_results_follow_the_add_ons_cards():
    assert st.step_result("amounts", 42) == (False, "none found")
    assert st.step_result("said", 42) == (False, "none found")
    assert st.step_result("duplicates", 42) == (False, "none found")
    assert st.step_result("contradictions", 42) == (False, "none found")
    assert st.step_result("contradictions", 0) == (True, "flagged")
    assert st.step_result("export", 2) == (True, "exit 2")


def test_not_a_kernel_box_is_refused(tmp_path):
    (tmp_path / "b").mkdir()
    stack = a_stack(tmp_path, "## p\n- light -- --box {box}\n")
    got = run("--box", str(tmp_path / "b"), "--stack", str(stack))
    assert got.returncode == 2 and "not a kernel box" in got.stderr


def test_an_unreadable_stack_is_refused(tmp_path):
    box = a_box(tmp_path)
    got = run("--box", str(box), "--stack", str(tmp_path / "missing.md"))
    assert got.returncode == 2 and "can't read the stack" in got.stderr


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    box = a_box(tmp_path)
    stack = a_stack(tmp_path, "## p\n- light -- --box {box}\n")
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
    stack = a_stack(tmp_path, "## p\n- heavy -- --box {box}\n- light -- --box {box}\n")
    before = snapshot(box)
    got = run("--box", str(box), "--stack", str(stack))
    assert got.returncode == 0, got.stderr
    assert snapshot(box) == before, "stack reads and composes; it writes no box"


def test_a_step_that_found_nothing_is_not_flagged(tmp_path):
    box = a_box(tmp_path)  # 4200 is written with no currency: no sums
    got = run("--box", str(box), "--stack",
              str(a_stack(tmp_path, "## money\n- amounts -- --box {box}\n")))  # fmt: skip
    assert got.returncode == 0, got.stdout + got.stderr
    assert "(none found)" in got.stdout
    assert "1 of 1 steps flagged" not in got.stdout
    assert "0 of 1 steps flagged" in got.stdout


def test_within_a_pool_the_tallest_step_comes_first(tmp_path):
    """Written light, heavy, amounts (one line, five, none): printed heavy,
    light, amounts, which is neither the order written nor its reverse."""
    box = a_box(tmp_path)
    stack = a_stack(tmp_path, "## p\n- light -- --box {box}\n- heavy -- --box {box}\n"
                    "- amounts -- --box {box}\n")  # fmt: skip
    page = run("--box", str(box), "--stack", str(stack)).stdout
    at = [
        page.index(f"- `{n} -- --box {{box}}`") for n in ("heavy", "light", "amounts")
    ]
    assert at == sorted(at), page


def test_a_card_saying_report_among_its_outputs_prints_a_report(tmp_path):
    for said, prints in (("report", True), ("report, suggestions", True),
                         ("suggestions, report", True), ("suggestions", False)):  # fmt: skip
        (tmp_path / "README.md").write_text(f"<!-- willow-addon\noutput: {said}\n-->\n")
        assert st.prints_a_report(tmp_path / "x.py") is prints, said


TWO_VERBS = """import json, sys
argv = sys.argv[1:]
if argv[:1] == ["ask"] and "--json" in argv:
    print("usage: twoverbs.py ask --box DIR QUESTION | score --box DIR [--json]", file=sys.stderr)
    sys.exit(2)
if argv[:1] == ["ask"]:
    print("asked")
    sys.exit(0)
print(json.dumps({"addon": "twoverbs", "state": "empty", "said": "nothing yet", "groups": []}))
"""


@pytest.mark.xfail(
    strict=True,
    reason="bug #285: stack adds --json to every step of a report add-on, so predict ask refuses inside a stack",
)
def test_a_report_add_ons_step_that_prints_no_report_runs_as_written(tmp_path):
    # predict's shape: its card says output: report, but only score prints one
    folder = STACK.parents[1] / "twoverbs"
    folder.mkdir()
    (folder / "twoverbs.py").write_text(TWO_VERBS)
    (folder / "README.md").write_text("<!-- willow-addon\noutput: report\n-->\n")
    box = a_box(tmp_path)
    got = run(
        "--box",
        str(box),
        "--stack",
        str(a_stack(tmp_path, '## p\n- twoverbs -- ask --box {box} "q"\n')),
    )
    assert "(exit 2)" not in got.stdout and "asked" in got.stdout, got.stdout


# ── a run kept in a folder, to follow as it goes ─────────────────────────────
THREE = "## a\n- heavy -- --box {box}\n- light -- --box {box}\n## b\n- amounts -- --box {box}\n"
BOXED = ["--box", "{box}"]


def started(n: str, name: str, args=BOXED) -> str:
    return f"{n} {name}: started ({st.mark(name, list(args))})\n"


def test_a_run_is_kept_step_by_step_and_the_page_is_the_same(tmp_path):
    box = a_box(tmp_path)
    stack = a_stack(tmp_path, THREE)
    plain = run("--box", str(box), "--stack", str(stack))
    to = tmp_path / "run"
    to.mkdir()
    before = snapshot(box)
    got = run("--box", str(box), "--stack", str(stack), "--to", str(to))
    assert (got.returncode, got.stdout, got.stderr) == (
        plain.returncode,
        plain.stdout,
        plain.stderr,
    )
    assert snapshot(box) == before, "the box is only read"
    assert sorted(p.name for p in to.iterdir()) == [
        "00-stack.txt", "01-heavy.txt", "02-light.txt", "03-amounts.txt",
    ]  # fmt: skip
    assert (to / "00-stack.txt").read_text() == (
        started("01", "heavy")
        + "01 heavy: exit 0, 5 lines\n"
        + started("02", "light")
        + "02 light: exit 0, 1 line\n"
        + started("03", "amounts")
        + "03 amounts: exit 42, 0 lines\n"
        "done: 0 of 3 steps flagged\n"
    )
    heavy = (to / "01-heavy.txt").read_text()
    assert heavy.count("\n") == 5 and heavy.startswith("heavy line 1, over a box of")
    assert (to / "02-light.txt").read_text().count("\n") == 1
    assert (to / "03-amounts.txt").read_text() == ""


def test_a_step_that_only_complains_keeps_its_complaint_and_is_flagged(tmp_path):
    box = a_box(tmp_path)
    to = tmp_path / "run"
    to.mkdir()
    got = run("--box", str(box), "--stack", str(a_stack(tmp_path, "## a\n- heavy -- --nope\n")), "--to", str(to))  # fmt: skip
    assert got.returncode == 42 and "refused: not a kernel box" in got.stdout
    assert (to / "01-heavy.txt").read_text() == "refused: not a kernel box\n"
    assert (to / "00-stack.txt").read_text() == (
        started("01", "heavy", ["--nope"])
        + "01 heavy: exit 2, 1 line, flagged\ndone: 1 of 1 steps flagged\n"
    )


def test_a_step_is_written_as_it_prints_not_when_it_ends(tmp_path):
    folder = STACK.parents[1] / "slow"
    folder.mkdir()
    (folder / "slow.py").write_text(
        "import sys, time\nif __name__ == '__main__':\n    print('first')\n"
        "    time.sleep(float(sys.argv[1]))\n    print('second')\n"
    )
    box = a_box(tmp_path)
    to = tmp_path / "run"
    to.mkdir()
    stack = a_stack(tmp_path, "## a\n- slow -- 4\n")
    p = subprocess.Popen(
        [sys.executable, str(STACK), "--box", str(box), "--stack", str(stack), "--to", str(to)],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )  # fmt: skip
    seen_early = False
    for _ in range(30):  # three seconds; the step itself takes four
        time.sleep(0.1)
        step = to / "01-slow.txt"
        if step.is_file() and step.read_text() == "first\n":
            seen_early = p.poll() is None
            break
    out, _ = p.communicate(timeout=30)
    assert seen_early, "the first line was there to follow while the step still ran"
    assert (to / "00-stack.txt").read_text().startswith("01 slow: started (")
    assert (to / "01-slow.txt").read_text() == "first\nsecond\n" and "second" in out


def test_a_report_step_is_kept_as_its_report_not_its_json(tmp_path):
    folder = STACK.parents[1] / "rep"
    folder.mkdir()
    (folder / "README.md").write_text("<!-- willow-addon\noutput: report\n-->\n")
    (folder / "rep.py").write_text(
        "import json, sys\n"
        "doc = {'addon': 'rep', 'state': 'populated', 'said': '1 thing', 'groups': "
        "[{'name': None, 'rows': [{'where': 'a.txt:1', 'what': 'the thing'}]}]}\n"
        "if __name__ == '__main__':\n"
        "    print(json.dumps(doc) if '--json' in sys.argv else 'not asked for json')\n"
    )
    box = a_box(tmp_path)
    to = tmp_path / "run"
    to.mkdir()
    got = run("--box", str(box), "--stack", str(a_stack(tmp_path, "## a\n- rep -- --box {box}\n")), "--to", str(to))  # fmt: skip
    assert got.returncode == 0, got.stdout + got.stderr
    kept = (to / "01-rep.txt").read_text()
    assert (
        kept.startswith("rep: populated, 1 thing\n")
        and "a.txt:1" in kept
        and "{" not in kept
    )
    assert "01 rep: exit 0, 2 lines\n" in (to / "00-stack.txt").read_text()


def test_a_run_wants_a_folder_of_its_own_that_is_there(tmp_path):
    box = a_box(tmp_path)
    stack = a_stack(tmp_path, THREE)
    missing = tmp_path / "nowhere"
    got = run("--box", str(box), "--stack", str(stack), "--to", str(missing))
    assert (
        got.returncode == 2 and f"{missing} isn't a folder that's there" in got.stderr
    )
    assert not missing.exists() and got.stdout == "", (
        "it makes no folder and runs no step"
    )
    full = tmp_path / "full"
    full.mkdir()
    (full / "yours.txt").write_text("keep me")
    got = run("--box", str(box), "--stack", str(stack), "--to", str(full))
    assert (
        got.returncode == 2 and f"{full} isn't empty" in got.stderr and got.stdout == ""
    )
    assert snapshot(full) == {"yours.txt": b"keep me"}
    got = run("--box", str(box), "--stack", str(stack), "--to")
    assert got.returncode == 2 and "stack.py" in got.stderr
    a_file = tmp_path / "a-file"
    a_file.write_text("x")
    got = run("--box", str(box), "--stack", str(stack), "--to", str(a_file))
    assert got.returncode == 2 and "isn't a folder" in got.stderr


def test_step_files_sort_in_the_order_they_ran_however_many(tmp_path, monkeypatch):
    # in this process, so the guard reads --to from here as it would from a run
    monkeypatch.setattr(sys, "argv", ["stack.py", "--to", str(tmp_path)])
    few = st.Run(tmp_path, 3)
    assert few.file(2, "todo").name == "02-todo.txt" and few.log.name == "00-stack.txt"
    many = tmp_path / "many"
    many.mkdir()
    lots = st.Run(many, 120)
    assert (
        lots.file(7, "todo").name == "007-todo.txt" and lots.log.name == "000-stack.txt"
    )
    lots.end(7, "todo", 0, "a\n\nb", 2, "", False)
    lots.end(8, "x", 42, "", 0, "", True)
    lots.end(9, "r", 42, "r: populated, 1 thing\n## g\n  a  b", 2, "populated", True)
    assert lots.log.read_text() == (
        "007 todo: exit 0, 2 lines\n008 x: exit 42, 0 lines, flagged\n"
        "009 r: exit 42, 3 lines, mass 2, populated, flagged\n"
    )


# ── going on with a run that was cut off, or whose stack grew ────────────────
REP = (
    "import json, sys\n"
    "doc = {'addon': 'rep', 'state': 'populated', 'said': '2 things', 'groups': "
    "[{'name': 'a group', 'rows': [{'where': 'a.txt:1', 'what': 'one'}, {'where': 'b.txt:2', 'what': 'two'}]}]}\n"
    "if __name__ == '__main__':\n"
    "    print(json.dumps(doc) if '--json' in sys.argv else 'not asked for json')\n"
    "    sys.exit(42)\n"
)
FOUR = THREE + "- rep -- --box {box}\n"


def a_run(tmp_path, text=FOUR):
    folder = STACK.parents[1] / "rep"
    folder.mkdir(exist_ok=True)
    (folder / "README.md").write_text("<!-- willow-addon\noutput: report\n-->\n")
    (folder / "rep.py").write_text(REP)
    box = a_box(tmp_path)
    stack = a_stack(tmp_path, text)
    to = tmp_path / "run"
    to.mkdir()
    first = run("--box", str(box), "--stack", str(stack), "--to", str(to))
    assert first.returncode in (0, 42), first.stdout + first.stderr
    return box, stack, to, first


def again(box, stack, to):
    return run("--box", str(box), "--stack", str(stack), "--to", str(to), "--resume")


def test_a_finished_run_resumed_runs_nothing_and_gives_the_same_page(tmp_path):
    box, stack, to, first = a_run(tmp_path)
    log = (to / "00-stack.txt").read_text()
    assert "04 rep: exit 42, 4 lines, mass 3, populated, flagged\n" in log
    files = snapshot(to)
    got = again(box, stack, to)
    assert (got.returncode, got.stdout, got.stderr) == (
        first.returncode,
        first.stdout,
        first.stderr,
    )
    assert (to / "00-stack.txt").read_text() == log + (
        "resumed: 4 of 4 steps had finished\n"
        "01 heavy: kept from before\n02 light: kept from before\n"
        "03 amounts: kept from before\n04 rep: kept from before\n"
        "done: 1 of 4 steps flagged\n"
    )
    del files["00-stack.txt"]
    assert {k: v for k, v in snapshot(to).items() if k != "00-stack.txt"} == files
    # and again: what it kept the second time, it keeps the third
    third = again(box, stack, to)
    assert (
        third.stdout == first.stdout
        and (to / "00-stack.txt").read_text().count("started (") == 4
    )


def test_a_run_cut_off_goes_on_from_the_step_it_was_in(tmp_path):
    box, stack, to, first = a_run(tmp_path)
    log = (to / "00-stack.txt").read_text()
    cut = log[: log.index("02 light: exit")]  # stopped while light was running
    (to / "00-stack.txt").write_text(cut)
    (to / "02-light.txt").write_text("half a li")
    (to / "03-amounts.txt").unlink()
    (to / "04-rep.txt").unlink()
    got = again(box, stack, to)
    assert (got.returncode, got.stdout) == (first.returncode, first.stdout)
    assert (to / "00-stack.txt").read_text() == cut + (
        "resumed: 1 of 4 steps had finished\n01 heavy: kept from before\n"
        + started("02", "light")
        + "02 light: exit 0, 1 line\n"
        + started("03", "amounts")
        + "03 amounts: exit 42, 0 lines\n"
        + started("04", "rep")
        + "04 rep: exit 42, 4 lines, mass 3, populated, flagged\n"
        "done: 1 of 4 steps flagged\n"
    )
    assert (to / "02-light.txt").read_text().startswith("light line 1")


def test_a_step_asked_another_way_runs_and_so_does_every_step_after_it(tmp_path):
    box, stack, to, _ = a_run(tmp_path)
    log = (to / "00-stack.txt").read_text()
    stack.write_text(
        FOUR.replace("- light -- --box {box}", "- light -- --box {box} more")
    )
    got = again(box, stack, to)
    added = (to / "00-stack.txt").read_text()[len(log) :]
    assert added == (
        "resumed: 4 of 4 steps had finished\n01 heavy: kept from before\n"
        + started("02", "light", [*BOXED, "more"])
        + "02 light: exit 0, 1 line\n"
        + started("03", "amounts")
        + "03 amounts: exit 42, 0 lines\n"
        + started("04", "rep")
        + "04 rep: exit 42, 4 lines, mass 3, populated, flagged\n"
        "done: 1 of 4 steps flagged\n"
    ), "amounts and rep had finished, and ran: they come after a step that changed"
    assert got.returncode == 42


def test_a_step_added_at_the_end_is_the_only_one_run(tmp_path):
    box, stack, to, _ = a_run(tmp_path, THREE)
    log = (to / "00-stack.txt").read_text()
    stack.write_text(THREE + "- heavy -- --box {box}\n")
    got = again(box, stack, to)
    added = (to / "00-stack.txt").read_text()[len(log) :]
    assert added == (
        "resumed: 3 of 4 steps had finished\n01 heavy: kept from before\n"
        "02 light: kept from before\n03 amounts: kept from before\n"
        + started("04", "heavy")
        + "04 heavy: exit 0, 5 lines\ndone: 0 of 4 steps flagged\n"
    )
    assert got.returncode == 0 and got.stdout.count("heavy line 1") == 2


def test_a_step_whose_output_is_gone_or_whose_add_on_changed_is_run(tmp_path):
    box, stack, to, first = a_run(tmp_path)
    (to / "01-heavy.txt").unlink()
    got = again(box, stack, to)
    assert got.stdout == first.stdout
    assert "kept from before" not in (to / "00-stack.txt").read_text()
    stack.write_text(
        FOUR.replace(
            "- heavy -- --box {box}\n- light", "- light -- --box {box}\n- light"
        )
    )
    again(box, stack, to)
    assert (
        "01 light: started (" in (to / "00-stack.txt").read_text().split("resumed:")[-1]
    )


def test_resume_wants_a_run_to_go_on_with(tmp_path):
    box = a_box(tmp_path)
    stack = a_stack(tmp_path, THREE)
    got = run("--box", str(box), "--stack", str(stack), "--resume")
    assert got.returncode == 2 and "stack.py" in got.stderr and got.stdout == ""
    other = tmp_path / "other"
    other.mkdir()
    (other / "yours.txt").write_text("keep me")
    got = run("--box", str(box), "--stack", str(stack), "--to", str(other), "--resume")
    assert got.returncode == 2 and "it has no log to resume from" in got.stderr
    assert snapshot(other) == {"yours.txt": b"keep me"} and got.stdout == ""
    got = run("--box", str(box), "--stack", str(stack), "--to", str(other))
    assert (
        got.returncode == 2
        and "--resume goes on with the run that's in it" in got.stderr
    )
    empty = tmp_path / "empty"
    empty.mkdir()
    plain = run("--box", str(box), "--stack", str(stack))
    got = run("--box", str(box), "--stack", str(stack), "--to", str(empty), "--resume")
    assert got.stdout == plain.stdout, "nothing to go on with is a run from the start"
    assert "resumed" not in (empty / "00-stack.txt").read_text()


def test_ended_reads_only_what_the_log_last_says_of_a_step():
    m1, m2 = st.mark("a", []), st.mark("b", ["x"])
    log = (
        f"01 a: started ({m1})\n01 a: exit 0, 3 lines\n"
        f"02 b: started ({m2})\n02 b: exit 42, 4 lines, mass 3, populated, flagged\n"
        "03 c: exit 0, 1 line\n"  # an end with no start
        f"04 d: started ({m1})\n04 e: exit 0, 1 line\n"  # an end under another name
        "done: 1 of 4 steps flagged\nresumed: 2 of 4 steps had finished\n"
        "01 a: kept from before\nnonsense\n\n"
    )
    assert st.ended(log) == {
        1: {
            "name": "a",
            "mark": m1,
            "fed": None,
            "code": 0,
            "size": 3,
            "flagged": False,
            "note": "",
        },
        2: {
            "name": "b",
            "mark": m2,
            "fed": None,
            "code": 42,
            "size": 3,
            "flagged": True,
            "note": "populated",
        },
    }
    # started again and not ended: not finished, whatever came before
    assert 1 not in st.ended(log + f"01 a: started ({m1})\n") and 2 in st.ended(
        log + f"01 a: started ({m1})\n"
    )
    assert st.ended("") == {}
    assert (
        st.mark("a", ["x"]) != st.mark("a", ["y"]) != st.mark("b", ["y"])
        and len(m1) == 8
    )


def test_a_report_steps_report_is_kept_as_data_beside_its_words(tmp_path):
    box, stack, to, _ = a_run(tmp_path)
    kept = sorted(p.name for p in (to / "reports").iterdir())
    assert kept == ["04-rep.json"], "only the step that printed a report"
    doc = json.loads((to / "reports" / "04-rep.json").read_text())
    assert doc["addon"] == "rep" and doc["state"] == "populated"
    assert [r["what"] for g in doc["groups"] for r in g["rows"]] == ["one", "two"]
    assert sorted(p.name for p in to.iterdir() if p.is_file()) == [
        "00-stack.txt", "01-heavy.txt", "02-light.txt", "03-amounts.txt", "04-rep.txt",
    ]  # fmt: skip
    # run again and printing no report this time, the old one is not left to be read
    (STACK.parents[1] / "rep" / "rep.py").write_text(
        "import sys\nif __name__ == '__main__':\n    print('not json')\n    sys.exit(0)\n"
    )
    (to / "04-rep.txt").unlink()
    again(box, stack, to)
    assert not (to / "reports" / "04-rep.json").exists()
    assert "not a report" in (to / "04-rep.txt").read_text()


# ── a step takes what an earlier step kept ──────────────────────────────────
SHOW = """import sys

argv = sys.argv[1:]
text = open(argv[argv.index("--of") + 1], encoding="utf-8").read()
print("shown: " + text.strip().replace("\\n", " | "))
if __name__ == "__main__":
    sys.exit(0)
"""
QUIET = """import sys

if __name__ == "__main__":
    sys.exit(0)
"""


def an_add_on(name: str, source: str, card: str = "") -> None:
    """A stand-in add-on beside the scratch stack.py, with a card if given."""
    folder = STACK.parents[1] / name
    folder.mkdir()
    (folder / f"{name}.py").write_text(source)
    if card:
        (folder / "README.md").write_text(card)


def test_a_step_takes_the_file_an_earlier_step_was_kept_in(tmp_path):
    box = a_box(tmp_path)
    an_add_on("show", SHOW)
    stack = a_stack(tmp_path, "## p\n- light -- --box {box}\n- show -- --of {01}\n")
    to = tmp_path / "run"
    to.mkdir()
    got = run("--box", str(box), "--stack", str(stack), "--to", str(to))
    assert got.returncode == 0, got.stdout + got.stderr
    said = (to / "02-show.txt").read_text()
    assert said == "shown: light line 1, over a box of 1 rows\n"
    assert "shown: light line 1" in got.stdout  # and on the page
    # the step is marked by what was written, not by where the run was kept
    assert (
        f"02 show: started ({st.mark('show', ['--of', '{01}'])})"
        in (to / "00-stack.txt").read_text()
    )


def test_a_number_without_its_zero_names_the_same_step(tmp_path):
    box = a_box(tmp_path)
    an_add_on("show", SHOW)
    stack = a_stack(tmp_path, "## p\n- light -- --box {box}\n- show -- --of {1}\n")
    to = tmp_path / "run"
    to.mkdir()
    got = run("--box", str(box), "--stack", str(stack), "--to", str(to))
    assert got.returncode == 0, got.stderr
    assert "shown: light line 1" in (to / "02-show.txt").read_text()


def test_a_report_steps_report_is_handed_on_as_data(tmp_path):
    box = a_box(tmp_path)
    an_add_on("show", SHOW)
    doc = {"addon": "tells", "state": "populated", "said": "one thing",
           "groups": [{"name": None, "rows": [{"where": "a.md:1", "what": "it"}]}]}  # fmt: skip
    an_add_on(
        "tells",
        f"import sys\nprint({json.dumps(json.dumps(doc))})\n"
        'if __name__ == "__main__":\n    sys.exit(0)\n',
        "<!-- willow-addon\noutput: report\n-->\n",
    )
    stack = a_stack(tmp_path, "## p\n- tells\n- show -- --of {01.json}\n")
    to = tmp_path / "run"
    to.mkdir()
    got = run("--box", str(box), "--stack", str(stack), "--to", str(to))
    assert got.returncode == 0, got.stdout + got.stderr
    shown = (to / "02-show.txt").read_text()
    assert json.loads(shown.removeprefix("shown: ")) == doc


def test_a_hand_on_that_cant_be_is_refused_before_anything_runs(tmp_path):
    box = a_box(tmp_path)
    an_add_on("show", SHOW)
    to = tmp_path / "run"
    to.mkdir()

    def refused(text: str, *more: str) -> str:
        got = run("--box", str(box), "--stack", str(a_stack(tmp_path, text)), *more)
        assert got.returncode == 2, got.stdout + got.stderr
        assert not any(to.iterdir()), "nothing ran, nothing kept"
        return got.stderr

    two = "## p\n- light -- --box {box}\n- show -- --of {01}\n"
    said = refused(two)  # the run isn't kept
    assert "step 2 (show) takes {01}" in said and "add --to FOLDER" in said
    keep = ("--to", str(to))
    said = refused("## p\n- show -- --of {01}\n- light -- --box {box}\n", *keep)
    assert "step 1 (show) takes {01}, which isn't a step before it" in said
    said = refused("## p\n- light -- --box {box}\n- show -- --of {03}\n", *keep)
    assert "takes {03}, which isn't a step before it" in said
    said = refused("## p\n- light -- --box {box}\n- show -- --of {00}\n", *keep)
    assert "takes {00}, which isn't a step before it" in said
    said = refused("## p\n- light -- --box {box}\n- show -- --of {01.json}\n", *keep)
    assert "step 1 (light) prints no report; {01} is what it said" in said


def test_a_step_whose_earlier_step_kept_nothing_is_not_run(tmp_path):
    box = a_box(tmp_path)
    an_add_on("show", SHOW)
    an_add_on("quiet", QUIET)
    stack = a_stack(
        tmp_path, "## p\n- quiet\n- show -- --of {01}\n- light -- --box {box}\n"
    )
    to = tmp_path / "run"
    to.mkdir()
    got = run("--box", str(box), "--stack", str(stack), "--to", str(to))
    assert got.returncode == 42, got.stdout + got.stderr
    log = (to / "00-stack.txt").read_text()
    assert "02 show: not run: step 1 (quiet) kept nothing to hand on\n" in log
    assert "02 show: started" not in log and not (to / "02-show.txt").exists()
    assert "not run: step 1 (quiet) kept nothing to hand on" in got.stdout
    assert "03 light: exit 0" in log, "the steps after it still run"
    assert "done: 1 of 3 steps flagged" in log


def test_hands_reads_each_earlier_step_a_steps_args_name():
    assert st.hands(["--of", "{01}", "--and", "x{12.json}y", "{box}", "{a}"]) == [
        (1, False),
        (12, True),
    ]
    assert st.hands(["--box", "{box}"]) == []


# ── a run notes the files each step was given ───────────────────────────────
def test_a_step_given_a_file_notes_its_bytes_beside_its_mark(tmp_path):
    box = a_box(tmp_path)
    an_add_on("show", SHOW)
    q = tmp_path / "q.txt"
    q.write_text("one\n")
    stack = a_stack(tmp_path, f"## p\n- light -- --box {{box}}\n- show -- --of {q}\n")
    to = tmp_path / "run"
    to.mkdir()
    assert (
        run("--box", str(box), "--stack", str(stack), "--to", str(to)).returncode == 0
    )
    log = (to / "00-stack.txt").read_text()
    given = st.fed(["--of", str(q)], str(box))
    assert len(given) == 8
    assert f"02 show: started ({st.mark('show', ['--of', str(q)])}, fed {given})" in log
    # a step given no file says nothing of it: a box is a folder, not a file
    assert f"01 light: started ({st.mark('light', ['--box', '{box}'])})\n" in log


def test_fed_is_the_files_a_step_is_given_as_they_are_now(tmp_path):
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("one\n")
    b.write_text("two\n")
    box = str(tmp_path)
    one = st.fed(["--of", str(a)], box)
    assert one and one == st.fed(["--of", str(a)], box), "the same bytes, the same"
    assert st.fed(["--of", str(b)], box) != one, "another file's bytes"
    assert st.fed(["--of", str(a), "--and", str(b)], box) != one
    a.write_text("one more\n")
    assert st.fed(["--of", str(a)], box) != one, "its bytes changed"
    # what it makes, an earlier step's output, a folder, and no file: not given
    assert st.fed(["--to", str(a)], box) == ""
    assert st.fed(["--of", "{01}"], box) == ""
    assert st.fed(["--from", str(tmp_path)], box) == ""
    assert st.fed(["--from", str(tmp_path / "nope")], box) == ""
    assert st.fed([], box) == ""
    # only the file after --to is left out, not the ones beside it
    assert st.fed(["--to", str(a), str(b)], box) == st.fed([str(b)], box) != ""
    # {box} is the box given, and the file is named as it was written
    (tmp_path / "in.txt").write_text("x\n")
    assert st.fed(["{box}/in.txt"], box) != ""
    assert st.fed(["{box}/in.txt"], str(tmp_path / "nope")) == ""


def test_a_changed_file_is_asked_again_and_an_unchanged_one_is_kept(tmp_path):
    box = a_box(tmp_path)
    an_add_on("show", SHOW)
    q = tmp_path / "q.txt"
    q.write_text("one\n")
    stack = a_stack(
        tmp_path,
        f"## p\n- light -- --box {{box}}\n- show -- --of {q}\n- heavy -- --box {{box}}\n",
    )
    to = tmp_path / "run"
    to.mkdir()
    argv = ("--box", str(box), "--stack", str(stack), "--to", str(to))
    assert run(*argv).returncode == 0
    assert run(*argv, "--resume").returncode == 0
    log = (to / "00-stack.txt").read_text()
    assert log.count("kept from before") == 3 and log.count("02 show: started") == 1
    q.write_text("two\n")
    assert run(*argv, "--resume").returncode == 0
    log = (to / "00-stack.txt").read_text()
    assert log.count("01 light: kept from before") == 2, "before it: still kept"
    assert log.count("02 show: started") == 2, "its file changed: asked again"
    assert log.count("03 heavy: started") == 2, "and so is every step after it"
    assert (to / "02-show.txt").read_text() == "shown: two\n"


def test_a_log_from_before_files_were_noted_is_taken_at_its_word(tmp_path):
    box = a_box(tmp_path)
    an_add_on("show", SHOW)
    q = tmp_path / "q.txt"
    q.write_text("one\n")
    stack = a_stack(tmp_path, f"## p\n- show -- --of {q}\n")
    to = tmp_path / "run"
    to.mkdir()
    argv = ("--box", str(box), "--stack", str(stack), "--to", str(to))
    assert run(*argv).returncode == 0
    log = to / "00-stack.txt"
    given = st.fed(["--of", str(q)], str(box))
    assert f", fed {given}" in log.read_text()
    log.write_text(log.read_text().replace(f", fed {given}", ""))  # as written then
    q.write_text("two\n")
    assert run(*argv, "--resume").returncode == 0
    assert "01 show: kept from before" in log.read_text()
    assert (to / "01-show.txt").read_text() == "shown: one\n"


def test_ended_reads_the_files_a_step_noted():
    m = st.mark("a", ["q.txt"])
    log = f"01 a: started ({m}, fed 0123abcd)\n01 a: exit 0, 1 line\n"
    assert st.ended(log)[1]["fed"] == "0123abcd"
    assert st.ended(log)[1]["mark"] == m


# ── a backslash the shell's rule would drop ─────────────────────────────────
def test_a_bare_backslash_before_a_letter_is_caught_and_quoted_ones_are_not():
    assert st.bare_backslash("--id INV-\\d+")
    assert st.bare_backslash("--box {box} --id \\w")
    assert st.bare_backslash("'quoted' then \\d")
    assert st.bare_backslash('"double" then \\9')
    assert not st.bare_backslash('--id "INV-\\d+"')
    assert not st.bare_backslash("--id 'INV-\\d+'")
    assert not st.bare_backslash('"a \\"quoted\\" word"')
    assert not st.bare_backslash("two\\ words")  # an escaped space is kept as one
    assert not st.bare_backslash("--box {box}")
    assert not st.bare_backslash("ends with \\")
    assert not st.bare_backslash("")


def test_a_stack_line_with_a_backslash_that_would_be_dropped_is_refused(tmp_path):
    box = a_box(tmp_path)
    stack = a_stack(
        tmp_path, "## p\n- light -- --box {box}\n- light -- --box {box} --id INV-\\d+\n"
    )
    got = run("--box", str(box), "--stack", str(stack))
    assert got.returncode == 2
    assert "line 3: a backslash outside quotes would be dropped" in got.stderr
    assert "put that option in quotes" in got.stderr
    quoted = a_stack(tmp_path, '## p\n- light -- --box {box} --id "INV-\\d+"\n')
    assert run("--box", str(box), "--stack", str(quoted)).returncode == 0
