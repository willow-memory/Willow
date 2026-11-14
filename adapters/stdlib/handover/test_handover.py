"""handover: where one project stands, read from what its records and its
stacks' runs kept, said as a report (and --json the same). Runs are made by
really running stack, and by hand where a precise shape is wanted."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
STACK = HERE.parent / "stack" / "stack.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]
QUIET = "nothing waits on you and no step is flagged"


def module(folder: str):
    """Another add-on's module, loaded as handover loads it."""
    path = HERE.parent / folder / f"{folder}.py"
    mod = types.ModuleType(f"test_handover_{folder}")
    mod.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
    return mod


ST, PR = module("stack"), module("projects")


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def handover(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "handover.py"), *map(str, argv)],
        capture_output=True,
        text=True,
    )


def report(p: Path) -> dict:
    return json.loads(handover("--project", p, "--json").stdout)


def groups(p: Path) -> dict[str, list[tuple[str, str]]]:
    """A project's report: each group's rows by the group's name."""
    return {
        g["name"]: [(r["where"], r["what"]) for r in g["rows"]]
        for g in report(p)["groups"]
    }


def project(tmp_path: Path, name: str = "proj") -> Path:
    """A project: a folder holding a record, in a home of its own."""
    pile = tmp_path / "pile"
    if not pile.is_dir():
        pile.mkdir()
        (pile / "garden.md").write_text(
            "Tomatoes want six hours of sun.\n\nWater at the root.\n"
        )
    p = tmp_path / "home" / name
    p.mkdir(parents=True)
    got = k("init", "--box", str(p / "box"), "--pile", str(pile),
            "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return p


def suggest(tmp_path: Path, box: Path, *answers: str) -> None:
    """Suggestions that wait in a record: proposed, and not approved."""
    got = json.loads(
        k("bite", "--box", str(box), *NOW, "how much sun do tomatoes want").stdout
    )
    rows = [
        {
            "path": f"sun{i}.md",
            "data": a,
            "cites": [got["served"][0]["id"]],
            "claim": "garden.md",
        }  # fmt: skip
        for i, a in enumerate(answers)
    ]
    f = tmp_path / f"rows-{box.parent.name}-{box.name}.jsonl"
    f.write_text("".join(json.dumps(r) + "\n" for r in rows))
    k("propose", "--box", str(box), "--file", str(f), *NOW)
    assert PR.tally(box)["waiting"] == len(answers)


def step(name: str, out: str | None = "", *, args: tuple = (), flagged: bool = False,
         kept=None, ended: bool = True) -> dict:  # fmt: skip
    """A step of a run written by hand: what it printed (None: its output is
    gone), and the report kept for it, as data or as the very text."""
    return {"name": name, "out": out, "args": list(args), "flagged": flagged,
            "kept": kept, "ended": ended}  # fmt: skip


def stack_file(p: Path, name: str, steps: list) -> None:
    """A stack file of these steps, each a line stack would run."""
    lines = [
        f"- {s['name']} -- {' '.join(s['args'])}" if s["args"] else f"- {s['name']}"
        for s in steps
    ]
    (p / name).write_text("# a stack\n\n## pool\n" + "\n".join(lines) + "\n")


def run_folder(run: Path, steps: list, finished: bool = True, width: int = 2) -> Path:
    """A run as stack keeps one, written by hand: its log, each step's
    output, and the reports kept as data."""
    run.mkdir(parents=True)
    log = []
    for n, s in enumerate(steps, 1):
        tag = f"{n:0{width}d}"
        log.append(f"{tag} {s['name']}: started ({ST.mark(s['name'], s['args'])})")
        if s["out"] is not None:
            (run / f"{tag}-{s['name']}.txt").write_text(s["out"])
        if s["kept"] is not None:
            (run / "reports").mkdir(exist_ok=True)
            (run / "reports" / f"{tag}-{s['name']}.json").write_text(
                s["kept"] if isinstance(s["kept"], str) else json.dumps(s["kept"])
            )
        if s["ended"]:
            log.append(
                f"{tag} {s['name']}: exit {42 if s['flagged'] else 0}, 1 line"
                + ", flagged" * s["flagged"]
            )
    if finished:
        flagged = sum(s["flagged"] for s in steps)
        log.append(f"done: {flagged} of {len(steps)} steps flagged")
    (run / f"{'0' * width}-stack.txt").write_text("\n".join(log) + "\n")
    return run


def really_run(tmp_path: Path, p: Path, stack: str, to: str) -> None:
    """A run made by stack itself, from the folder above the home."""
    (p / to).mkdir(parents=True)
    got = subprocess.run(
        [sys.executable, str(STACK), "--box", str((p / "box").relative_to(tmp_path)),
         "--stack", str(p / stack), "--to", str(p / to)],
        capture_output=True, text=True, cwd=tmp_path,
    )  # fmt: skip
    assert got.returncode in (0, 42), got.stderr


def work(tmp_path: Path) -> Path:
    """A project whose stack was really run: two report steps (one with
    nothing to list), a step that prints no report, and a step that was
    refused, so flagged."""
    p = project(tmp_path)
    shutil.copytree(p / "box", tmp_path / "quiet" / "calm" / "box")
    inner = tmp_path / "inner.md"
    inner.write_text("## in\n- projects -- --home quiet\n")
    (p / "work.md").write_text(
        "The day's checks.\n\n## checks\n"
        "- projects -- --home {box}\n"
        "- projects -- --home quiet\n"
        f"- stack -- --box {{box}} --stack {inner}\n"
        "- projects -- --home nowhere\n"
    )
    really_run(tmp_path, p, "work.md", "mine/run-1")
    return p


def everything(tmp_path: Path) -> Path:
    """A project with a row for every group."""
    p = project(tmp_path)
    suggest(tmp_path, p / "box", "Six hours.", "Eight hours.")
    ran = [
        step("sort", "sort: 3 files sorted\n"),
        step("glance", "bad\n", flagged=True),
    ]
    stack_file(p, "a-work.md", ran)
    run_folder(p / "mine" / "run-work", ran)
    stack_file(p, "b-full.md", [step("sort"), step("said"), step("todo")])
    c = ("--pile", "c")  # asked another way: another stack's steps, not a-work's
    was = [step("sort", "sorted\n", args=c), step("glance", "seen\n", args=c),
           step("said", "said\n", args=c)]  # fmt: skip
    stack_file(p, "c-start.md", [*was[:2], step("todo")])
    run_folder(p / "mine" / "run-start", was)
    return p


def kept_as_it_is(top: Path) -> dict:
    return {
        str(f.relative_to(top)): f.read_bytes() if f.is_file() else None
        for f in sorted(top.rglob("*"))
    }


def test_a_bad_command_line_is_refused_and_names_the_script():
    got = subprocess.run(
        [sys.executable, str(HERE / "handover.py")], capture_output=True, text=True
    )
    assert got.returncode == 2 and "handover.py" in got.stderr


def test_each_way_a_command_line_can_be_wrong_is_refused(tmp_path):
    p = project(tmp_path)
    for argv in (
        ["--project"],
        ["--project", ""],
        ["--home", p],
        ["--project", p, "more"],
        ["--json", "--project"],
    ):
        got = handover(*argv)
        assert got.returncode == 2 and got.stdout == "", argv
        assert got.stderr == "usage: handover.py --project FOLDER [--json]\n", argv


def test_what_is_not_a_folder_is_refused_by_name(tmp_path):
    for path in (tmp_path / "nowhere", tmp_path / "a-file.md"):
        if path.suffix:
            path.write_text("not a folder\n")
        for more in ([], ["--json"]):
            got = handover("--project", path, *more)
            assert got.returncode == 2 and got.stdout == ""
            assert got.stderr == f"refused: {path} isn't a folder\n"


def test_a_folder_that_holds_no_record_couldnt_be_looked_at_and_says_why(tmp_path):
    p = project(tmp_path)
    bare = p.parent / "bare"
    bare.mkdir()
    stack_file(bare, "work.md", [step("sort")])  # stacks, but no record
    said = f"{bare} holds no record, so it is no project"
    got = handover("--project", bare)
    assert (got.returncode, got.stdout, got.stderr) == (
        42,
        f"handover: unreachable, {said}\n",
        "",
    )
    data = handover("--project", bare, "--json")
    assert data.returncode == 42 and json.loads(data.stdout) == {
        "addon": "handover", "state": "unreachable", "said": said, "groups": []
    }  # fmt: skip


def test_it_reports_the_project_named_not_the_one_beside_it(tmp_path):
    p = project(tmp_path)
    first = project(tmp_path, "first")  # sorts before it, and has a suggestion
    suggest(tmp_path, first / "box", "Six hours.")
    got = handover("--project", p)
    assert got.returncode == 0 and got.stdout == f"handover: empty, proj: {QUIET}\n"
    assert report(first)["said"] == "first: 1 suggestion waits on you"


def test_a_project_with_nothing_waiting_and_nothing_flagged_says_so(tmp_path):
    p = project(tmp_path)
    got = handover("--project", p)
    assert (got.returncode, got.stdout, got.stderr) == (
        0,
        f"handover: empty, proj: {QUIET}\n",
        "",
    )
    data = handover("--json", "--project", p)  # --json may come first
    assert data.returncode == 0 and json.loads(data.stdout) == {
        "addon": "handover", "state": "empty", "said": f"proj: {QUIET}", "groups": []
    }  # fmt: skip
    assert data.stdout.count("\n") == 1  # one object, on one line


def test_a_project_can_be_named_from_where_you_stand(tmp_path):
    p = project(tmp_path)
    got = subprocess.run(
        [sys.executable, str(HERE / "handover.py"), "--project", "."],
        capture_output=True, text=True, cwd=p,
    )  # fmt: skip
    assert got.returncode == 0 and got.stdout == f"handover: empty, proj: {QUIET}\n"


def test_one_suggestion_waits_and_two_wait(tmp_path):
    p = project(tmp_path)
    suggest(tmp_path, p / "box", "Six hours.")
    got = handover("--project", p)
    assert got.returncode == 42
    rows = PR.tally(p / "box")["rows"]
    assert got.stdout == (
        "handover: populated, proj: 1 suggestion waits on you\n"
        "## waits on you\n"
        f"  box  1 suggestion waiting, of {rows} rows\n"
    )
    two = project(tmp_path, "two")
    suggest(tmp_path, two / "box", "Six hours.", "Eight hours.")
    doc = report(two)
    assert doc["said"] == "two: 2 suggestions wait on you"
    assert doc["groups"] == [{"name": "waits on you", "rows": [
        {"where": "box", "what": f"2 suggestions waiting, of {rows + 1} rows"}]}]  # fmt: skip


def test_suggestions_are_added_up_over_every_record_and_a_quiet_record_has_no_row(
    tmp_path,
):
    p = project(tmp_path)
    for name in ("again", "calm"):
        shutil.copytree(p / "box", p / name)
    suggest(tmp_path, p / "box", "Six hours.", "Eight hours.")
    suggest(tmp_path, p / "again", "Six hours.")
    doc = report(p)
    assert doc["said"] == "proj: 3 suggestions wait on you"
    assert [r["where"] for r in doc["groups"][0]["rows"]] == ["again", "box"]


def test_a_record_whose_chain_is_broken_waits_on_you_and_is_not_counted_as_a_suggestion(
    tmp_path,
):
    p = project(tmp_path)
    suggest(tmp_path, p / "box", "Six hours.")
    record = p / "box" / "record.jsonl"
    record.write_bytes(
        record.read_bytes().replace(b'"verdict":"pass"', b'"verdict":"fail"', 1)
    )
    why = PR.tally(p / "box")["broken"]
    got = handover("--project", p)
    assert got.returncode == 42 and why
    assert got.stdout == (
        "handover: populated, proj: 1 record broken\n"
        "## waits on you\n"
        f"  box  its chain is broken: {why}\n"
    )
    shutil.copytree(tmp_path / "home" / "proj" / "box", p / "also")
    ok = project(tmp_path, "ok")
    shutil.move(str(ok / "box"), str(p / "fine"))
    suggest(tmp_path, p / "fine", "Six hours.", "Eight hours.")
    doc = report(p)
    assert doc["said"] == "proj: 2 suggestions wait on you, 2 records broken"
    assert [r["where"] for r in doc["groups"][0]["rows"]] == ["also", "box", "fine"]


def test_a_stack_really_run_is_said_step_by_step_with_its_flagged_steps_first(tmp_path):
    p = work(tmp_path)
    got = handover("--project", p)
    assert got.returncode == 42 and got.stderr == ""
    assert got.stdout == (
        "handover: populated, proj: 1 step flagged, 1 stack run\n"
        "## flagged\n"
        "  work.md step 04  projects: refused: nowhere isn't a folder (mine/run-1/04-projects.txt)\n"
        "## last runs\n"
        "  work.md          mine/run-1: 4 steps, 1 flagged\n"
        "  work.md step 01  projects: empty, no folder under home/proj/box holds a record\n"
        "  work.md step 02  projects: populated, 1 project under quiet: 1 record, 0 stacks, 0 runs\n"
        "  work.md step 03  stack: # stack over home/proj/box: 1 step in 1 pool, peaks first\n"
    )  # fmt: skip
    # every flagged line names a file that is there, and holds what was said
    for row in groups(p)["flagged"]:
        said, _, where = row[1].rpartition(" (")
        assert said.split(": ", 1)[1].split(", ")[-1] in (p / where[:-1]).read_text()


def test_the_text_is_the_json_report_as_every_report_is_printed(tmp_path):
    p = work(tmp_path)
    suggest(tmp_path, p / "box", "Six hours.")
    text, data = handover("--project", p), handover("--project", p, "--json")
    assert text.returncode == data.returncode == 42
    doc = json.loads(data.stdout)
    assert text.stdout == ST.report_text(doc) + "\n"
    assert list(doc) == ["addon", "state", "said", "groups"]
    assert (doc["addon"], doc["state"]) == ("handover", "populated")
    assert [g["name"] for g in doc["groups"]] == [
        "waits on you",
        "flagged",
        "last runs",
    ]
    assert all(list(g) == ["name", "rows"] and g["rows"] for g in doc["groups"])
    assert all(list(r) == ["where", "what"] for g in doc["groups"] for r in g["rows"])
    assert handover("--project", p, "--json").stdout == data.stdout  # the same twice


def test_a_step_whose_report_is_gone_is_said_by_its_outputs_first_line(tmp_path):
    p = work(tmp_path)
    before = groups(p)
    shutil.rmtree(p / "mine" / "run-1" / "reports")
    # the step's name is taken off the front: the line reads as the report's did
    assert groups(p) == before


def test_a_file_a_stack_was_given_that_has_changed_is_said(tmp_path):
    p = work(tmp_path)
    assert "changed since its last run" not in groups(p)
    (tmp_path / "inner.md").write_text("## in\n- projects -- --home quiet\n\nA note.\n")
    doc = report(p)
    assert doc["groups"][-1] == {"name": "changed since its last run", "rows": [
        {"where": "work.md", "what": "a file it was given is not as it was"}]}  # fmt: skip
    assert doc["said"] == "proj: 1 step flagged, 1 stack run"
    assert handover("--project", p).stdout.splitlines()[-2:] == [
        "## changed since its last run",
        "  work.md          a file it was given is not as it was",
    ]


def test_a_stack_whose_steps_are_not_what_its_run_ran_is_said(tmp_path):
    p = project(tmp_path)
    was = [step("sort", "sorted\n"), step("glance", "seen\n"), step("said", "said\n")]
    stack_file(p, "start.md", [*was[:2], step("todo")])
    run_folder(p / "mine" / "run-3", was)
    got = handover("--project", p)
    assert got.returncode == 0
    assert got.stdout == (
        f"handover: populated, proj: {QUIET}, 1 stack run\n"
        "## last runs\n"
        "  start.md          mine/run-3: 3 steps, nothing flagged\n"
        "  start.md step 01  sort: sorted\n"
        "  start.md step 02  glance: seen\n"
        "  start.md step 03  said: said\n"
        "## changed since its last run\n"
        "  start.md          its steps are not what mine/run-3 ran\n"
    )


def test_a_run_of_no_stack_that_is_here_is_not_handed_on_as_one(tmp_path):
    p = project(tmp_path)
    stack_file(p, "work.md", [step("sort"), step("glance")])
    run_folder(p / "mine" / "run-1", [step("todo", "x\n"), step("said", "y\n")])
    assert groups(p) == {"never run": [("work.md", "2 steps")]}


def test_a_stack_never_run_is_listed_with_its_steps(tmp_path):
    p = project(tmp_path)
    stack_file(p, "full.md", [step("sort"), step("glance"), step("said")])
    stack_file(p, "one.md", [step("sort")])
    (p / "notes.md").write_text("Notes, and no steps.\n")  # no stack: not listed
    got = handover("--project", p)
    assert got.returncode == 0
    assert got.stdout == (
        f"handover: populated, proj: {QUIET}, 2 stacks never run\n"
        "## never run\n"
        "  full.md  3 steps\n"
        "  one.md   1 step\n"
    )
    (p / "one.md").unlink()
    assert report(p)["said"] == f"proj: {QUIET}, 1 stack never run"


def test_every_group_in_its_order_and_the_first_line_counts_each(tmp_path):
    p = everything(tmp_path)
    rows = PR.tally(p / "box")["rows"]
    got = handover("--project", p)
    assert got.returncode == 42
    assert got.stdout == (
        "handover: populated, proj: 2 suggestions wait on you, 1 step flagged, "
        "2 stacks run, 1 stack never run\n"
        "## waits on you\n"
        f"  box                 2 suggestions waiting, of {rows} rows\n"
        "## flagged\n"
        "  a-work.md step 02   glance: bad (mine/run-work/02-glance.txt)\n"
        "## last runs\n"
        "  a-work.md           mine/run-work: 2 steps, 1 flagged\n"
        "  a-work.md step 01   sort: 3 files sorted\n"
        "  c-start.md          mine/run-start: 3 steps, nothing flagged\n"
        "  c-start.md step 01  sort: sorted\n"
        "  c-start.md step 02  glance: seen\n"
        "  c-start.md step 03  said: said\n"
        "## never run\n"
        "  b-full.md           3 steps\n"
        "## changed since its last run\n"
        "  c-start.md          its steps are not what mine/run-start ran\n"
    )


def test_a_flagged_step_alone_waits_on_you_and_a_clean_run_does_not(tmp_path):
    p = project(tmp_path)
    ran = [step("sort", "fine\n"), step("glance", "seen\n")]
    stack_file(p, "work.md", ran)
    run_folder(p / "run-1", ran)  # a run in the project's own folder
    got = handover("--project", p)
    assert got.returncode == 0
    assert got.stdout.splitlines()[:3] == [
        f"handover: populated, proj: {QUIET}, 1 stack run",
        "## last runs",
        "  work.md          run-1: 2 steps, nothing flagged",
    ]
    bad = project(tmp_path, "bad")
    ran = [step("sort", "fine\n", flagged=True), step("glance", "seen\n", flagged=True)]
    stack_file(bad, "work.md", ran)
    run_folder(bad / "run-1", ran)
    got = handover("--project", bad)
    assert got.returncode == 42
    assert (
        got.stdout.splitlines()[0]
        == "handover: populated, bad: 2 steps flagged, 1 stack run"
    )
    assert groups(bad)["flagged"] == [
        ("work.md step 01", "sort: fine (run-1/01-sort.txt)"),
        ("work.md step 02", "glance: seen (run-1/02-glance.txt)"),
    ]
    assert groups(bad)["last runs"] == [("work.md", "run-1: 2 steps, 2 flagged")]


def test_a_stack_is_said_by_its_newest_run(tmp_path):
    p = project(tmp_path)
    ran = [step("sort", "the first go\n")]
    stack_file(p, "work.md", ran)
    old = run_folder(p / "mine" / "run-1", ran)
    new = run_folder(p / "run-0", [step("sort", "the second go\n", flagged=True)])
    os.utime(old / "00-stack.txt", (1_000_000, 1_000_000))
    os.utime(new / "00-stack.txt", (2_000_000, 2_000_000))
    assert groups(p) == {
        "flagged": [("work.md step 01", "sort: the second go (run-0/01-sort.txt)")],
        "last runs": [("work.md", "run-0: 1 step, 1 flagged")],
    }
    assert report(p)["said"] == "proj: 1 step flagged, 1 stack run"
    os.utime(old / "00-stack.txt", (3_000_000, 3_000_000))
    assert groups(p) == {
        "last runs": [("work.md", "mine/run-1: 1 step, nothing flagged"),
                      ("work.md step 01", "sort: the first go")],
    }  # fmt: skip


def test_a_run_that_was_cut_off_says_so_and_has_no_row_for_the_step_it_was_in(tmp_path):
    p = project(tmp_path)
    ran = [step("sort", "fine\n"), step("glance", "half a li", ended=False)]
    stack_file(p, "work.md", [*ran, step("said")])
    run_folder(p / "mine" / "run-1", ran, finished=False)
    assert groups(p) == {
        "last runs": [("work.md", "mine/run-1: 2 steps, nothing flagged, not finished"),
                      ("work.md step 01", "sort: fine")],
    }  # fmt: skip


def test_a_step_is_said_by_its_kept_report_before_its_output(tmp_path):
    p = project(tmp_path)
    doc = {
        "addon": "todo",
        "state": "populated",
        "said": "2 to do, 1 done",
        "groups": [],
    }
    ran = [
        step("todo", "todo: something else\n", kept=doc),
        step("sort", "sort: from its output\n", kept="{not json"),
        step("glance", "glance: no said in it\n", kept={"state": "empty"}),
        step("said", "said: no state in it\n", kept={"said": "x"}),
    ]
    stack_file(p, "work.md", ran)
    run_folder(p / "mine" / "run-1", ran)
    assert groups(p)["last runs"][1:] == [
        ("work.md step 01", "todo: populated, 2 to do, 1 done"),
        ("work.md step 02", "sort: from its output"),
        ("work.md step 03", "glance: no said in it"),
        ("work.md step 04", "said: no state in it"),
    ]


def test_a_step_with_no_report_is_said_by_its_first_line_that_is_not_blank(tmp_path):
    p = project(tmp_path)
    ran = [
        step("sort", "\n   \n  435 files: 271 sorted  \nand more\n"),
        step("glance", "glance: glance: 18 questions\n"),  # its name comes off once
        step("said", "sort: said by another\n"),  # another's name stays
        step("todo", "to do, todo: 3\n"),  # and only from the front
        step("amounts", "\n \n"),
        step("stale", ""),
        step("rank", None),
        step("mirror", '{"path": "a.md"}\n{"path": "b.md"}\n\n{"path": "c.md"}\n'),
    ]
    stack_file(p, "work.md", ran)
    run_folder(p / "mine" / "run-1", ran)
    assert groups(p)["last runs"][1:] == [
        ("work.md step 01", "sort: 435 files: 271 sorted"),
        ("work.md step 02", "glance: glance: 18 questions"),
        ("work.md step 03", "said: sort: said by another"),
        ("work.md step 04", "todo: to do, todo: 3"),
        ("work.md step 05", "amounts: said nothing"),
        ("work.md step 06", "stale: said nothing"),
        ("work.md step 07", "rank: its output is gone"),
        ("work.md step 08", "mirror: 4 lines for a program"),
    ]


def test_a_long_line_is_cut_at_a_word_and_one_that_fits_is_whole(tmp_path):
    p = project(tmp_path)
    fits = "a b " + "x" * 106  # 110 characters
    over = "a b " + "x" * 100 + " yyyyy z"  # 112: cut where the last word began
    one = "x" * 111  # no word to cut at
    assert (len(fits), len(over)) == (110, 112)
    long = {
        "state": "populated",
        "said": "a long thing said " + "w" * 70 + " and on and on and on",
    }
    ran = [
        step("sort", fits + "\n"),
        step("glance", over + "\n"),
        step("said", one + "\n"),
        step("todo", "short\n", kept=long),
        step("stale", "stale: " + fits + "\n"),  # measured with its name off
    ]
    stack_file(p, "work.md", ran)
    run_folder(p / "mine" / "run-1", ran)
    assert groups(p)["last runs"][1:] == [
        ("work.md step 01", f"sort: {fits}"),
        ("work.md step 02", "glance: a b " + "x" * 100 + "…"),
        ("work.md step 03", "said: " + "x" * 110 + "…"),
        (
            "work.md step 04",
            "todo: populated, a long thing said " + "w" * 70 + " and on…",
        ),
        ("work.md step 05", f"stale: {fits}"),
    ]


def test_a_flagged_step_is_cut_the_same_and_still_names_its_file(tmp_path):
    p = project(tmp_path)
    ran = [step("sort", "a b " + "x" * 100 + " yyyyy z\n", flagged=True)]
    stack_file(p, "work.md", ran)
    run_folder(p / "mine" / "run-1", ran)
    assert groups(p)["flagged"] == [
        ("work.md step 01", "sort: a b " + "x" * 100 + "… (mine/run-1/01-sort.txt)")
    ]


def test_eight_clean_steps_have_a_row_each_and_nine_are_said_by_what_ran(tmp_path):
    p = project(tmp_path)
    names = ["sort", "glance", "sort", "said", "todo", "glance", "sort", "stale"]
    eight = [step(n, f"{n} {i}\n", args=(f"--n={i}",)) for i, n in enumerate(names)]
    stack_file(p, "work.md", eight)
    run_folder(p / "mine" / "run-8", eight)
    last = groups(p)["last runs"]
    assert len(last) == 9 and last[0] == (
        "work.md",
        "mine/run-8: 8 steps, nothing flagged",
    )
    assert last[1] == ("work.md step 01", "sort: sort 0")
    assert last[8] == ("work.md step 08", "stale: stale 7")

    long = project(tmp_path, "long")
    nine = [*eight, step("rank", "rank 8\n")]
    stack_file(long, "work.md", nine)
    run_folder(long / "mine" / "run-9", nine)
    got = handover("--project", long)
    assert got.returncode == 0
    assert got.stdout == (
        f"handover: populated, long: {QUIET}, 1 stack run\n"
        "## last runs\n"
        "  work.md        mine/run-9: 9 steps, nothing flagged\n"
        "  work.md steps  sort ×3, glance ×2, said, todo, stale, rank: each in mine/run-9\n"
    )


def test_it_is_the_clean_steps_that_are_counted_and_a_flagged_one_always_has_its_row(
    tmp_path,
):
    p = project(tmp_path)
    names = ["sort", "glance", "said", "todo", "stale", "rank", "mirror", "amounts"]
    ran = [step(n, f"{n} ran\n") for n in names] + [
        step("pii", "a number\n", flagged=True)
    ]
    stack_file(p, "work.md", ran)
    run_folder(p / "mine" / "run-1", ran)
    got = groups(p)
    assert got["flagged"] == [
        ("work.md step 09", "pii: a number (mine/run-1/09-pii.txt)")
    ]
    assert len(got["last runs"]) == 9  # eight clean: a row each

    long = project(tmp_path, "long")
    ran = [*ran, step("sort", "sort again\n", args=("--again",))]
    stack_file(long, "work.md", ran)
    run_folder(long / "mine" / "run-1", ran)
    got = groups(long)
    assert got["flagged"] == [
        ("work.md step 09", "pii: a number (mine/run-1/09-pii.txt)")
    ]
    assert got["last runs"] == [
        ("work.md", "mine/run-1: 10 steps, 1 flagged"),
        ("work.md steps", "sort ×2, glance, said, todo, stale, rank, mirror, amounts: each in mine/run-1"),
    ]  # fmt: skip
    assert report(long)["said"] == "long: 1 step flagged, 1 stack run"


def test_a_run_of_a_hundred_steps_numbers_them_in_three_places(tmp_path):
    p = project(tmp_path)
    ran = [step("sort", "fine\n"), step("glance", "bad\n", flagged=True)]
    stack_file(p, "work.md", ran)
    run_folder(p / "mine" / "run-1", ran, width=3)
    assert groups(p) == {
        "flagged": [("work.md step 002", "glance: bad (mine/run-1/002-glance.txt)")],
        "last runs": [("work.md", "mine/run-1: 2 steps, 1 flagged"),
                      ("work.md step 001", "sort: fine")],
    }  # fmt: skip


def test_a_stack_named_for_its_steps_is_still_counted_as_run(tmp_path):
    p = project(tmp_path)
    ran = [step("sort", "fine\n")]
    for name in ("next steps.md", "two step.md"):
        stack_file(p, name, ran)
    run_folder(p / "mine" / "run-1", ran)
    doc = report(p)
    assert doc["said"] == f"proj: {QUIET}, 1 stack run, 1 stack never run"
    assert [g["name"] for g in doc["groups"]] == ["last runs", "never run"]


def test_the_place_column_is_as_wide_as_its_longest_up_to_sixty(tmp_path):
    p = project(tmp_path)
    stack_file(p, "a.md", [step("sort")])
    stack_file(p, "b" * 57 + ".md", [step("sort"), step("said")])  # sixty
    assert handover("--project", p).stdout.splitlines()[2:] == [
        "  a.md" + " " * 56 + "  1 step",
        "  " + "b" * 57 + ".md  2 steps",
    ]
    stack_file(p, "c" * 58 + ".md", [step("sort"), step("said"), step("todo")])
    assert handover("--project", p).stdout.splitlines()[2:] == [
        "  a.md" + " " * 56 + "  1 step",
        "  " + "b" * 57 + ".md  2 steps",
        "  " + "c" * 58 + ".md  3 steps",
    ]


def test_it_reads_and_never_writes(tmp_path):
    p = everything(tmp_path)
    before = kept_as_it_is(tmp_path)
    assert handover("--project", p).returncode == 42
    assert handover("--project", p, "--json").returncode == 42
    assert handover("--project", p.parent).returncode == 42  # no project: couldn't look
    assert kept_as_it_is(tmp_path) == before


def test_a_record_with_no_stack_and_nothing_waiting_is_an_empty_report(tmp_path):
    p = tmp_path / "home" / "fresh"
    p.mkdir(parents=True)
    pile = p / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("Tomatoes want sun.\n")
    subprocess.run(
        [sys.executable, str(KERNEL), "init", "--box", str(p / "box"), "--pile",
         str(pile), "--key", str(tmp_path / "key"), "--now", "2026-10-23T00:00:00Z"],
        check=True, capture_output=True,
    )  # fmt: skip
    got = handover("--project", p, "--json")
    assert got.returncode == 0, got.stderr
    doc = json.loads(got.stdout)
    assert doc["state"] == "empty" and doc["groups"] == []
    assert doc["said"] == f"fresh: {QUIET}"
    text = handover("--project", p)
    assert text.stdout == f"handover: empty, fresh: {QUIET}\n"
