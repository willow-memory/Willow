"""projects: each folder that holds a record is a project, listed with its
records, its stacks and its runs; a run is tied to a stack by its steps'
marks, never its name; and nothing is written, nor the key read."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
STACK = HERE.parent / "stack" / "stack.py"
NOW = ["--now", "2026-11-10T00:00:00Z"]

_spec = importlib.util.spec_from_file_location("stack_for_projects_tests", STACK)
ST = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ST)

#: stacks whose steps are never run here: their logs are written by hand
MEND = "# mending\n\n## look\n- todo -- --box {box}\n- stale -- --box {box}\n\n## tell\n- said -- --box {box}\n"
#: stacks that are really run: the only add-ons sure to be beside this one
#: are itself and stack, so its steps are those
QUIET = "## look\n- projects -- --home {box}/../..\n"
LOUD = "## look\n- projects -- --home {box}/../..\n- projects -- --home {box}\n"


def k(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(KERNEL), *map(str, argv)],
                          capture_output=True, text=True)  # fmt: skip


def projects(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "projects.py"), *map(str, argv)],
                          capture_output=True, text=True)  # fmt: skip


def listed(home: Path) -> dict[str, dict[str, str]]:
    """What --json says: each project's rows, where to what."""
    doc = json.loads(projects("--home", home, "--json").stdout)
    return {g["name"]: {r["where"]: r["what"] for r in g["rows"]} for g in doc["groups"]}  # fmt: skip


def record(project: Path, name: str = "box") -> Path:
    """A record in a project folder; its files and its key are kept well
    outside the folder that is listed."""
    aside = project.parents[1] / "aside" / f"{project.name}-{name}"
    aside.mkdir(parents=True)
    (aside / "pile").mkdir()
    (aside / "pile" / "garden.md").write_text(
        "Tomatoes want six hours of sun.\n\nWater at the root.\n"
    )
    project.mkdir(parents=True, exist_ok=True)
    b = project / name
    got = k("init", "--box", b, "--pile", aside / "pile", "--key", aside / "key", *NOW)
    assert got.returncode == 0, got.stderr
    return b


def suggest(b: Path, *lines: str) -> list[str]:
    """A question asked, and a suggestion for each line (a line that isn't
    one is refused at the door); the subjects of those that wait."""
    got = k("bite", "--box", b, *NOW, "how much sun do tomatoes want")
    cite = json.loads(got.stdout)["served"][0]["id"]
    rows = [
        json.dumps({"path": f"sun{i}.md", "data": x, "cites": [cite], "claim": "garden.md"})
        if x else "not a suggestion"
        for i, x in enumerate(lines)
    ]  # fmt: skip
    f = b.parents[2] / "aside" / "rows.jsonl"
    f.write_text("\n".join(rows) + "\n")
    out = k("propose", "--box", b, "--file", f, *NOW).stdout
    return [ln.split()[1] for ln in out.splitlines() if ln.startswith("pass")]


def steps_of(stack: str) -> list:
    pools, err = ST.parse_stack(stack)
    assert err is None
    return [s for _, ss in pools for s in ss]


def log(run: Path, steps: list, *, flagged=(), finished: bool = True, when: float = 1e9,
        name: str = "00-stack.txt") -> Path:  # fmt: skip
    """A run's log written by hand, in the stack add-on's words (a real run
    is held to the same rows in the tests below), its time set to `when`."""
    run.mkdir(parents=True)
    lines = []
    for n, (step, args) in enumerate(steps, 1):
        lines.append(f"{n:02d} {step}: started ({ST.mark(step, args)})")
        lines.append(f"{n:02d} {step}: exit 42, 3 lines, flagged" if n in flagged
                     else f"{n:02d} {step}: exit 0, 3 lines")  # fmt: skip
    if finished:
        lines.append(f"done: {len(flagged)} of {len(steps)} steps flagged")
    (run / name).write_text("".join(ln + "\n" for ln in lines))
    os.utime(run / name, (when, when))
    return run


