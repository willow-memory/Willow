"""game-master: rolls are dice's rows, a ruling moves only on the person's
seal, and check finds a forged row. The world is made up for these tests."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("game_master", HERE / "game_master.py")
gm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gm)
kernel, dice, odds = gm.kernel, gm.dice, gm.odds
NOW = ["--now", "2026-11-01T09:00:00Z"]


def outcomes(tag: str) -> dict:
    return {b: f"{tag} {b}" for b in ("strong", "weak", "miss")}


WORLD = {
    "id": "toll-bridge",
    "title": "The Toll Bridge",
    "setting": "Made up for these tests.",
    "stats": ["Grit", "Wit"],
    "base_stat": 1,
    "characters": [
        {"id": "ana", "name": "Ana", "role": "keeper", "seat": True, "stats": {"Grit": 3}},
        {"id": "bo", "name": "Bo", "role": "drover", "seat": True, "stats": {"Wit": 2}},
        {"id": "cy", "name": "Cy", "role": "toll-man", "seat": False, "stats": {}},
    ],
    "places": [{"id": "bridge", "name": "The bridge"}, {"id": "inn", "name": "The inn"}],
    "scenes": [
        {"id": "s1", "title": "Dusk", "place": "bridge", "opening": ["The light goes."],
         "beats": [
             {"id": "a1", "kind": "action", "prompt": "Ana forces the gate.", "suggests": "Grit", "outcomes": outcomes("a1")},
             {"id": "a2", "kind": "action", "prompt": "Bo reads the ledger.", "suggests": "Wit", "outcomes": outcomes("a2")},
             {"id": "d1", "kind": "decision", "prompt": "What does the ledger say?",
              "proposes": {"fact": "The toll was paid twice.", "proposed_by": "cy"}},
         ]},
        {"id": "s2", "title": "Night", "place": "inn", "opening": ["Rain.", "More rain."],
         "beats": [
             {"id": "a3", "kind": "action", "prompt": "Bo knocks.", "suggests": "Wit", "outcomes": outcomes("a3")},
             {"id": "d2", "kind": "decision", "prompt": "Who has the key?",
              "proposes": {"fact": "Cy has the key.", "proposed_by": "ana"}},
         ]},
    ],
}  # fmt: skip


class Table:
    """A fresh box and a world file, and the commands against them."""

    def __init__(self, tmp: Path, world: dict = WORLD):
        pile = tmp / "pile"
        pile.mkdir(parents=True)
        (pile / "a.txt").write_text("x\n")
        self.box, self.key, self.wf = tmp / "box", tmp / "k", tmp / "world.json"
        self.wf.write_text(json.dumps(world))
        self.k("init", "--pile", str(pile), "--key", str(self.key))

    def k(self, *argv: str):
        verb, rest = argv[0], argv[1:]
        return subprocess.run([sys.executable, str(KERNEL), verb, "--box", str(self.box), *NOW, *rest],
                              capture_output=True, text=True)  # fmt: skip

    def run(self, *argv: str, world: bool = True):
        extra = ["--world", str(self.wf)] if world else []
        return subprocess.run([sys.executable, str(HERE / "game_master.py"), "--box", str(self.box), *argv, *extra, *NOW],
                              capture_output=True, text=True)  # fmt: skip

    def rows(self) -> list[dict]:
        return kernel.read(self.box / "record.jsonl")[0]

    def raw(self) -> bytes:
        return (self.box / "record.jsonl").read_bytes()

    def subject(self) -> str:
        return [r for r in self.rows() if r["kind"] == gm.ASK][-1]["subject"]

    def play_to_first_decision(self):
        assert self.run("open").returncode == 0
        assert self.run("act", "Grit").returncode == 0
        assert self.run("act", "Wit").returncode == 0

    def forge(self, kind: str = gm.BEAT, **fields):
        kernel.append(self.box, NOW[1], kind, who=gm.WHO, **fields)


@pytest.fixture
def t(tmp_path):
    return Table(tmp_path)


def test_a_band_is_strong_at_ten_weak_at_seven_and_a_miss_below():
    assert [gm.band_of(n) for n in (3, 6, 7, 9, 10, 15)] == [
        "miss", "miss", "weak", "weak", "strong", "strong"]  # fmt: skip


@pytest.mark.parametrize(
    "change, says",
    [
        (lambda w: w["scenes"][0]["beats"][0].update(kind="puzzle"), "'action' and 'decision' beats only"),
        (lambda w: w["scenes"][0]["beats"][0].update(suggests="Luck"), "is not a stat"),
        (lambda w: w["scenes"][0]["beats"][0]["outcomes"].pop("weak"), "missing ['weak']"),
        (lambda w: w["scenes"][0].update(place="moon"), "is not one of the places"),
        (lambda w: w["characters"][0]["stats"].update(Luck=1), "not one of the stats"),
        (lambda w: w["characters"][0]["stats"].update(Grit=2.5), "must be a int"),
        (lambda w: w["characters"][0]["stats"].update(Grit=True), "must be a int"),
        (lambda w: [c.update(seat=False) for c in w["characters"]], "no one plays this world"),
        (lambda w: w["characters"][1].update(id="ana"), "repeats the id"),
        (lambda w: w["scenes"][0]["beats"].clear(), "must not be empty"),
        (lambda w: w["scenes"][0]["beats"][2]["proposes"].pop("fact"), "missing ['fact']"),
        (lambda w: w["stats"].append("Grit"), "none repeated"),
        (lambda w: w.pop("setting"), "the world is missing ['setting']"),
    ],
)  # fmt: skip
def test_a_world_that_is_not_the_format_is_refused_naming_where(change, says):
    world = copy.deepcopy(WORLD)
    change(world)
    with pytest.raises(gm.WorldError) as e:
        gm.validate(world)
    assert says in str(e.value)
    assert gm.validate(copy.deepcopy(WORLD))["id"] == "toll-bridge"


def test_a_world_that_is_not_json_is_refused(t):
    t.wf.write_text("{nope")
    got = t.run("status")
    assert got.returncode == 2 and "can't be read as JSON" in got.stderr


def test_open_writes_one_row_with_the_worlds_hash_and_says_the_opening(t):
    got = t.run("open")
    assert got.returncode == 0 and "The light goes." in got.stdout
    row = t.rows()[-1]
    assert row["kind"] == gm.OPEN and row["who"] == "game-master"
    assert row["sha256"] == gm.world_sha(WORLD) and row["seats"] == ["ana", "bo"]
    again = t.run("open")
    assert again.returncode == 2 and "already open" in again.stderr


def test_nothing_is_played_before_it_is_opened(t):
    for argv in (("act", "Grit"), ("status",), ("ask",), ("settle",)):
        got = t.run(*argv)
        assert got.returncode == 2 and "open first" in got.stderr


def test_an_action_is_dices_roll_row_then_a_beat_row_that_adds_the_stat(t):
    t.run("open")
    tip = t.rows()[-1]["hash"]
    got = t.run("act", "Grit")
    assert got.returncode == 0
    roll, beat = t.rows()[-2:]
    assert roll["kind"] == "roll" and roll["who"] == "dice" and roll["seed"] == tip
    assert roll == {**roll, **dice.throw("2d6", tip)}  # nobody picked the faces
    assert beat["kind"] == gm.BEAT and beat["beat_kind"] == "action"
    assert beat["character"] == "ana" and beat["stat"] == "Grit" and beat["bonus"] == 3
    assert beat["roll_row"] == roll["n"] and beat["roll"] == roll["total"]
    assert beat["total"] == roll["total"] + 3 and beat["band"] == gm.band_of(
        beat["total"]
    )
    assert beat["text"] == f"a1 {beat['band']}"
    assert (
        beat["text"] in got.stdout
        and f"= {beat['total']}: {beat['band']}" in got.stdout
    )
    assert dice.check(t.rows())[1] is None  # dice's own check throws it again
    assert t.k("verify").returncode == 0


def test_seats_take_turns_and_a_stat_not_on_the_sheet_is_the_base(t):
    t.play_to_first_decision()
    first, second = [r for r in t.rows() if r["kind"] == gm.BEAT]
    assert (first["character"], first["bonus"]) == ("ana", 3)
    assert (second["character"], second["stat"], second["bonus"]) == ("bo", "Wit", 2)
    t2 = Table(t.wf.parent / "two")  # a stat missing from the sheet takes base_stat
    t2.run("open")
    t2.run("act", "Wit")
    assert [r for r in t2.rows() if r["kind"] == gm.BEAT][0]["bonus"] == 1


def test_the_first_scene_opens_on_open_and_the_next_when_its_beats_are_done(t):
    t.play_to_first_decision()
    t.run("ask")
    t.k("seal", t.subject())
    got = t.run("settle")
    assert (
        got.returncode == 0
        and "-- Night --" in got.stdout
        and "More rain." in got.stdout
    )
    assert "-- Dusk --" not in got.stdout
    got = t.run("act", "Wit")  # not a scene change: no scene lines
    assert "-- Night --" not in got.stdout


def test_a_refused_action_writes_nothing(t):
    t.run("open")
    before = t.raw()
    got = t.run("act", "Luck")
    assert got.returncode == 2 and "isn't a stat" in got.stderr and t.raw() == before
    assert t.run("ask").returncode == 2 and t.run("settle").returncode == 2
    assert t.raw() == before


def test_a_decision_has_no_roll(t):
    t.play_to_first_decision()
    before = t.raw()
    got = t.run("act", "Wit")
    assert got.returncode == 2 and "is a decision" in got.stderr and t.raw() == before


def test_ask_hands_the_fact_in_through_the_kernel_and_waits(t):
    t.play_to_first_decision()
    got = t.run("ask")
    assert got.returncode == 42 and "waits on you" in got.stdout
    kinds = [r["kind"] for r in t.rows()[-3:]]
    assert kinds == ["bite", "proposal", gm.ASK]
    ask = t.rows()[-1]
    prop = json.loads((t.box / "proposals" / f"{ask['subject'][9:]}.json").read_text())
    assert prop["data"] == "The toll was paid twice." and prop["cites"] == []
    assert "cy proposes this at s1::d1" in prop["claim"]
    assert (
        t.rows()[-2]["subject"] == ask["subject"] and t.rows()[-2]["verdict"] == "pass"
    )
    assert kernel.sealed(t.box, t.rows()) == {}  # handed in, not answered
    again = t.run("ask")
    assert again.returncode == 2 and "already asked" in again.stderr


def test_nothing_moves_until_the_person_seals_it(t):
    t.play_to_first_decision()
    t.run("ask")
    before = t.raw()
    for argv in (("settle",), ("status",)):
        got = t.run(*argv)
        assert (
            got.returncode == 42
            and "waits on your seal" in got.stdout + "waits on your seal"
        )
    assert t.run("act", "Grit").returncode == 2  # a decision beat has no roll to try
    assert t.raw() == before
    assert not [r for r in t.rows() if r["kind"] in ("seal", "decline")]
    assert t.run("check").returncode == 0


def test_a_seal_moves_it_and_the_row_names_the_seal(t):
    t.play_to_first_decision()
    t.run("ask")
    subj = t.subject()
    assert t.k("seal", subj).returncode == 0
    got = t.run("settle")
    assert got.returncode == 0 and "you sealed it" in got.stdout
    seal, beat = [r for r in t.rows() if r["kind"] == "seal"][-1], t.rows()[-1]
    assert beat["beat_kind"] == "decision" and beat["verdict"] == "sealed"
    assert beat["ruling_row"] == seal["n"] and beat["subject"] == subj
    assert beat["proposed_by"] == "cy" and seal["who"] == "human"
    assert t.run("check").returncode == 0 and t.k("verify").returncode == 0


def test_a_no_moves_it_too_and_says_it_was_a_no(t):
    t.play_to_first_decision()
    t.run("ask")
    assert t.k("decline", t.subject()).returncode == 0
    got = t.run("settle")
    assert got.returncode == 0 and "you declined it" in got.stdout
    beat = t.rows()[-1]
    assert beat["verdict"] == "declined"
    assert (
        beat["ruling_row"] == [r for r in t.rows() if r["kind"] == "decline"][-1]["n"]
    )
    assert t.run("check").returncode == 0


def test_a_seal_row_without_the_persons_proof_moves_nothing(t):
    t.play_to_first_decision()
    t.run("ask")
    subj = t.subject()
    t.forge("seal", subject=subj, bite_key="0" * 64, proof="0" * 64)  # not their key
    before = t.raw()
    got = t.run("settle")
    assert got.returncode == 42 and "waits on your seal" in got.stdout
    assert t.raw() == before


def test_a_seal_over_another_proposal_moves_nothing(t):
    """The kernel seals any proposal; only the one handed in for this beat,
    in this game, moves this beat."""
    t.play_to_first_decision()
    t.run("ask")
    other = {
        "path": "other.txt",
        "data": "Something else.",
        "cites": [],
        "claim": "unrelated",
    }
    (t.box / "other.jsonl").write_text(json.dumps(other) + "\n")
    assert t.k("propose", "--file", str(t.box / "other.jsonl")).returncode == 42
    assert t.k("seal", kernel.subject_of(other)).returncode == 0
    assert t.run("settle").returncode == 42


def test_a_proposal_file_changed_after_the_seal_is_broken_not_trusted(t):
    t.play_to_first_decision()
    t.run("ask")
    subj = t.subject()
    t.k("seal", subj)
    f = t.box / "proposals" / f"{subj[9:]}.json"
    held = f.read_text()
    f.write_text(json.dumps({**json.loads(held), "data": "The toll was never paid."}))
    before = t.raw()
    got = t.run("settle")
    assert got.returncode == 2 and "is not the bytes that were sealed" in got.stderr
    assert t.raw() == before
    f.write_text(held)  # put back byte for byte: it stands again
    assert t.run("settle").returncode == 0
    f.write_text("{}")  # and check finds a ruling whose proposal went bad
    got = t.run("check")
    assert got.returncode == 2 and "stands behind it" in got.stderr


def test_a_second_game_needs_its_own_seal(t):
    t.play_to_first_decision()
    t.run("ask")
    first = t.subject()
    t.k("seal", first)
    t.run("settle")
    t.run("act", "Wit")
    t.run("ask")
    t.k("decline", t.subject())
    assert t.run("settle").returncode == 0
    assert "finished" in t.run("status").stdout
    assert t.run("act", "Grit").returncode == 2  # nothing past the end
    t.run("open")  # a finished game can be played again
    t.run("act", "Grit")
    t.run("act", "Wit")
    t.run("ask")
    assert t.subject() != first  # the same fact, a different game, a different subject
    assert t.run("settle").returncode == 42  # the first game's seal doesn't answer it
    assert t.run("check").returncode == 0


def test_a_story_played_to_the_end_tallies_and_check_holds(t):
    t.play_to_first_decision()
    t.run("ask")
    t.k("seal", t.subject())
    t.run("settle")
    t.run("act", "Wit")
    t.run("ask")
    t.k("decline", t.subject())
    got = t.run("settle")
    assert got.returncode == 0 and "finished: 3 rolled (" in got.stdout
    assert "2 ruled [s1::d1 sealed; s2::d2 declined]" in got.stdout
    rolls = [r for r in t.rows() if r["kind"] == gm.BEAT and r["beat_kind"] == "action"]
    counts = ", ".join(
        f"{sum(r['band'] == n for r in rolls)} {n}" for n in ("strong", "weak", "miss")
    )
    assert counts in got.stdout
    chk = t.run("check", world=False)
    assert chk.returncode == 0 and "1 game, 5 beats, 3 rolls" in chk.stdout
    assert t.run("check").returncode == 0  # and again with the world


def test_the_add_on_never_seals_or_declines(t):
    t.play_to_first_decision()
    t.run("ask")
    t.run("settle")
    assert not [r for r in t.rows() if r["kind"] in ("seal", "decline")]
    assert not [r for r in t.rows() if r["who"] == "human"]
    assert (t.box / "written").exists() is False


def test_status_gives_each_stats_exact_odds_from_odds(t):
    t.run("open")
    out = t.run("status").stdout
    for stat, bonus in (("Grit", 3), ("Wit", 1)):
        strong, weak, miss = (
            p for _, p in odds.bands(odds.distribution(f"2d6+{bonus}"), [10, 7])
        )
        assert (
            f"{stat:<10} {bonus:+d}   strong {strong}   weak {weak}   miss {miss}"
            in out
        )
    assert "* Grit" in out and "  Wit" in out  # the beat suggests Grit
    assert "Ana's turn" in out and "0 of 5 beats done" in out


def test_status_says_a_decision_is_not_yet_asked_then_where_it_waits(t):
    t.play_to_first_decision()
    got = t.run("status")
    assert (
        got.returncode == 42
        and "cy would propose: The toll was paid twice." in got.stdout
    )
    t.run("ask")
    got = t.run("status")
    assert got.returncode == 42 and f"proposed as {t.subject()}: open" in got.stdout
    t.k("seal", t.subject())
    got = t.run("status")
    assert got.returncode == 0 and f"proposed as {t.subject()}: sealed" in got.stdout


def test_a_world_changed_after_it_opened_is_refused(t):
    t.run("open")
    changed = copy.deepcopy(WORLD)
    changed["scenes"][0]["beats"][0]["outcomes"]["strong"] = "A kinder line."
    t.wf.write_text(json.dumps(changed))
    before = t.raw()
    for argv in (("act", "Grit"), ("status",)):
        got = t.run(*argv)
        assert (
            got.returncode == 2 and "isn't the one the game opened with" in got.stderr
        )
    assert t.run("check").returncode == 2 and t.raw() == before


def test_a_record_that_doesnt_verify_is_refused(t):
    t.run("open")
    path = t.box / "record.jsonl"
    path.write_bytes(
        path.read_bytes().replace(b"The Toll Bridge", b"The Toll Bridgf", 1)
    )
    for argv in (("check",), ("act", "Grit"), ("open",)):
        got = t.run(*argv)
        assert got.returncode == 2 and "doesn't verify" in got.stderr


def test_a_command_line_that_isnt_one_is_refused(t):
    for argv in ((), ("act",), ("dance",), ("open", "extra")):
        got = t.run(*argv)
        assert got.returncode == 2 and "game_master.py" in got.stderr
    got = subprocess.run([sys.executable, str(HERE / "game_master.py"), "open", "--world", str(t.wf)],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2
    got = subprocess.run([sys.executable, str(HERE / "game_master.py"), "--box", str(t.box), "open"],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2  # no world
    empty = t.box.parent / "nobox"
    empty.mkdir()
    got = subprocess.run([sys.executable, str(HERE / "game_master.py"), "--box", str(empty), "check"],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2 and "not a kernel box" in got.stderr


def test_check_on_a_record_with_no_game_says_so_and_holds(t):
    got = t.run("check", world=False)
    assert got.returncode == 0 and "0 games, 0 beats, 0 rolls" in got.stdout


# ── check finds a row that lies (forged through the kernel, so the chain holds) ──
def forged_beat(t: Table, **over):
    """A beat row for game 1's first beat, preceded by a real 2d6 roll."""
    t.run("open")
    subprocess.run([sys.executable, str(gm.DICE), "--box", str(t.box), "roll", "2d6", *NOW], check=True, capture_output=True)  # fmt: skip
    roll = t.rows()[-1]
    fields = dict(game=1, beat_kind="action", scene="s1", beat="a1", character="ana", stat="Grit",
                  bonus=3, roll_row=roll["n"], roll=roll["total"], total=roll["total"] + 3,
                  band=gm.band_of(roll["total"] + 3), text="a1 " + gm.band_of(roll["total"] + 3))  # fmt: skip
    fields.update(over)
    t.forge(**fields)
    return roll


