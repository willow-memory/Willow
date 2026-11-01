"""market-calls: a call is forecasts' wager naming its market, made before the
close; the close proposes each outcome, settled only by the person's seal;
the score keeps the losers."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "market_calls.py"
spec = importlib.util.spec_from_file_location("market_calls", SCRIPT)
mc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc)
BEFORE = ["--now", "2026-11-05T09:00:00Z"]
AFTER = ["--now", "2026-11-06T22:00:00Z"]


def run(*argv: str, script: Path = SCRIPT) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *argv],
                          capture_output=True, text=True)  # fmt: skip


def make(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "notes.md").write_text("Index funds, mostly.\n")
    box = tmp_path / "box"
    got = run("init", "--box", str(box), "--pile", str(pile),
              "--key", str(tmp_path / "key"), *BEFORE, script=KERNEL)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return box


def rows(box: Path) -> list[dict]:
    got, breaks = mc.kernel.read(box / "record.jsonl")
    assert breaks == []
    return got


def call(box: Path, p: str, *words: str, now=BEFORE) -> subprocess.CompletedProcess:
    return run("call", "--box", str(box), "--p", p, *now, *words)


def seal_all(box: Path) -> None:
    for r in rows(box):
        if r["kind"] == "settle":
            got = run("seal", "--box", str(box), r["subject"], *AFTER, script=KERNEL)
            assert got.returncode == 0, got.stderr  # the person's act, with their key


def test_a_call_is_a_wager_naming_its_market_and_never_its_words(tmp_path):
    box = make(tmp_path)
    got = call(box, "0.7", "SPY", "up", "2026-11-06")
    assert got.returncode == 0 and "call row 1: SPY up 2026-11-06, p 0.7" in got.stdout
    row = rows(box)[-1]
    assert row["kind"] == "wager" and row["who"] == "market-calls" and row["p"] == 0.7
    assert row["market"] == {"symbol": "SPY", "kind": "up", "close_date": "2026-11-06"}
    assert row["claim"] == mc.kernel.h256("SPY up 2026-11-06")
    got = call(box, "0.4", "SPY", "above:600.0", "2026-11-06")
    assert got.returncode == 0
    assert rows(box)[-1]["market"]["threshold"] == "600.0", "a decimal, exact"


def test_one_call_per_question_made_before_the_market_is_known(tmp_path):
    box = make(tmp_path)
    assert call(box, "0.7", "SPY", "up", "2026-11-06").returncode == 0
    got = call(box, "0.3", "SPY", "up", "2026-11-06")
    assert got.returncode == 2 and "one call per question" in got.stderr
    assert call(box, "0.3", "SPY", "up", "2026-11-09").returncode == 0, "another day"
    late = ["--now", "2026-11-06T13:00:00Z"]
    got = call(box, "0.6", "QQQ", "up", "2026-11-06", now=late)
    assert got.returncode == 2 and "the market may be known" in got.stderr
    early = ["--now", "2026-11-06T12:59:59Z"]
    assert call(box, "0.6", "QQQ", "up", "2026-11-06", now=early).returncode == 0
    run("close", "--box", str(box), *AFTER, "DIA", "2026-11-06", "4", "3")
    got = call(box, "0.6", "DIA", "up", "2026-11-06", now=early)
    assert got.returncode == 2 and "has closed on the record" in got.stderr


def test_the_close_proposes_each_outcome_and_only_the_seal_settles_it(tmp_path):
    box = make(tmp_path)
    call(box, "0.7", "SPY", "up", "2026-11-06")
    call(box, "0.4", "SPY", "above:600", "2026-11-06")
    call(box, "0.6", "QQQ", "up", "2026-11-06")
    got = run(
        "close", "--box", str(box), *AFTER, "SPY", "2026-11-06", "589.50", "585.10"
    )
    assert got.returncode == 42, got.stderr
    assert "row 1 SPY up 2026-11-06: wager 1: it happened" in got.stdout
    assert "row 2 SPY above:600 2026-11-06: wager 2: it didn't" in got.stdout
    assert "QQQ" not in got.stdout, "another symbol waits for its own close"
    c = next(r for r in rows(box) if r["kind"] == "close")
    assert (c["symbol"], c["close"], c["prev_close"]) == ("SPY", "589.50", "585.10")
    assert not any(r["kind"] == "seal" for r in rows(box)), "code never seals"
    got = run("score", "--box", str(box))
    assert got.returncode == 42 and "waiting     row 1" in got.stdout
    again = run(
        "close", "--box", str(box), *AFTER, "SPY", "2026-11-06", "589.5", "585.1"
    )
    assert again.returncode == 0 and "row 1 SPY up 2026-11-06: waiting" in again.stdout
    assert sum(r["kind"] == "close" for r in rows(box)) == 1, "the same close, once"
    got = run("close", "--box", str(box), "SPY", "2026-11-06", "590", "585.10")
    assert got.returncode == 2 and "two closes for one day" in got.stderr


def test_the_score_keeps_the_losers(tmp_path):
    box = make(tmp_path)
    got = run("score", "--box", str(box))
    assert got.returncode == 42 and "no market calls yet" in got.stdout
    call(box, "0.7", "SPY", "up", "2026-11-06")
    call(box, "0.8", "SPY", "above:600", "2026-11-06")
    call(box, "0.5", "QQQ", "up", "2026-11-06")
    call(box, "0.6", "DIA", "up", "2026-11-06")
    got = run("score", "--box", str(box))
    assert got.returncode == 42 and "nothing settled yet" in got.stdout
    run("close", "--box", str(box), *AFTER, "SPY", "2026-11-06", "589.50", "585.10")
    run("close", "--box", str(box), *AFTER, "QQQ", "2026-11-06", "500", "501")
    seal_all(box)
    got = run("score", "--box", str(box))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "right       row 1  SPY up 2026-11-06  p 0.7",
        "wrong       row 2  SPY above:600 2026-11-06  p 0.8",
        "even        row 3  QQQ up 2026-11-06  p 0.5",
        "open        row 4  DIA up 2026-11-06  p 0.6",
        "1 of 3 settled calls right, Brier 0.327",
    ]


def test_a_broken_outcome_is_refused(tmp_path):
    box = make(tmp_path)
    call(box, "0.7", "SPY", "up", "2026-11-06")
    run("close", "--box", str(box), *AFTER, "SPY", "2026-11-06", "589.50", "585.10")
    seal_all(box)
    subj = next(r["subject"] for r in rows(box) if r["kind"] == "settle")
    f = box / "proposals" / f"{subj.split(':')[1]}.json"
    prop = json.loads(f.read_text())
    f.write_text(json.dumps({**prop, "data": prop["data"].replace("true", "false")}))
    got = run("score", "--box", str(box))
    assert got.returncode == 2 and "broken      row 1" in got.stdout


def test_the_answer_is_exact():
    up = {"kind": "up"}
    assert mc.answer(up, "585.10", "585.1") is False, "equal is not up"
    assert mc.answer(up, "585.11", "585.1") is True
    above = {"kind": "above", "threshold": "600"}
    assert mc.answer(above, "600.00", "1") is False
    assert mc.answer(above, "600.01", "1") is True
    assert mc.verdict(0.5, True) == "even" and mc.verdict(0.3, False) == "right"
    assert mc.verdict(0.51, False) == "wrong"


def test_a_bad_command_line_or_box_is_refused(tmp_path):
    box = make(tmp_path)
    b = str(box)
    for argv in ([], ["fly"], ["call", "--box", b, "SPY", "up", "2026-11-06"],
                 ["call", "--box", b, "--p", "0.7", "spy", "up", "2026-11-06"],
                 ["call", "--box", b, "--p", "0.7", "SPY", "down", "2026-11-06"],
                 ["call", "--box", b, "--p", "0.7", "SPY", "above:-1", "2026-11-06"],
                 ["call", "--box", b, "--p", "0.7", "SPY", "above:x", "2026-11-06"],
                 ["call", "--box", b, "--p", "0.7", "SPY", "up", "2026-13-06"],
                 ["call", "--box", b, "--p", "0.7", "SPY", "up", "2026-1-6"],
                 ["call", "--box", b, "--p", "1", "SPY", "up", "2026-11-06"],
                 ["call", "--box", b, "--p", "x", "SPY", "up", "2026-11-06"],
                 ["call", "--box", b, "--p", "", "SPY", "up", "2026-11-06"],
                 ["close", "--box", b, "SPY", "2026-11-06", "1"],
                 ["close", "--box", b, "SPY", "2026-11-06", "0", "1"],
                 ["close", "--box", b, "SPY", "2026-11-06", "1", "nan"],
                 ["close", "--box", b, "--p", "0.5", "SPY", "2026-11-06", "1", "2"],
                 ["score", "--box", b, "SPY"], ["score", "--box", b, *AFTER],
                 ["score", "--box", b, "--x", "y"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "market_calls.py" in got.stderr, argv
    assert len(rows(box)) == 1, "nothing written by a refusal"
    got = run("score", "--box", str(tmp_path / "nobox"))
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    call(box, "0.7", "SPY", "up", "2026-11-06")
    rec = box / "record.jsonl"
    rec.write_text(rec.read_text().replace('"wager"', '"wages"', 1))
    got = run("score", "--box", b)
    assert got.returncode == 2 and "doesn't verify" in got.stderr