def really_run(b: Path, stack: Path, to: Path, when: float = 1e9) -> Path:
    """The stack add-on run into a folder, as a person would."""
    to.mkdir(parents=True)
    got = subprocess.run([sys.executable, str(STACK), "--box", str(b), "--stack", str(stack),
                          "--to", str(to)], capture_output=True, text=True)  # fmt: skip
    assert got.returncode in (0, 42), got.stderr
    os.utime(to / "00-stack.txt", (when, when))
    return to


def snapshot(root: Path) -> dict:
    return {str(p.relative_to(root)): (p.stat().st_mtime_ns, p.read_bytes() if p.is_file() else None)
            for p in sorted(root.rglob("*"))}  # fmt: skip


# ── the command line ────────────────────────────────────────────────────────
def test_a_bad_command_line_is_refused_and_names_the_script():
    got = subprocess.run(
        [sys.executable, str(HERE / "projects.py")], capture_output=True, text=True
    )
    assert got.returncode == 2 and "projects.py" in got.stderr


def test_every_other_bad_command_line_is_refused_too(tmp_path):
    record(tmp_path / "home" / "garden")
    home = tmp_path / "home"
    assert projects("--home", home).returncode == 0  # the one that works
    for bad in (["--home"], ["--box", home], [home, "--home"], ["--home", home, "more"],
                ["--home", ""], ["--json"], ["--home", "--json"]):  # fmt: skip
        got = projects(*bad)
        assert (got.returncode, got.stdout) == (2, ""), bad
        assert got.stderr == "usage: projects.py --home FOLDER [--json]\n", bad


def test_a_home_that_isnt_a_folder_is_refused(tmp_path):
    (tmp_path / "notes.txt").write_text("not a folder\n")
    for bad in (tmp_path / "notes.txt", tmp_path / "nowhere"):
        got = projects("--home", bad)
        assert (got.returncode, got.stdout) == (2, "")
        assert got.stderr == f"refused: {bad} isn't a folder\n"


# ── what a project is ───────────────────────────────────────────────────────
def test_a_folder_that_holds_no_project_is_empty_and_waits_on_you(tmp_path):
    home = tmp_path / "home"
    (home / "plain").mkdir(parents=True)
    (home / "plain" / "mend.md").write_text(MEND)  # a stack, but no record beside it
    log(home / "plain" / "run-1", steps_of(MEND))
    (home / "notes.txt").write_text("a file, not a folder\n")
    got = projects("--home", home)
    assert got.returncode == 42
    assert got.stdout == f"projects: empty, no folder under {home} holds a record\n"
    data = projects("--home", home, "--json")
    assert data.returncode == 42 and json.loads(data.stdout) == {
        "addon": "projects",
        "state": "empty",
        "said": f"no folder under {home} holds a record",
        "groups": [],
    }


def test_a_record_right_under_the_folder_is_not_a_project(tmp_path):
    """A project is a folder that holds a record, so the record itself, one
    level too high, is nobody's."""
    record(tmp_path / "home")
    got = projects("--home", tmp_path / "home")
    assert got.returncode == 42 and got.stdout.startswith("projects: empty, ")


def test_a_project_is_found_by_what_it_holds_whatever_it_is_called(tmp_path):
    home = tmp_path / "home"
    record(home / "zebra", "the-record")
    record(home / "apple", "one")
    record(home / "apple", "two")
    record(home / ".hidden")
    (home / "plain").mkdir()
    (home / "stray.md").write_text(MEND)
    got = projects("--home", home)
    assert got.returncode == 0
    assert got.stdout.splitlines() == [
        f"projects: populated, 2 projects under {home}: 3 records, 0 stacks, 0 runs",
        "## apple",
        "  one         1 row: 0 asked, 0 approved, 0 waiting",
        "  two         1 row: 0 asked, 0 approved, 0 waiting",
        "## zebra",
        "  the-record  1 row: 0 asked, 0 approved, 0 waiting",
    ]


