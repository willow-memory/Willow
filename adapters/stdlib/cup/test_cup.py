"""cup: dice shaken into a cup, only a hash on the record until it's lifted;
the faces settled by the secret alone, so no row written before the lift
changes them; every lift held to its cup by check, and every cup still down
named."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import stat
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "cup.py"
spec = importlib.util.spec_from_file_location("cup", SCRIPT)
cup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cup)
NOW = ["--now", "2026-11-20T21:00:00Z"]


def run(*argv: str, script: Path = SCRIPT) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *argv], capture_output=True, text=True)  # fmt: skip


def make(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(parents=True)
    (pile / "notes.md").write_text("The gremlins hate fire.\n")
    box = tmp_path / "box"
    got = run("init", "--box", str(box), "--pile", str(pile), "--key", str(tmp_path / "key"), *NOW, script=KERNEL)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return box


def rows(box: Path) -> list[dict]:
    got, breaks = cup.kernel.read(box / "record.jsonl")
    assert breaks == []
    return got


def shake(
    box: Path, to: Path, dice: str = "2d6", *more: str
) -> subprocess.CompletedProcess:
    return run("--box", str(box), "shake", "--dice", dice, "--to", str(to), *more, *NOW)


def lift(box: Path, cupfile: Path) -> subprocess.CompletedProcess:
    return run("--box", str(box), "lift", "--cup", str(cupfile), *NOW)


def test_a_shake_puts_only_the_secrets_hash_on_the_record(tmp_path):
    box = make(tmp_path)
    got = shake(box, tmp_path / "a.cup", "2d6", "--for", "Mira climbs")
    assert got.returncode == 0, got.stderr
    row = rows(box)[-1]
    held = json.loads((tmp_path / "a.cup").read_text())
    assert row["kind"] == "cup" and row["who"] == "cup" and row["dice"] == "2d6" and row["for"] == "Mira climbs"  # fmt: skip
    assert row["commit"] == hashlib.sha256(held["secret"].encode()).hexdigest() == held["commit"]  # fmt: skip
    assert (
        held["cup"] == row["n"] and held["dice"] == "2d6" and len(held["secret"]) == 64
    )
    assert held["secret"] not in (box / "record.jsonl").read_text()  # only the hash
    assert stat.S_IMODE((tmp_path / "a.cup").stat().st_mode) == 0o600
    assert got.stdout == f"the die is in the cup (row {row['n']}): 2d6, for Mira climbs, under {row['commit'][:12]}\n"  # fmt: skip


def test_a_lift_throws_from_the_secret_and_puts_it_on_the_record(tmp_path):
    box = make(tmp_path)
    shake(box, tmp_path / "a.cup", "4d6kh3")
    secret = json.loads((tmp_path / "a.cup").read_text())["secret"]
    got = lift(box, tmp_path / "a.cup")
    assert got.returncode == 0, got.stderr
    row = rows(box)[-1]
    again = cup.play_dice5e.throw("4d6kh3", secret)
    assert row["kind"] == "cup-lift" and row["cup"] == rows(box)[-2]["n"] and row["secret"] == secret  # fmt: skip
    assert (row["faces"], row["kept"], row["total"], row["dice"]) == (again["faces"], again["kept"], again["total"], "4d6kh3")  # fmt: skip
    assert got.stdout == f"{cup.play_dice5e.said(row)}, lifted from the cup at row {row['cup']}   (row {row['n']})\n"  # fmt: skip


def test_no_row_written_before_the_lift_changes_the_roll(tmp_path):
    """The point of a cup: the same secret gives the same faces however
    many rows (a ruling, a note, another roll) come between."""
    a, b = make(tmp_path / "a"), make(tmp_path / "b")
    shake(a, tmp_path / "a.cup", "3d6")
    (tmp_path / "b.cup").write_text((tmp_path / "a.cup").read_text())
    rb = rows(b)
    cup.kernel.append(b, "2026-11-20T21:00:01Z", "cup", who="cup", dice="3d6", commit=rows(a)[-1]["commit"])  # fmt: skip
    for k in range(3):
        cup.kernel.append(b, "2026-11-20T21:00:02Z", "note", who="test", text=f"a ruling {k}")  # fmt: skip
    held = json.loads((tmp_path / "b.cup").read_text())
    (tmp_path / "b.cup").write_text(json.dumps({**held, "cup": len(rb)}))
    assert lift(a, tmp_path / "a.cup").returncode == 0
    assert lift(b, tmp_path / "b.cup").returncode == 0
    assert rows(a)[-1]["faces"] == rows(b)[-1]["faces"] and rows(a)[-1]["total"] == rows(b)[-1]["total"]  # fmt: skip


def test_a_cup_is_lifted_once(tmp_path):
    box = make(tmp_path)
    shake(box, tmp_path / "a.cup")
    assert lift(box, tmp_path / "a.cup").returncode == 0
    again = lift(box, tmp_path / "a.cup")
    n = rows(box)[-2]["n"]
    assert again.returncode == 2 and again.stderr == f"refused: the cup at row {n} is lifted already\n"  # fmt: skip


def test_check_names_every_cup_still_down(tmp_path):
    box = make(tmp_path)
    shake(box, tmp_path / "a.cup", "2d6", "--for", "Mira climbs")
    shake(box, tmp_path / "b.cup", "1d20", "--for", "the screen roll")
    shake(box, tmp_path / "c.cup", "1d4")
    lift(box, tmp_path / "a.cup")
    got = run("--box", str(box), "check")
    n = [r["n"] for r in rows(box) if r["kind"] == "cup"]
    assert got.returncode == 0
    assert got.stdout == f'1 cup lifted, every one holds; 2 still down (row {n[1]}, 1d20, "the screen roll"; row {n[2]}, 1d4)\n'  # fmt: skip
    for f in ("b.cup", "c.cup"):
        lift(box, tmp_path / f)
    assert run("--box", str(box), "check").stdout == "3 cups lifted, every one holds\n"
    fresh = make(tmp_path / "fresh")
    assert (
        run("--box", str(fresh), "check").stdout == "0 cups lifted, every one holds\n"
    )


def test_check_finds_a_lift_that_doesnt_hold(tmp_path):
    box = make(tmp_path)
    shake(box, tmp_path / "a.cup", "2d6")
    lift(box, tmp_path / "a.cup")
    good = rows(box)
    n = good[-2]["n"]

    def fails(change: dict, why: str, at: int = -1) -> None:
        rs = [dict(r) for r in good]
        rs[at].update(change)
        held, down, said = cup.check(rs)
        assert held == 0 and down == [] and said == f"row {rs[-1]['n']}: {why}"

    fails(
        {"total": good[-1]["total"] + 1}, "its faces aren't what the cup's secret gives"
    )
    fails({"faces": [[1, 1]]}, "its faces aren't what the cup's secret gives")
    fails({"kept": [[0]]}, "its faces aren't what the cup's secret gives")
    fails({"dice": "2d8"}, "its faces aren't what the cup's secret gives")
    fails(
        {"secret": "ab" * 32},
        f"its secret isn't the one shaken into the cup at row {n}",
    )
    fails({"commit": "0" * 64}, f"its secret isn't the one shaken into the cup at row {n}", at=-2)  # fmt: skip
    fails({"cup": good[-1]["n"]}, "it lifts no cup shaken before it")
    fails({"cup": 0}, "it lifts no cup shaken before it")
    fails({"cup": "x"}, "it lifts no cup shaken before it")
    fails({"dice": "2d6kh9"}, "2d6kh9: keep 1 to 2", at=-2)
    twice = [dict(r) for r in good] + [{**good[-1], "n": good[-1]["n"] + 1}]
    assert cup.check(twice) == (1, [], f"row {good[-1]['n'] + 1}: the cup at row {n} is lifted twice")  # fmt: skip
    assert cup.check(good) == (1, [], None)


def test_a_record_that_doesnt_verify_is_refused(tmp_path):
    box = make(tmp_path)
    shake(box, tmp_path / "a.cup")
    f = box / "record.jsonl"
    f.write_text(f.read_text().replace('"2d6"', '"2d8"', 1))
    for argv in (["check"], ["lift", "--cup", str(tmp_path / "a.cup")], ["shake", "--dice", "1d6", "--to", str(tmp_path / "b.cup")]):  # fmt: skip
        got = run("--box", str(box), *argv, *NOW)
        assert got.returncode == 2 and got.stderr.startswith("refused: the record doesn't verify: ")  # fmt: skip
    assert run("--box", str(box), "check").stdout == ""


@pytest.mark.parametrize(
    "dice, to, why",
    [
        ("2x6", "a.cup", "'2x6' isn't dice notation"),
        ("2d6", "there.cup", "is already there; a cup is never written over"),
        ("2d6", "nowhere/a.cup", "nowhere isn't a folder"),
        (
            "2d6",
            "box/a.cup",
            "the cup file goes outside the box, so the record never holds the secret",
        ),  # fmt: skip
    ],
)
def test_a_shake_it_cant_make_is_refused_and_nothing_written(tmp_path, dice, to, why):
    box = make(tmp_path)
    (tmp_path / "there.cup").write_text("mine\n")
    before = rows(box)
    got = shake(box, tmp_path / to, dice)
    assert (
        got.returncode == 2 and why in got.stderr and got.stderr.startswith("refused: ")
    )
    assert rows(box) == before and (tmp_path / "there.cup").read_text() == "mine\n"
    assert not (tmp_path / "a.cup").exists() and not (box / "a.cup").exists()


def test_a_cup_file_that_isnt_this_boxs_or_isnt_one_is_refused(tmp_path):
    box, other = make(tmp_path / "one"), make(tmp_path / "two")
    shake(other, tmp_path / "theirs.cup")
    shake(box, tmp_path / "mine.cup")
    held = json.loads((tmp_path / "mine.cup").read_text())
    cases = {
        "theirs.cup": None,
        "garbled.cup": "not json",
        "short.cup": json.dumps({"cup": held["cup"]}),
        "far.cup": json.dumps({**held, "cup": 999}),
        "row0.cup": json.dumps({**held, "cup": 0}),
        "swapped.cup": json.dumps({**held, "secret": "cd" * 32}),
        "neg.cup": json.dumps({**held, "cup": -1}),
    }
    for name, text in cases.items():
        if text is not None:
            (tmp_path / name).write_text(text)
        got = lift(box, tmp_path / name)
        why = "isn't a cup file" if name in ("garbled.cup", "short.cup") else "isn't a cup shaken in this box"  # fmt: skip
        assert got.returncode == 2 and got.stderr == f"refused: {tmp_path / name} {why}\n", (name, got.stderr)  # fmt: skip
    gone = lift(box, tmp_path / "missing.cup")
    assert gone.returncode == 2 and "isn't a cup file" in gone.stderr
    assert [r["kind"] for r in rows(box)].count("cup-lift") == 0


@pytest.mark.parametrize(
    "argv",
    [[], ["shake"], ["--box", "{box}"], ["--box", "{box}", "roll"], ["--box", "{box}", "shake", "--dice", "2d6"],
     ["--box", "{box}", "shake", "--to", "x.cup"], ["--box", "{box}", "lift"], ["--box", "{box}", "check", "x"]],
)  # fmt: skip
def test_a_bad_command_line_prints_how_to_use_it(tmp_path, argv):
    box = make(tmp_path)
    got = run(*[a.format(box=box) for a in argv])
    assert got.returncode == 2 and got.stderr.strip() == cup.USAGE.strip()
    assert "python adapters/stdlib/cup/cup.py --box DIR shake" in got.stderr


def test_a_folder_that_isnt_a_box_is_refused(tmp_path):
    got = run("--box", str(tmp_path), "check")
    assert got.returncode == 2 and got.stderr == f"refused: {tmp_path} isn't a box: make one with kernel.py init\n"  # fmt: skip
