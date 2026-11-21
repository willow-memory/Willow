"""dice-tower: a die dropped in the tower, only a hash on the record until it's
out; the faces settled by the secret alone, so no row written before the out
changes them; every die out held to its drop by check, every die still inside
named, and the tower drawn as a page."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "dice_tower.py"
spec = importlib.util.spec_from_file_location("dice-tower", SCRIPT)
tower = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tower)
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
    got, breaks = tower.kernel.read(box / "record.jsonl")
    assert breaks == []
    return got


def drop(
    box: Path, to: Path, dice: str = "2d6", *more: str
) -> subprocess.CompletedProcess:
    return run("--box", str(box), "drop", "--dice", dice, "--to", str(to), *more, *NOW)


def in_process(monkeypatch, *argv: str) -> int:
    """main() called here, with argv where the guard reads it (sys.argv), so
    a write to --to is judged as one."""
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), *argv])
    return tower.main(list(argv))


def out(box: Path, diefile: Path) -> subprocess.CompletedProcess:
    return run("--box", str(box), "out", "--die", str(diefile), *NOW)


def test_a_drop_puts_only_the_secrets_hash_on_the_record(tmp_path):
    box = make(tmp_path)
    got = drop(box, tmp_path / "a.die", "2d6", "--for", "Mira climbs")
    assert got.returncode == 0, got.stderr
    row = rows(box)[-1]
    held = json.loads((tmp_path / "a.die").read_text())
    assert row["kind"] == "tower-drop" and row["who"] == "dice-tower" and row["dice"] == "2d6" and row["for"] == "Mira climbs"  # fmt: skip
    assert row["commit"] == hashlib.sha256(held["secret"].encode()).hexdigest() == held["commit"]  # fmt: skip
    assert "drop" not in held and held["dice"] == "2d6" and len(held["secret"]) == 64
    assert held["secret"] not in (box / "record.jsonl").read_text()  # only the hash
    assert stat.S_IMODE((tmp_path / "a.die").stat().st_mode) == 0o600
    assert got.stdout == f"in the tower (row {row['n']}): 2d6, for Mira climbs, under {row['commit'][:12]}\n"  # fmt: skip
    plain = drop(box, tmp_path / "b.die", "1d4")
    assert plain.stdout == f"in the tower (row {rows(box)[-1]['n']}): 1d4, under {rows(box)[-1]['commit'][:12]}\n"  # fmt: skip
    assert "for" not in rows(box)[-1]


def test_the_die_file_is_kept_and_only_yours_before_the_hash_goes_on(tmp_path, monkeypatch):  # fmt: skip
    box, die, seen = make(tmp_path), tmp_path / "a.die", {}
    append = tower.kernel.append

    def watched(*args, **kw):  # the moment the hash goes on the record
        seen["mode"] = stat.S_IMODE(die.stat().st_mode) if die.exists() else None
        seen["kept"] = die.exists() and json.loads(die.read_text())["commit"] == kw["commit"]  # fmt: skip
        return append(*args, **kw)

    monkeypatch.setattr(tower.kernel, "append", watched)
    was = os.umask(0)  # a umask that would leave a written file open to everyone
    try:
        assert in_process(monkeypatch, "--box", str(box), "drop", "--dice", "1d6", "--to", str(die), *NOW) == 0  # fmt: skip
    finally:
        os.umask(was)
    assert seen == {"mode": 0o600, "kept": True}


def test_a_drop_the_record_wont_take_leaves_no_die_file(tmp_path, monkeypatch, capsys):
    box = make(tmp_path)
    before = rows(box)

    def full(*_, **__):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(tower.kernel, "append", full)
    assert in_process(monkeypatch, "--box", str(box), "drop", "--dice", "1d6", "--to", str(tmp_path / "a.die"), *NOW) == 2  # fmt: skip
    assert "the die wasn't dropped" in capsys.readouterr().err
    assert not (tmp_path / "a.die").exists() and rows(box) == before


def test_a_die_file_that_names_its_row_still_comes_out(tmp_path):
    box = make(tmp_path)
    drop(box, tmp_path / "a.die", "1d20")
    n = rows(box)[-1]["n"]
    held = json.loads((tmp_path / "a.die").read_text())
    (tmp_path / "old.die").write_text(
        json.dumps({"drop": n, **held})
    )  # as they were written before
    got = out(box, tmp_path / "old.die")
    assert got.returncode == 0, got.stderr
    assert rows(box)[-1]["drop"] == n


def test_out_throws_from_the_secret_and_puts_it_on_the_record(tmp_path):
    box = make(tmp_path)
    drop(box, tmp_path / "a.die", "4d6kh3")
    secret = json.loads((tmp_path / "a.die").read_text())["secret"]
    got = out(box, tmp_path / "a.die")
    assert got.returncode == 0, got.stderr
    row = rows(box)[-1]
    again = tower.play_dice5e.throw("4d6kh3", secret)
    assert row["kind"] == "tower-out" and row["drop"] == rows(box)[-2]["n"] and row["secret"] == secret  # fmt: skip
    assert (row["faces"], row["kept"], row["total"], row["dice"]) == (again["faces"], again["kept"], again["total"], "4d6kh3")  # fmt: skip
    assert got.stdout == f"{tower.play_dice5e.said(row)}, out of the tower from row {row['drop']}   (row {row['n']})\n"  # fmt: skip


def test_no_row_written_before_the_out_changes_the_roll(tmp_path):
    """The point of a tower: the same secret gives the same faces however
    many rows (a ruling, a note, another roll) come between."""
    a, b = make(tmp_path / "a"), make(tmp_path / "b")
    drop(a, tmp_path / "a.die", "3d6")
    held = json.loads((tmp_path / "a.die").read_text())
    at = len(rows(b))
    tower.kernel.append(b, "2026-11-20T21:00:01Z", "tower-drop", who="dice-tower", dice="3d6", commit=held["commit"])  # fmt: skip
    for k in range(3):
        tower.kernel.append(b, "2026-11-20T21:00:02Z", "note", who="test", text=f"a ruling {k}")  # fmt: skip
    (tmp_path / "b.die").write_text(json.dumps({**held, "drop": at}))
    assert out(a, tmp_path / "a.die").returncode == 0
    assert out(b, tmp_path / "b.die").returncode == 0
    assert rows(a)[-1]["faces"] == rows(b)[-1]["faces"] and rows(a)[-1]["total"] == rows(b)[-1]["total"]  # fmt: skip


def test_a_die_comes_out_once(tmp_path):
    box = make(tmp_path)
    drop(box, tmp_path / "a.die")
    assert out(box, tmp_path / "a.die").returncode == 0
    again = out(box, tmp_path / "a.die")
    n = rows(box)[-2]["n"]
    assert again.returncode == 2 and again.stderr == f"refused: the die dropped at row {n} is out already\n"  # fmt: skip


def test_check_names_every_die_still_inside(tmp_path):
    box = make(tmp_path)
    drop(box, tmp_path / "a.die", "2d6", "--for", "Mira climbs")
    drop(box, tmp_path / "b.die", "1d20", "--for", "the screen roll")
    drop(box, tmp_path / "c.die", "1d4")
    out(box, tmp_path / "a.die")
    got = run("--box", str(box), "check")
    n = [r["n"] for r in rows(box) if r["kind"] == "tower-drop"]
    assert got.returncode == 0
    assert got.stdout == f'1 die out of the tower, every one holds; 2 still inside (row {n[1]}, 1d20, "the screen roll"; row {n[2]}, 1d4)\n'  # fmt: skip
    for f in ("b.die", "c.die"):
        out(box, tmp_path / f)
    assert run("--box", str(box), "check").stdout == "3 dice out of the tower, every one holds\n"  # fmt: skip
    fresh = make(tmp_path / "fresh")
    assert run("--box", str(fresh), "check").stdout == "0 dice out of the tower, every one holds\n"  # fmt: skip


def test_check_finds_a_die_out_that_doesnt_hold(tmp_path):
    box = make(tmp_path)
    drop(box, tmp_path / "a.die", "2d6")
    out(box, tmp_path / "a.die")
    good = rows(box)
    n = good[-2]["n"]

    def fails(change: dict, why: str, at: int = -1) -> None:
        rs = [dict(r) for r in good]
        rs[at].update(change)
        held, inside, said = tower.check(rs)
        assert held == 0 and inside == [] and said == f"row {rs[-1]['n']}: {why}"

    fails({"total": good[-1]["total"] + 1}, "its faces aren't what the dropped secret gives")  # fmt: skip
    other = [[f % 6 + 1 for f in g] for g in good[-1]["faces"]]  # every face moved, so never the real ones  # fmt: skip
    fails({"faces": other}, "its faces aren't what the dropped secret gives")
    fails({"kept": [[0]]}, "its faces aren't what the dropped secret gives")
    fails({"dice": "2d8"}, "its faces aren't what the dropped secret gives")
    fails({"secret": "ab" * 32}, f"its secret isn't the one dropped in at row {n}")
    fails(
        {"commit": "0" * 64}, f"its secret isn't the one dropped in at row {n}", at=-2
    )
    fails({"drop": good[-1]["n"]}, "it brings out no die dropped before it")
    fails({"drop": 0}, "it brings out no die dropped before it")
    fails({"drop": "x"}, "it brings out no die dropped before it")
    fails({"dice": "2d6kh9"}, "2d6kh9: keep 1 to 2", at=-2)
    twice = [dict(r) for r in good] + [{**good[-1], "n": good[-1]["n"] + 1}]
    assert tower.check(twice) == (1, [], f"row {good[-1]['n'] + 1}: the die dropped at row {n} is out twice")  # fmt: skip
    assert tower.check(good) == (1, [], None)


def test_a_record_that_doesnt_verify_is_refused(tmp_path):
    box = make(tmp_path)
    drop(box, tmp_path / "a.die")
    f = box / "record.jsonl"
    f.write_text(f.read_text().replace('"2d6"', '"2d8"', 1))
    for argv in (["check"], ["out", "--die", str(tmp_path / "a.die")], ["drop", "--dice", "1d6", "--to", str(tmp_path / "b.die")], ["page", "--to", str(tmp_path / "t.html")]):  # fmt: skip
        got = run("--box", str(box), *argv, *NOW)
        assert got.returncode == 2 and got.stderr.startswith("refused: the record doesn't verify: ")  # fmt: skip
    assert not (tmp_path / "t.html").exists() and not (tmp_path / "b.die").exists()


@pytest.mark.parametrize(
    "dice, to, why",
    [
        ("2x6", "a.die", "'2x6' isn't dice notation"),
        ("2d6", "there.die", "is already there; a die file is never written over"),
        ("2d6", "nowhere/a.die", "nowhere isn't a folder"),
        (
            "2d6",
            "box/a.die",
            "a die file goes outside the box, so the record never holds the secret",
        ),  # fmt: skip
    ],
)
def test_a_drop_it_cant_make_is_refused_and_nothing_written(tmp_path, dice, to, why):
    box = make(tmp_path)
    (tmp_path / "there.die").write_text("mine\n")
    before = rows(box)
    got = drop(box, tmp_path / to, dice)
    assert (
        got.returncode == 2 and why in got.stderr and got.stderr.startswith("refused: ")
    )
    assert rows(box) == before and (tmp_path / "there.die").read_text() == "mine\n"
    assert not (tmp_path / "a.die").exists() and not (box / "a.die").exists()


def test_a_die_file_that_isnt_this_boxs_or_isnt_one_is_refused(tmp_path):
    box, other = make(tmp_path / "one"), make(tmp_path / "two")
    drop(other, tmp_path / "theirs.die")
    drop(box, tmp_path / "mine.die")
    held = json.loads((tmp_path / "mine.die").read_text())
    cases = {
        "theirs.die": None,
        "garbled.die": "not json",
        "short.die": json.dumps({"drop": 1}),
        "far.die": json.dumps({**held, "drop": 999}),
        "row0.die": json.dumps({**held, "drop": 0}),
        "swapped.die": json.dumps({**held, "secret": "cd" * 32}),
        "neg.die": json.dumps({**held, "drop": -1}),
    }
    for name, text in cases.items():
        if text is not None:
            (tmp_path / name).write_text(text)
        got = out(box, tmp_path / name)
        why = "isn't a die file" if name in ("garbled.die", "short.die") else "isn't a die dropped in this box"  # fmt: skip
        assert got.returncode == 2 and got.stderr == f"refused: {tmp_path / name} {why}\n", (name, got.stderr)  # fmt: skip
    gone = out(box, tmp_path / "missing.die")
    assert gone.returncode == 2 and "isn't a die file" in gone.stderr
    assert [r["kind"] for r in rows(box)].count("tower-out") == 0


def test_the_page_draws_the_tower_the_tray_and_whether_they_hold(tmp_path):
    box = make(tmp_path)
    drop(box, tmp_path / "a.die", "2d6", "--for", "Mira <climbs>")
    drop(box, tmp_path / "b.die", "1d20", "--for", "the screen roll")
    out(box, tmp_path / "a.die")
    got = run("--box", str(box), "page", "--to", str(tmp_path / "tower.html"))
    assert got.returncode == 0 and got.stdout == f"the tower is drawn at {tmp_path / 'tower.html'}: 1 out, 1 inside\n"  # fmt: skip
    page = (tmp_path / "tower.html").read_text()
    inside, tray = page.split('<section class="tray">')
    d, o = rows(box)[-2], rows(box)[-1]
    assert f"the screen roll:</span> 1d20 <code>row {d['n']}, under {d['commit'][:12]}</code>" in inside  # fmt: skip
    assert f"Mira &lt;climbs&gt;:</span> {tower.play_dice5e.said(o)} <code>row {o['n']}, dropped at row {o['drop']}</code>" in tray  # fmt: skip
    assert (
        "Mira <climbs>" not in page and o["secret"] not in page
    )  # escaped; never a secret still inside
    assert (
        '<p class="ok">1 out of the tower, every one holds; 1 still inside.</p>' in page
    )
    assert page.startswith("<!doctype html>") and "prefers-color-scheme: dark" in page and "http" not in page  # fmt: skip


def test_an_empty_tower_and_one_that_doesnt_hold_are_drawn_as_such(tmp_path):
    box = make(tmp_path)
    empty = run("--box", str(box), "page", "--to", str(tmp_path / "empty.html"))
    assert empty.returncode == 0 and (tmp_path / "empty.html").read_text().count("<li>empty</li>") == 2  # fmt: skip
    drop(box, tmp_path / "a.die")
    out(box, tmp_path / "a.die")
    rs = rows(box)
    rs[-1]["total"] += 1
    page = tower.page(rs, *tower.check(rs))
    assert f'<p class="bad">row {rs[-1]["n"]}: its faces aren&#x27;t what the dropped secret gives</p>' in page  # fmt: skip
    again = run("--box", str(box), "page", "--to", str(tmp_path / "empty.html"))
    assert again.returncode == 2 and "is already there; a page is never written over" in again.stderr  # fmt: skip
    inbox = run("--box", str(box), "page", "--to", str(box / "t.html"))
    assert inbox.returncode == 2 and "a page goes outside the box" in inbox.stderr


@pytest.mark.parametrize(
    "argv",
    [[], ["drop"], ["--box", "{box}"], ["--box", "{box}", "roll"], ["--box", "{box}", "drop", "--dice", "2d6"],
     ["--box", "{box}", "drop", "--to", "x.die"], ["--box", "{box}", "out"], ["--box", "{box}", "page"],
     ["--box", "{box}", "check", "x"]],
)  # fmt: skip
def test_a_bad_command_line_prints_how_to_use_it(tmp_path, argv):
    box = make(tmp_path)
    got = run(*[a.format(box=box) for a in argv])
    assert got.returncode == 2 and got.stderr.strip() == tower.USAGE.strip()
    assert (
        "python adapters/stdlib/dice-tower/dice_tower.py --box DIR drop" in got.stderr
    )


def test_a_folder_that_isnt_a_box_is_refused(tmp_path):
    got = run("--box", str(tmp_path), "check")
    assert got.returncode == 2 and got.stderr == f"refused: {tmp_path} isn't a box: make one with kernel.py init\n"  # fmt: skip