# ── a record's row ──────────────────────────────────────────────────────────
def test_a_record_is_counted_from_its_rows(tmp_path):
    home = tmp_path / "home"
    b = record(home / "garden")
    assert listed(home) == {"garden": {"box": "1 row: 0 asked, 0 approved, 0 waiting"}}
    yes, no, later = suggest(b, "Six hours.", "Seven hours.", "", "Eight hours.")
    assert len((b / "record.jsonl").read_text().splitlines()) == 6
    got = projects("--home", home)
    assert got.returncode == 42, "a suggestion waits"
    assert got.stdout.splitlines() == [
        f"projects: populated, 1 project under {home}: 1 record, 0 stacks, 0 runs; "
        "3 suggestions wait on you",
        "## garden",
        "  box  6 rows: 1 asked, 0 approved, 3 waiting",
    ]
    assert k("seal", "--box", b, yes, *NOW).returncode == 0
    assert k("decline", "--box", b, no, *NOW).returncode == 0
    got = projects("--home", home)
    assert got.returncode == 42
    head, _, row = got.stdout.splitlines()
    assert head.endswith(": 1 record, 0 stacks, 0 runs; 1 suggestion waits on you")
    assert row == "  box  8 rows: 1 asked, 1 approved, 1 waiting"
    assert k("seal", "--box", b, later, *NOW).returncode == 0
    got = projects("--home", home)
    assert got.returncode == 0, "nothing waits any more"
    head, _, row = got.stdout.splitlines()
    assert head.endswith(": 1 record, 0 stacks, 0 runs")
    assert row == "  box  9 rows: 1 asked, 2 approved, 0 waiting"


def test_what_waits_is_added_up_over_every_project(tmp_path):
    home = tmp_path / "home"
    suggest(record(home / "garden"), "Six hours.")
    suggest(record(home / "kitchen"), "Six hours.")
    record(home / "shed")
    got = projects("--home", home)
    assert got.returncode == 42
    assert got.stdout.splitlines()[0] == (
        f"projects: populated, 3 projects under {home}: 3 records, 0 stacks, 0 runs; "
        "2 suggestions wait on you"
    )


def test_a_record_whose_chain_is_broken_is_said_not_counted(tmp_path):
    home = tmp_path / "home"
    b = record(home / "garden")
    suggest(b, "Six hours.")
    record(home / "kitchen")
    path = b / "record.jsonl"
    path.write_bytes(
        path.read_bytes().replace(b'"verdict":"pass"', b'"verdict":"fail"', 1)
    )
    got = projects("--home", home)
    assert got.returncode == 42, "a broken chain waits on you"
    assert got.stdout.splitlines() == [
        f"projects: populated, 2 projects under {home}: 2 records, 0 stacks, 0 runs",
        "## garden",
        "  box  its chain is broken: row 2: chain broken",
        "## kitchen",
        "  box  1 row: 0 asked, 0 approved, 0 waiting",
    ]
    assert projects("--home", home, "--json").returncode == 42


# ── a stack's row ───────────────────────────────────────────────────────────
def test_a_stack_is_a_markdown_file_with_steps_beside_the_record(tmp_path):
    home = tmp_path / "home"
    p = home / "garden"
    record(p)
    (p / "mend.md").write_text(MEND)
    (p / "one.md").write_text("## look\n- todo -- --box {box}\n")
    (p / "notes.md").write_text("# Notes\n\nNothing to run here.\n")  # no step
    (p / "wrong.md").write_text("- todo -- --box {box}\n")  # a step before any pool
    (p / "mend.txt").write_text(MEND)  # not markdown
    (p / "folder.md").mkdir()
    (p / "deeper").mkdir()
    (p / "deeper" / "lower.md").write_text(MEND)  # not beside the record
    got = projects("--home", home)
    assert got.returncode == 0
    assert got.stdout.splitlines() == [
        f"projects: populated, 1 project under {home}: 1 record, 2 stacks, 0 runs",
        "## garden",
        "  box      1 row: 0 asked, 0 approved, 0 waiting",
        "  mend.md  3 steps; never run",
        "  one.md   1 step; never run",
    ]


