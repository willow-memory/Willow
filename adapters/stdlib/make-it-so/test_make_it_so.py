"""make-it-so: an order held, never carried out; the plan checked against the
files it cited; a plan never written over, inside the box or its pile; a bad
command line refused."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "make_it_so.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-30T00:00:00Z"]
GARDEN = "Notes\n\nTomatoes want six hours of sun.\nWater them daily.\n\nThe bins go out on Thursday night.\n"
ASK = "how much sun do tomatoes want"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def box(tmp_path: Path, words: str | None = None) -> tuple[Path, Path]:
    pile = tmp_path / "pile"
    (pile / "notes").mkdir(parents=True)
    (pile / "notes" / "garden.md").write_text(GARDEN)
    b = tmp_path / "box"
    argv = [
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    ]
    if words is not None:
        (tmp_path / "w.txt").write_text(words)
        (tmp_path / "w.txt").chmod(0o600)
        argv += ["--words", str(tmp_path / "w.txt")]
    got = subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )
    assert got.returncode == 0, got.stderr
    return b, pile


def plan(b: Path, to: Path, cmd: str = "echo hi", q: str = ASK, *more: str):
    return run("plan", "--box", str(b), "--to", str(to), "--cmd", cmd, *NOW, *more, q)


def test_a_plan_holds_the_order_the_command_as_given_and_what_it_rests_on(tmp_path):
    b, pile = box(tmp_path)
    to = tmp_path / "plan.json"
    got = plan(b, to, "sed -i 's/six/eight/' notes/garden.md")
    assert got.returncode == 0, got.stderr
    order = json.loads(to.read_text())
    sha = hashlib.sha256((pile / "notes" / "garden.md").read_bytes()).hexdigest()
    assert order["made"] == "2026-10-30T00:00:00Z" and order["order"] == ASK
    assert order["command"] == "sed -i 's/six/eight/' notes/garden.md"
    assert (
        order["command_sha256"] == hashlib.sha256(order["command"].encode()).hexdigest()
    )
    first = order["passages"][0]
    assert first["path"] == "notes/garden.md" and first["line"] == 3
    assert first["file_sha256"] == sha and first["id"]
    lines = got.stdout.splitlines()
    assert lines[0] == f"order: {ASK}"
    assert lines[1] == "command (not run): sed -i 's/six/eight/' notes/garden.md"
    assert lines[2] == "  notes/garden.md:3  Tomatoes want six hours of sun."
    assert lines[-1].endswith("nothing was run. The command is yours to run.")


def test_the_command_is_never_run(tmp_path):
    b, _ = box(tmp_path)
    ran = tmp_path / "ran"
    got = plan(b, tmp_path / "plan.json", f"touch {ran}")
    assert got.returncode == 0 and not ran.exists()
    assert run("check", "--box", str(b), str(tmp_path / "plan.json")).returncode == 0
    assert not ran.exists()


def test_a_plan_is_private_deterministic_and_never_written_over(tmp_path):
    b, _ = box(tmp_path)
    one, two = tmp_path / "one.json", tmp_path / "two.json"
    assert plan(b, one).returncode == 0 and plan(b, two).returncode == 0
    assert one.read_bytes() == two.read_bytes() and one.stat().st_mode & 0o777 == 0o600
    before = one.read_bytes()
    again = plan(b, one, "echo other")
    assert again.returncode == 2 and again.stderr.startswith("refused:")
    assert one.read_bytes() == before and again.stdout == ""


def test_a_plan_inside_the_box_or_its_pile_or_in_a_missing_folder_is_refused(tmp_path):
    b, pile = box(tmp_path)
    for to in (b / "plan.json", pile / "plan.json", pile / "notes" / "p.json"):
        got = plan(b, to)
        assert got.returncode == 2 and "inside the box or its pile" in got.stderr
        assert not to.exists()
    missing = tmp_path / "nope" / "plan.json"
    got = plan(b, missing)
    assert got.returncode == 2 and not missing.parent.exists()


def test_a_question_nothing_holds_writes_no_order(tmp_path):
    b, _ = box(tmp_path)
    to = tmp_path / "plan.json"
    got = plan(b, to, "echo hi", "zzz qqq unknown words")
    assert got.returncode == 42 and not to.exists()
    assert got.stdout == "no passage holds that; no order was written\n"


def test_the_limit_caps_the_passages_an_order_rests_on(tmp_path):
    b, pile = box(tmp_path)
    (pile / "notes" / "more.md").write_text("Tomatoes also want sun in the morning.\n")
    one, many = tmp_path / "one.json", tmp_path / "many.json"
    assert plan(b, one, "echo hi", ASK, "--limit", "1").returncode == 0
    assert plan(b, many).returncode == 0
    assert len(json.loads(one.read_text())["passages"]) == 1
    assert len(json.loads(many.read_text())["passages"]) == 2


def test_a_bad_command_line_is_refused(tmp_path):
    b, _ = box(tmp_path)
    to = str(tmp_path / "plan.json")
    base = ["plan", "--box", str(b), "--to", to, "--cmd", "echo hi"]
    bad = [
        ["plan"],
        ["plan", "--box", str(b), "--to", to, ASK],
        ["plan", "--box", str(b), "--cmd", "echo hi", ASK],
        ["plan", "--to", to, "--cmd", "echo hi", ASK],
        ["plan", "--box", str(b), "--to", to, "--cmd", "  ", ASK],
        [*base],
        [*base, "  "],
        [*base, ASK, "extra"],
        [*base, "--sun"],
        [*base, "--limit", "0", ASK],
        [*base, "--limit", "21", ASK],
        [*base, "--limit", "many", ASK],
        [*base, "--box", str(b), ASK],
        ["check"],
        ["check", "--box", str(b)],
        ["check", "--box", str(b), to, "extra"],
        ["check", "--box", str(b), "--plan"],
        ["nonsense"],
        [],
    ]
    for argv in bad:
        got = run(*argv)
        assert got.returncode == 2 and got.stderr.startswith("refused:"), argv
        assert got.stdout == "", argv
    assert not Path(to).exists()


def test_something_that_is_not_a_box_is_refused(tmp_path):
    (tmp_path / "plain").mkdir()
    got = plan(tmp_path / "plain", tmp_path / "plan.json")
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    got = run("check", "--box", str(tmp_path / "plain"), str(tmp_path / "plan.json"))
    assert got.returncode == 2 and "not a kernel box" in got.stderr


def test_the_boxs_words_list_is_used_and_a_list_that_does_not_read_is_refused(tmp_path):
    b, _ = box(tmp_path, words="sunshine = sun\n")
    to = tmp_path / "plan.json"
    assert plan(b, to, "echo hi", "sunshine").returncode == 0
    assert json.loads(to.read_text())["passages"][0]["line"] == 3
    (tmp_path / "w.txt").write_text("not a list line\n")
    bad = plan(b, tmp_path / "other.json", "echo hi", "sunshine")
    assert bad.returncode == 2 and not (tmp_path / "other.json").exists()


def test_a_plan_holds_until_a_cited_file_changes_or_goes(tmp_path):
    b, pile = box(tmp_path)
    to = tmp_path / "plan.json"
    assert plan(b, to).returncode == 0
    ok = run("check", "--box", str(b), str(to))
    assert ok.returncode == 0 and ok.stdout == "holds\n"
    (pile / "notes" / "garden.md").write_text(GARDEN + "More.\n")
    changed = run("check", "--box", str(b), str(to))
    assert changed.returncode == 42
    assert changed.stdout.splitlines() == [
        "changed: notes/garden.md",
        "the plan no longer holds: 1 of 1 files differ",
    ]
    (pile / "notes" / "garden.md").unlink()
    gone = run("check", "--box", str(b), str(to))
    assert gone.returncode == 42 and gone.stdout.startswith("gone: notes/garden.md\n")


def test_a_plan_that_was_edited_or_is_not_one_is_refused(tmp_path):
    b, _ = box(tmp_path)
    to = tmp_path / "plan.json"
    assert plan(b, to).returncode == 0
    good = json.loads(to.read_text())
    cases = {
        "swapped command": {**good, "command": "rm -rf ~"},
        "no passages": {**good, "passages": []},
        "passages not a list": {**good, "passages": "x"},
        "no command": {k: v for k, v in good.items() if k != "command"},
        "a path out": {
            **good,
            "passages": [{**good["passages"][0], "path": "../box/kernel.json"}],
        },
        "a list": [1, 2],
    }
    for name, doc in cases.items():
        (tmp_path / "x.json").write_text(json.dumps(doc))
        got = run("check", "--box", str(b), str(tmp_path / "x.json"))
        assert got.returncode == 2 and got.stderr.startswith("refused:"), name
        assert got.stdout == "", name
    (tmp_path / "x.json").write_text("not json")
    assert run("check", "--box", str(b), str(tmp_path / "x.json")).returncode == 2
    assert run("check", "--box", str(b), str(tmp_path / "none.json")).returncode == 2


def test_it_changes_nothing_but_the_plan(tmp_path):
    b, _ = box(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    to = tmp_path / "plan.json"
    assert plan(b, to).returncode == 0
    run("check", "--box", str(b), str(to))
    after = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert set(after) - set(before) == {to}
    assert all(after[p] == before[p] for p in before)
