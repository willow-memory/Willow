"""pools, the trace: a step's row says what was seen (its exit, a report's
state, the rows it added, the map it wrote, the places it named, salted), the
pile is left as it was, and nothing of the pile's words is in a row."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import trace  # noqa: E402

STEPS = ["markdown", "csv-rows", "dice", "pii-audit", "almanac-keep"]


def pile_at(tmp: Path) -> Path:
    pile = tmp / "pile"
    (pile / "notes").mkdir(parents=True)
    (pile / "garden.md").write_text(
        "Tomatoes want sun.\n\nWater them at dusk.\n\nCall 555-0142 about zebrafinch seed.\n"
    )
    (pile / "notes" / "spend.csv").write_text(
        "date,what,amount\n2026-05-04,seeds,12.50\n"
    )
    return pile


def traced(tmp: Path, salt: str = "a salt", name: str = "work") -> dict[str, dict]:
    args = ["pile", "--pile", str(tmp / "pile"), "--name", "tiny", "--salt", salt,
            "--work", str(tmp / name), "--to", str(tmp / f"{name}.jsonl")]  # fmt: skip
    for step in STEPS:
        args += ["--only", step]
    assert trace.main(args) == 0
    return {
        r["step"]: r
        for r in map(json.loads, (tmp / f"{name}.jsonl").read_text().splitlines())
    }


def test_a_row_says_what_was_seen_and_keeps_none_of_the_piles_words(tmp_path):
    pile = pile_at(tmp_path)
    before = trace.manifest(pile)
    rows = traced(tmp_path)
    assert list(rows) == STEPS and trace.manifest(pile) == before, (
        "the pile is as it was"
    )
    assert all(
        r["pile"] == "tiny" and r["manifest"] == before[0] and r["breaches"] == 0
        for r in rows.values()
    )
    assert rows["markdown"]["maps"] == 1 and rows["csv-rows"]["maps"] == 1, (
        "each wrote a mirror's map"
    )
    assert rows["markdown"]["wrote"] == {".txt": 1} and rows["markdown"]["exit"] == 0
    assert rows["dice"]["rows"] == {"roll": 1} and rows["dice"]["maps"] == 0
    assert rows["pii-audit"]["state"] in ("populated", "empty")
    assert (
        rows["almanac-keep"]["exit"] == 2
        and rows["almanac-keep"]["refusal_names"] == "the pile"
    )
    assert all(len(r["card"]) == len(r["code"]) == 64 for r in rows.values())
    text = (tmp_path / "work.jsonl").read_text()
    for word in (
        "zebrafinch",
        "Tomatoes",
        "555-0142",
        "garden.md",
        "spend.csv",
        str(tmp_path),
    ):
        assert word not in text, word
    assert not (tmp_path / "work" / "steps").exists() or not any(
        (tmp_path / "work" / "steps").iterdir()
    )


def test_a_place_is_hashed_with_the_piles_salt_and_goes_back_through_a_map(tmp_path):
    pile = pile_at(tmp_path)
    known = set(trace.manifest(pile)[1])
    out = f"  garden.md:3  a thing\n  {pile}/notes/spend.csv, and (garden.md:3) again; nothing.md:1\n"
    assert trace.places(pile, known, out) == [
        ("garden.md", "line 3", False),
        ("notes/spend.csv", "", False),
    ]
    # a mirror in the pile, with its map: a place in it is the original's
    (pile / "mirror" / ".places").mkdir(parents=True)
    (pile / "mirror" / "garden.md.txt").write_text(
        "Tomatoes want sun.\n\nWater them at dusk.\n"
    )
    (pile / "mirror" / ".places" / "garden.md.txt.json").write_text(
        json.dumps({"source": "garden.md", "places": {"1": "line 1", "3": "line 3"}}))  # fmt: skip
    known = set(trace.manifest(pile)[1])
    assert trace.places(pile, known, "mirror/garden.md.txt:4 x") == [
        ("garden.md", "line 3", True)
    ]
    one = traced(tmp_path, "a salt", "one")["pii-audit"]
    other = traced(tmp_path, "another salt", "other")["pii-audit"]
    assert one["out"] == other["out"]
    if one["places"]:
        assert set(one["places"]).isdisjoint(other["places"]), (
            "another salt, other hashes"
        )


def test_a_bad_command_line_or_a_place_inside_the_repository_is_refused(
    tmp_path, capsys
):
    pile = pile_at(tmp_path)
    base = [
        "pile",
        "--pile",
        str(pile),
        "--name",
        "tiny",
        "--salt",
        "s",
        "--to",
        str(tmp_path / "r"),
    ]
    assert trace.main([]) == 2 and trace.main(base) == 2
    assert (
        trace.main([*base, "--work", str(HERE / "work")]) == 2
        and not (HERE / "work").exists()
    )
    assert (
        trace.main([*base, "--work", str(tmp_path / "w"), "--only", "no-such-add-on"])
        == 2
    )
    assert "not a step" in capsys.readouterr().err


def test_a_stack_runs_in_its_order_on_one_box_and_a_taker_sees_what_the_giver_left(
    tmp_path,
):
    pile = pile_at(tmp_path)
    steps = trace.table(trace.contract())
    args = {
        n: {"args": [a.replace("{tmp}", "{tmp}/" + n) for a in steps[n][1]]}
        for n in ("dice", "game-master")
    }
    grid = tmp_path / "manifest.json"
    grid.write_text(json.dumps({"steps": args, "stacks": [
        {"id": "pair/dice--game-master", "steps": ["dice", "game-master"]},
        {"id": "pair/game-master--dice", "steps": ["game-master", "dice"]}]}))  # fmt: skip
    base = ["--pile", str(pile), "--name", "tiny", "--salt", "s"]
    assert trace.main(["stack", "--grid", str(grid), "--stack", "pair/dice--game-master", "--stack",
                       "pair/game-master--dice", *base, "--work", str(tmp_path / "w"),
                       "--to", str(tmp_path / "s.jsonl")]) == 0  # fmt: skip
    rows = [json.loads(x) for x in (tmp_path / "s.jsonl").read_text().splitlines()]
    assert [(r["stack"].split("/")[1], r["at"], r["step"]) for r in rows] == [
        ("dice--game-master", 0, "dice"), ("dice--game-master", 1, "game-master"),
        ("game-master--dice", 0, "game-master"), ("game-master--dice", 1, "dice")]  # fmt: skip
    assert trace.main(["pile", *base, "--only", "game-master", "--work", str(tmp_path / "a"),
                       "--to", str(tmp_path / "a.jsonl")]) == 0  # fmt: skip
    alone = json.loads((tmp_path / "a.jsonl").read_text())
    after, before = rows[1], rows[2]
    assert before["out"] == alone["out"], "before the giver, it is as it is alone"
    assert after["out"] != alone["out"], (
        "after the giver, it has the giver's roll to tell of"
    )
    assert trace.main(["stack", "--grid", str(grid), "--stack", "no/such", *base,
                       "--work", str(tmp_path / "x"), "--to", str(tmp_path / "x.jsonl")]) == 2  # fmt: skip
    assert (
        trace.main(
            [
                "stack",
                *base,
                "--work",
                str(tmp_path / "y"),
                "--to",
                str(tmp_path / "y.jsonl"),
            ]
        )
        == 2
    )


def test_the_runs_own_folders_and_the_time_of_day_are_taken_out_before_hashing(
    tmp_path,
):
    fill = {"box": "/w/1/box", "pile": "/p", "tmp": "/w/1/tmp"}
    one = trace.steady(
        "wrote /w/1/tmp/x/a.txt from /p/g.md at 2026-11-12T13:01:02Z\n",
        fill,
        Path("/w/1/tmp/x"),
    )
    fill2 = {"box": "/w/2/box", "pile": "/p", "tmp": "/w/2/tmp"}
    two = trace.steady(
        "wrote /w/2/tmp/x/a.txt from /p/g.md at 2026-11-13 09:44\n",
        fill2,
        Path("/w/2/tmp/x"),
    )
    assert one == two == "wrote {mine}/a.txt from {pile}/g.md at {when}\n"


def _memo_grid(tmp: Path, stacks: dict[str, list[str]]) -> Path:
    steps = trace.table(trace.contract())
    names = {n for v in stacks.values() for n in v}
    args = {
        n: {"args": [a.replace("{tmp}", "{tmp}/" + n) for a in steps[n][1]]}
        for n in names
    }
    grid = tmp / "manifest.json"
    grid.write_text(json.dumps({"steps": args, "stacks": [{"id": k, "steps": v} for k, v in stacks.items()]}))  # fmt: skip
    return grid


def _memo_run(
    tmp: Path, grid: Path, ids: list[str], name: str, *more: str
) -> list[dict]:
    args = ["stack", "--grid", str(grid), *[x for i in ids for x in ("--stack", i)],
            "--pile", str(tmp / "pile"), "--name", "tiny", "--salt", "s",
            "--work", str(tmp / name), "--to", str(tmp / f"{name}.jsonl"), *more]  # fmt: skip
    assert trace.main(args) == 0
    return [json.loads(x) for x in (tmp / f"{name}.jsonl").read_text().splitlines()]


def test_the_memory_reuses_a_step_whose_reads_are_as_they_were_and_runs_one_whose_arent(
    tmp_path,
):
    pile_at(tmp_path)
    stacks = {"a": ["markdown", "csv-rows", "game-master"], "b": ["markdown", "csv-rows", "game-master"],
              "c": ["dice", "game-master"]}  # fmt: skip
    grid = _memo_grid(tmp_path, stacks)
    memo = ["--memo", str(tmp_path / "memo"), "--check", "0"]
    rows = _memo_run(tmp_path, grid, ["a", "b", "c"], "w", *memo)
    got = {(r["stack"], r["step"]): r for r in rows}
    assert [got["a", s]["memo"] for s in stacks["a"]] == ["ran", "ran", "ran"]
    assert [got["b", s]["memo"] for s in stacks["b"]] == ["reused", "reused", "reused"]
    for s in stacks["b"]:
        assert all(got["b", s][k] == got["a", s][k] for k in trace.SAME), s
    assert got["c", "dice"]["memo"] == "ran", (
        "a step that adds a row is never remembered"
    )
    assert got["c", "game-master"]["memo"] == "ran", (
        "the record it reads has the giver's row now"
    )
    assert got["c", "game-master"]["out"] != got["a", "game-master"]["out"]
    plain = _memo_run(tmp_path, grid, ["a", "b", "c"], "p")
    for r, q in zip(rows, plain):
        assert "memo" not in q
        if "dice" in stacks[r["stack"]]:
            continue  # dice rolls at random, and what reads its roll tells of it
        assert all(r[k] == q[k] for k in trace.SAME), (r["stack"], r["step"])


def test_a_remembered_step_drawn_to_be_checked_runs_and_is_held_to_the_memory(tmp_path):
    pile_at(tmp_path)
    grid = _memo_grid(
        tmp_path, {"a": ["markdown", "game-master"], "b": ["markdown", "game-master"]}
    )
    never = tmp_path / "never.json"
    never.write_text(json.dumps(["game-master"]))
    rows = _memo_run(tmp_path, grid, ["a", "b"], "w", "--memo", str(tmp_path / "m"), "--check", "1",
                     "--never", str(never))  # fmt: skip
    got = {(r["stack"], r["step"]): r for r in rows}
    assert (
        got["b", "markdown"]["memo"] == "checked"
        and got["b", "markdown"]["memo_same"] is True
    )
    assert got["a", "game-master"]["memo"] == got["b", "game-master"]["memo"] == "never"


def test_reads_count_only_on_the_runs_roots_and_a_program_started_ends_the_memory(
    tmp_path,
):
    roots = {r: tmp_path / r for r in ("pile", "box", "tmp")}
    for p in roots.values():
        p.mkdir()
    (roots["pile"] / "a.md").write_text("x")
    mine = roots["tmp"] / "me"
    log = tmp_path / "log"
    log.write_text("\n".join(json.dumps({"e": e, "p": str(p)}) for e, p in [
        ("open", roots["pile"] / "a.md"), ("list", roots["pile"]), ("open", mine / "own.txt"),
        ("open", Path("/etc/hostname")), ("open", roots["box"] / "gone")]) + "\n")  # fmt: skip
    got = trace._reads(log, roots, mine)
    assert set(got) == {"file pile a.md", "list pile .", "file box gone"}
    assert got["file box gone"] == "absent"
    log.write_text(log.read_text() + json.dumps({"e": "run", "p": "git"}) + "\n")
    assert trace._reads(log, roots, mine) is None


def test_the_memory_is_refused_inside_the_repository_or_off_a_stack(tmp_path):
    pile_at(tmp_path)
    grid = _memo_grid(tmp_path, {"a": ["markdown"]})
    base = [
        "--pile",
        str(tmp_path / "pile"),
        "--name",
        "t",
        "--salt",
        "s",
        "--to",
        str(tmp_path / "o.jsonl"),
    ]
    assert trace.main(["stack", "--grid", str(grid), "--stack", "a", *base, "--work", str(tmp_path / "w1"),
                       "--memo", str(trace.ROOT / "memo-here")]) == 2  # fmt: skip
    assert (
        trace.main(
            [
                "pile",
                *base,
                "--work",
                str(tmp_path / "w2"),
                "--memo",
                str(tmp_path / "m"),
            ]
        )
        == 2
    )
    assert trace.main(["stack", "--grid", str(grid), "--stack", "a", *base, "--work", str(tmp_path / "w3"),
                       "--check", "0.5"]) == 2  # fmt: skip


def test_nothing_remembered_on_one_day_is_reused_on_the_next(tmp_path, monkeypatch):
    """syllabus counts days from today, and the clock is a read no audit event
    names: on Kaggle a run that crossed midnight reused yesterday's row."""
    pile_at(tmp_path)
    grid = _memo_grid(tmp_path, {"a": ["markdown"], "b": ["markdown"]})
    memo = ["--memo", str(tmp_path / "m"), "--check", "0"]
    monkeypatch.setattr(trace, "today", lambda: "2026-11-13")
    first = _memo_run(tmp_path, grid, ["a", "b"], "w1", *memo)
    assert [r["memo"] for r in first] == ["ran", "reused"]
    monkeypatch.setattr(trace, "today", lambda: "2026-11-14")
    second = _memo_run(tmp_path, grid, ["a", "b"], "w2", *memo)
    assert [r["memo"] for r in second] == ["ran", "reused"], (
        "the new day runs it again, then remembers"
    )
