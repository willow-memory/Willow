"""forge: a sentence in, the add-ons it names or means out, as a plan the
Forge reads; the settled forks and the stack to the kernel's door, for the
person to seal; what they sealed read back by both sides. The cards are this
willow's own, read beside the script; the box is a fresh one in a scratch
folder. The tests seal with the box's key, as the person would; the script
never does."""

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


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


@pytest.fixture
def box(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "flat.txt").write_text("The boiler service is due in March.\n")
    box = tmp_path / "box"
    got = k(
        "init", "--box", str(box), "--pile", str(pile), "--key", str(tmp_path / "k.key")
    )
    assert got.returncode == 0, got.stderr
    return box


def rows(box: Path) -> list[dict]:
    return [json.loads(ln) for ln in (box / "record.jsonl").read_text().splitlines()]


def proposed(box: Path, *choose: str) -> dict[str, str]:
    """`propose` with the choices given; {path: subject} of what waits."""
    got = run(
        "propose",
        EMAIL,
        "--box",
        str(box),
        *[a for c in choose for a in ("--choose", c)],
    )
    assert got.returncode == 42, got.stdout + got.stderr
    return {
        ln.split()[2]: ln.split()[1]
        for ln in got.stdout.splitlines()
        if ln.startswith("proposed")
    }


# ── refusals ──────────────────────────────────────────────────────────────────


def test_no_arguments_is_refused_with_the_name():
    got = run()
    assert got.returncode == 2 and "suggest.py" in got.stderr


def test_a_stray_argument_is_refused(box):
    got = run("suggest", EMAIL, "--box", str(box), "--stray", "more")
    assert got.returncode == 2 and "suggest.py" in got.stderr


def test_a_folder_that_is_not_a_box_is_refused(tmp_path):
    got = run("suggest", EMAIL, "--box", str(tmp_path))
    assert got.returncode == 2 and "not a box" in got.stderr


def test_a_record_that_does_not_verify_is_refused(box):
    rec = box / "record.jsonl"
    rec.write_text(
        rec.read_text()
        .replace('"kind": "boot"', '"kind": "boat"')
        .replace('"kind":"boot"', '"kind":"boat"')
    )
    for verb in ("suggest", "propose"):
        got = run(verb, EMAIL, "--box", str(box))
        assert got.returncode == 2 and "doesn't verify" in got.stderr


def test_a_card_that_will_not_read_is_refused_not_a_traceback(box, monkeypatch):
    card_box = pytest.importorskip("forge.card_box")
    card_table = pytest.importorskip("forge.card_table")

    def broken(root):
        raise card_table.CardTableError(
            "adapters/stdlib/x/README.md: no willow-addon header"
        )

    monkeypatch.setattr(card_box, "CardBox", broken)
    assert suggest.main(["suggest", EMAIL, "--box", str(box)]) == 2


def test_without_forge_play_it_refuses_and_names_the_fix(box, monkeypatch):
    monkeypatch.setattr(suggest, "forge", lambda: None)
    assert suggest.main(["suggest", EMAIL, "--box", str(box)]) == 2


# ── suggest ───────────────────────────────────────────────────────────────────


def test_a_sentence_with_forks_waits_on_you_and_names_them(box):
    before = len(rows(box))
    got = run("suggest", EMAIL, "--box", str(box))
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
    assert len(rows(box)) == before, "suggest writes nothing to the record"


def test_one_card_named_and_nothing_else_is_a_step_and_exit_0(box):
    got = run("suggest", "a merkle proof of one row", "--box", str(box))
    assert got.returncode == 0, got.stdout + got.stderr
    assert got.stdout.count("step    ") == 1 and "step    merkle" in got.stdout
    assert "fork" not in got.stdout


def test_one_fork_waits_in_the_singular(box):
    got = run("suggest", "my email", "--box", str(box))
    assert got.returncode == 42 and got.stdout.rstrip().endswith("1 fork waits on you")


def test_nothing_named_says_so_and_is_42(box):
    got = run("suggest", CLUB, "--box", str(box))
    assert got.returncode == 42
    assert "nothing named" in got.stdout and "search-words.txt" in got.stdout


