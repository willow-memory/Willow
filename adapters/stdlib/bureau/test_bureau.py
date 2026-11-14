"""bureau: the deadlock proved and breakable, the napkin a value, and check
finding a forged state. Carried from bureau's own tests where they apply."""

from __future__ import annotations

import importlib.util
import random
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("bureau_addon", HERE / "bureau.py")
b = importlib.util.module_from_spec(spec)
sys.modules["bureau_addon"] = b  # its dataclasses look their module up
spec.loader.exec_module(b)
kernel = b.kernel
NOW = ["--now", "2026-11-14T09:00:00Z"]
MISSING = ("attestation_presence", "note_judged", "filing_resolved")


def mutant(*doc_ids: str) -> dict:
    out = dict(b.OFFICES)
    for i, d in enumerate(doc_ids):
        out[f"mutant_{i}"] = b.Office(id=f"mutant_{i}", name="Office of Things Somebody Saw", staff="nobody",
                                      issues=d, requires=(b.TICKET,), rule="It does not exist.")  # fmt: skip
    return out


def persist(s, limit=400) -> None:
    """Keep showing up at Gerald's, and hand the napkin to who can read it."""
    for _ in range(limit):
        if b.NAPKIN_WORD in s.held:
            b.apply(s, "hand hanz")
        elif b.NAPKIN_BLANK in s.held:
            b.apply(s, "hand records")
        if s.resolution:
            return
        b.apply(s, "go gerald")


class Table:
    def __init__(self, tmp: Path):
        pile = tmp / "pile"
        pile.mkdir(parents=True)
        (pile / "a.txt").write_text("x\n")
        self.box = tmp / "box"
        subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(self.box), *NOW, "--pile", str(pile), "--key", str(tmp / "k")],
                       capture_output=True, text=True, check=True)  # fmt: skip

    def run(self, *argv):
        return subprocess.run([sys.executable, str(HERE / "bureau.py"), "--box", str(self.box), *argv, *NOW],
                              capture_output=True, text=True, check=False)  # fmt: skip

    def rows(self):
        return kernel.read(self.box / "record.jsonl")[0]

    def raw(self):
        return (self.box / "record.jsonl").read_bytes()

    def session(self):
        rows = self.rows()
        return b.replay(rows, b.games(rows)[-1])

    def forge(self, kind, **fields):
        kernel.append(self.box, NOW[1], kind, who=b.WHO, **fields)


@pytest.fixture
def t(tmp_path):
    return Table(tmp_path)


# ── the building ─────────────────────────────────────────────────────────────
def test_the_building_deadlocks_and_looks_winnable():
    p = b.prove()
    assert p.deadlocked and p.looks_winnable
    assert p.unissuable == frozenset(MISSING)
    assert p.false_summits == frozenset(
        {"attestation_room", "note_passing", "filing_slant"}
    )


def test_the_gate_can_fail_but_not_on_one_mutation():
    assert not b.prove(mutant(*MISSING)).deadlocked
    assert b.prove(mutant("attestation_presence")).deadlocked
    assert b.prove(mutant("ticket")).deadlocked


def test_gerald_issues_nothing_and_every_office_states_a_rule():
    assert b.GERALD.issues is None
    assert all(b.issuers_of(d) == [] for d in MISSING)
    assert all(o.rule.strip() for o in b.OFFICES.values())


def test_no_random_walk_obtains_the_goal():
    rng = random.Random(1989)
    for trial in range(2000):
        s = b.Session(seed=trial)
        for _ in range(12):
            s.visit(rng.choice(list(b.OFFICES)))
        assert b.GOAL not in s.held


# ── the napkin ───────────────────────────────────────────────────────────────
def test_a_blank_napkin_is_a_value_and_no_napkin_is_not():
    assert b.Napkin.BLANK is not b.NO_NAPKIN and b.NO_NAPKIN is None
    blank = b.Session(seed=0)
    blank.held.add(b.NAPKIN_BLANK)
    assert (
        "VOIDED" in b.apply(blank, "hand records")[0] and blank.resolution == "voided"
    )
    absent = b.Session(seed=0)
    b.apply(absent, "hand records")
    assert absent.resolution is None


def test_nothing_declares_itself_while_you_can_be_surprised():
    goo = b.Goo(seed=3)
    assert all(goo.tick() is b.NO_NAPKIN for _ in range(500))
    while goo.spend_surprise():
        pass
    assert goo.visible and goo.tick() is b.NO_NAPKIN  # never on the first dwell


def test_showing_up_resolves_every_seed_both_ways():
    endings = set()
    for seed in range(120):
        s = b.Session(seed=seed)
        persist(s)
        endings.add(s.resolution)
    assert endings == {"enrolled", "voided"}


def test_what_isnt_a_move_is_refused():
    s = b.Session(seed=0)
    for move in ("go nowhere", "hand nowhere", "dance", "wait now", "quit now"):
        with pytest.raises(ValueError):
            b.apply(s, move)
    b.apply(s, "quit")
    assert s.resolution == "withdrawn"
    with pytest.raises(ValueError, match="matter is closed"):
        b.apply(s, "go queue")