def test_a_stack_says_its_last_run_how_it_went_and_how_many_came_before(tmp_path):
    home = tmp_path / "home"
    p = home / "garden"
    record(p)
    (p / "mend.md").write_text(MEND)
    log(p / "run-b", steps_of(MEND), flagged={1, 3}, when=2000)
    assert listed(home)["garden"]["mend.md"] == "3 steps; last run run-b, 2 flagged"
    log(p / "run-c", steps_of(MEND), when=1000)  # older, though its name sorts later
    assert listed(home)["garden"]["mend.md"] == (
        "3 steps; last run run-b, 2 flagged; 1 run before it"
    )
    log(p / "run-a", steps_of(MEND), flagged={2}, when=3000)
    log(p / "run-d", steps_of(MEND), when=1500)
    got = projects("--home", home)
    assert got.returncode == 0, "a flagged step is the run's to say, not a suggestion"
    assert got.stdout.splitlines() == [
        f"projects: populated, 1 project under {home}: 1 record, 1 stack, 4 runs",
        "## garden",
        "  box      1 row: 0 asked, 0 approved, 0 waiting",
        "  mend.md  3 steps; last run run-a, 1 flagged; 3 runs before it",
    ]


def test_two_runs_of_one_moment_are_put_by_name(tmp_path):
    home = tmp_path / "home"
    p = home / "garden"
    record(p)
    (p / "mend.md").write_text(MEND)
    log(p / "run-b", steps_of(MEND), flagged={1})
    log(p / "run-a", steps_of(MEND))
    assert listed(home)["garden"]["mend.md"] == (
        "3 steps; last run run-a, nothing flagged; 1 run before it"
    )


def test_a_run_that_was_cut_off_is_not_finished(tmp_path):
    home = tmp_path / "home"
    p = home / "garden"
    record(p)
    (p / "mend.md").write_text(MEND)
    run = log(p / "run-1", steps_of(MEND)[:2], flagged={2}, finished=False)
    assert listed(home)["garden"]["mend.md"] == (
        "3 steps; last run run-1, 1 flagged, not finished"
    )
    # its second step began and never ended: still the stack's, as far as it got
    text = (run / "00-stack.txt").read_text()
    (run / "00-stack.txt").write_text(text[: text.index("02 stale: exit")])
    assert listed(home)["garden"]["mend.md"] == (
        "3 steps; last run run-1, nothing flagged, not finished"
    )


def test_a_run_is_looked_for_beside_the_record_and_one_folder_down_only(tmp_path):
    home = tmp_path / "home"
    p = home / "garden"
    b = record(p)
    (p / "mend.md").write_text(MEND)
    log(p / "mine" / "run-1", steps_of(MEND), when=2000)
    log(p / "run-0", steps_of(MEND), when=1000)
    log(p / "mine" / "old" / "run-9", steps_of(MEND), when=9000)  # two down
    log(b / "run-8", steps_of(MEND), when=8000)  # inside the record
    log(b / "runs" / "run-7", steps_of(MEND), when=7000)
    (b / "00-stack.txt").write_text((p / "run-0" / "00-stack.txt").read_text())
    os.utime(b / "00-stack.txt", (6000, 6000))
    (p / "mine" / "notes.txt").write_text("a file among the runs, not a run\n")
    (p / "empty").mkdir()
    got = projects("--home", home)
    assert got.returncode == 0
    assert got.stdout.splitlines() == [
        f"projects: populated, 1 project under {home}: 1 record, 1 stack, 2 runs",
        "## garden",
        "  box      1 row: 0 asked, 0 approved, 0 waiting",
        "  mend.md  3 steps; last run mine/run-1, nothing flagged; 1 run before it",
    ]


def test_a_long_stacks_log_is_a_run_too(tmp_path):
    """A stack of a hundred steps or more numbers them with three digits,
    its log included."""
    home = tmp_path / "home"
    p = home / "garden"
    record(p)
    (p / "mend.md").write_text(MEND)
    log(p / "run-1", steps_of(MEND), name="000-stack.txt")
    assert (
        listed(home)["garden"]["mend.md"] == "3 steps; last run run-1, nothing flagged"
    )