def test_an_idea_is_said_as_one_and_is_not_a_step(box):
    ideas = json.loads((ROOT / "adapters" / "planned.json").read_text())
    name = ideas[0]["name"]
    got = run("suggest", f"I want {name} on this", "--box", str(box), "--json")
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
    got = run("suggest", EMAIL, "--box", str(box), "--json")
    assert got.returncode == 42
    d = json.loads(got.stdout)
    assert (
        d["cards"]["built"] > 300
        and d["forks"].keys() == {"email", "due"}
        and d["sealed"] == {}
    )
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
    got = run("suggest", "a merkle proof, and my email", "--box", str(box), "--json")
    d = json.loads(got.stdout)
    assert [e["kind"] for e in d["plan"]["entries"]] == ["file_write", "fork"]
    assert d["plan"]["entries"][0]["dest_path"] == "steps/merkle.md"


# ── propose ───────────────────────────────────────────────────────────────────


def test_an_unsettled_fork_is_refused_naming_its_options_and_nothing_is_written(box):
    before = len(rows(box))
    got = run("propose", EMAIL, "--box", str(box), "--choose", "email=mail")
    assert (
        got.returncode == 2
        and "“due” is not settled: --choose due=coming-up|renewals" in got.stderr
    )
    assert len(rows(box)) == before and not (box / "proposals").exists()


def test_a_choice_not_on_offer_is_refused(box):
    got = run(
        "propose",
        EMAIL,
        "--box",
        str(box),
        "--choose",
        "email=pdf",
        "--choose",
        "due=renewals",
    )
    assert got.returncode == 2 and "pdf is not an option for “email”" in got.stderr
    got = run(
        "propose",
        EMAIL,
        "--box",
        str(box),
        "--choose",
        "email=mail",
        "--choose",
        "due=renewals",
        "--choose",
        "x=y",
    )
    assert got.returncode == 2 and "nothing to choose for “x”" in got.stderr
    got = run("propose", EMAIL, "--box", str(box), "--choose", "email")
    assert got.returncode == 2 and "WORD=VALUE" in got.stderr


def test_nothing_to_propose_is_refused(box):
    got = run("propose", CLUB, "--box", str(box))
    assert got.returncode == 2 and "nothing to propose" in got.stderr


def test_propose_puts_each_settled_fork_and_the_stack_at_the_door(box):
    waiting = proposed(box, "email=mail", "due=coming-up")
    assert set(waiting) == {
        "forge/decisions/willow-email.json",
        "forge/decisions/willow-due.json",
        "forge/stack.md",
    }
    out = k("out", "--box", str(box))
    assert out.returncode == 42 and out.stdout.count("waiting on your seal") == 3
    kinds = [(r["kind"], r.get("verdict")) for r in rows(box)]
    assert kinds[1:] == [("bite", None), ("proposal", "pass")] * 3 + [("out", None)]
    rec = rows(box)
    assert rec[1]["served"] == [] and rec[1]["bite_key"] == suggest.kernel.bite_key(
        "forge decision willow-email"
    )
    subj = waiting["forge/decisions/willow-email.json"]
    prop = json.loads((box / "proposals" / f"{subj[9:]}.json").read_text())
    data = json.loads(prop["data"])
    assert (
        data["chose"] == "mail"
        and data["over"] == ["apple-mail"]
        and data["word"] == "email"
    )
    assert (
        data["card"]["where"] == "adapters/stdlib/mail/README.md"
        and len(data["card"]["sha256"]) == 64
    )
    assert prop["claim"].endswith("no reason given")
    stack = json.loads(
        (box / "proposals" / f"{waiting['forge/stack.md'][9:]}.json").read_text()
    )
    assert stack["data"].splitlines() == [
        f"# {EMAIL}",
        "",
        f"## for “{EMAIL}”",
        "- mail -- --box {box}",
        "- coming-up -- --box {box}",
    ]


def test_a_reason_rides_on_the_decision(box):
    got = run(
        "propose",
        "my email",
        "--box",
        str(box),
        "--choose",
        "email=mail",
        "--why",
        "email=the flat's mail is mbox",
    )
    assert got.returncode == 42, got.stderr
    subj = [ln.split()[1] for ln in got.stdout.splitlines() if "willow-email" in ln][0]
    prop = json.loads((box / "proposals" / f"{subj[9:]}.json").read_text())
    assert json.loads(prop["data"])["why"] == "the flat's mail is mbox" and prop[
        "claim"
    ].endswith("the flat's mail is mbox")


def test_a_proposal_is_not_an_answer_until_sealed(box):
    proposed(box, "email=mail", "due=coming-up")
    got = run("suggest", EMAIL, "--box", str(box), "--json")
    d = json.loads(got.stdout)
    assert (
        got.returncode == 42
        and d["sealed"] == {}
        and d["forks"].keys() == {"email", "due"}
    )


