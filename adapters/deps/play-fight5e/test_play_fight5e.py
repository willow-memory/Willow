"""play-fight5e: an encounter fought on dice from the tower, every blow a row
naming the dice behind it; check holds it to the tower and fights it again;
a blow changed, dropped or added, an ending lost, dice reused, dropped before
the encounter opened or left over, a die left in the tower, each refused with
why; the encounters listed; the board drawn from the rows with no dice; a
sweep that writes nothing; and a refusal, never a quiet skip, without the
dice library."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "play_fight5e.py"
TOWER = HERE.parents[1] / "stdlib" / "dice-tower" / "dice_tower.py"
spec = importlib.util.spec_from_file_location("play_fight5e", SCRIPT)
pe = importlib.util.module_from_spec(spec)
sys.modules["play_fight5e"] = pe
spec.loader.exec_module(pe)
NOW = ["--now", "2026-11-23T20:00:00Z"]
TS = NOW[1]
#: the kernel's own fields on a row; the rest are what the row says
KERNEL_FIELDS = ("n", "kind", "who", "family", "standing", "version", "ts", "prev", "hash")  # fmt: skip


def run(*argv, script: Path = SCRIPT, **kw) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *map(str, argv)], capture_output=True, text=True, **kw)  # fmt: skip


def make(where: Path) -> Path:
    pile = where / "pile"
    pile.mkdir(parents=True)
    (pile / "notes.md").write_text("The warden wakes at dusk.\n")
    box = where / "box"
    got = run("init", "--box", box, "--pile", pile, "--key", where / "key", *NOW, script=KERNEL)  # fmt: skip
    assert got.returncode == 0, got.stderr
    (where / "dice").mkdir()
    return box


def rows(box: Path) -> list[dict]:
    got, breaks = pe.kernel.read(box / "record.jsonl")
    assert breaks == []
    return got


def fight(box: Path, encounter: str = "warden") -> subprocess.CompletedProcess:
    return run("--box", box, "fight", encounter, "--to", box.parent / "dice", *NOW)


def check(box: Path) -> subprocess.CompletedProcess:
    return run("--box", box, "check")


def rewrite(box: Path, keep: int, changed: list[dict]) -> None:
    """The record cut back to its first `keep` rows, then `changed` appended
    by the kernel: a chain that holds, saying what the test wants it to."""
    path = box / "record.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    path.write_text("".join(lines[:keep]), encoding="utf-8")
    for r in changed:
        fields = {k: v for k, v in r.items() if k not in KERNEL_FIELDS}
        pe.kernel.append(box, r["ts"], r["kind"], who=r["who"], **fields)


@pytest.fixture(scope="module")
def fought(tmp_path_factory) -> Path:
    pytest.importorskip("dice")
    where = tmp_path_factory.mktemp("fought")
    box = make(where)
    got = fight(box)
    assert got.returncode == 0, got.stderr
    return where


@pytest.fixture
def box(fought, tmp_path) -> Path:
    return shutil.copytree(fought, tmp_path / "t") / "box"


# ── without the dice library ────────────────────────────────────────────────


def without_dice(*argv) -> subprocess.CompletedProcess:
    """The script run as if the dice library weren't installed."""
    code = (
        "import runpy, sys; sys.modules['dice'] = None; "
        f"sys.argv = {[str(SCRIPT), *map(str, argv)]!r}; "
        f"runpy.run_path({str(SCRIPT)!r}, run_name='__main__')"
    )
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)  # fmt: skip


def test_without_the_dice_library_it_refuses_and_names_the_install(tmp_path):
    box = make(tmp_path)
    for argv in (["fight", "warden", "--to", tmp_path / "dice"], ["check"]):
        got = without_dice("--box", box, *argv)
        assert got.returncode == 2, got.stderr
        assert "pip install -r adapters/deps/play-fight5e/requirements.txt" in got.stderr  # fmt: skip
    assert without_dice("sim", "raiders").returncode == 2
    assert not [r for r in rows(box) if r["kind"] == pe.OPEN]


def test_the_board_needs_no_dice_only_the_rows(box):
    got = without_dice("--box", box, "board")
    assert got.returncode == 0, got.stderr
    assert "The party" in got.stdout and "Mind-Forge Warden" in got.stdout
    assert without_dice("list").returncode == 0


# ── the command line ────────────────────────────────────────────────────────


def test_the_encounters_are_listed():
    got = run("list")
    assert got.returncode == 0
    assert [line.split()[0] for line in got.stdout.splitlines()] == ["warden", "enforcers", "raiders", "bruiser"]  # fmt: skip


