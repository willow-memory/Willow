"""demo/marisol: what was frozen is what is here, her folder is made the same
every time and holds what was planted, each question is frozen with its rule,
and the judging holds a run to them (tried on made-up answers, which a dry run
that serves nothing cannot do)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FROZEN = json.loads((HERE / "FROZEN.json").read_text(encoding="utf-8"))
QUESTIONS = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))

spec = importlib.util.spec_from_file_location("marisol_run", HERE / "run.py")
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_every_frozen_file_is_as_it_was_frozen():
    for name, want in FROZEN["files"].items():
        assert sha(HERE / name) == want, f"{name} changed since the freeze"


def test_the_last_freeze_says_why():
    last = FROZEN["freezes"][-1]
    assert last["n"] == len(FROZEN["freezes"]) and len(last["why"]) > 40


def test_life_is_made_the_same_and_holds_what_was_planted(tmp_path):
    (tmp_path / "make_life.py").write_bytes((HERE / "make_life.py").read_bytes())
    make = [sys.executable, str(tmp_path / "make_life.py")]
    assert subprocess.run(make, capture_output=True).returncode == 0
    first = {p: p.read_bytes() for p in (tmp_path / "life").rglob("*") if p.is_file()}
    got = subprocess.run([*make, "--check"], capture_output=True, text=True)
    assert got.returncode == 0, got.stdout
    subprocess.run(make, capture_output=True)
    again = {p: p.read_bytes() for p in (tmp_path / "life").rglob("*") if p.is_file()}
    assert first == again, "the same bytes every run"
    text = "".join(p.read_text(encoding="utf-8") for p in first)
    for key in ("father", "note", "day76", "transfer"):
        assert QUESTIONS["planted"][key] in text, key


def test_a_question_is_frozen_with_its_kind_and_expectation():
    ids = [q["id"] for q in QUESTIONS["questions"]]
    assert len(ids) == len(set(ids))
    for q in QUESTIONS["questions"]:
        assert q["kind"] in {
            "bite",
            "words-es",
            "claim",
            "amounts",
            "quotes",
            "contradictions",
        }
        assert q["expect"] in {"hit", "miss", "silent", "total", "almost", "gap"}
        assert (q["holds"] is None) == (
            q["expect"] in {"silent", "total", "almost", "gap"}
        )
        assert (q["ask"] is None) == (
            q["kind"] in {"amounts", "quotes", "contradictions"}
        )
    assert set(QUESTIONS["pass_rules"]) == {
        "served", "gap", "amounts", "quotes", "unsealed", "verify"
    }  # fmt: skip


def test_a_claim_checks_row_is_read_for_its_place_and_a_hit_is_a_phrase_in_the_first_three():
    assert (
        run.ROW.match(
            "some parts   life/log/outages.txt:27   76, días, luz   lacks sin"
        ).group(1)
        == "life/log/outages.txt:27"
    )
    assert (
        run.ROW.match("all parts    sources/a.txt:3   a, b").group(1)
        == "sources/a.txt:3"
    )
    assert run.ROW.match("no file has  holds") is None
    q = {"holds": "Día 76"}
    assert (
        run.hit(q, {"served": [{"text": "x"}, {"text": "2017-12-04 día 77 volvió"}]})
        is False
    )
    assert (
        run.hit(q, {"served": [{"text": "x"}, {"text": "2017-12-04 DÍA   76: volvió"}]})
        is True
    )
    assert run.hit({"holds": None}, {"served": [{"text": "anything"}]}) is False


def _box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("Tomatoes want sun.\n", encoding="utf-8")
    box = tmp_path / "box"
    run.quiet(run.kernel.init, box, pile, tmp_path / "k.key", run.NOW)
    return box


def _answers(**over: dict) -> list[dict]:
    """A run that does what the frozen rules expect, with what `over` changes."""
    ok = {
        "Q1": ["NSF Engines - Type 1"], "Q2": ["on Tuesday took over"],
        "Q3": ["se acabó en el noventa y seis"], "Q4": ["se terminó en 2005"],
        "Q5": ["repeal in 2005"], "Q6": ["unrelated"], "Q7": ["Día 76"],
        "Q8": ["$6,000"], "Q9": [],
    }  # fmt: skip
    ok.update(over)
    got = [
        {"id": k, "kind": "x", "asked": "", "exit": 0, "stdout": "",
         "served": [{"where": "w", "text": t} for t in ts]}
        for k, ts in ok.items()
    ]  # fmt: skip
    amounts = "".join(
        f"2018-03-14  ${c / 100:,.2f}  life/receipts/outage-costs.csv.txt:{i}  row\n"
        for i, c in enumerate([1_000_000, 487_350], 1)
    )
    got += [
        {"id": "Q10", "kind": "amounts", "asked": "", "exit": 0, "served": [], "stdout": amounts},
        {"id": "Q11", "kind": "quotes", "asked": "", "exit": 42, "served": [],
         "stdout": 'almost  x.md:9  "Whoever keeps the log decides"\n  dropped    alone\n'},
        {"id": "Q12", "kind": "contradictions", "asked": "", "exit": 0, "served": [],
         "stdout": "AMOUNT  battery, inverter\n        a.txt:1  $1\n        b.txt:2  $2\n"},
    ]  # fmt: skip
    return got


def test_a_run_that_does_what_was_frozen_holds_every_rule(tmp_path):
    res = run.judge(_answers(), _box(tmp_path))
    assert {r: v["ok"] for r, v in res.items()} == dict.fromkeys(
        QUESTIONS["pass_rules"], True
    )


def test_a_missing_hit_a_served_silence_and_a_gap_that_closed_are_each_failed(tmp_path):
    res = run.judge(
        _answers(Q1=["unrelated"], Q9=["something"], Q6=["Día 76"]), _box(tmp_path)
    )
    assert not res["served"]["ok"] and len(res["served"]["why"]) == 2
    assert not res["gap"]["ok"] and "Q6" in res["gap"]["why"][0]


def test_amounts_quotes_and_contradictions_are_held_to_their_rules(tmp_path):
    a = _answers()
    for x in a:
        if x["id"] == "Q10":
            x["stdout"] += (
                "2018-03-14  $40,000.00  life/receipts/outage-costs.csv.txt:9  row\n"
            )
        if x["id"] == "Q11":
            x["stdout"] = 'as written  x.md:9  "Whoever keeps the log decides"\n'
        if x["id"] == "Q12":
            x["stdout"] = (
                "DATE  credit\n   notes/ernesto-interview.vtt.txt:1  1996\n   nota-credito-936.md:5  2005\n"
            )
    res = run.judge(a, _box(tmp_path))
    assert not res["amounts"]["ok"] and not res["quotes"]["ok"] and not res["gap"]["ok"]


def test_a_seal_on_the_box_fails_unsealed(tmp_path):
    box = _box(tmp_path)
    run.kernel.append(box, run.NOW, "seal", who="x")
    assert not run.judge(_answers(), box)["unsealed"]["ok"]