# ── whose run it is: by its steps' marks, never its name ────────────────────
def test_a_run_is_tied_to_its_stack_by_its_steps_not_its_name(tmp_path):
    home = tmp_path / "home"
    p = home / "garden"
    record(p)
    (p / "mend.md").write_text(MEND)
    (p / "tell.md").write_text(
        "## tell\n- said -- --box {box}\n- todo -- --box {box}\n"
    )
    log(p / "run-mend-1", steps_of((p / "tell.md").read_text()), flagged={1})
    assert listed(home)["garden"] == {
        "box": "1 row: 0 asked, 0 approved, 0 waiting",
        "mend.md": "3 steps; never run",
        "tell.md": "2 steps; last run run-mend-1, 1 flagged",
    }


def test_the_same_add_on_asked_another_way_is_another_step(tmp_path):
    home = tmp_path / "home"
    p = home / "garden"
    record(p)
    (p / "one.md").write_text("## look\n- todo -- --box {box}\n")
    log(p / "run-1", steps_of("## look\n- todo -- --box {box} --all\n"))
    assert listed(home)["garden"]["one.md"] == "1 step; never run"
    assert listed(home)["garden"]["run-1"] == (
        "a run of no stack that is here now: 1 step, nothing flagged"
    )


def test_a_stack_that_grew_still_owns_the_run_made_before(tmp_path):
    """As far as the run got, its steps are the stack's own, in order."""
    home = tmp_path / "home"
    p = home / "garden"
    record(p)
    (p / "mend.md").write_text(MEND + "- amounts -- --box {box}\n")
    log(p / "run-1", steps_of(MEND))
    assert (
        listed(home)["garden"]["mend.md"] == "4 steps; last run run-1, nothing flagged"
    )


def test_a_whole_run_of_a_short_stack_is_its_own_not_a_longer_stacks_start(tmp_path):
    """Two stacks that begin the same way: a run of all the short one's
    steps is the short one's, whichever file comes first."""
    home = tmp_path / "home"
    p = home / "garden"
    record(p)
    (p / "a-long.md").write_text(MEND)
    (p / "b-short.md").write_text(
        "## look\n- todo -- --box {box}\n- stale -- --box {box}\n"
    )
    (p / "c-long.md").write_text(MEND + "- amounts -- --box {box}\n")
    log(p / "run-1", steps_of(MEND)[:2], flagged={2})
    assert listed(home)["garden"] == {
        "box": "1 row: 0 asked, 0 approved, 0 waiting",
        "a-long.md": "3 steps; never run",
        "b-short.md": "2 steps; last run run-1, 1 flagged",
        "c-long.md": "4 steps; never run",
    }
    # a run that got only as far as what they share is the first's that has it
    log(p / "run-2", steps_of(MEND)[:1], finished=False, when=2e9)
    assert listed(home)["garden"]["a-long.md"] == (
        "3 steps; last run run-2, nothing flagged, not finished"
    )


def test_a_run_sharing_most_of_a_stacks_steps_is_of_the_stack_before_it_changed(tmp_path):  # fmt: skip
    home = tmp_path / "home"
    p = home / "garden"
    record(p)
    (p / "mend.md").write_text(MEND.replace("said", "amounts"))  # its last step changed
    log(p / "run-1", steps_of(MEND), flagged={2})
    assert listed(home)["garden"] == {
        "box": "1 row: 0 asked, 0 approved, 0 waiting",
        "mend.md": "3 steps; last run run-1, 1 flagged, of the stack before it changed",
    }
    # a step taken out: the run has one the stack no longer has
    (p / "mend.md").write_text(
        "## look\n- todo -- --box {box}\n- stale -- --box {box}\n"
    )
    assert listed(home)["garden"]["mend.md"] == (
        "2 steps; last run run-1, 1 flagged, of the stack before it changed"
    )
    # the same steps in another order are not the stack's own in order
    (p / "mend.md").write_text(
        "## look\n- stale -- --box {box}\n- todo -- --box {box}\n- said -- --box {box}\n"
    )
    assert listed(home)["garden"]["mend.md"] == (
        "3 steps; last run run-1, 1 flagged, of the stack before it changed"
    )
    log(p / "run-0", steps_of(MEND), when=5)
    assert listed(home)["garden"]["mend.md"].endswith(
        ", of the stack before it changed; 1 run before it"
    )


