"""mutants: a break the tests miss fails the add-on; an accepted one doesn't;
a stale acceptance does; ids don't move with the lines; the repo is never
touched. A check that can't fail is no check (CONST-IV-9)."""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("willow_mutants", HERE / "mutants.py")
mu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mu)

TOY = """import sys


def big(n):
    return n > 10
"""
CAUGHT = """import sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import toy


def test_big():
    assert toy.big(11) and not toy.big(10)
"""
MISSED = """import sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import toy


def test_big():
    assert toy.big(100)
"""


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A repo with one add-on, toy, its code one comparison and one number."""
    root = tmp_path / "repo"
    here = root / "adapters" / "stdlib" / "toy"
    here.mkdir(parents=True)
    shutil.copy(HERE.parents[2] / "kernel.py", root / "kernel.py")
    (here / "toy.py").write_text(TOY)
    accepted = tmp_path / "accepted.json"
    accepted.write_text("{}")
    monkeypatch.setattr(mu, "ROOT", root)
    monkeypatch.setattr(mu, "STDLIB", root / "adapters" / "stdlib")
    monkeypatch.setattr(mu, "ACCEPTED", accepted)
    return here, accepted


def test_breaks_the_tests_catch_pass(repo, capsys):
    here, _ = repo
    (here / "test_toy.py").write_text(CAUGHT)
    assert mu.run(["toy"], 6) == 0
    assert "toy: 2 of 2 killed" in capsys.readouterr().out


def test_a_break_the_tests_miss_fails_until_accepted_with_a_reason(repo, capsys):
    here, accepted = repo
    (here / "test_toy.py").write_text(MISSED)
    assert mu.run(["toy"], 6) == 2
    out = capsys.readouterr().out
    survivors = [ln.split()[1] for ln in out.splitlines() if "survived" in ln]
    assert survivors and "toy.py:5" in out
    accepted.write_text(json.dumps({"toy": {s: "a reason" for s in survivors}}))
    assert mu.run(["toy"], 6) == 0
    (here / "test_toy.py").write_text(CAUGHT)  # the tests got better
    assert mu.run(["toy"], 6) == 2
    assert "stale" in capsys.readouterr().out


def test_tests_that_cant_run_kill_nothing(repo, capsys):
    here, _ = repo
    (here / "test_toy.py").write_text("import no_such_module\n")
    assert mu.run(["toy"], 6) == 2
    assert "couldn't run" in capsys.readouterr().out


def test_ids_stay_when_lines_move_and_the_repo_is_never_touched(repo):
    here, _ = repo
    (here / "test_toy.py").write_text(CAUGHT)
    before = {m["id"] for m in mu.mutants("toy")}
    (here / "toy.py").write_text("# a comment above\n\n" + TOY)
    assert {m["id"] for m in mu.mutants("toy")} == before
    source = (here / "toy.py").read_text()
    mu.run(["toy"], 6)
    assert (here / "toy.py").read_text() == source


def test_each_kind_of_break():
    src = "x = a == b and c in d\ny = 3\n"
    kinds = {k for k, _ in mu.points(__import__("ast").parse(src))}
    assert kinds == {"compare", "and-or", "number"}
    made = {
        mu.broken(src, i) for i in range(len(mu.points(__import__("ast").parse(src))))
    }
    assert "x = a != b and c in d\ny = 3\n" in made
    assert "x = a == b or c in d\ny = 3\n" in made
    assert "x = a == b and c not in d\ny = 3\n" in made
    assert "x = a == b and c in d\ny = 4\n" in made


TWINS = """def a():
    return 1


def b():
    return 1
"""
ONLY_B = """import sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import toy


def test_b():
    assert toy.b() == 1
"""


def test_a_mutant_never_runs_the_last_ones_cached_code(repo, capsys):
    """Breaking a's 1 and then b's 1 makes two files of the same size, often
    in the same second. Python's bytecode cache would serve the second the
    first's code, b's break would pass as a survivor, and the count would
    depend on the clock. Only a's break survives."""
    here, _ = repo
    (here / "toy.py").write_text(TWINS)
    (here / "test_toy.py").write_text(ONLY_B)
    assert mu.run(["toy"], 6) == 2
    out = capsys.readouterr().out
    assert "toy: 1 of 2 killed" in out
    assert out.count("survived") == 1 and "toy.py:2" in out


def test_the_entry_guard_is_never_broken():
    src = 'if __name__ == "__main__":\n    x = a == b\n'
    compares = [n for k, n in mu.points(__import__("ast").parse(src)) if k == "compare"]
    assert len(compares) == 1 and compares[0].left.id == "a"


def test_the_copy_leaves_out_a_demos_life_but_not_an_add_on_named_life():
    demo = mu.ROOT / "demo" / "odile"
    assert mu.skipped(str(demo), ["life", "make_life.py"]) == {"life"}
    assert mu.skipped(str(mu.ROOT / "adapters" / "stdlib"), ["life", "dice"]) == set()
    assert mu.skipped(str(mu.ROOT / "ports"), ["bin", "obj", "src"]) == {"bin", "obj"}