# ── the seal, and both sides reading it back ──────────────────────────────────


def seal_all(box: Path, waiting: dict[str, str]) -> None:
    for subj in waiting.values():
        got = k("seal", "--box", str(box), subj)
        assert got.returncode == 0, got.stderr


def test_a_sealed_decision_settles_the_fork_and_asks_nothing_twice(box):
    waiting = proposed(box, "email=mail", "due=coming-up")
    seal_all(box, {p: s for p, s in waiting.items() if p != "forge/stack.md"})
    got = run("suggest", "my email, and what is due", "--box", str(box), "--json")
    assert got.returncode == 0, got.stdout + got.stderr
    d = json.loads(got.stdout)
    assert d["forks"] == {} and [s["name"] for s in d["steps"]] == ["mail", "coming-up"]
    assert d["steps"][0]["why"].startswith("you sealed it for “email” (row ")
    assert (
        d["sealed"]["email"]["chose"] == "mail"
        and d["sealed"]["email"]["decision_type"] == "willow-email"
    )
    assert [e["kind"] for e in d["plan"]["entries"]] == ["file_write", "file_write"]


def test_a_sealed_stack_for_the_same_words_is_served_first(box):
    waiting = proposed(box, "email=mail", "due=coming-up")
    seal_all(box, waiting)
    got = run("suggest", EMAIL.upper() + "?", "--box", str(box))
    assert got.returncode == 0 and "stack   sealed for these words at row" in got.stdout
    assert "- mail -- --box {box}" in got.stdout and "fork" not in got.stdout
    again = run(
        "propose",
        EMAIL,
        "--box",
        str(box),
        "--choose",
        "email=mail",
        "--choose",
        "due=coming-up",
    )
    assert again.returncode == 2 and "sealed for these words already" in again.stderr
    bite = k("bite", "--box", str(box), EMAIL)
    assert bite.returncode == 0 and json.loads(bite.stdout)["state"] == "sealed"


def test_the_forge_reads_the_sealed_decision_back_through_the_kernel(box):
    willow_record = pytest.importorskip("forge.willow_record")
    waiting = proposed(box, "email=mail", "due=renewals")
    rec = willow_record.WillowRecord(KERNEL, box)
    assert rec.has_sealed("willow-email") is None, "not before the seal"
    seal_all(box, waiting)
    assert rec.has_sealed("willow-email").chosen == "mail"
    assert rec.has_sealed("willow-due").chosen == "renewals"
    assert rec.stack_for(EMAIL).splitlines()[-1] == "- renewals -- --box {box}"


def test_a_changed_proposal_is_no_longer_sealed_for_either_side(box):
    waiting = proposed(box, "email=mail", "due=renewals")
    seal_all(box, waiting)
    f = box / "proposals" / f"{waiting['forge/decisions/willow-email.json'][9:]}.json"
    f.write_text(f.read_text().replace("no reason given", "a reason given"))  # any byte
    got = run("suggest", "my email", "--box", str(box), "--json")
    d = json.loads(got.stdout)
    assert got.returncode == 42 and d["sealed"] == {} and "email" in d["forks"]


def test_a_seal_for_a_card_that_no_longer_does_the_word_is_said_and_asked_again(box):
    """The person sealed a decision whose option isn't among the word's cards
    now (the alias file changed, say): stale, said, and the fork stays open."""
    data = json.dumps(
        {
            "word": "email",
            "decision_type": "willow-email",
            "chose": "pdf",
            "over": [],
            "why": "",
        }
    )
    prop = {
        "path": "forge/decisions/willow-email.json",
        "data": data,
        "cites": [],
        "claim": "pdf",
    }
    assert k("bite", "--box", str(box), "forge decision willow-email").returncode == 42
    f = box / "p.jsonl"
    f.write_text(json.dumps(prop) + "\n")
    got = k("propose", "--box", str(box), "--file", str(f))
    assert got.returncode == 42, got.stderr
    assert k("seal", "--box", str(box), got.stdout.split()[1]).returncode == 0
    got = run("suggest", "my email", "--box", str(box))
    assert got.returncode == 42
    assert (
        "sealed  “email”: pdf no longer does “email” here" in got.stdout
        and "fork    “email”" in got.stdout
    )


def test_the_decision_type_is_the_forges_naming():
    willow_record = pytest.importorskip("forge.willow_record")
    assert willow_record.decision_type("coming up") == "willow-coming-up"
