"""forge: a sentence in, the add-ons it names or means out, as a report and
as a plan the Forge reads. The cards are this willow's own, read beside the
script; the box is a fresh one in a scratch folder, and only read. The
report contract is held here the way test_contract.py holds the stdlib
report add-ons, since a deps add-on's tests run in its own environment."""

from __future__ import annotations

import ast
import importlib.util
import json
import re
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
HEAD = re.compile(r"[a-z0-9-]+: (?:populated|empty|unreachable), \S.*")
ROW = re.compile(r"  \S.*")


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


def holds_the_contract(
    text: subprocess.CompletedProcess, data: subprocess.CompletedProcess
) -> dict:
    """test_contract.py's report assertions, on one run as text and one as JSON."""
    assert text.returncode == data.returncode, "--json changes nothing but the form"
    doc = json.loads(data.stdout)
    assert text.stdout.rstrip("\n") == suggest.report_text(doc), (
        "printed the same from its JSON"
    )
    assert set(doc) == {"addon", "state", "said", "groups"} and doc["addon"] == "forge"
    head, *body = text.stdout.rstrip("\n").splitlines()
    assert HEAD.fullmatch(head) and "\n" not in doc["said"], head
    found = [r for g in doc["groups"] for r in g["rows"]]
    names = [g["name"] for g in doc["groups"]]
    assert None not in names[1:], "rows of no group come first"
    assert all(g["rows"] for g in doc["groups"]), "an empty group isn't printed"
    assert all(
        set(r) == {"where", "what"}
        and r["where"].strip()
        and "\n" not in r["where"] + r["what"]
        for r in found
    )
    assert all(ROW.fullmatch(ln) or ln.startswith("## ") for ln in body), body
    state, code = doc["state"], text.returncode
    assert (state == "populated") == bool(found), "populated is having rows"
    assert {
        "empty": code == 0,
        "unreachable": code == 42,
        "populated": code in (0, 42),
    }[state], (state, code)
    return doc


# ── refusals ──────────────────────────────────────────────────────────────────


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


def test_a_card_that_will_not_read_is_refused_not_a_traceback(box, monkeypatch):
    card_box = pytest.importorskip("forge.card_box")
    card_table = pytest.importorskip("forge.card_table")

    def broken(root):
        raise card_table.CardTableError(
            "adapters/stdlib/x/README.md: no willow-addon header"
        )

    monkeypatch.setattr(card_box, "CardBox", broken)
    assert suggest.main([EMAIL, "--box", str(box)]) == 2


def test_without_forge_play_the_report_is_unreachable_and_says_the_fix(
    box, monkeypatch, capsys
):
    monkeypatch.setattr(suggest, "forge", lambda: None)
    assert suggest.main([EMAIL, "--box", str(box)]) == 42
    assert capsys.readouterr().out.startswith(
        "forge: unreachable, forge-play 0.10 or newer is not installed"
    )
    assert suggest.main([EMAIL, "--box", str(box), "--json"]) == 42
    assert json.loads(capsys.readouterr().out)["state"] == "unreachable"


# ── the report ────────────────────────────────────────────────────────────────


def test_the_twenty_lines_are_the_stack_add_ons_word_for_word():
    """Each report add-on keeps its own copy of what prints a report; this
    one's is the stack add-on's, so the two can't drift."""
    mine = ast.parse(SCRIPT.read_text())
    theirs = ast.parse(
        (ROOT / "adapters" / "stdlib" / "stack" / "stack.py").read_text()
    )

    def source(tree, name):
        f = next(
            n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name
        )
        return ast.unparse(f)

    assert source(mine, "report_text") == source(theirs, "report_text")


