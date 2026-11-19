"""rules_study: the questions, the hit rule and the three pass rules as frozen, the
refusal of a pile that isn't the pinned one, and a dry run's wiring, none of it
needing the network (a fake pile stands in for the fetched rules)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rules_study as rs  # noqa: E402

SOURCES = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))["sources"]


def test_the_questions_are_twelve_six_and_six_and_name_a_pinned_file():
    workers = rs.lines_of(HERE / "questions/workers.txt")
    off = rs.lines_of(HERE / "questions/offtopic.txt")
    non = rs.lines_of(HERE / "questions/nonsense.txt")
    assert (len(workers), len(off), len(non)) == (12, 6, 6)
    ids = [r[0] for r in workers + off + non]
    assert len(set(ids)) == 24
    stems = {Path(s["file"]).stem for s in SOURCES if s["folder"] == "ecfr"}
    for qid, q, want, phrase in workers:
        assert want in stems and q and phrase, qid


def test_a_hit_is_a_passage_in_the_first_three_from_the_right_file_with_the_words():
    right = {
        "where": "17-cfr-243.101.txt:7",
        "text": "means as soon as reasonably practicable",
    }
    other = {"where": "17-cfr-243.100.txt:3", "text": "something else"}
    assert rs.hit(
        [other, other, right], "17-cfr-243.101", "As soon as reasonably practicable"
    )
    assert not rs.hit(
        [other, other, other, right], "17-cfr-243.101", "reasonably practicable"
    )
    assert not rs.hit([{"where": "17-cfr-243.100.txt:3", "text": right["text"]}],
                      "17-cfr-243.101", "reasonably practicable")  # fmt: skip
    curly = {"where": "x-243.101.txt:1", "text": "a “person” who agrees"}
    assert rs.hit([curly], "x-243.101", 'a "person" who agrees')


def asked(hits: int, off: int, non: int) -> dict:
    mk = lambda n, k: [{"served": [1] if i < k else []} for i in range(n)]  # noqa: E731
    return {"workers": [{"hit": i < hits} for i in range(12)],
            "offtopic": mk(6, off), "nonsense": mk(6, non)}  # fmt: skip


def test_the_pass_rules_are_the_frozen_thresholds():
    ok = rs.score(asked(8, 2, 0))
    assert {k: v["state"] for k, v in ok.items()} == {
        "S1": "pass",
        "S2": "pass",
        "S3": "pass",
    }
    assert rs.score(asked(7, 2, 0))["S1"]["state"] == "fail"
    assert rs.score(asked(8, 3, 0))["S2"]["state"] == "fail"
    assert rs.score(asked(8, 2, 1))["S3"]["state"] == "fail"
    assert ok["S1"]["needed"] == ">= 8 of 12"


def test_a_pile_that_is_not_the_pinned_one_is_refused(tmp_path, capsys):
    assert rs.held(tmp_path)  # every source missing
    got = rs.main(["run", "--pile", str(tmp_path), "--to", str(tmp_path / "out")])
    assert got == 2 and "refused" in capsys.readouterr().err
    assert rs.main(["run", "--pile"]) == 2


def test_a_dry_run_wires_the_hit_rule_over_a_fake_pile(tmp_path, monkeypatch, capsys):
    pile = tmp_path / "pile" / "ecfr"
    pile.mkdir(parents=True)
    (pile / "17-cfr-243.100.xml").write_text(
        "<DIV><HEAD>A rule about words</HEAD></DIV>"
    )
    monkeypatch.setattr(rs, "held", lambda p: [])
    study = tmp_path / "study"
    got = rs.main(["run", "--pile", str(tmp_path / "pile"), "--to", str(tmp_path / "out"),
                   "--dry", "--box", str(study)])  # fmt: skip
    assert got == 0, capsys.readouterr().out
    rows = [json.loads(x) for x in (study / "record.jsonl").read_text().splitlines()]
    verdicts = [r for r in rows if r["kind"] == "verdict"]
    assert [r["gate"] for r in verdicts] == [
        f"blackout-rules:dry:S{i}" for i in (1, 2, 3)
    ]
    assert {r["state"] for r in verdicts} == {"wired"}
    res = json.loads((tmp_path / "out" / "results.json").read_text())
    assert res["dry"] is True and all(a["hit"] for a in res["asked"]["workers"])


@pytest.mark.parametrize("name", ["workers", "offtopic", "nonsense"])
def test_no_question_file_holds_an_email_address(name):
    import re

    text = (HERE / "questions" / f"{name}.txt").read_text(encoding="utf-8")
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
