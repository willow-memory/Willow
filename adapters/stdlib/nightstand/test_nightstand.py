"""nightstand: one thing in hand, a bite for every pick-up, nothing deleted,
and the state only ever replayed from the rows."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("nightstand", HERE / "nightstand.py")
ns = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ns)
NOW = ["--now", "2026-11-01T09:00:00Z"]


def make(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.txt").write_text("x\n")
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key", str(tmp_path / "k"), *NOW],
                   check=True, capture_output=True)  # fmt: skip
    return b


def run(box: Path, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "nightstand.py"), "--box", str(box), *argv],
        capture_output=True,
        text=True,
    )


def rows_of(box: Path) -> list[dict]:
    return [json.loads(x) for x in (box / "record.jsonl").read_text().splitlines()]


def stocked(tmp_path: Path) -> Path:
    """Row 1 heavy, row 2 light, row 3 medium, row 4 light (newer)."""
    b = make(tmp_path)
    for weight, what in (("heavy", "tax return"), ("light", "water the ferns"),
                         ("medium", "call the roofer"), ("light", "email Sam")):  # fmt: skip
        assert run(b, "down", "--weight", weight, what, *NOW).returncode == 0
    return b


def test_down_writes_one_row_with_words_and_weight(tmp_path):
    b = make(tmp_path)
    got = run(b, "down", "--weight", "heavy", "file", "the", "taxes", *NOW)
    assert got.returncode == 0 and "(row 1)" in got.stdout
    r = rows_of(b)[-1]
    assert (r["kind"], r["who"], r["act"]) == ("nightstand", "nightstand", "down")
    assert (r["what"], r["weight"], r["standing"]) == ("file the taxes", "heavy", "unattested")  # fmt: skip
    assert run(b, "down", "plain", *NOW).returncode == 0
    assert rows_of(b)[-1]["weight"] == "medium"


def test_a_bad_weight_or_empty_words_are_refused_not_defaulted(tmp_path):
    b = make(tmp_path)
    for argv in (["down", "--weight", "enormous", "x"], ["down", "  "], ["down"]):
        assert run(b, *argv, *NOW).returncode == 2
    assert len(rows_of(b)) == 1


def test_one_is_the_lightest_then_the_oldest(tmp_path):
    b = stocked(tmp_path)
    got = run(b, "one")
    assert got.returncode == 0 and got.stdout.split()[0] == "2"
    assert "water the ferns" in got.stdout
    assert len(rows_of(b)) == 5  # asking writes nothing
    assert [t["id"] for t in ns.waiting(ns.replay(rows_of(b)))] == [2, 4, 3, 1]


def test_one_with_nothing_waiting_says_so(tmp_path):
    b = make(tmp_path)
    got = run(b, "one")
    assert got.returncode == 2 and "nothing is waiting" in got.stderr


def test_pick_needs_a_bite_and_writes_nothing_without_one(tmp_path):
    b = stocked(tmp_path)
    for argv in (["pick", "2"], ["pick", "one"], ["pick", "2", "  "]):
        got = run(b, *argv, *NOW)
        assert got.returncode == 2 and "bite" in got.stderr
    assert len(rows_of(b)) == 5


def test_pick_records_the_bite_and_one_picks_the_offered_thing(tmp_path):
    b = stocked(tmp_path)
    assert run(b, "pick", "one", "just", "the", "watering", *NOW).returncode == 0
    r = rows_of(b)[-1]
    assert (r["act"], r["thing"], r["bite"], r["displaces"]) == ("pick", 2, "just the watering", None)  # fmt: skip
    things = ns.replay(rows_of(b))
    assert things[2]["status"] == "in_hand" and things[2]["pickups"] == 1
    assert ns.in_hand(things)["id"] == 2


def test_picking_a_second_puts_the_first_down_in_the_same_row(tmp_path):
    b = stocked(tmp_path)
    run(b, "pick", "2", "first bite", *NOW)
    n = len(rows_of(b))
    assert run(b, "pick", "1", "open the envelope", *NOW).returncode == 0
    assert len(rows_of(b)) == n + 1  # one row, so never two in hand
    assert rows_of(b)[-1]["displaces"] == 2
    things = ns.replay(rows_of(b))
    assert things[1]["status"] == "in_hand" and things[2]["status"] == "down"
    assert sum(t["status"] == "in_hand" for t in things.values()) == 1
    assert run(b, "pick", "2", "second bite", *NOW).returncode == 0
    assert ns.replay(rows_of(b))[2]["bites"] == ["first bite", "second bite"]
    assert ns.replay(rows_of(b))[2]["pickups"] == 2


def test_back_keeps_the_thing_and_done_ends_it(tmp_path):
    b = stocked(tmp_path)
    assert run(b, "back").returncode == 2  # nothing in hand
    assert run(b, "done").returncode == 2
    run(b, "pick", "2", "water", *NOW)
    assert run(b, "back", *NOW).returncode == 0
    assert ns.replay(rows_of(b))[2]["status"] == "down"
    run(b, "pick", "2", "water again", *NOW)
    assert run(b, "done", *NOW).returncode == 0
    t = ns.replay(rows_of(b))[2]
    assert t["status"] == "done" and t["pickups"] == 2
    assert run(b, "pick", "2", "again", *NOW).returncode == 2  # done is final


def test_archive_only_from_down_and_nothing_is_ever_deleted(tmp_path):
    b = stocked(tmp_path)
    run(b, "pick", "1", "open", *NOW)
    assert run(b, "archive", "1", *NOW).returncode == 2  # in hand: set it back first
    assert run(b, "archive", "99", *NOW).returncode == 2
    assert run(b, "archive", "x", *NOW).returncode == 2
    assert run(b, "archive", "3", *NOW).returncode == 0
    before = rows_of(b)
    assert ns.replay(before)[3]["status"] == "archived"
    assert run(b, "pick", "3", "x", *NOW).returncode == 2
    assert not hasattr(ns, "delete") and "delete" not in ns.ACTS
    assert run(b, "delete", "3").returncode == 2
    assert rows_of(b) == before
    shown = run(b, "show", "--all").stdout
    assert "email Sam" in shown and "call the roofer" in shown and "[archived" in shown


def test_show_replays_the_rows(tmp_path):
    b = stocked(tmp_path)
    run(b, "pick", "one", "water the big one", *NOW)
    run(b, "pick", "3", "get the number", *NOW)
    run(b, "archive", "1", *NOW)
    out = run(b, "show").stdout
    assert "in hand: 3  medium  call the roofer" in out
    assert "bite: get the number" in out
    assert "down (2)" in out and "done 0, archived 1" in out
    assert out.index("water the ferns") < out.index("email Sam")
    assert "tax return" not in out  # archived: only in --all
    assert "tax return" in run(b, "show", "--all").stdout


def test_show_of_an_empty_box_and_check_on_a_good_record(tmp_path):
    b = make(tmp_path)
    assert "in hand: nothing" in run(b, "show").stdout
    assert "0 things on the record" in run(b, "check").stdout
    (tmp_path / "s").mkdir()
    b2 = stocked(tmp_path / "s")
    run(b2, "pick", "one", "x", *NOW)
    assert "4 things on the record; every row keeps the three rules." in run(b2, "check").stdout  # fmt: skip


def forge(box: Path, **fields) -> None:
    """A row the add-on would never write, through the kernel's own door."""
    ns.kernel.append(box, "2026-11-01T10:00:00Z", "nightstand", who="x", **fields)