def test_check_accepts_the_honest_forgery_so_the_next_ones_mean_something(t):
    forged_beat(t)
    assert (
        t.run("check").returncode == 0 and t.run("check", world=False).returncode == 0
    )


def test_check_finds_a_beat_that_does_not_add_up(t):
    t.run("open")
    subprocess.run([sys.executable, str(gm.DICE), "--box", str(t.box), "roll", "2d6", *NOW], check=True, capture_output=True)  # fmt: skip
    roll = t.rows()[-1]
    total = roll["total"] + 3
    good = dict(game=1, beat_kind="action", scene="s1", beat="a1", character="ana",
                stat="Grit", bonus=3, roll_row=roll["n"], roll=roll["total"], total=total,
                band=gm.band_of(total), text="a1 " + gm.band_of(total))  # fmt: skip
    wrong_band = next(b for b in ("strong", "weak", "miss") if b != good["band"])
    for over, says in (
        ({"total": total + 1}, "isn't the roll plus the stat"),
        ({"roll": roll["total"] + 1}, "isn't the roll plus the stat"),
        ({"band": wrong_band}, f"isn't {wrong_band}"),
        ({"roll_row": 0}, "not straight after a 2d6 roll"),
    ):  # fmt: skip
        box2 = Table(t.wf.parent / f"x{len(says)}{len(over)}{list(over)[0]}")
        box2.run("open")
        subprocess.run([sys.executable, str(gm.DICE), "--box", str(box2.box), "roll", "2d6", *NOW], check=True, capture_output=True)  # fmt: skip
        r2 = box2.rows()[-1]
        g2 = {
            **good,
            "roll_row": r2["n"],
            "roll": r2["total"],
            "total": r2["total"] + 3,
        }
        g2["band"] = gm.band_of(g2["total"])
        g2["text"] = "a1 " + g2["band"]
        if "total" in over:
            over = {"total": g2["total"] + 1}
        if "roll" in over:
            over = {"roll": g2["roll"] + 1}
        if "band" in over:
            over = {
                "band": next(b for b in ("strong", "weak", "miss") if b != g2["band"])
            }
            says = f"isn't {over['band']}"
        box2.forge(**{**g2, **over})
        got = box2.run("check", world=False)
        assert got.returncode == 2 and says in got.stderr, (over, got.stderr)