def test_a_run_sharing_half_a_stacks_steps_or_fewer_is_listed_alone(tmp_path):
    home = tmp_path / "home"
    p = home / "garden"
    record(p)
    (p / "pair.md").write_text(
        "## look\n- todo -- --box {box}\n- amounts -- --box {box}\n"
    )
    log(
        p / "run-half",
        steps_of("## look\n- todo -- --box {box}\n- said -- --box {box}\n"),
    )
    log(p / "mine" / "run-none", steps_of("## look\n- stale -- --box {box}\n"), flagged={1},
        finished=False, when=5)  # fmt: skip
    got = projects("--home", home)
    assert got.returncode == 0
    assert got.stdout.splitlines() == [
        f"projects: populated, 1 project under {home}: 1 record, 1 stack, 2 runs",
        "## garden",
        "  box            1 row: 0 asked, 0 approved, 0 waiting",
        "  pair.md        2 steps; never run",
        "  run-half       a run of no stack that is here now: 2 steps, nothing flagged",
        "  mine/run-none  a run of no stack that is here now: 1 step, 1 flagged, not finished",
    ]
    # a long stack that holds a short run's steps, but not first, shares too little
    (p / "pair.md").write_text(
        "## look\n- amounts -- --box {box}\n- todo -- --box {box}\n- said -- --box {box}\n"
        "- stale -- --box {box}\n- out -- --box {box}\n"
    )
    assert listed(home)["garden"]["pair.md"] == "5 steps; never run"


def test_of_two_stacks_a_changed_run_goes_to_the_one_it_shares_most_with(tmp_path):
    home = tmp_path / "home"
    p = home / "garden"
    record(p)
    step = "- {} -- --box {{box}}\n".format
    ran = "## look\n" + step("todo") + step("stale") + step("said") + step("amounts")
    (p / "a.md").write_text(ran.replace("amounts", "out"))  # three of the run's four
    (p / "b.md").write_text(  # all four, in another order
        "## look\n" + step("stale") + step("todo") + step("said") + step("amounts")
    )
    (p / "c.md").write_text(ran.replace("amounts", "dates"))  # three again, but later
    log(p / "run-1", steps_of(ran))
    assert listed(home)["garden"] == {
        "box": "1 row: 0 asked, 0 approved, 0 waiting",
        "a.md": "4 steps; never run",
        "b.md": "4 steps; last run run-1, nothing flagged, of the stack before it changed",
        "c.md": "4 steps; never run",
    }
    (p / "b.md").unlink()  # of two that share as much, the first
    assert listed(home)["garden"]["a.md"].endswith("of the stack before it changed")
    assert listed(home)["garden"]["c.md"] == "4 steps; never run"


def test_a_run_that_began_no_step_belongs_to_no_stack(tmp_path):
    home = tmp_path / "home"
    p = home / "garden"
    record(p)
    (p / "mend.md").write_text(MEND)
    (p / "run-1").mkdir()
    (p / "run-1" / "00-stack.txt").write_text("")
    assert listed(home)["garden"] == {
        "box": "1 row: 0 asked, 0 approved, 0 waiting",
        "mend.md": "3 steps; never run",
        "run-1": "a run of no stack that is here now: 0 steps, nothing flagged, not finished",
    }


# ── real runs, made by the stack add-on ─────────────────────────────────────
def test_a_real_run_is_its_stacks_and_says_what_it_flagged(tmp_path):
    home = tmp_path / "home"
    p = home / "garden"
    b = record(p)
    (p / "quiet.md").write_text(QUIET)
    (p / "loud.md").write_text(LOUD)
    really_run(b, p / "loud.md", p / "run-1", when=1000)
    really_run(b, p / "quiet.md", p / "mine" / "run-2", when=2000)
    really_run(b, p / "loud.md", p / "mine" / "run-3", when=3000)
    assert "done: 1 of 2 steps flagged" in (p / "run-1" / "00-stack.txt").read_text()
    got = projects("--home", home)
    assert got.returncode == 0
    assert got.stdout.splitlines() == [
        f"projects: populated, 1 project under {home}: 1 record, 2 stacks, 3 runs",
        "## garden",
        "  box       1 row: 0 asked, 0 approved, 0 waiting",
        "  loud.md   2 steps; last run mine/run-3, 1 flagged; 1 run before it",
        "  quiet.md  1 step; last run mine/run-2, nothing flagged",
    ]
    # cut off: the log as it stood before its last line
    path = p / "mine" / "run-3" / "00-stack.txt"
    path.write_text("".join(ln + "\n" for ln in path.read_text().splitlines()[:-1]))
    assert listed(home)["garden"]["loud.md"] == (
        "2 steps; last run mine/run-3, 1 flagged, not finished; 1 run before it"
    )


