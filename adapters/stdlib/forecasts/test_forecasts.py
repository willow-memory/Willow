"""forecasts: a wager written before the outcome, an outcome that counts only
once the person seals it, and the scores over what is settled."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "forecasts.py"
spec = importlib.util.spec_from_file_location("forecasts", SCRIPT)
fc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fc)
NOW = ["--now", "2026-11-01T09:00:00Z"]


def run(*argv: str, script: Path = SCRIPT) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *argv],
                          capture_output=True, text=True)  # fmt: skip


def make(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("The bees swarmed in May.\n")
    box = tmp_path / "box"
    got = run("init", "--box", str(box), "--pile", str(pile),
              "--key", str(tmp_path / "key"), *NOW, script=KERNEL)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return box


def rows(box: Path) -> list[dict]:
    got, breaks = fc.kernel.read(box / "record.jsonl")
    assert breaks == []
    return got


def wager(box: Path, p: str, claim: str) -> int:
    got = run("wager", "--box", str(box), "--p", p, *NOW, claim)
    assert got.returncode == 0, got.stderr
    return rows(box)[-1]["n"]


def settle(box: Path, n: int, said: str, seal: bool = True) -> str:
    got = run("settle", "--box", str(box), *NOW, str(n), said)
    assert got.returncode == 42 and "waiting on your seal" in got.stdout, got.stderr
    subj = rows(box)[-1]["subject"]
    if seal:  # the person's act, with their key
        s = run("seal", "--box", str(box), subj, *NOW, script=KERNEL)
        assert s.returncode == 0, s.stderr
    return subj


def test_a_wager_keeps_its_p_and_the_claims_hash_never_its_words(tmp_path):
    box = make(tmp_path)
    n = wager(box, "0.8", "the bees swarm before June")
    row = rows(box)[n]
    assert row["kind"] == "wager" and row["p"] == 0.8 and row["who"] == "forecasts"
    assert row["claim"] == fc.kernel.h256("the bees swarm before June")
    assert "bees" not in (box / "record.jsonl").read_text()


def test_an_outcome_counts_only_once_the_person_seals_it(tmp_path):
    box = make(tmp_path)
    got = run("score", "--box", str(box))
    assert got.returncode == 42 and "no wagers yet" in got.stdout
    n = wager(box, "0.8", "the bees swarm before June")
    got = run("score", "--box", str(box))
    assert got.returncode == 42 and "1 open of 1 wagers" in got.stdout
    settle(box, n, "yes", seal=False)
    assert fc.outcomes(box, rows(box))[n]["state"] == "waiting"
    got = run("score", "--box", str(box))
    assert got.returncode == 42 and f"row {n}: waiting" in got.stdout
    assert "nothing settled yet" in got.stdout
    assert not any(r["kind"] == "seal" for r in rows(box)), "code never seals"


def test_the_scores_over_what_is_settled(tmp_path):
    box = make(tmp_path)
    a = wager(box, "0.8", "the bees swarm before June")
    b = wager(box, "0.3", "it rains on the fete")
    wager(box, "0.6", "the hives come through winter")
    settle(box, a, "yes")
    settle(box, b, "no")
    told = fc.outcomes(box, rows(box))
    assert told[a] == {"p": 0.8, "state": "settled", "happened": True}
    assert told[b] == {"p": 0.3, "state": "settled", "happened": False}
    got = run("score", "--box", str(box))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "2 settled, 1 open of 3 wagers",
        "Brier 0.065  log score 0.290  over 2 settled",
        "  said 0.7-0.8: right 100% of 1",
        "  said 0.8-0.9: right 100% of 1",
    ]
    got = run("settle", "--box", str(box), *NOW, str(a), "no")
    assert got.returncode == 2 and "settled already" in got.stderr


def test_both_outcomes_sealed_is_said_and_not_scored(tmp_path):
    box = make(tmp_path)
    n = wager(box, "0.7", "the bees swarm before June")
    first = settle(box, n, "yes", seal=False)
    settle(box, n, "no")
    assert run("seal", "--box", str(box), first, *NOW, script=KERNEL).returncode == 0
    assert fc.outcomes(box, rows(box))[n]["state"] == "conflicting"
    got = run("score", "--box", str(box))
    assert got.returncode == 42 and f"row {n}: conflicting" in got.stdout


def test_a_sealed_outcome_whose_file_changed_is_broken(tmp_path):
    box = make(tmp_path)
    n = wager(box, "0.7", "the bees swarm before June")
    subj = settle(box, n, "yes")
    f = box / "proposals" / f"{subj.split(':')[1]}.json"
    prop = json.loads(f.read_text())
    prop["data"] = prop["data"].replace("true", "false")
    f.write_text(json.dumps(prop))
    assert fc.outcomes(box, rows(box))[n]["state"] == "broken"
    got = run("score", "--box", str(box))
    assert got.returncode == 2 and f"row {n}: broken" in got.stdout


def test_the_scores_are_the_one_scripts():
    assert fc.brier(0.8, True) == pytest.approx(0.04)
    assert fc.brier(0.5, False) == 0.25
    assert fc.log_score(0.8, False) == pytest.approx(1.6094379)
    assert fc.log_score(1.0, False) == pytest.approx(20.7232658)
    assert fc.fold((0.3, False)) == (0.7, True) and fc.fold((0.5, True)) == (0.5, True)
    got = fc.bins([(0.5, True), (0.55, False), (1.0, True), (0.9, False)])
    assert [(b["lo"], b["n"], b["hit_rate"]) for b in got] == [
        (0.5, 2, 0.5), (0.6, 0, None), (0.7, 0, None), (0.8, 0, None), (0.9, 2, 0.5),
    ]  # fmt: skip


def test_a_bad_command_line_or_box_is_refused(tmp_path):
    box = make(tmp_path)
    n = wager(box, "0.8", "the bees swarm")
    b = str(box)
    for argv in ([], ["fly"], ["wager", "--box", b, "claim"],
                 ["wager", "--box", b, "--p", "1", "claim"],
                 ["wager", "--box", b, "--p", "0.001", "claim"],
                 ["wager", "--box", b, "--p", "x", "claim"],
                 ["wager", "--box", b, "--p", "0.5"],
                 ["wager", "--box", b, "--p", "0.5", "--top", "3", "c"],
                 ["settle", "--box", b, str(n)], ["settle", "--box", b, "²", "yes"],
                 ["settle", "--box", b, "--p", "0.5", str(n), "yes"],
                 ["settle", "--box", b, str(n), "maybe"],
                 ["score", "--box", b, "x"], ["score", "--box", b, *NOW],
                 ["score", "--box", ""]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "forecasts.py" in got.stderr, argv
    got = run("settle", "--box", b, "0", "yes")
    assert got.returncode == 2 and "row 0 is not a wager" in got.stderr
    got = run("score", "--box", str(tmp_path / "nobox"))
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    rec = box / "record.jsonl"
    rec.write_text(rec.read_text().replace('"wager"', '"wages"', 1))
    got = run("score", "--box", b)
    assert got.returncode == 2 and "doesn't verify" in got.stderr