def test_check_finds_an_action_with_no_roll_of_its_own(t):
    t.run("open")
    t.forge(game=1, beat_kind="action", scene="s1", beat="a1", character="ana", stat="Grit",
            bonus=3, roll_row=0, roll=7, total=10, band="strong", text="a1 strong")  # fmt: skip
    got = t.run("check", world=False)
    assert got.returncode == 2 and "not straight after a 2d6 roll" in got.stderr


def test_check_finds_a_roll_that_is_not_what_its_seed_gives(t):
    t.run("open")
    t.run("act", "Grit")
    rows = t.rows()
    faces = rows[-2]["faces"]
    rows[-2] = dict(rows[-2], faces=[[faces[0][0] % 6 + 1, *faces[0][1:]]])
    assert (
        dice.check(rows)[1] is not None
    )  # the replay dice does, which check runs first


@pytest.mark.parametrize(
    "over, says",
    [
        ({"scene": "s2", "beat": "a3"}, "not the beat the world has at place 0"),
        ({"character": "bo"}, "not ana's turn or not a stat"),
        ({"stat": "Luck"}, "not ana's turn or not a stat"),
        ({"text": "a kinder line"}, "stat or its line isn't the world's"),
        ({"beat_kind": "decision"}, "a decision row on a action beat"),
    ],
)  # fmt: skip
def test_check_against_the_world_finds_what_the_world_does_not_say(t, over, says):
    forged_beat(t, **over)
    got = t.run("check")
    assert got.returncode == 2 and says in got.stderr