def test_a_run_of_files_that_have_changed_since_says_so(tmp_path):
    """A step notes the files it was given; a file that is no longer what it
    was then makes the run one of files that have changed."""
    home = tmp_path / "home"
    p = home / "garden"
    b = record(p)
    (p / "parts").mkdir()
    (p / "parts" / "inner.md").write_text(QUIET)
    (p / "outer.md").write_text(
        QUIET + "- stack -- --box {box} --stack {box}/../parts/inner.md\n"
    )
    run = really_run(b, p / "outer.md", p / "run-1")
    assert ", fed " in (run / "00-stack.txt").read_text()
    assert (
        listed(home)["garden"]["outer.md"] == "2 steps; last run run-1, nothing flagged"
    )
    (p / "parts" / "inner.md").write_text(LOUD)
    got = projects("--home", home)
    assert got.returncode == 0
    assert listed(home)["garden"]["outer.md"] == (
        "2 steps; last run run-1, nothing flagged, of files that have changed since"
    )
    (p / "parts" / "inner.md").write_text(QUIET)  # put back byte for byte
    assert (
        listed(home)["garden"]["outer.md"] == "2 steps; last run run-1, nothing flagged"
    )
    (p / "parts" / "inner.md").unlink()  # gone is changed
    assert listed(home)["garden"]["outer.md"].endswith(
        ", of files that have changed since"
    )
    # an older run of the same files is counted, and nothing more is said of it
    (p / "parts" / "inner.md").write_text(QUIET)
    really_run(b, p / "outer.md", p / "run-2", when=2e9)
    (p / "parts" / "inner.md").write_text(LOUD)
    assert listed(home)["garden"]["outer.md"] == (
        "2 steps; last run run-2, nothing flagged, of files that have changed since; "
        "1 run before it"
    )


def test_a_run_that_noted_no_files_is_taken_at_its_word(tmp_path):
    """A log from before files were noted says nothing of them."""
    home = tmp_path / "home"
    p = home / "garden"
    b = record(p)
    (p / "parts").mkdir()
    (p / "parts" / "inner.md").write_text(QUIET)
    (p / "outer.md").write_text(
        QUIET + "- stack -- --box {box} --stack {box}/../parts/inner.md\n"
    )
    run = really_run(b, p / "outer.md", p / "run-1")
    text = (run / "00-stack.txt").read_text()
    given = ST.fed(steps_of((p / "outer.md").read_text())[1][1], str(b))
    assert text.count(f", fed {given})") == 1
    (run / "00-stack.txt").write_text(text.replace(f", fed {given})", ")"))
    (p / "parts" / "inner.md").write_text(LOUD)
    assert (
        listed(home)["garden"]["outer.md"] == "2 steps; last run run-1, nothing flagged"
    )


def test_a_changed_stack_is_said_before_its_changed_files(tmp_path):
    home = tmp_path / "home"
    p = home / "garden"
    b = record(p)
    (p / "parts").mkdir()
    (p / "parts" / "inner.md").write_text(QUIET)
    (p / "parts" / "other.md").write_text(QUIET)
    line = "- stack -- --box {box} --stack {box}/../parts/inner.md\n"
    (p / "outer.md").write_text(QUIET + line + line.replace("inner", "other"))
    really_run(b, p / "outer.md", p / "run-1")
    (p / "outer.md").write_text(QUIET + line + "- projects -- --home {box}\n")
    (p / "parts" / "inner.md").write_text(LOUD)
    assert listed(home)["garden"]["outer.md"] == (
        "3 steps; last run run-1, nothing flagged, of the stack before it changed"
    )


