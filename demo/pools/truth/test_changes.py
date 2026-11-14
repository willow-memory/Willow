"""changes.py, on planted rows: a stack is held to its own run's alone rows,
so a step that counts days doesn't break; a step that prints the same on an
empty pile hasn't fired; a giver that moves its taker is a held bridge
beyond the controls; a kind stack ties a reader to the writer's rows; and
the pools are what changed what."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("changes", HERE / "changes.py")
ch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ch)


def _row(step, out, stack=None, at=0, lines=2, rows=None, groups=None, pile="p"):
    r = {"pile": pile, "step": step, "out": out, "exit": 0, "timed_out": False, "breaches": 0,
         "state": None, "lines": lines, "rows": rows or {}, "row_groups": groups or []}  # fmt: skip
    if stack:
        r.update(stack=stack, at=at)
    return r


def _write(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


GRID = {"stacks": [
    {"id": "single/syllabus", "way": "single", "steps": ["syllabus"]},
    {"id": "bridge/dice--game-master", "way": "bridge", "steps": ["dice", "game-master"]},
    {"id": "kind/dice--serve", "way": "kind", "steps": ["dice", "serve"]},
    {"id": "kind/quiz--serve", "way": "kind", "steps": ["quiz", "serve"]},
]}  # fmt: skip
PAIRS = {
    "stacks": [
        {"id": f"pair-{i}", "way": "no-bridge", "steps": ["a", "b"]} for i in range(9)
    ]
}


def _run(tmp: Path) -> Path:
    run = tmp / "run"
    run.mkdir()
    # alone today: syllabus says "in 3 days" today; empty pile: echo prints the same as on the pile
    _write(run / "rows-alone.jsonl", [_row("syllabus", "today"), _row("dice", "r"), _row("game-master", "gm0"),
           _row("serve", "s0"), _row("quiz", "q"), _row("a", "a0"), _row("b", "b0"), _row("echo", "same")])  # fmt: skip
    _write(
        run / "rows-empty.jsonl", [_row("echo", "same"), _row("syllabus", "nothing")]
    )
    stacks = [_row("syllabus", "today", "single/syllabus"),
              _row("dice", "r", "bridge/dice--game-master", 0, rows={"roll": 1}),
              _row("game-master", "gm-rolled", "bridge/dice--game-master", 1),
              _row("dice", "r", "kind/dice--serve", 0, rows={"roll": 1}, groups=["roll:abc"]),
              _row("serve", "s0", "kind/dice--serve", 1),
              _row("quiz", "q", "kind/quiz--serve", 0, rows={"quiz": 1}, groups=["quiz:def"]),
              _row("serve", "s-quizzed", "kind/quiz--serve", 1)]  # fmt: skip
    stacks += [
        r
        for i in range(9)
        for r in (_row("a", "a0", f"pair-{i}", 0), _row("b", "b0", f"pair-{i}", 1))
    ]
    _write(run / "rows-0-0.jsonl", stacks)
    return run


def test_the_same_runs_baseline_the_empty_pile_bridges_kinds_and_pools(tmp_path):
    res = ch.measure([_run(tmp_path)], [GRID, PAIRS])
    p = res["piles"]["p"]
    assert "echo" not in p["fired_steps"] and "syllabus" in p["fired_steps"], (
        "same on nothing is not firing"
    )
    assert p["unsteady"] == [] and p["stack_runs_changed"] == 2, (
        "syllabus held to today's alone: no break"
    )
    assert res["bridges"]["changed"] == 1 and res["controls"]["changed"] == 0
    assert res["bridges_beyond_controls_p"] < 0.2
    moved = {(k["writer"], k["reader"]): k for k in res["kinds"]}
    assert moved["quiz", "serve"]["changed"] and moved["quiz", "serve"]["groups"] == [
        "quiz:def"
    ]
    assert not moved["dice", "serve"]["changed"], "serve doesn't read rolls"
    assert res["pools"] == [["dice", "game-master"], ["quiz", "serve"]]
    text = ch.report(res)
    assert (
        "`dice` then `game-master`" in text
        and "`quiz` (quiz) moved: `serve` (1 piles)" in text
    )


def test_a_step_unsteady_in_the_run_or_in_stage_0_is_held_to_nothing(tmp_path):
    run = _run(tmp_path)
    (run / "run.json").write_text(json.dumps({"never": ["game-master"]}))
    res = ch.measure([run], [GRID, PAIRS])
    assert res["bridges"]["stacks"] == 0 and "game-master" in res["unsteady"]


def test_fisher_is_the_hypergeometric_tail():
    assert abs(ch.fisher_greater(3, 0, 0, 3) - 0.05) < 1e-9
    assert ch.fisher_greater(0, 5, 0, 5) == 1.0


def test_a_bad_command_line_is_refused():
    assert ch.main([]) == 2 and ch.main(["measure", "--run"]) == 2


def test_a_row_from_another_day_than_its_baseline_is_held_to_nothing(tmp_path):
    run = _run(tmp_path)
    rows = [json.loads(x) for x in (run / "rows-0-0.jsonl").read_text().splitlines()]
    for r in rows:
        r["day"] = "2026-11-15" if r["step"] == "game-master" else "2026-11-14"
    (run / "rows-0-0.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    alone = [json.loads(x) for x in (run / "rows-alone.jsonl").read_text().splitlines()]
    (run / "rows-alone.jsonl").write_text(
        "".join(json.dumps({**r, "day": "2026-11-14"}) + "\n" for r in alone)
    )
    res = ch.measure([run], [GRID, PAIRS])
    assert res["bridges"]["stacks"] == 0, (
        "game-master ran after midnight: not held to yesterday's alone"
    )
    assert res["controls"]["stacks"] == 9