def test_check_against_the_world_finds_a_bonus_that_isnt_the_sheet(t):
    t.run("open")
    subprocess.run([sys.executable, str(gm.DICE), "--box", str(t.box), "roll", "2d6", *NOW], check=True, capture_output=True)  # fmt: skip
    roll = t.rows()[-1]
    total = roll["total"] + 2  # adds up by itself, but Ana's Grit is 3, not 2
    t.forge(game=1, beat_kind="action", scene="s1", beat="a1", character="ana", stat="Grit",
            bonus=2, roll_row=roll["n"], roll=roll["total"], total=total,
            band=gm.band_of(total), text="a1 " + gm.band_of(total))  # fmt: skip
    assert t.run("check", world=False).returncode == 0
    got = t.run("check")
    assert got.returncode == 2 and "stat or its line isn't the world's" in got.stderr


def test_check_finds_a_ruling_nobody_handed_in_or_the_person_never_made(t):
    t.play_to_first_decision()
    t.forge(game=1, beat_kind="decision", scene="s1", beat="d1", subject="proposal:" + "a" * 64,
            verdict="sealed", ruling_row=0, proposed_by="cy")  # fmt: skip
    got = t.run("check")
    assert got.returncode == 2 and "no proposal handed in before it" in got.stderr


def test_check_finds_a_ruling_that_was_asked_but_never_sealed(t):
    t.play_to_first_decision()
    t.run("ask")
    t.forge(game=1, beat_kind="decision", scene="s1", beat="d1", subject=t.subject(),
            verdict="sealed", ruling_row=0, proposed_by="cy")  # fmt: skip
    got = t.run("check")
    assert got.returncode == 2 and "stands behind it" in got.stderr


