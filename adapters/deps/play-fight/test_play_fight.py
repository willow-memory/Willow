"""play-fight: a fight played on dice from the tower, every row on the record
naming the dice behind it; check holds it to the tower and plays it again;
rows changed, dice reused, dice dropped before the fight, a fight with no end,
each refused with why; the fighters file held to its fields; and a refusal,
never a quiet skip, without dndwright."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "play_fight.py"
TOWER = HERE.parents[1] / "stdlib" / "dice-tower" / "dice_tower.py"
spec = importlib.util.spec_from_file_location("play_fight", SCRIPT)
pf = importlib.util.module_from_spec(spec)
sys.modules["play_fight"] = pf  # a dataclass looks itself up by its module
spec.loader.exec_module(pf)
NOW = ["--now", "2026-11-23T20:00:00Z"]
TS = NOW[1]

TAMSIN = {"name": "Tamsin", "side": "party", "hp": 14, "ac": 13, "init_mod": 0, "attack_bonus": 4, "damage": "1d6+2"}  # fmt: skip
ORO = {"name": "Oro", "side": "party", "hp": 12, "ac": 13, "init_mod": 2, "attack_bonus": 2, "damage": "1d6"}  # fmt: skip
RAIDER = {"name": "Raider", "side": "foes", "hp": 11, "ac": 12, "init_mod": 1, "attack_bonus": 3, "damage": "1d6+1", "attacks": 2}  # fmt: skip
#: the kernel's own fields on a row; the rest are what the row says
KERNEL_FIELDS = ("n", "kind", "who", "family", "standing", "version", "ts", "prev", "hash")  # fmt: skip


def run(*argv: str, script: Path = SCRIPT) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *argv], capture_output=True, text=True)  # fmt: skip


def make(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(parents=True)
    (pile / "notes.md").write_text("The raiders came at dusk.\n")
    box = tmp_path / "box"
    got = run("init", "--box", str(box), "--pile", str(pile), "--key", str(tmp_path / "key"), *NOW, script=KERNEL)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return box


def rows(box: Path) -> list[dict]:
    got, breaks = pf.kernel.read(box / "record.jsonl")
    assert breaks == []
    return got


def fighters_file(tmp_path: Path, fighters: list) -> Path:
    path = tmp_path / "fighters.json"
    path.write_text(json.dumps(fighters))
    return path


def fight(tmp_path: Path, box: Path, fighters: list | None = None) -> subprocess.CompletedProcess:  # fmt: skip
    dice = tmp_path / "dice"
    dice.mkdir(exist_ok=True)
    f = fighters_file(tmp_path, fighters or [TAMSIN, ORO, RAIDER])
    return run("--box", str(box), "fight", "--fighters", str(f), "--to", str(dice), *NOW)  # fmt: skip


def rewrite(box: Path, keep: int, changed: list[dict]) -> None:
    """The record cut back to its first `keep` rows, then `changed` appended
    by the kernel: a chain that holds, saying what the test wants it to."""
    path = box / "record.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    path.write_text("".join(lines[:keep]), encoding="utf-8")
    for r in changed:
        fields = {k: v for k, v in r.items() if k not in KERNEL_FIELDS}
        pf.kernel.append(box, r["ts"], r["kind"], who=r["who"], **fields)


def check(box: Path) -> subprocess.CompletedProcess:
    return run("--box", str(box), "check")


# ── without dndwright ───────────────────────────────────────────────────────


def test_without_dndwright_it_refuses_and_names_the_install(tmp_path):
    box = make(tmp_path)
    code = (
        "import runpy, sys; sys.modules['dndwright'] = None; "
        f"sys.argv = [{str(SCRIPT)!r}, '--box', {str(box)!r}, 'check']; "
        f"runpy.run_path({str(SCRIPT)!r}, run_name='__main__')"
    )
    got = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert got.returncode == 2
    assert "pip install -r adapters/deps/play-fight/requirements.txt" in got.stderr
    assert rows(box)[-1]["kind"] != pf.BEGIN


def test_a_command_line_it_has_not_is_refused_with_its_usage(tmp_path):
    box = make(tmp_path)
    for argv in (["--box", str(box)], ["--box", str(box), "fight"], ["--box", str(box), "roll"], ["check"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2, argv
        assert "play_fight.py --box DIR check" in got.stderr


# ── the fighters file ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "bad, said",
    [
        ({}, "a JSON list"),
        ([], "a JSON list"),
        ([TAMSIN, "Raider"], "fighter 2 isn't an object"),
        ([TAMSIN, {**RAIDER, "speed": 30}], "fighter 2 has speed"),
        (
            [TAMSIN, {k: v for k, v in RAIDER.items() if k != "ac"}],
            "fighter 2 has no ac",
        ),
        ([TAMSIN, {**RAIDER, "name": "Tamsin"}], "two fighters are named Tamsin"),
        ([TAMSIN, {**RAIDER, "name": " "}], "fighter 2 has no name"),
        ([TAMSIN, {**RAIDER, "side": "monsters"}], "not party or foes"),
        ([TAMSIN, {**RAIDER, "hp": "11"}], "hp isn't a whole number"),
        ([TAMSIN, {**RAIDER, "ac": True}], "ac isn't a whole number"),
        ([TAMSIN, {**RAIDER, "hp": 0}], "at least 1 hp"),
        ([TAMSIN, {**RAIDER, "attacks": 0}], "at least 1 hp and 1 attack"),
        ([TAMSIN, {**RAIDER, "damage": "a lot"}], "isn't dice"),
        ([TAMSIN, {**RAIDER, "damage": 6}], "isn't dice"),
        ([TAMSIN, ORO], "no fighter is on the foes side"),
    ],
)
def test_the_fighters_are_held_to_their_fields(bad, said):
    with pytest.raises(ValueError, match=said):
        pf.fighters_from(bad)


def test_dice_with_more_than_one_term_are_dice():
    got = pf.fighters_from([TAMSIN, {**RAIDER, "damage": "2d6+1d4-1"}])
    assert got[1].damage == "2d6+1d4-1" and got[0].attacks == 1


def test_a_fighters_file_wrong_or_missing_is_refused_and_nothing_written(tmp_path):
    pytest.importorskip("dndwright")
    box = make(tmp_path)
    before = len(rows(box))
    got = fight(tmp_path, box, [TAMSIN, {**RAIDER, "side": "monsters"}])
    assert got.returncode == 2 and "not party or foes" in got.stderr
    missing = run("--box", str(box), "fight", "--fighters", str(tmp_path / "none.json"), "--to", str(tmp_path), *NOW)  # fmt: skip
    assert missing.returncode == 2 and "can't be read" in missing.stderr
    assert len(rows(box)) == before


def test_a_die_folder_not_there_is_refused_not_made(tmp_path):
    pytest.importorskip("dndwright")
    box = make(tmp_path)
    f = fighters_file(tmp_path, [TAMSIN, RAIDER])
    got = run("--box", str(box), "fight", "--fighters", str(f), "--to", str(tmp_path / "dice"), *NOW)  # fmt: skip
    assert got.returncode == 2 and "isn't a folder" in got.stderr
    assert not (tmp_path / "dice").exists()


def test_a_folder_that_is_not_a_box_is_refused(tmp_path):
    pytest.importorskip("dndwright")
    got = run("--box", str(tmp_path), "check")
    assert got.returncode == 2 and "isn't a box" in got.stderr


# ── the fight, on faces handed in ───────────────────────────────────────────


def test_a_fight_on_faces_handed_in_comes_out_the_same_every_time():
    dw = pf.dndwright() or pytest.skip("dndwright isn't installed")
    fighters = pf.fighters_from([TAMSIN, RAIDER])
    # initiative: Tamsin 15, Raider 3; Tamsin hits on 18 for 6+2, then on 20 (a critical) for 4+5+2
    faces = [15, 3, 18, 6, 1, 1, 20, 4, 5]
    got = pf.fight(dw, fighters, faces)
    assert got == pf.fight(dw, fighters, faces)
    assert [r["kind"] for r in got] == ["init", "init", "blow", "blow", "blow", "blow", "down", "end"]  # fmt: skip
    first = got[2]
    assert (first["who"], first["target"], first["hit"], first["damage"], first["hp_after"]) == ("Tamsin", "Raider", True, 8, 3)  # fmt: skip
    assert [b["hit"] for b in got[3:5]] == [
        False,
        False,
    ]  # the Raider's two blows, natural 1s
    crit = got[5]
    assert crit["crit"] and crit["dice"] == [4, 5] and crit["hp_after"] == 0
    assert got[-1] == {"kind": "end", "round": 2, "winner": "party"}
    assert [f for r in got for f in pf.faces_of(r)] == faces


def test_out_of_faces_is_refused_never_guessed():
    dw = pf.dndwright() or pytest.skip("dndwright isn't installed")
    with pytest.raises(pf.OutOfFaces):
        pf.fight(dw, pf.fighters_from([TAMSIN, RAIDER]), [15, 3])


def test_a_face_not_on_the_die_is_refused():
    dw = pf.dndwright() or pytest.skip("dndwright isn't installed")
    with pytest.raises(ValueError, match="21 is not on a d20"):
        pf.fight(dw, pf.fighters_from([TAMSIN, RAIDER]), [21])


def test_a_fight_nobody_can_win_ends_in_a_stalemate():
    dw = pf.dndwright() or pytest.skip("dndwright isn't installed")
    a = {**TAMSIN, "attack_bonus": 0}
    b = {**RAIDER, "attacks": 1, "attack_bonus": 0}
    got = pf.fight(dw, pf.fighters_from([a, b]), [10, 5] + [2] * (2 * pf.MAX_ROUNDS))
    assert got[-1] == {"kind": "end", "round": pf.MAX_ROUNDS, "winner": "stalemate"}
    assert pf.said(got[-1]) == f"no side won in {pf.MAX_ROUNDS} rounds"


def test_each_row_in_words():
    assert pf.said({"kind": "init", "who": "Oro", "d20": 9, "total": 11}) == "Oro rolls 9 for initiative: 11"  # fmt: skip
    miss = {"kind": "blow", "round": 1, "who": "Oro", "target": "Raider", "total": 7, "ac": 12, "hit": False}  # fmt: skip
    assert pf.said(miss) == "round 1: Oro attacks Raider, 7 against armor 12: a miss"
    hit = {**miss, "total": 22, "hit": True, "crit": True, "damage": 9, "hp_after": 2}
    assert pf.said(hit).endswith("a critical hit: 9 damage, Raider at 2")
    assert pf.said({"kind": "down", "who": "Raider"}) == "Raider is down"
    assert pf.said({"kind": "end", "round": 3, "winner": "foes"}) == "the foes side won in round 3"  # fmt: skip


# ── on the record, from the tower ───────────────────────────────────────────


def test_a_fight_on_the_tower_is_on_the_record_and_holds(tmp_path):
    pytest.importorskip("dndwright")
    box = make(tmp_path)
    got = fight(tmp_path, box)
    assert got.returncode == 0, got.stderr
    assert "side won in round" in got.stdout or "no side won" in got.stdout
    rs = rows(box)
    begun = next(r for r in rs if r["kind"] == pf.BEGIN)
    assert begun["fighters"][2] == RAIDER and begun["engine"].startswith("dndwright ")
    assert begun["who"] == pf.WHO and begun["standing"] == "unattested"
    mine = [r for r in rs if r["kind"] == pf.ROW]
    assert mine and all(r["fight"] == begun["n"] for r in mine)
    named = [m for r in mine for m in r.get("dice", [])]
    outs = [r["n"] for r in rs if r["kind"] == pf.tower.OUT]
    assert named == outs  # every die out is one a row names, in order, none twice
    for r in mine:
        assert [int(rs[m]["faces"][0][0]) for m in r.get("dice", [])] == pf.faces_of(r["row"])  # fmt: skip
    drops = [r for r in rs if r["kind"] == pf.tower.DROP]
    assert drops[0]["for"].endswith("rolls initiative")
    assert len(list((tmp_path / "dice").glob("die-*.json"))) == len(drops)
    assert not any(r["kind"] == "seal" for r in rs)
    held = check(box)
    assert held.returncode == 0, held.stderr
    assert held.stdout.strip() == "1 fight on the record, every one holds"


def test_a_second_fight_goes_on_from_the_dice_already_there(tmp_path):
    pytest.importorskip("dndwright")
    box = make(tmp_path)
    assert fight(tmp_path, box).returncode == 0
    first = len(list((tmp_path / "dice").glob("die-*.json")))
    assert fight(tmp_path, box, [TAMSIN, RAIDER]).returncode == 0
    assert len(list((tmp_path / "dice").glob("die-*.json"))) > first
    assert check(box).stdout.strip() == "2 fights on the record, every one holds"


def test_a_record_with_no_fight_holds_none(tmp_path):
    pytest.importorskip("dndwright")
    box = make(tmp_path)
    got = check(box)
    assert got.returncode == 0 and got.stdout.strip() == "0 fights on the record, every one holds"  # fmt: skip


def test_a_blow_changed_in_the_file_breaks_the_chain(tmp_path):
    pytest.importorskip("dndwright")
    box = make(tmp_path)
    assert fight(tmp_path, box).returncode == 0
    path = box / "record.jsonl"
    lines = path.read_text().splitlines()
    i = next(i for i, line in enumerate(lines) if '"kind":"blow"' in line)
    lines[i] = lines[i].replace('"kind":"blow"', '"kind":"blow","hp_after_fixed":1', 1)  # fmt: skip
    path.write_text("\n".join(lines) + "\n")
    got = check(box)
    assert got.returncode == 2 and "doesn't verify" in got.stderr


def test_a_blow_changed_on_a_sound_chain_does_not_come_out_as_written(tmp_path):
    pytest.importorskip("dndwright")
    box = make(tmp_path)
    assert fight(tmp_path, box).returncode == 0
    rs = rows(box)
    k = next(r["n"] for r in rs if r["kind"] == pf.ROW and r["row"]["kind"] == "blow")
    changed = [dict(r) for r in rs[k:]]
    changed[0]["row"] = {
        **changed[0]["row"],
        "hp_after": changed[0]["row"]["hp_after"] + 5,
    }
    rewrite(box, k, changed)
    got = check(box)
    assert got.returncode == 2
    assert f"row {k} doesn't come out as written" in got.stderr


def test_a_face_the_tower_did_not_bring_out_is_refused(tmp_path):
    pytest.importorskip("dndwright")
    box = make(tmp_path)
    assert fight(tmp_path, box).returncode == 0
    rs = rows(box)
    k = next(r["n"] for r in rs if r["kind"] == pf.ROW and r["row"]["kind"] == "init")
    changed = [dict(r) for r in rs[k:]]
    d20 = changed[0]["row"]["d20"]
    changed[0]["row"] = {**changed[0]["row"], "d20": d20 % 20 + 1}
    rewrite(box, k, changed)
    got = check(box)
    assert got.returncode == 2 and "the tower brought out" in got.stderr


def test_rows_with_no_tower_dice_behind_them_are_refused(tmp_path):
    pytest.importorskip("dndwright")
    box = make(tmp_path)
    assert fight(tmp_path, box).returncode == 0
    rs = rows(box)
    k = next(r["n"] for r in rs if r["kind"] == pf.ROW)
    changed = [{k2: v for k2, v in r.items() if k2 != "dice"} for r in rs[k:]]
    rewrite(box, k, changed)
    got = check(box)
    assert got.returncode == 2 and "names 0 tower dice" in got.stderr


def test_a_row_naming_what_is_not_a_die_out_is_refused(tmp_path):
    pytest.importorskip("dndwright")
    box = make(tmp_path)
    assert fight(tmp_path, box).returncode == 0
    rs = rows(box)
    k = next(r["n"] for r in rs if r["kind"] == pf.ROW)
    changed = [dict(r) for r in rs[k:]]
    changed[0]["dice"] = [0]
    rewrite(box, k, changed)
    got = check(box)
    assert got.returncode == 2 and "names row 0, which isn't a die out of the tower" in got.stderr  # fmt: skip


def test_dice_used_twice_are_refused(tmp_path):
    pytest.importorskip("dndwright")
    box = make(tmp_path)
    assert fight(tmp_path, box).returncode == 0
    rs = rows(box)
    begun = next(r for r in rs if r["kind"] == pf.BEGIN)
    again = [dict(begun)] + [{**r, "fight": len(rs)} for r in rs if r["kind"] == pf.ROW]
    rewrite(
        box, len(rs), again
    )  # the same fight once more, begun anew, on the same dice
    got = check(box)
    assert got.returncode == 2 and "which another row used" in got.stderr


def test_dice_dropped_before_the_fight_began_are_refused(tmp_path):
    pytest.importorskip("dndwright")
    box = make(tmp_path)
    assert fight(tmp_path, box).returncode == 0
    rs = rows(box)
    begun = next(r for r in rs if r["kind"] == pf.BEGIN)
    first = next(r["n"] for r in rs if r["kind"] == pf.ROW)
    # the begin row moved after the dice, a note in its place so each die keeps its row
    note = {"kind": "note", "who": "test", "ts": TS}
    tower_rows = [dict(r) for r in rs[begun["n"] + 1 : first]]
    fight_rows = [{**r, "fight": first} for r in rs[first:]]
    rewrite(box, begun["n"], [note, *tower_rows, dict(begun), *fight_rows])
    got = check(box)
    assert got.returncode == 2 and "before the fight began" in got.stderr


def test_a_fight_with_no_end_on_the_record_does_not_hold(tmp_path):
    pytest.importorskip("dndwright")
    box = make(tmp_path)
    assert fight(tmp_path, box).returncode == 0
    rs = rows(box)
    rewrite(box, len(rs) - 1, [])  # the end row cut away
    got = check(box)
    assert got.returncode == 2 and "has no end on the record" in got.stderr


def test_a_die_left_in_the_tower_is_named(tmp_path):
    pytest.importorskip("dndwright")
    box = make(tmp_path)
    assert fight(tmp_path, box).returncode == 0
    spare = str(tmp_path / "dice" / "spare.json")
    dropped = run("--box", str(box), "drop", "--dice", "1d20", "--to", spare, *NOW, script=TOWER)  # fmt: skip
    assert dropped.returncode == 0, dropped.stderr
    got = check(box)
    assert got.returncode == 2 and "1 die is still in the tower" in got.stderr


def test_a_tower_that_refuses_a_die_stops_the_fight_and_says_so(tmp_path):
    dw = pf.dndwright() or pytest.skip("dndwright isn't installed")
    box = make(tmp_path)
    dice = tmp_path / "dice"
    dice.mkdir()
    (dice / "die-0001.json").write_text(
        "{}"
    )  # the next die's file is there: never written over
    src = pf.TowerFaces(box, dice, TS)
    src.n = 0
    with pytest.raises(
        RuntimeError, match="would not take a d20: .*never written over"
    ):
        pf.fight(dw, pf.fighters_from([TAMSIN, RAIDER]), src)
