"""debts: an owing word is enough, lent and borrowed need a sum, nothing is
netted, and each line is dated as the files say and cited."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("debts", HERE / "debts.py")
db = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db)
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(parents=True)
    for name, text in files.items():
        p = pile / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    return b


def test_an_owing_word_is_enough_lent_and_borrowed_need_a_sum():
    assert db.speaks_of_debt("Terry says Gerry owes him $10")
    assert db.speaks_of_debt("I still owe Dev for the mixer"), "a sum isn't needed"
    assert db.speaks_of_debt("first £100 paid back, thank you")
    assert db.speaks_of_debt("an IOU from the quiz night")
    assert db.speaks_of_debt("borrowed £20 from Mags till Friday")
    assert not db.speaks_of_debt("Mara borrowed the Foxfire set"), "lending's job"
    assert not db.speaks_of_debt("lent Teo my good drill"), "lending's job"
    assert not db.speaks_of_debt("the rent is $450"), "a sum alone owes nothing"
    assert not db.speaks_of_debt("flowers for the party")


def test_dated_as_the_files_say_oldest_first_with_the_sum_or_a_dash(tmp_path):
    b = box(tmp_path, {
        "chats/mags.txt": "17/04/2023, 12:27 pm - Mags: Terry says Gerry owes him $10 from the footy\n",
        "notes/2025-01-05.md": "I still owe Dev for the mixer\n",
        "diary.md": "2024-06-01 a fine day\nlent Ana £20 at the market\n",
    })  # fmt: skip
    got = run(str(HERE / "debts.py"), "--box", str(b))
    lines = got.stdout.splitlines()
    assert got.returncode == 0
    assert lines[0].startswith("2023-04-17  $10 ") and "mags.txt:1" in lines[0]
    assert lines[1].startswith("2024-06-01  £20 ")
    assert lines[1].endswith("(date from line 1)")
    assert lines[2].startswith("2025-01-05  -  ")
    assert lines[2].endswith("(date from file name)")
    assert lines[3] == "3 lines speak of debts: 2 with a sum, 0 undated"
    assert got.stdout == run(str(HERE / "debts.py"), "--box", str(b)).stdout


def test_a_paid_back_line_is_listed_beside_the_debt_never_netted(tmp_path):
    b = box(tmp_path, {"chats/teo.txt": (
        "28/02/2025, 17:30 - Teo: I owe you £170 for the parts\n"
        "28/03/2025, 09:00 - Teo: first £100 paid back, thank you again x\n")})  # fmt: skip
    got = run(str(HERE / "debts.py"), "--box", str(b))
    lines = got.stdout.splitlines()
    assert len(lines) == 3 and "£170" in lines[0] and "£100" in lines[1]
    assert lines[2] == "2 lines speak of debts: 2 with a sum, 0 undated"


def test_an_undated_debt_comes_last_marked_undated():
    rows = db.found([
        {"path": "a.md", "line": 1, "text": "owe the window man\n"},
        {"path": "b.md", "line": 1, "text": "2024-01-01 owes me $5\n"},
    ])  # fmt: skip
    assert [r["when"] for r in rows] == ["20240101", ""]
    assert db.show(rows)[1].startswith("undated")


def test_a_long_line_is_cut_at_110_characters():
    text = "2024-01-01 owes me $5 " + "x" * 300
    shown = db.show(db.found([{"path": "a.md", "line": 1, "text": text}]))
    assert "x" * 88 in shown[0] and text[:111] not in shown[0]


def test_none_spoken_of_is_42_and_refusals(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(str(HERE / "debts.py"), "--box", str(b))
    assert got.returncode == 42 and "speaks of money owed" in got.stdout
    b1 = box(tmp_path / "one", {"a.md": "2024-01-01 owes me $5\n"})
    got = run(str(HERE / "debts.py"), "--box", str(b1))
    assert (
        got.stdout.splitlines()[-1] == "1 line speaks of debts: 1 with a sum, 0 undated"
    )
    got = run(str(HERE / "debts.py"))
    assert got.returncode == 2 and "debts.py" in got.stderr
    got = run(str(HERE / "debts.py"), "--box", str(tmp_path))
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    got = run(str(HERE / "debts.py"), "--box", str(b), "--stray", "more")
    assert got.returncode == 2 and "debts.py" in got.stderr