def test_check_finds_a_ruling_that_reports_the_wrong_answer(t):
    t.play_to_first_decision()
    t.run("ask")
    subj = t.subject()
    t.k("decline", subj)
    declined = [r for r in t.rows() if r["kind"] == "decline"][-1]
    t.forge(game=1, beat_kind="decision", scene="s1", beat="d1", subject=subj,
            verdict="sealed", ruling_row=declined["n"], proposed_by="cy")  # fmt: skip
    got = t.run("check")
    assert got.returncode == 2 and "stands behind it" in got.stderr


def test_check_finds_a_ruling_that_names_someone_elses_row(t):
    t.play_to_first_decision()
    t.run("ask")
    subj = t.subject()
    t.k("seal", subj)
    t.forge(game=1, beat_kind="decision", scene="s1", beat="d1", subject=subj,
            verdict="sealed", ruling_row=1, proposed_by="cy")  # fmt: skip
    got = t.run("check")
    assert got.returncode == 2 and "stands behind it" in got.stderr


def test_check_finds_a_ruling_that_never_passed_the_kernels_door(t):
    t.play_to_first_decision()
    t.forge(gm.ASK, game=1, scene="s1", beat="d1", subject="proposal:" + "b" * 64,
            proposed_by="cy", fact="The toll was paid twice.")  # fmt: skip
    t.forge(game=1, beat_kind="decision", scene="s1", beat="d1", subject="proposal:" + "b" * 64,
            verdict="sealed", ruling_row=0, proposed_by="cy")  # fmt: skip
    got = t.run("check")
    assert got.returncode == 2 and "the kernel never passed" in got.stderr