@pytest.mark.parametrize("argv", [[], ["fight", "warden"], ["--box", "{b}"], ["--box", "{b}", "fight"], ["--box", "{b}", "fight", "warden"], ["--box", "{b}", "check", "x"], ["--box", "{b}", "roll"], ["list", "x"], ["sim"]])  # fmt: skip
def test_a_command_line_it_has_not_is_refused_with_its_usage(tmp_path, argv):
    got = run(*[a.format(b=tmp_path) for a in argv])
    assert got.returncode == 2
    assert got.stderr.strip() == pe.USAGE.strip()


def test_a_folder_that_is_not_a_box_is_refused(tmp_path):
    got = run("--box", tmp_path, "check")
    assert got.returncode == 2 and "isn't a box" in got.stderr


def test_an_encounter_that_isnt_one_is_refused_and_nothing_written(tmp_path):
    pytest.importorskip("dice")
    box = make(tmp_path)
    before = rows(box)
    got = fight(box, "dragon")
    assert got.returncode == 2
    assert "no encounter 'dragon': warden, enforcers, raiders, bruiser" in got.stderr
    assert rows(box) == before


def test_a_die_folder_not_there_is_refused_not_made(tmp_path):
    pytest.importorskip("dice")
    box = make(tmp_path)
    got = run("--box", box, "fight", "warden", "--to", tmp_path / "none", *NOW)
    assert got.returncode == 2 and "isn't a folder" in got.stderr
    assert not (tmp_path / "none").exists()


# ── a fight on the record ───────────────────────────────────────────────────


def test_a_fight_is_kept_blow_by_blow_each_naming_its_tower_dice_and_checks(box):
    rs = rows(box)
    opened = next(r for r in rs if r["kind"] == pe.OPEN)
    assert opened["encounter"] == "warden" and opened["engine"] == pe.ENGINE
    assert opened["desc"].startswith("the full party vs a Mind-Forge Warden")
    mine = [r for r in rs if r["kind"] in (pe.BLOW, pe.END)]
    assert mine[-1]["kind"] == pe.END and sum(r["kind"] == pe.END for r in mine) == 1
    assert {r["fight"] for r in mine} == {opened["n"]}
    assert mine[0]["note"].startswith("initiative: ")
    named = [m for r in mine for m in r["dice"]]
    outs = [r["n"] for r in rs if r["kind"] == pe.tower.OUT]
    assert named == outs and len(set(named)) == len(named)  # every die once, in order
    assert all(rs[m]["drop"] > opened["n"] for m in named)
    assert {r["who"] for r in [opened, *mine]} == {pe.WHO}
    assert {r["ts"] for r in rs[opened["n"] :]} == {TS}  # the time given
    assert not [r for r in rs if r["kind"] in ("seal", "decline")]  # it seals nothing
    assert len(list((box.parent / "dice").glob("die-*.json"))) == len(named)
    got = check(box)
    assert got.returncode == 0, got.stderr
    assert got.stdout == "1 encounter on the record; every blow holds\n"


def test_what_is_printed_is_what_is_on_the_record(tmp_path):
    pytest.importorskip("dice")
    box = make(tmp_path)
    got = fight(box, "raiders")
    assert got.returncode == 0, got.stderr
    rs = rows(box)
    for r in rs:
        if r["kind"] == pe.BLOW:
            assert f"  {r['note']}\n" in got.stdout
    res = rs[-1]["result"]
    assert f"{res['outcome'].upper()} in {res['rounds']} rounds; standing: " in got.stdout  # fmt: skip


def test_a_second_fight_goes_on_from_the_dice_already_there(box):
    first = len(list((box.parent / "dice").glob("die-*.json")))
    assert fight(box, "raiders").returncode == 0
    assert len(list((box.parent / "dice").glob("die-*.json"))) > first
    assert check(box).stdout == "2 encounters on the record; every blow holds\n"


def test_a_record_with_no_fight_holds_none(tmp_path):
    pytest.importorskip("dice")
    got = check(make(tmp_path))
    assert got.returncode == 0 and got.stdout == "0 encounters on the record; every blow holds\n"  # fmt: skip


def test_a_blow_changed_in_the_file_breaks_the_chain(box):
    path = box / "record.jsonl"
    path.write_text(path.read_text().replace(" hits ", " misses ", 1))
    for argv in (["check"], ["board"]):
        got = run("--box", box, *argv)
        assert got.returncode == 2 and "the record doesn't verify" in got.stderr


def first(rs: list[dict], kind: str, has: str = "") -> int:
    return next(r["n"] for r in rs if r["kind"] == kind and has in r.get("note", has))