def test_a_file_inside_a_record_is_tried_as_each_record_of_the_project(tmp_path):
    """A run doesn't say which record it was run on, so `{box}` is each in
    turn: the file is unchanged if it is as it was in any of them."""
    home = tmp_path / "home"
    p = home / "garden"
    a, b = record(p, "a-box"), record(p, "b-box")
    assert (a / "kernel.json").read_bytes() != (b / "kernel.json").read_bytes()
    (p / "peek.md").write_text("## look\n- projects -- --home {box}/kernel.json\n")
    really_run(b, p / "peek.md", p / "run-1")
    assert listed(home)["garden"]["peek.md"] == "1 step; last run run-1, 1 flagged"
    held = (b / "kernel.json").read_bytes()
    (b / "kernel.json").write_bytes(held + b"\n")
    assert listed(home)["garden"]["peek.md"] == (
        "1 step; last run run-1, 1 flagged, of files that have changed since"
    )


# ── the report, and what it never does ──────────────────────────────────────
def test_json_is_the_same_report_as_one_object(tmp_path):
    home = tmp_path / "home"
    p = home / "garden"
    record(p)
    record(home / "kitchen")
    (p / "mend.md").write_text(MEND)
    log(p / "run-1", steps_of(MEND))
    other = steps_of("## look\n- out -- --box {box}\n- dates -- --box {box}\n")
    log(p / "mine" / "run-0", other, flagged={1}, when=5)
    for argv in (["--home", home, "--json"], ["--json", "--home", home]):
        got = projects(*argv)
        assert got.returncode == 0 and got.stderr == ""
        assert json.loads(got.stdout) == {
            "addon": "projects",
            "state": "populated",
            "said": f"2 projects under {home}: 2 records, 1 stack, 2 runs",
            "groups": [
                {"name": "garden", "rows": [
                    {"where": "box", "what": "1 row: 0 asked, 0 approved, 0 waiting"},
                    {"where": "mend.md", "what": "3 steps; last run run-1, nothing flagged"},
                    {"where": "mine/run-0",
                     "what": "a run of no stack that is here now: 2 steps, 1 flagged"},
                ]},
                {"name": "kitchen", "rows": [
                    {"where": "box", "what": "1 row: 0 asked, 0 approved, 0 waiting"},
                ]},
            ],
        }  # fmt: skip
    text = projects("--home", home).stdout
    assert text == ST.report_text(json.loads(got.stdout)) + "\n", "as stack prints it"


def test_the_where_column_is_as_wide_as_its_longest_up_to_sixty(tmp_path):
    home = tmp_path / "home"
    p = home / "garden"
    record(p)
    log(p / ("r" * 60), [], when=2)
    lines = projects("--home", home).stdout.splitlines()
    assert lines[2] == "  box" + " " * 59 + "1 row: 0 asked, 0 approved, 0 waiting"
    assert lines[3].startswith("  " + "r" * 60 + "  a run of no stack")
    log(p / ("s" * 70), [], when=1)
    lines = projects("--home", home).stdout.splitlines()
    assert lines[2] == "  box" + " " * 59 + "1 row: 0 asked, 0 approved, 0 waiting"
    assert lines[4].startswith("  " + "s" * 70 + "  a run of no stack")


def test_it_writes_nothing_and_says_the_same_twice(tmp_path):
    home = tmp_path / "home"
    p = home / "garden"
    b = record(p)
    suggest(b, "Six hours.")
    (p / "mend.md").write_text(MEND)
    (p / "quiet.md").write_text(QUIET)
    log(p / "mine" / "run-1", steps_of(MEND))
    really_run(b, p / "quiet.md", p / "run-2")
    before = snapshot(tmp_path)
    first = projects("--home", home)
    assert projects("--home", home).stdout == first.stdout
    assert projects("--home", home, "--json").returncode == first.returncode == 42
    assert snapshot(tmp_path) == before