@pytest.mark.parametrize(
    "fields, why",
    [
        ({"act": "pick", "thing": 1, "displaces": None}, "no bite"),
        ({"act": "pick", "thing": 1, "bite": " ", "displaces": None}, "no bite"),
        ({"act": "pick", "thing": 1, "bite": "b", "displaces": 2}, "rule 1"),
        ({"act": "pick", "thing": 77, "bite": "b", "displaces": None}, "no thing"),
        ({"act": "delete", "thing": 1}, "isn't a move"),
        ({"act": "back", "thing": 1}, "not in hand"),
        ({"act": "done", "thing": 1}, "not in hand"),
        ({"act": "down", "what": "", "weight": "light"}, "no words"),
        ({"act": "down", "what": "x", "weight": "huge"}, "isn't light"),
    ],
)
def test_check_names_the_first_row_that_breaks_a_rule(tmp_path, fields, why):
    b = stocked(tmp_path)
    forge(b, **fields)
    got = run(b, "check")
    assert got.returncode == 2 and why in got.stderr and "row 5" in got.stderr
    assert run(b, "show").returncode == 2  # nothing reads a record that breaks a rule
    assert run(b, "down", "more", *NOW).returncode == 2  # nor writes to one


def test_check_catches_two_in_hand_and_a_bite_on_a_double_pick(tmp_path):
    b = stocked(tmp_path)
    run(b, "pick", "1", "a", *NOW)
    forge(b, act="pick", thing=2, bite="b", displaces=None)  # the race: two writers
    got = run(b, "check")
    assert got.returncode == 2 and "while 1 is in hand (rule 1)" in got.stderr
    rows = rows_of(b)
    assert ns.check(rows[:-1]) == (4, None)
    assert ns.check(rows)[1].startswith("row 6")
    forge(b, act="pick", thing=1, bite="c", displaces=2)
    assert "row 6" in run(b, "check").stderr  # the first break is the one named


def test_other_kinds_of_row_are_not_ours(tmp_path):
    b = stocked(tmp_path)
    ns.kernel.append(b, "2026-11-01T10:00:00Z", "wager", who="forecasts", act="delete", thing=1)  # fmt: skip
    assert run(b, "check").returncode == 0


def test_a_replayed_state_equals_the_moves_made(tmp_path):
    b = stocked(tmp_path)
    moves = [("pick", "2", "w"), ("back",), ("pick", "3", "r"), ("pick", "4", "e"),
             ("done",), ("archive", "1")]  # fmt: skip
    for m in moves:
        assert run(b, *m, *NOW).returncode == 0, m
    got = {i: t["status"] for i, t in ns.replay(rows_of(b)).items()}
    assert got == {1: "archived", 2: "down", 3: "down", 4: "done"}


def test_a_bad_command_line_is_refused_and_says_how_to_run_it(tmp_path):
    b = make(tmp_path)
    for argv in ([], ["--box", str(b)], ["--box", str(b), "dance"], ["--box", str(b), "one", "x"],
                 ["--box", str(b), "show", "--weight", "heavy"], ["--box", str(b), "--bogus", "show"],
                 ["--box", str(b), "archive"]):  # fmt: skip
        got = subprocess.run([sys.executable, str(HERE / "nightstand.py"), *argv], capture_output=True, text=True)  # fmt: skip
        assert got.returncode == 2 and "nightstand.py" in got.stderr, argv
    not_a_box = tmp_path / "empty"
    not_a_box.mkdir()
    assert "not a kernel box" in run(not_a_box, "show").stderr
    assert "neither a row number" in run(b, "pick", "soon", "x").stderr


def test_a_record_that_doesnt_verify_is_refused(tmp_path):
    b = stocked(tmp_path)
    p = b / "record.jsonl"
    lines = p.read_text().splitlines()
    p.write_text("\n".join([lines[0], lines[1].replace("tax return", "tax returns"), *lines[2:]]) + "\n")  # fmt: skip
    got = run(b, "show")
    assert got.returncode == 2 and "doesn't verify" in got.stderr