def test_a_blow_changed_on_a_sound_chain_isnt_what_its_dice_give(box):
    rs = rows(box)
    k = first(rs, pe.BLOW, " hits ")
    changed = [dict(r) for r in rs[k:]]
    changed[0]["note"] = changed[0]["note"].replace(" hits ", " misses ", 1)
    rewrite(box, k, changed)
    got = check(box)
    assert got.returncode == 2
    assert f"row {k}, " in got.stderr and "isn't what its dice give" in got.stderr


@pytest.mark.parametrize("cut", ["blow", "end"])
def test_a_blow_or_the_ending_dropped_is_refused(box, cut):
    rs = rows(box)
    kind = pe.BLOW if cut == "blow" else pe.END
    k = max(r["n"] for r in rs if r["kind"] == kind)
    rewrite(box, k, [dict(r) for r in rs[k + 1 :]])
    got = check(box)
    assert got.returncode == 2
    assert ("endings on the record" if cut == "end" else "its dice give") in got.stderr  # fmt: skip


def test_rows_with_no_tower_dice_behind_them_are_refused(box):
    rs = rows(box)
    k = first(rs, pe.BLOW)
    rewrite(box, k, [{**r, "dice": []} if r["kind"] in (pe.BLOW, pe.END) else dict(r) for r in rs[k:]])  # fmt: skip
    got = check(box)
    assert got.returncode == 2 and "its dice don't make the fight" in got.stderr


def test_a_row_naming_what_is_not_a_die_out_is_refused(box):
    rs = rows(box)
    k = first(rs, pe.BLOW)
    changed = [dict(r) for r in rs[k:]]
    changed[0]["dice"] = [0]
    rewrite(box, k, changed)
    got = check(box)
    assert got.returncode == 2 and "names row 0, which isn't a die out of the tower" in got.stderr  # fmt: skip


def test_dice_used_twice_are_refused(box):
    rs = rows(box)
    opened = next(r for r in rs if r["kind"] == pe.OPEN)
    again = [dict(opened)] + [{**r, "fight": len(rs)} for r in rs if r["kind"] in (pe.BLOW, pe.END)]  # fmt: skip
    rewrite(
        box, len(rs), again
    )  # the same encounter once more, opened anew, on the same dice
    got = check(box)
    assert got.returncode == 2 and "which another row used" in got.stderr


def test_dice_dropped_before_the_encounter_opened_are_refused(box):
    rs = rows(box)
    opened = next(r for r in rs if r["kind"] == pe.OPEN)
    k = first(rs, pe.BLOW)
    # the open row moved after the first blow's dice, a note in its place so each die keeps its row
    note = {"kind": "note", "who": "test", "ts": TS}
    rewrite(box, opened["n"], [note, *[dict(r) for r in rs[opened["n"] + 1 : k]], dict(opened), *[{**r, "fight": k} for r in rs[k:]]])  # fmt: skip
    got = check(box)
    assert got.returncode == 2 and "before the encounter opened" in got.stderr


def test_dice_left_over_are_named(box):
    rs = rows(box)
    spare = box.parent / "dice" / "spare.json"
    assert run("--box", box, "drop", "--dice", "1d20", "--to", spare, *NOW, script=TOWER).returncode == 0  # fmt: skip
    assert run("--box", box, "out", "--die", spare, *NOW, script=TOWER).returncode == 0
    rs = rows(box)
    end = next(r for r in rs if r["kind"] == pe.END)
    moved = {
        **end,
        "dice": [*end["dice"], rs[-1]["n"]],
    }  # the spare's out row, named by the end
    rewrite(box, end["n"], [moved, *[dict(r) for r in rs[end["n"] + 1 :]]])
    got = check(box)
    assert got.returncode == 2 and "names 1 more dice than its fight throws" in got.stderr  # fmt: skip


def test_a_die_left_in_the_tower_is_named(box):
    spare = box.parent / "dice" / "spare.json"
    assert run("--box", box, "drop", "--dice", "1d20", "--to", spare, *NOW, script=TOWER).returncode == 0  # fmt: skip
    got = check(box)
    assert got.returncode == 2 and "1 die is still in the tower" in got.stderr


class Cycle:
    """Faces that walk round each die: no tower, the same every time."""

    def __init__(self, step: int):
        self.step, self.drawn = step, 0

    def draw(self, sides: int) -> int:
        self.drawn += 1
        return 1 + (self.drawn * self.step) % sides