def test_a_sentence_with_forks_is_populated_waits_on_you_and_writes_nothing(box):
    before = rows(box)
    text, data = run(EMAIL, "--box", str(box)), run(EMAIL, "--box", str(box), "--json")
    doc = holds_the_contract(text, data)
    assert text.returncode == 42 and doc["said"] == "2 forks wait on you"
    assert [g["name"] for g in doc["groups"]] == ["fork “email”", "fork “due”"]
    email = {r["what"].split(":")[0]: r["where"] for r in doc["groups"][0]["rows"]}
    assert email == {
        "apple-mail": "adapters/stdlib/apple-mail/README.md",
        "mail": "adapters/stdlib/mail/README.md",
    }
    assert rows(box) == before, "suggest writes nothing to the record"


def test_one_card_named_alone_is_a_step_and_exit_0(box):
    text = run("a merkle proof of one row", "--box", str(box))
    data = run("a merkle proof of one row", "--box", str(box), "--json")
    doc = holds_the_contract(text, data)
    assert text.returncode == 0 and doc["said"] == "1 step, nothing waits on you"
    assert [g["name"] for g in doc["groups"]] == ["steps"] and doc["groups"][0]["rows"][
        0
    ]["what"].startswith("merkle: ")


def test_one_fork_waits_in_the_singular(box):
    got = run("my email", "--box", str(box))
    assert got.returncode == 42 and got.stdout.startswith(
        "forge: populated, 1 fork waits on you"
    )


def test_nothing_named_is_empty_and_exit_0(box):
    text, data = run(CLUB, "--box", str(box)), run(CLUB, "--box", str(box), "--json")
    doc = holds_the_contract(text, data)
    assert (
        text.returncode == 0
        and doc["state"] == "empty"
        and "search-words.txt" in doc["said"]
    )


def test_an_idea_is_a_row_under_ideas_and_not_a_step(box):
    ideas = json.loads((ROOT / "adapters" / "planned.json").read_text())
    name = next(i["name"] for i in ideas if i["name"] != "forge")
    sentence = f"I want {name} on this"
    text, data = (
        run(sentence, "--box", str(box)),
        run(sentence, "--box", str(box), "--json"),
    )
    doc = holds_the_contract(text, data)
    assert text.returncode == 0 and doc["said"] == "only ideas, nothing built to run"
    assert [g["name"] for g in doc["groups"]] == ["ideas"]
    assert doc["groups"][0]["rows"][0]["where"] == "adapters/planned.json"


def test_the_same_box_gives_the_same_report_twice(box):
    assert run(EMAIL, "--box", str(box)).stdout == run(EMAIL, "--box", str(box)).stdout


# ── the plan ──────────────────────────────────────────────────────────────────


def test_the_plan_is_one_the_forge_validates_and_extracts(box):
    plan_shape = pytest.importorskip("forge.plan_shape")
    decision_extract = pytest.importorskip("forge.decision_extract")
    got = run(EMAIL, "--box", str(box), "--plan")
    assert got.returncode == 42, "the same exit as the report"
    d = json.loads(got.stdout)
    assert set(d) == {"cards", "steps", "forks", "ideas", "plan"}
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


def test_an_idea_alone_is_a_plan_of_nothing(box):
    ideas = json.loads((ROOT / "adapters" / "planned.json").read_text())
    name = next(i["name"] for i in ideas if i["name"] != "forge")
    d = json.loads(run(f"I want {name} on this", "--box", str(box), "--plan").stdout)
    assert (
        [i["name"] for i in d["ideas"]] == [name]
        and d["steps"] == []
        and d["plan"] is None
    )


def test_a_step_and_a_fork_together_is_a_plan_with_both(box):
    d = json.loads(
        run("a merkle proof, and my email", "--box", str(box), "--plan").stdout
    )
    assert [e["kind"] for e in d["plan"]["entries"]] == ["file_write", "fork"]
    assert d["plan"]["entries"][0]["dest_path"] == "steps/merkle.md"


def test_the_decision_type_is_the_forges_naming():
    willow_record = pytest.importorskip("forge.willow_record")
    assert willow_record.decision_type("coming up") == "willow-coming-up"
