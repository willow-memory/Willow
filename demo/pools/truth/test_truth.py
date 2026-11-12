"""truth.py: the pools study's rules hold on rows made to test them, each
rule shown to fail when broken, and the report made byte for byte."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("truth", HERE / "truth.py")
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
SAMPLE = HERE / "sample"


def pairs_of(m: dict, level: str | None = None) -> set:
    return {(p["a"], p["b"]) for p in m["pairs"] if level in (None, p["level"])}


# ── the dry runs, and that each can fail ─────────────────────────────────────
def test_nonsense_rows_give_no_pair_and_no_duplicate():
    m = t.measure(*t.dry_nonsense(), t.DRY_GRID)
    assert m["pairs"] == [] and m["duplicates"] == [] and m["steps"] == 30


def test_the_planted_rows_give_back_what_was_planted_and_nothing_else():
    m = t.measure(*t.dry_planted(), t.DRY_GRID)
    assert pairs_of(m) == {("a", "b"), ("c", "d"), ("r", "t")}
    assert [(d["a"], d["b"]) for d in m["duplicates"]] == [("c", "d")]
    assert [g["kind"] for g in m["gaps"]] == [".zzz"] and m["gaps"][0]["ideas"] == [
        "zz-reader"
    ]
    assert m["neighbours"]["a"] == ["b"] and "x" in m["no_partner"]


def test_firing_together_alone_never_makes_a_pair():
    """a and r fire on the same ten piles and name no place in common: with
    the place rule taken off they pair, so it is the rule that keeps them
    apart (CONST-IV-9: a check shown to fail on a planted break)."""
    m = t.measure(*t.dry_planted(), t.DRY_GRID)
    assert ("a", "r") not in pairs_of(m)
    loose = {**t.RULES, "pair_jaccard": 0.0}
    rows, shapes, cards = t.dry_planted()
    jp = t.measure(rows, shapes, cards, t.DRY_GRID, loose)
    assert ("a", "r") in pairs_of(jp)


def test_the_reader_and_its_taker_meet_only_through_the_map():
    off = t.measure(*t.dry_planted(map_on=False), t.DRY_GRID)
    assert ("r", "t") not in pairs_of(off, "acts on the same thing")


def test_a_taker_meets_its_reader_only_in_a_stack():
    """Alone, no step is given another's mirror, so the reader and its
    taker share no place there: with the stack rows dropped, they don't
    pair; the places a step names are read from all its runs."""
    rows, shapes, cards = t.dry_planted()
    alone = [r for r in rows if "stack" not in r]
    assert ("r", "t") not in pairs_of(t.measure(alone, shapes, cards, t.DRY_GRID))
    assert ("r", "t") in pairs_of(
        t.measure(rows, shapes, cards, t.DRY_GRID), "acts on the same thing"
    )


def test_shuffled_piles_lose_every_planted_pair():
    m = t.measure(*t.dry_shuffled(), t.DRY_GRID)
    assert not pairs_of(m) & {("a", "b"), ("c", "d"), ("r", "t")}


def test_the_false_discovery_rule_is_what_holds_back_chance():
    """With q at 1 every pair tested is kept: BH is doing the work."""
    rows, shapes, cards = t.dry_nonsense(steps=12)
    for r in rows:
        r["places"] = r["files"] = ["shared"]  # every row names the same place
    strict = t.measure(rows, shapes, cards, t.DRY_GRID)
    loose = t.measure(rows, shapes, cards, t.DRY_GRID, {**t.RULES, "fdr_q": 1.0})
    assert len(loose["pairs"]) > len(strict["pairs"])


def test_dry_writes_its_verdicts_as_kernel_rows_named_apart(tmp_path):
    pile, box = tmp_path / "pile", tmp_path / "box"
    pile.mkdir()
    (pile / "a.md").write_text("a\n")
    subprocess.run([sys.executable, str(ROOT / "kernel.py"), "init", "--box", str(box),
                    "--pile", str(pile), "--key", str(tmp_path / "k")], check=True, capture_output=True)  # fmt: skip
    assert t.main(["dry", "--box", str(box)]) == 0
    rows = [json.loads(x) for x in (box / "record.jsonl").read_text().splitlines()]
    gates = [r["gate"] for r in rows if r["kind"] == "verdict"]
    assert gates == [
        "study:dry:nonsense",
        "study:dry:planted",
        "study:dry:map-off",
        "study:dry:shuffled",
    ]
    assert all(r["verdict"] == "pass" for r in rows if r["kind"] == "verdict")
    assert subprocess.run([sys.executable, str(ROOT / "kernel.py"), "verify", "--box", str(box)],
                          capture_output=True).returncode == 0  # fmt: skip


# ── the measure's parts ──────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "row, want",
    [
        ({"exit": 0, "state": "populated", "lines": 4}, "fires"),
        ({"exit": 42, "state": None, "lines": 1}, "fires"),
        ({"exit": 0, "state": "empty", "lines": 1}, "silent"),
        ({"exit": 0, "state": None, "lines": 0}, "silent"),
        ({"exit": 2, "state": None, "lines": 1}, "refused"),
        ({"exit": 0, "state": "populated", "lines": 4, "breaches": 1}, "refused"),
        ({"exit": None, "timed_out": True, "lines": 4}, "refused"),
    ],
)
def test_what_fires_is_the_rules_words(row, want):
    assert t.verdict(row) == want


def test_the_tail_and_the_false_discovery_rate():
    assert t.tail_p(10, 20, 10, 10) == pytest.approx(1 / 184756)
    assert t.tail_p(0, 20, 10, 10) == pytest.approx(1.0)
    assert t.bh({"x": 0.001, "y": 0.02, "z": 0.9}, 0.05) == {"x", "y"}
    assert t.bh({"x": 0.04, "y": 0.9}, 0.05) == set()


def test_overlap_is_within_a_pile_never_across():
    a = {"p": {"places": ["1", "2"]}, "q": {"places": ["3"]}}
    b = {"p": {"places": ["2"]}, "q": {"places": ["1"]}}  # "1" in q is q's own
    assert t.jaccard(a, b, ["p", "q"], "places") == pytest.approx(
        1 / 4
    )  # p: 1 of 2; q: 0 of 2


def test_a_card_applies_where_its_kind_of_file_is():
    assert t.applies({"reads": []}, {})
    assert t.applies({"reads": [".csv"]}, {".csv": 2})
    assert not t.applies({"reads": [".csv"]}, {".md": 2})
    assert t.applies({"reads": ["package-lock.json"]}, {".json": 1})


def test_a_shape_keeps_no_word_and_hashes_as_the_trace_does(tmp_path):
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "garden.md").write_text("Tomatoes want sun.\n")
    (tmp_path / ".hidden").write_text("x\n")
    got = t.shape(tmp_path, "pile-1", "salt")
    assert got["kinds"] == {".md": 1}
    assert got["files"] == {t.salted("salt", "notes/garden.md"): ".md"}
    assert "garden" not in json.dumps(got) and "Tomatoes" not in json.dumps(got)


# ── bridges and order ────────────────────────────────────────────────────────
GRID = {
    "steps": {n: {} for n in ("giver", "taker", "far", "lone", "other")},
    "bridges": [{"from": "giver", "to": "taker", "by": ["card"]}, {"from": "taker", "to": "far", "by": ["record"]}],
    "stacks": [{"id": "s1", "steps": ["giver", "lone", "taker", "far"]},
               {"id": "s2", "steps": ["taker", "giver", "lone"]}],
}  # fmt: skip


def test_a_step_is_reached_by_a_bridge_from_earlier_in_its_stack_or_through_one():
    g = t.bridge_map(GRID)
    assert t.reached(GRID["stacks"][0]["steps"], 2, g)  # taker, after giver
    assert t.reached(GRID["stacks"][0]["steps"], 3, g)  # far, through taker
    assert not t.reached(GRID["stacks"][0]["steps"], 1, g)  # lone
    assert not t.reached(GRID["stacks"][1]["steps"], 0, g)  # taker, giver after


def test_a_change_with_no_bridge_to_it_breaks_the_null_and_one_with_does_not():
    alone = [{"pile": "p", "step": s, "exit": 0, "state": "populated", "lines": 1, "out": f"{s}-alone"}
             for s in ("giver", "lone", "taker", "far")]  # fmt: skip
    ran = [{**r, "stack": "s1", "at": i, "out": r["out"] if r["step"] == "giver" else "changed"}
           for i, r in enumerate(alone[i] for i in (0, 1, 2, 3))]  # fmt: skip
    m = t.measure(alone + ran, [{"pile": "p", "kinds": {}, "files": {}}], {}, GRID)
    assert [b["step"] for b in m["order_breaks"]] == ["lone"]
    # lone draws at random: run alone twice it differs, so it is unsteady,
    # listed apart, and no stack is held to it
    again = [{**alone[1], "out": "lone-again"}]
    m = t.measure(
        alone + again + ran, [{"pile": "p", "kinds": {}, "files": {}}], {}, GRID
    )
    assert m["order_breaks"] == [] and m["unsteady"] == ["lone"]


def test_the_seeded_pairs_have_no_bridge_and_are_the_same_every_time():
    grid = {
        "steps": {f"s{i}": {} for i in range(30)},
        "bridges": [{"from": "s0", "to": "s1"}],
    }
    one = t.no_bridge_pairs(grid, 50, 9)
    assert one == t.no_bridge_pairs(grid, 50, 9) and len(one) == 50
    assert ["s0", "s1"] not in one and ["s1", "s0"] not in one
    m = t.pairs_manifest({**grid, "stacks": []})
    assert len(m["stacks"]) == 2 * min(t.RULES["no_bridge_pairs"], 434)
    assert {s["way"] for s in m["stacks"]} == {"no-bridge"}


# ── probes ───────────────────────────────────────────────────────────────────
def test_a_probe_hits_where_the_kernel_serves_its_answer_and_misses_a_split_entry(
    tmp_path,
):
    pile = tmp_path / "pile"
    (pile / "good").mkdir(parents=True)
    (pile / "good" / "dict.md").write_text("Saudade: a longing for something absent.\n")
    (pile / "split").mkdir()
    (pile / "split" / "dict.md").write_text(
        "Saudade:\n\na longing for something absent.\n"
    )
    probes = [
        {"id": "c1", "gap": "control", "reader": "markdown", "folder": "good", "expect": "hit",
         "question": "saudade longing absent", "answer": {"file": "dict.md", "line": 1}},
        {"id": "g1", "gap": "headword split from its gloss", "reader": "markdown", "folder": "split",
         "expect": "miss", "question": "saudade longing absent", "answer": {"file": "dict.md", "line": 1}},
    ]  # fmt: skip
    got = t.probe(probes, pile)
    assert [r["hit"] for r in got] == [True, False]
    assert "saudade" not in json.dumps(got)  # the question kept as a hash


def test_a_gap_is_found_only_when_its_readers_controls_hit():
    def res(gap, hit, reader="csv-rows"):
        return {
            "id": "x",
            "gap": gap,
            "reader": reader,
            "expect": "",
            "hit": hit,
            "question": "",
        }

    found = [res("control", True)] + [res("tsv quotes", False)] * 3
    assert t.probes_held(found)[0]["state"] == "found"
    broken = [res("control", False)] + [res("tsv quotes", False)] * 3
    assert t.probes_held(broken)[0]["state"] == "can't be read"
    few = [res("control", True)] + [res("tsv quotes", False)] * 2
    assert t.probes_held(few)[0]["state"] == "can't be read"
    read = [res("control", True)] + [res("tsv quotes", True)] * 3
    assert t.probes_held(read)[0]["state"] == "not found"


# ── the report ───────────────────────────────────────────────────────────────
def test_the_report_is_made_from_the_result_byte_for_byte():
    """sample/: the planted dry run's result and its report, kept; made
    again here, and held to them byte for byte."""
    result = t.measure(*t.dry_planted(), t.DRY_GRID)
    kept = json.loads((SAMPLE / "planted.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(result, sort_keys=True)) == kept
    assert t.report(kept) == (SAMPLE / "planted.md").read_text(encoding="utf-8")
    assert t.report(kept) == t.report(json.loads(json.dumps(kept)))


def test_every_claim_names_its_rows_and_says_how_many():
    text = t.report(t.measure(*t.dry_planted(), t.DRY_GRID))
    for line in text.splitlines():
        if line.startswith("- `") and (" and `" in line and "rows:" not in line):
            raise AssertionError(f"a pair or duplicate without its rows: {line}")
    assert "10 rows" in text or "20 rows" in text


def test_the_cards_are_read_as_the_rules_need_them():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "adapters" / "stdlib" / "csv-rows").mkdir(parents=True)
        (root / "adapters" / "stdlib" / "csv-rows" / "README.md").write_text(
            "<!-- willow-addon\nsection: Reading\nline: Rows.\nrole: reads\nreads: .csv, .tsv\n-->\n# x\n"
        )
        (root / "adapters" / "planned.json").write_text(
            json.dumps(
                [
                    {
                        "name": "hurdat2",
                        "line": "HURDAT2 storm tracks.",
                        "section": "Reading",
                    }
                ]
            )
        )
        got = t.cards(root)
    assert got["csv-rows"] == {"section": "Reading", "role": "reads", "reads": [".csv", ".tsv"],
                               "line": "Rows.", "built": True}  # fmt: skip
    assert got["hurdat2"]["built"] is False


@pytest.mark.parametrize(
    "argv", [[], ["measure"], ["dry"], ["shape", "--pile"], ["bogus", "--to", "x"]]
)
def test_a_bad_command_line_is_refused(argv):
    assert t.main(argv) == 2
