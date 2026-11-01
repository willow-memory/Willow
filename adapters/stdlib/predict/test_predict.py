"""predict: what a question will come to, written on the chain before it is
asked, counted from the earlier bites, never guessed, and graded after."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "predict.py"
spec = importlib.util.spec_from_file_location("predict", SCRIPT)
pr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr)
NOW = ["--now", "2026-10-24T09:00:00Z"]


def run(*argv: str, script: Path = SCRIPT) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *argv],
                          capture_output=True, text=True)  # fmt: skip


def make(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text(
        "Tomatoes want six hours of sun.\n\nThe bees swarmed in May.\n"
    )
    box = tmp_path / "box"
    got = run("init", "--box", str(box), "--pile", str(pile),
              "--key", str(tmp_path / "key"), *NOW, script=KERNEL)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return box


def rows(box: Path) -> list[dict]:
    got, breaks = pr.kernel.read(box / "record.jsonl")
    assert breaks == []
    return got


def ask(box: Path, question: str) -> tuple[int, dict]:
    got = run("ask", "--box", str(box), *NOW, question)
    return got.returncode, json.loads(got.stdout)


def test_the_prediction_is_on_the_chain_before_the_bite(tmp_path):
    box = make(tmp_path)
    code, doc = ask(box, "bees swarm")
    assert code == 0 and doc["state"] == "populated"
    assert doc["predicted"]["likely"] is None and doc["predicted"]["right"] is None
    p, b, g = rows(box)[-3:]
    assert [p["kind"], b["kind"], g["kind"]] == ["predict", "bite", "graded"]
    assert p["n"] < b["n"] and g["of"] == p["n"] and g["bite_row"] == b["n"]
    assert p["who"] == g["who"] == "predict"
    assert "bees" not in json.dumps([p, g]), "the record keeps no words"


def test_it_counts_what_bites_came_to_and_grades_against_it(tmp_path):
    box = make(tmp_path)
    ask(box, "bees swarm")
    code, doc = ask(box, "tomatoes sun")
    assert code == 0
    assert doc["predicted"] == {"likely": "populated", "bites": 1,
                                "seen": {"populated": 1}, "row": doc["predicted"]["row"],
                                "got": "populated", "right": True}  # fmt: skip
    code, doc = ask(box, "qqqq zzzz")
    assert code == 42 and doc["predicted"]["likely"] == "populated"
    assert doc["predicted"]["got"] == "empty" and doc["predicted"]["right"] is False
    got = run("score", "--box", str(box))
    assert got.returncode == 0
    assert got.stdout.splitlines() == [
        "1 of 2 predictions right",
        "  said populated  1 of 2 held",
    ]


def test_a_tie_goes_to_empty_the_answer_that_asks_the_person():
    bite = {"kind": "bite"}
    served = {**bite, "served": [{"echo": False}]}
    echo = {**bite, "served": [{"echo": True}]}
    assert pr.declare([]) == {"likely": None, "bites": 0, "seen": {}}
    assert pr.declare([served, echo])["likely"] == "empty", "an echo serves nothing"
    assert pr.declare([served, served, echo])["likely"] == "populated"
    sealed = {**bite, "answered_by": 3}
    assert pr.declare([sealed, served])["likely"] == "populated", "then by name"
    assert pr.declare([sealed, sealed, served, {"kind": "seal"}]) == {
        "likely": "sealed", "bites": 3, "seen": {"populated": 1, "sealed": 2}}  # fmt: skip


def test_it_reads_the_one_scripts_own_predict_rows():
    rows_ = [
        {"n": 0, "kind": "predict", "likely": "empty", "got": "empty", "right": True},
        {"n": 1, "kind": "predict", "likely": None, "got": "empty", "right": None},
        {"n": 2, "kind": "predict", "likely": "empty", "n_": 1},
        {"n": 3, "kind": "graded", "of": 2, "right": False},
        {"n": 4, "kind": "graded", "of": 9, "right": True},
    ]
    assert pr.grades(rows_) == [
        {"likely": "empty", "right": True},
        {"likely": "empty", "right": False},
    ]


def test_nothing_graded_waits_and_a_broken_record_is_refused(tmp_path):
    box = make(tmp_path)
    got = run("score", "--box", str(box))
    assert got.returncode == 42 and "nothing graded yet" in got.stdout
    ask(box, "bees")
    assert run("score", "--box", str(box)).returncode == 42, "the first isn't graded"
    rec = box / "record.jsonl"
    rec.write_text(rec.read_text().replace('"graded"', '"gradeq"', 1))
    for argv in (["score", "--box", str(box)], ["ask", "--box", str(box), "bees"]):
        got = run(*argv)
        assert got.returncode == 2 and "doesn't verify" in got.stderr
    got = run("ask", "--box", str(tmp_path / "nobox"), "bees")
    assert got.returncode == 2 and "not a kernel box" in got.stderr


def test_a_bad_command_line_is_refused(tmp_path):
    box = str(make(tmp_path))
    for argv in ([], ["fly"], ["ask", "--box", box], ["ask", "bees"],
                 ["ask", "--box", box, "--now", "", "bees"],
                 ["ask", "--box", box, "--top", "3", "bees"],
                 ["score", "--box", box, "bees"], ["score", "--box", box, *NOW]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "predict.py" in got.stderr, argv
    assert len(rows(Path(box))) == 1, "nothing written by a refusal"
