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
