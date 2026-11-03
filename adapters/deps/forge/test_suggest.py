"""forge: a sentence in, the add-ons it names or means out, as a plan the
Forge reads. The cards are this willow's own, read beside the script; the box
is a fresh one in a scratch folder, and only read."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
KERNEL = ROOT / "kernel.py"
SCRIPT = HERE / "suggest.py"

spec = importlib.util.spec_from_file_location("willow_forge_suggest", SCRIPT)
suggest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suggest)

EMAIL = "I want to read my email about the flat and know when the boiler is due"
CLUB = "a site for my running club with the race dates"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


@pytest.fixture
def box(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "flat.txt").write_text("The boiler service is due in March.\n")
    box = tmp_path / "box"
    got = subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "init",
            "--box",
            str(box),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "k.key"),
        ],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 0, got.stderr
    return box


def rows(box: Path) -> int:
    return len((box / "record.jsonl").read_text().splitlines())


def test_no_arguments_is_refused_with_the_name():
    got = run()
    assert got.returncode == 2 and "suggest.py" in got.stderr


def test_a_stray_argument_is_refused(box):
    got = run(EMAIL, "--box", str(box), "--stray", "more")
    assert got.returncode == 2 and "suggest.py" in got.stderr


def test_a_folder_that_is_not_a_box_is_refused(tmp_path):
    got = run(EMAIL, "--box", str(tmp_path))
    assert got.returncode == 2 and "not a box" in got.stderr


def test_a_record_that_does_not_verify_is_refused(box):
    rec = box / "record.jsonl"
    rec.write_text(
        rec.read_text()
        .replace('"kind": "boot"', '"kind": "boat"')
        .replace('"kind":"boot"', '"kind":"boat"')
    )
    got = run(EMAIL, "--box", str(box))
    assert got.returncode == 2 and "doesn't verify" in got.stderr


def test_a_sentence_with_forks_waits_on_you_and_names_them(box):
    before = rows(box)
    got = run(EMAIL, "--box", str(box))
    assert got.returncode == 42, got.stderr
    assert (
        "fork    “email” could be:" in got.stdout
        and "fork    “due” could be:" in got.stdout
    )
    assert (
        "mail " in got.stdout
        and "apple-mail" in got.stdout
        and "coming-up" in got.stdout
    )
    assert got.stdout.rstrip().endswith("2 forks wait on you")
    assert rows(box) == before, "suggest writes nothing to the record"


def test_one_card_named_and_nothing_else_is_a_step_and_exit_0(box):
    got = run("a merkle proof of one row", "--box", str(box))
    assert got.returncode == 0, got.stdout + got.stderr
    assert got.stdout.count("step    ") == 1 and "step    merkle" in got.stdout
    assert "fork" not in got.stdout


def test_one_fork_waits_in_the_singular(box):
    got = run("my email", "--box", str(box))
    assert got.returncode == 42 and got.stdout.rstrip().endswith("1 fork waits on you")


def test_nothing_named_says_so_and_is_42(box):
    got = run(CLUB, "--box", str(box))
    assert got.returncode == 42
    assert "nothing named" in got.stdout and "search-words.txt" in got.stdout


def test_an_idea_is_said_as_one_and_is_not_a_step(box):
    ideas = json.loads((ROOT / "adapters" / "planned.json").read_text())
    name = ideas[0]["name"]
    got = run(f"I want {name} on this", "--box", str(box), "--json")
    assert got.returncode == 42
    d = json.loads(got.stdout)
    assert (
        [i["name"] for i in d["ideas"]] == [name]
        and d["steps"] == []
        and d["plan"] is None
    )


def test_the_json_is_a_plan_the_forge_validates_and_extracts(box):
    plan_shape = pytest.importorskip("forge.plan_shape")
    decision_extract = pytest.importorskip("forge.decision_extract")
    got = run(EMAIL, "--box", str(box), "--json")
    assert got.returncode == 42
    d = json.loads(got.stdout)
    assert d["cards"]["built"] > 300 and d["forks"].keys() == {"email", "due"}
    doc = plan_shape.validate(d["plan"])
    assert doc.app_name == "willow-stack"
    forks = [e for e in doc.entries if isinstance(e, plan_shape.Fork)]
    assert [f.decision_type for f in forks] == ["willow-email", "willow-due"]
    assert all(f.recommended is None and f.confidence is None for f in forks), (
        "no fabricated 0.5"
    )
    assert set(forks[0].labels) == {"mail", "apple-mail"}
    assert all(
        f.resolves[n][0].content == f"- {n} -- --box {{box}}\n"
        for f in forks
        for n in f.labels
    )
    ex = decision_extract.extract(doc)
    assert len(ex.decisions) == 2 and not ex.refused, ex.to_dict()


def test_a_step_and_a_fork_together_is_a_plan_with_both(box):
    got = run("a merkle proof, and my email", "--box", str(box), "--json")
    d = json.loads(got.stdout)
    kinds = [e["kind"] for e in d["plan"]["entries"]]
    assert kinds == ["file_write", "fork"]
    assert d["plan"]["entries"][0]["dest_path"] == "steps/merkle.md"


def test_the_decision_type_is_the_word_in_the_forges_charset():
    assert suggest.decision_type("email") == "willow-email"
    assert suggest.decision_type("coming up") == "willow-coming-up"
    assert suggest.decision_type("l'été!") == "willow-l-t"


def test_a_card_that_will_not_read_is_refused_not_a_traceback(
    box, monkeypatch, tmp_path
):
    card_box = pytest.importorskip("forge.card_box")
    card_table = pytest.importorskip("forge.card_table")

    def broken(root):
        raise card_table.CardTableError(
            "adapters/stdlib/x/README.md: no willow-addon header"
        )

    monkeypatch.setattr(card_box, "CardBox", broken)
    assert suggest.main([EMAIL, "--box", str(box)]) == 2


def test_without_forge_play_it_refuses_and_names_the_fix(box, monkeypatch):
    monkeypatch.setattr(suggest, "forge", lambda: None)
    assert suggest.main([EMAIL, "--box", str(box)]) == 2