def test_a_fight_on_faces_handed_in_comes_out_the_same_every_time():
    pytest.importorskip("dice")
    combat = pe.engine()
    one = pe.play(combat, "raiders", Cycle(7))
    two = pe.play(combat, "raiders", Cycle(7))
    assert one == two and one[1]["outcome"] in ("party", "foe", "stalemate")


def test_out_of_faces_is_refused_never_guessed():
    pytest.importorskip("dice")
    with pytest.raises(pe.OutOfFaces):
        pe.play(pe.engine(), "warden", pe.Faces([10, 10]))


def test_a_draw_that_isnt_a_die_is_refused():
    src = pe.SaidRandom(pe.Faces([3]))
    for draw in (src.random, src.shuffle, lambda: src.choice([1, 2]), lambda: src.randrange(6)):  # fmt: skip
        with pytest.raises(RuntimeError, match="isn't a die"):
            draw()
    assert src.randint(1, 6) == 3
    with pytest.raises(ValueError):
        src.randint(0, 6)


def test_a_tower_that_refuses_a_die_stops_the_fight_and_says_so(tmp_path):
    pytest.importorskip("dice")
    box = make(tmp_path)
    dice = tmp_path / "dice"
    (dice / "die-0001.json").write_text(
        "{}"
    )  # the next die's file is there: never written over
    src = pe.TowerFaces(box, dice, TS)
    src.n = 0
    with pytest.raises(
        RuntimeError, match="would not take a d20: .*never written over"
    ):
        pe.play(pe.engine(), "warden", src)


# ── the board ───────────────────────────────────────────────────────────────


def test_the_board_at_the_end_is_what_the_end_says(box):
    end = rows(box)[-1]["result"]
    got = run("--box", box, "board")
    assert got.returncode == 0, got.stderr
    said = {"party": "the party won", "foe": "the party fell"}[end["outcome"]]
    assert got.stdout.startswith(f"⚔️  the full party vs a Mind-Forge Warden (the gallery's guardian wakes), round {end['rounds']} of {end['rounds']}: {said}\n")  # fmt: skip
    standing = set(end["party_survivors"] + end["foe_survivors"])
    for name in ["Sena Koll", "Tide-touched Scout", "Warforged", "Mind-Forge Warden"]:
        mark = next(x for x in got.stdout.splitlines() if x.strip().startswith(name + " "))  # fmt: skip
        assert ("✖ down" in mark) == (name not in standing), mark
    assert "▶" not in got.stdout  # it's over: no one's turn


def test_the_board_after_a_round_is_the_fight_as_it_stood_then(box):
    end = rows(box)[-1]["result"]
    got = run("--box", box, "board", "--round", "1")
    assert got.returncode == 0 and f", round 1 of {end['rounds']}\n" in got.stdout
    assert ("▶" in got.stdout) == (end["rounds"] > 1)  # whose turn, mid-fight


def test_a_board_it_cant_draw_is_refused(tmp_path, box):
    empty = make(tmp_path / "e")
    assert run("--box", empty, "board").stderr == "play-fight5e: no encounter on the record\n"  # fmt: skip
    at = next(r["n"] for r in rows(box) if r["kind"] == pe.OPEN)
    got = run("--box", box, "board", "--fight", "2")
    assert got.stderr == f"play-fight5e: row 2 doesn't open an encounter; encounters open at rows {at}\n"  # fmt: skip
    assert run("--box", box, "board", "--round", "x").returncode == 2
    assert run("--box", box, "board", "--fight", str(at)).returncode == 0


# ── a sweep ─────────────────────────────────────────────────────────────────


def test_a_sweep_says_where_an_encounter_rolls_out_and_writes_nothing(tmp_path):
    pytest.importorskip("dice")
    got = run("sim", "raiders", "--runs", "20", cwd=tmp_path)
    assert got.returncode == 0, got.stderr
    assert "raiders · 20 runs · seeds 0..19" in got.stdout and "party wins :" in got.stdout  # fmt: skip
    assert list(tmp_path.iterdir()) == []
    assert (
        run("sim", "raiders", "--runs", "20").stdout == got.stdout
    )  # seeded: the same sweep
    for bad in (["sim", "dragon"], ["sim", "raiders", "--runs", "0"], ["sim", "raiders", "--runs", "x"]):  # fmt: skip
        assert run(*bad).returncode == 2


def test_the_record_holds_json_the_engine_gave():
    pytest.importorskip("dice")
    blows, res = pe.play(pe.engine(), "bruiser", Cycle(11))
    assert all(json.loads(json.dumps(s)) == s for _, s, _ in blows)
    assert set(res) == {"outcome", "rounds", "party_survivors", "foe_survivors"}