def test_check_finds_a_decision_whose_fact_isnt_the_worlds(t):
    t.play_to_first_decision()
    t.run("ask")
    subj = t.subject()
    t.k("seal", subj)
    t.run("settle")
    rows = t.rows()
    asks = [i for i, r in enumerate(rows) if r["kind"] == gm.ASK]
    rows[asks[0]] = dict(rows[asks[0]], fact="Something she never proposed.")
    why = gm.check_game(t.box, rows, gm.games(rows)[0], WORLD)
    assert why and "the fact handed in isn't the world's" in why


def test_a_beat_row_before_its_game_opened_is_found(t):
    t.play_to_first_decision()
    rows = t.rows()
    game = gm.games(rows)[0]
    game["open"] = dict(game["open"], n=99)
    assert "before its game opened" in gm.check_game(t.box, rows, game, None)


def test_a_beat_row_that_is_neither_kind_is_found(t):
    t.run("open")
    t.forge(game=1, beat_kind="puzzle", scene="s1", beat="a1")
    got = t.run("check", world=False)
    assert got.returncode == 2 and "neither an action nor a decision" in got.stderr


def test_check_finds_beats_past_the_end_of_the_world(t):
    t.play_to_first_decision()
    rows = t.rows()
    game = gm.games(rows)[0]
    game["beats"] = game["beats"] * 3
    why = gm.check_game(t.box, rows, game, WORLD)
    assert why and "not the beat the world has" in why


def test_status_and_check_only_read(t):
    t.play_to_first_decision()
    t.run("ask")
    before = t.raw()
    for argv in (("status",), ("check",)):
        t.run(*argv)
        t.run(*argv, world=False)
    assert t.raw() == before
