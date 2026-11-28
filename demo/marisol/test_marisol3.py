"""demo/marisol, freeze 3: life-more/ is made the same every time and holds
what was planted, each strand's questions are frozen with their rules, and
the judging holds a run to them (tried on made-up answers, which a dry run
that serves nothing cannot do). test_marisol.py holds every frozen file's
hash, freeze 3's among them."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
Q3 = json.loads((HERE / "questions-3.json").read_text(encoding="utf-8"))
FROZEN = json.loads((HERE / "FROZEN.json").read_text(encoding="utf-8"))

spec = importlib.util.spec_from_file_location("marisol_run3", HERE / "run3.py")
run3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run3)


def test_freeze_3_holds_its_files():
    for name in ("make_life_3.py", "questions-3.json", "run3.py", "PLANTED.md"):
        assert name in FROZEN["files"], name


def test_life_more_is_made_the_same_and_holds_what_was_planted(tmp_path):
    (tmp_path / "make_life_3.py").write_bytes((HERE / "make_life_3.py").read_bytes())
    make = [sys.executable, str(tmp_path / "make_life_3.py")]
    assert subprocess.run(make, capture_output=True).returncode == 0
    more = tmp_path / "life-more"
    first = {p: p.read_bytes() for p in more.rglob("*") if p.is_file()}
    got = subprocess.run([*make, "--check"], capture_output=True, text=True)
    assert got.returncode == 0, got.stdout
    subprocess.run(make, capture_output=True)
    assert first == {p: p.read_bytes() for p in more.rglob("*") if p.is_file()}
    assert not (tmp_path / "life").exists(), "life/ is never written by freeze 3"


def test_each_strand_is_frozen_with_its_kinds_and_rules():
    assert set(Q3["strands"]) == {"life", "claims", "misses"}
    ids = [q["id"] for s in Q3["strands"].values() for q in s["questions"]]
    assert len(ids) == len(set(ids))
    for s in Q3["strands"].values():
        assert {"unsealed", "verify"} <= set(s["pass_rules"])
        for q in s["questions"]:
            assert q["kind"] in {"claim", "words-es", "count", "amounts",
                                 "all-passages", "pile-rank"}  # fmt: skip
            assert (q["ask"] is None) == (q["kind"] in run3.NO_QUESTION)
            assert (q["holds"] is None) == (q["expect"] in {"silent", "budget"})


def _box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("Tomatoes want sun.\n", encoding="utf-8")
    box = tmp_path / "box"
    run3.run.quiet(run3.kernel.init, box, pile, tmp_path / "k.key", run3.NOW)
    return box


def _answers(strand: str, **over) -> list[dict]:
    """A run of one strand that does what was frozen, with what `over` changes."""
    got = []
    for q in Q3["strands"][strand]["questions"]:
        a = {"id": q["id"], "kind": q["kind"], "asked": q["ask"], "exit": 0,
             "stdout": "", "served": []}  # fmt: skip
        if q["expect"] in ("hit", "within"):
            a["served"] = [{"rank": 1, "where": "w:1", "text": f"x {q['holds']} y"}]
        elif q["expect"] == "miss":
            a["served"] = [{"where": "w:1", "text": "unrelated"}]
        if q["kind"] == "all-passages":
            a["kernel_served"] = ["w:1"]
        if q["kind"] == "count":
            a["holding"] = [f"calendar/c.txt:{i}" for i in range(q["n"])]
        if q["kind"] == "amounts":
            a["stdout"] = (
                "undated  $3,468.00  office/budget/presupuesto-laboratorio.xlsx.txt:3  row\n"
                "undated  $4,040.00  office/budget/presupuesto-laboratorio.xlsx.txt:3  row\n"
            )
        a.update(over.get(q["id"], {}))
        got.append(a)
    return got


def test_a_run_that_does_what_was_frozen_holds_every_rule(tmp_path):
    box = _box(tmp_path)
    for strand, s in Q3["strands"].items():
        res = run3.judge(strand, _answers(strand), box, {"a": "nothing"})
        held = {r: v["ok"] for r, v in res.items()}
        assert held == dict.fromkeys(s["pass_rules"], True), (strand, res)


def test_life_fails_a_missed_hit_a_closed_gap_a_wrong_count_and_the_draft_figure(
    tmp_path,
):
    res = run3.judge("life", _answers("life", L2={"served": []},
                                      L1={"served": [{"where": "w", "text": "Cierre por apagón"}]},
                                      L3={"holding": ["x"] * 9}), _box(tmp_path),
                     {"p:1": "we need $18,000"})  # fmt: skip
    assert not res["served"]["ok"] and not res["gap"]["ok"]
    assert not res["count"]["ok"] and not res["budget"]["ok"]


def test_misses_fail_out_of_reach_a_changed_order_and_a_pile_rank_miss(tmp_path):
    far = [{"rank": i, "where": f"w:{i}", "text": "x"} for i in range(1, 11)]
    res = run3.judge("misses", _answers("misses", M1={"served": far, "kernel_served": ["w:1", "w:2", "w:3"]},
                                        M2={"kernel_served": ["other"]},
                                        M3={"served": []}), _box(tmp_path), {})  # fmt: skip
    assert not res["reach"]["ok"] and len(res["reach"]["why"]) == 2
    assert not res["phrases"]["ok"]


def test_a_silent_question_that_serves_fails(tmp_path):
    res = run3.judge("claims", _answers("claims", K8={"served": [{"where": "w", "text": "t"}]}),
                     _box(tmp_path), {})  # fmt: skip
    assert not res["served"]["ok"] and "K8" in res["served"]["why"][0]
