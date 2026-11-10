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
        "01 heavy: started\n01 heavy: exit 0, 5 lines\n"
        "02 light: started\n02 light: exit 0, 1 line\n"
        "03 amounts: started\n03 amounts: exit 42, 0 lines\n"
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
        "01 heavy: started\n01 heavy: exit 2, 1 line, flagged\ndone: 1 of 1 steps flagged\n"
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
    assert (to / "00-stack.txt").read_text().startswith("01 slow: started\n")
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


def test_step_files_sort_in_the_order_they_ran_however_many(tmp_path):
    few = st.Run(tmp_path, 3)
    assert few.file(2, "todo").name == "02-todo.txt" and few.log.name == "00-stack.txt"
    many = tmp_path / "many"
    many.mkdir()
    lots = st.Run(many, 120)
    assert (
        lots.file(7, "todo").name == "007-todo.txt" and lots.log.name == "000-stack.txt"
    )
    lots.end(7, "todo", 0, "a\n\nb", "")
    lots.end(8, "x", 42, "", "flagged")
    assert (
        lots.log.read_text()
        == "007 todo: exit 0, 2 lines\n008 x: exit 42, 0 lines, flagged\n"
    )
