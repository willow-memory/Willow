"""The game box: a table laid with nothing sealed, a night played through
every piece under the seal of whoever holds the key, and the table's own
check finding a forged row. The key here is the test's, made in a scratch
folder; the test plays the person who rules the table."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

STDLIB = ROOT / "adapters" / "stdlib"
NOW = ["--now", "2026-11-14T10:00:00Z"]


def py(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *map(str, argv)], capture_output=True, text=True
    )


class Table:
    def __init__(self, tmp: Path):
        self.dir, self.key = tmp / "table", tmp / "gm.key"
        self.box, self.pile = self.dir / "record", self.dir / "pile"
        self.world = self.pile / "worlds" / "lantern-fair.json"

    def open(self):
        return py(
            HERE / "open_table.py", "open", "--table", self.dir, "--key", self.key, *NOW
        )

    def check(self):
        return py(HERE / "open_table.py", "check", "--table", self.dir)

    def k(self, *argv):
        return py(ROOT / "kernel.py", argv[0], "--box", self.box, *NOW, *argv[1:])

    def addon(self, name: str, *argv):
        script = STDLIB / name / f"{name.replace('-', '_')}.py"
        return py(script, *argv)

    def gm(self, *argv):
        return self.addon(
            "game-master", "--box", self.box, *argv, "--world", self.world, *NOW
        )

    def checkers(self, *argv):
        return self.addon("checkers", "--box", self.box, *argv, *NOW)

    def rows(self) -> list[dict]:
        return kernel.read(self.box / "record.jsonl")[0]

    def waiting(self) -> list[str]:
        sealed = {r["subject"] for r in self.rows() if r["kind"] in ("seal", "decline")}
        return [r["subject"] for r in self.rows()
                if r["kind"] == "proposal" and r.get("verdict") == "pass" and r["subject"] not in sealed]  # fmt: skip

    def seal(self, subject: str):
        got = self.k("seal", subject)
        assert got.returncode == 0, got.stderr


@pytest.fixture
def t(tmp_path):
    return Table(tmp_path)


def test_open_lays_a_table_and_seals_nothing(t):
    got = t.open()
    assert got.returncode == 42, got.stderr
    assert "7 waiting on the seal, nothing sealed" in got.stdout
    kinds = [r["kind"] for r in t.rows()]
    assert kinds.count("proposal") == 7 and "table-open" in kinds
    assert not [
        r
        for r in t.rows()
        if r["kind"] in ("seal", "decline") or r.get("who") == "human"
    ]
    assert t.key.exists() and not any(p.name == t.key.name for p in t.dir.rglob("*"))
    assert sorted(p.name for p in t.pile.iterdir()) == [
        "check.md",
        "house-rules.md",
        "worlds",
    ]
    assert t.k("verify").returncode == 0


def test_the_check_page_says_what_waits_until_the_rules_are_sealed(t):
    t.open()
    got = t.check()
    assert got.returncode == 42 and "1 of 5 steps flagged (exit 42)" in got.stdout
    assert len(re.findall(r"waiting +the rule", got.stdout)) == 7
    for subj in t.waiting():
        t.seal(subj)
    got = t.check()
    assert got.returncode == 0 and "0 of 5 steps flagged (exit 0)" in got.stdout
    assert len(re.findall(r"sealed +the rule", got.stdout)) == 7


def test_a_night_at_the_table_through_every_piece(t):
    t.open()
    for subj in t.waiting():  # the house rules, sealed by whoever rules the table
        t.seal(subj)
    rule = t.addon("rules", "ask", "--box", t.box, *NOW, "Draws")
    assert rule.returncode == 0 and "ruled by whoever rules the table" in rule.stdout

    # the story: two actions, a ruling sealed, one more action, a ruling declined
    for argv in (("act", "Grit"), ("act", "Wit"), ("ask",)):
        assert t.gm(*argv).returncode in (0, 42)
    t.seal(t.waiting()[0])
    assert t.gm("settle").returncode == 0
    assert t.gm("act", "Heart").returncode == 0
    assert t.gm("ask").returncode == 42
    assert t.k("decline", t.waiting()[0]).returncode == 0
    end = t.gm("settle")
    assert end.returncode == 0 and "finished" in end.stdout

    # checkers: a few moves, a draw offered, and the ruler seals it
    assert t.checkers("new").returncode == 0
    for m in ("11-15", "23-19", "8-11", "22-17"):
        assert t.checkers("move", m).returncode == 0
    assert t.checkers("offer").returncode == 42
    t.seal(t.waiting()[0])
    assert "a draw" in t.checkers("settle").stdout

    # a logic grid, seeded by the record's tip
    assert t.addon("catgrid", "--box", t.box, "play", *NOW).returncode == 0

    got = t.check()
    assert got.returncode == 0, got.stdout
    for says in ("1 game, 5 beats, 3 rolls", "1 game of checkers", "1 game on the record", "3 rolls on the record"):  # fmt: skip
        assert says in got.stdout, says
    assert "the chain holds" in got.stdout
    seals = [r for r in t.rows() if r["kind"] == "seal"]
    assert len(seals) == 9 and {r["who"] for r in seals} == {
        "human"
    }  # 7 rules, a ruling, a draw


def test_a_forged_move_is_caught_by_the_tables_own_check(t):
    t.open()
    assert t.checkers("new").returncode == 0
    game = [r for r in t.rows() if r["kind"] == "checkers-open"][-1]["n"]
    kernel.append(t.box, NOW[1], "checkers-move", who="checkers", game=game, ply=0,
                  side="black", move="11-14", result="on")  # fmt: skip
    got = t.check()
    assert got.returncode == 42
    assert "checkers -- --box {box} check`  (exit 2)" in got.stdout
    assert "isn't a move black may make" in got.stdout


def test_an_edited_row_breaks_the_chain_and_the_check_says_so(t):
    t.open()
    raw = (t.box / "record.jsonl").read_bytes()
    (t.box / "record.jsonl").write_bytes(
        raw.replace(b"Lantern Fair", b"Lantern Fail", 1)
    )
    got = t.check()
    assert got.returncode == 2 and "the chain" in got.stderr


def test_open_refuses_a_table_already_there_or_a_key_inside_it(t, tmp_path):
    t.dir.mkdir()
    got = t.open()
    assert got.returncode == 2 and "already there" in got.stderr
    inside = py(HERE / "open_table.py", "open", "--table", tmp_path / "t2", "--key", tmp_path / "t2" / "k", *NOW)  # fmt: skip
    assert inside.returncode == 2 and "outside the table" in inside.stderr
    assert not (tmp_path / "t2").exists()


def test_a_command_line_that_isnt_one_is_refused(t, tmp_path):
    for argv in (
        (),
        ("open",),
        ("fly", "--table", "x"),
        ("open", "--table", str(tmp_path / "x")),
    ):
        assert py(HERE / "open_table.py", *argv).returncode == 2
    got = py(HERE / "open_table.py", "check", "--table", tmp_path / "nowhere")
    assert got.returncode == 2 and "isn't a table" in got.stderr


def test_the_world_is_one_game_master_takes_and_names_no_player():
    world = json.loads((HERE / "table" / "worlds" / "lantern-fair.json").read_text())
    assert "never a player" in world["setting"]
    sys.path.insert(0, str(STDLIB / "game-master"))
    import game_master

    game_master.validate(world)