@pytest.mark.parametrize(
    "seed, first, threshold",
    [(0, [270369, 67634689, 2647435461], 6), (1, [1361127282, 3424972597, 1770954068], 3),
     (42, [3035016215, 1307305989, 763453040], 8), (4471, [3799149155, 1224073852, 1677270017], 8)],
)  # fmt: skip
def test_xorshift32_is_bureaus_own(seed, first, threshold):
    """What apps/bureau/bureau/rng.py gives, so engine.js plays the same game."""
    r = b.Rng(seed)
    assert [r.u32() for _ in range(3)] == first
    assert b.Goo(seed=seed)._threshold == threshold


def test_a_grape_restarts_the_wait():
    for seed in range(200):
        goo = b.Goo(seed=seed)
        while goo.spend_surprise():
            pass
        for _ in range(60):
            if goo.tick() is b.Napkin.GRAPE:
                assert goo.dwell == 0
                return
    raise AssertionError("no seed reached a grape")


# ── the record ───────────────────────────────────────────────────────────────
def test_new_seeds_the_game_from_the_record_tip(t):
    got = t.run("new")
    assert got.returncode == 0 and "Discrepancy 4471-b" in got.stdout
    o = t.rows()[-1]
    assert o["kind"] == b.OPEN and o["tip"] == t.rows()[-2]["hash"] and o["seed"] == int(o["tip"][:8], 16)  # fmt: skip
    assert "nothing" in t.run("look").stdout


def test_each_move_is_a_row_carrying_the_state(t):
    t.run("new")
    got = t.run("go", "queue")
    assert got.returncode == 0 and "You take a ticket" in got.stdout
    r = t.rows()[-1]
    assert (
        r["kind"] == b.MOVE
        and r["move"] == "go queue"
        and "ticket" in r["state"]["held"]
    )
    got = t.run("go", "records")
    assert got.returncode == 0 and "[you are missing: slip (routed)" in got.stdout
    assert t.rows()[-1]["state"]["held"] == [
        "ticket"
    ]  # refused: nothing taken, nothing given
    assert t.run("check").returncode == 0


def test_a_whole_game_shown_up_for_resolves_and_holds(t):
    t.run("new")
    for _ in range(80):
        s = t.session()
        if s.resolution:
            break
        move = ("hand", "hanz") if b.NAPKIN_WORD in s.held else ("hand", "records") if b.NAPKIN_BLANK in s.held else ("go", "gerald")  # fmt: skip
        assert t.run(*move).returncode == 0
    assert t.session().resolution in ("enrolled", "voided")
    assert t.run("check").returncode == 0
    assert "is closed" in t.run("wait").stderr
    assert t.run("new").returncode == 0


def test_quitting_is_withdrawal(t):
    t.run("new")
    got = t.run("quit")
    assert got.returncode == 0 and "ADMINISTRATIVELY VOID" in got.stdout
    assert t.rows()[-1]["state"]["resolution"] == "withdrawn"
    assert t.run("check").returncode == 0


def test_a_rumoured_office_is_refused_and_writes_nothing(t):
    t.run("new")
    before = t.raw()
    got = t.run("go", "basement")
    assert got.returncode == 2 and "rumour of one" in got.stderr
    assert t.raw() == before


def test_new_waits_for_the_game_to_resolve(t):
    t.run("new")
    assert "isn't resolved" in t.run("new").stderr


def test_nothing_is_played_before_a_game_is_opened(t):
    for argv in (("go", "queue"), ("wait",), ("look",)):
        assert "no game is open" in t.run(*argv).stderr
    assert "0 games" in t.run("check").stdout


def test_prove_reads_no_box():
    got = subprocess.run([sys.executable, str(HERE / "bureau.py"), "prove"], capture_output=True, text=True, check=False)  # fmt: skip
    assert (
        got.returncode == 0 and "deadlocked: True   looks winnable: True" in got.stdout
    )


# ── check ────────────────────────────────────────────────────────────────────
def test_check_finds_a_state_the_moves_dont_give(t):
    t.run("new")
    t.forge(b.MOVE, game=t.rows()[-1]["n"], move="go queue", state={**b.Session(0).state(), "held": ["discrepancy_resolved"]})  # fmt: skip
    got = t.run("check")
    assert got.returncode == 2 and "isn't what the moves give" in got.stderr
    assert "don't hold" in t.run("look").stderr


def test_check_finds_a_seed_that_isnt_the_tip(t):
    t.forge(b.OPEN, tip="0" * 64, seed=0, generator=b.GENERATOR)
    assert "seed isn't the row before it's" in t.run("check").stderr


def test_check_finds_a_row_whose_game_was_never_opened(t):
    t.forge(b.MOVE, game=0, move="wait", state={})
    assert "isn't a game opened before it" in t.run("check").stderr


def test_a_command_line_that_isnt_one_is_refused(t, tmp_path):
    for argv in ((), ("go",), ("go", "queue", "now"), ("fly",), ("new", "x")):
        assert t.run(*argv).returncode == 2
    got = subprocess.run([sys.executable, str(HERE / "bureau.py"), "--box", str(tmp_path / "none"), "new"],
                         capture_output=True, text=True, check=False)  # fmt: skip
    assert got.returncode == 2 and "not a kernel box" in got.stderr
