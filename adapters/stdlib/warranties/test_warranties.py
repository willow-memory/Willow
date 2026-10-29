"""warranties: a thing, the day its cover ends (said, or bought plus a
length), and the receipt (said, or a receipt file naming the thing)."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("warranties", HERE / "warranties.py")
wr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wr)
NOW = ["--now", "2026-10-29T00:00:00Z"]
SCRIPT = str(HERE / "warranties.py")


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


def test_the_sibling_it_reads_through_is_put_at_the_front():
    here = sys.path.index(str(HERE.parent / "car"))
    root = str(HERE.parents[2])
    assert sys.path[here - 1] == root and sys.path[here + 1] == root


def test_the_thing_is_what_the_line_starts_with():
    n = wr.named
    assert n("Dishwasher, bought 2024-03-02, 2 year warranty") == "Dishwasher"
    assert n("Fridge: warranty until 2027-05-01") == "Fridge"
    assert n("2025-01-10 Kettle - 1 year guarantee") == "Kettle"
    assert (
        n("- Washing machine bought 2023-06-01, 18 months warranty")
        == "Washing machine"
    )
    assert n("Oven (Bosch) warranty ends 2028-03-01") == "Oven"
    assert n("Laptop warranty") == "Laptop"
    assert n("Mum's  TV   guarantee") == "Mum's TV"
    assert n("12345") == ""


def test_the_end_is_said_or_bought_plus_a_length():
    e = wr.end_of
    assert e("Dishwasher, bought 2024-03-02, 2 year warranty", "20240302") == (
        date(2024, 3, 2),
        date(2026, 3, 2),
    )
    assert e("Fridge: warranty until 2027-05-01", "20270501") == (
        None,
        date(2027, 5, 1),
    )
    assert e("Kettle bought 2025-01-10, 1 year guarantee", "20250110")[1] == date(
        2026, 1, 10
    )
    assert e("Washer bought 2023-06-01, 18 months warranty", "20230601")[1] == date(
        2024, 12, 1
    )
    assert e("Washer bought 2023-06-01, 18-month warranty", "20230601")[1] == date(
        2024, 12, 1
    )
    assert e("TV bought 2023-06-01, three years guarantee", "20230601")[1] == date(
        2026, 6, 1
    )
    assert e("TV bought 2023-06-01, 3 yr guarantee", "20230601")[1] == date(2026, 6, 1)
    assert e("TV bought 2024-01-31, 1 month warranty", "20240131")[1] == date(
        2024, 2, 29
    )
    assert e("TV warranty 2 years", "20240101") == (
        date(2024, 1, 1),
        date(2026, 1, 1),
    ), "the line's own day"
    assert e("TV, bought 2024-01-01, warranty ends 2030-02-03", "20300203") == (
        date(2024, 1, 1),
        date(2030, 2, 3),
    )
    assert e("TV warranty expires 2030-02-03, bought 2024-05-06", "20300203")[
        1
    ] == date(2030, 2, 3), "the first date after the word"
    assert e("TV warranty ends soon", "20240101") == (date(2024, 1, 1), None)
    assert e("TV bought 2024-01-01, warranty", "20240101") == (date(2024, 1, 1), None)


def test_a_receipt_is_said_or_a_file_names_it():
    pile = [
        {"path": "kitchen/log.md", "line": 1, "text": (
            "Dishwasher, bought 2024-03-02, 2 year warranty, receipt: red folder in the hall\n"
            "Kettle bought 2025-01-10, 1 year guarantee\n"
            "Fridge bought 2025-01-10, 5 year warranty\n"
            "Toaster bought 2025-01-10, 1 year warranty\n"
            "2025-01-11 sunny\n")},
        {"path": "receipts/kettle.pdf.txt", "line": 1, "text": "Kettle $30\n"},
        {"path": "docs/fridge-receipt.txt", "line": 1, "text": "x\n"},
    ]  # fmt: skip
    got = wr.warranties(pile)
    assert got["Dishwasher"][:3] == (
        date(2026, 3, 2),
        date(2024, 3, 2),
        "red folder in the hall",
    )
    assert got["Kettle"][2] == "receipts/kettle.pdf.txt"
    assert got["Fridge"][2] == "docs/fridge-receipt.txt"
    assert got["Toaster"][2] == "not found"


def test_the_latest_line_for_a_thing_counts():
    pile = [{"path": "log.md", "line": 1, "text": "2024-03-02 Dishwasher warranty 1 year\n2025-03-02 Dishwasher extended warranty 3 years\n"}]  # fmt: skip
    got = wr.warranties(pile)
    assert got["Dishwasher"][0] == date(2028, 3, 2)
    reverse = [{"path": "log.md", "line": 1, "text": "2025-03-02 Dishwasher extended warranty 3 years\n2024-03-02 Dishwasher warranty 1 year\n"}]  # fmt: skip
    assert wr.warranties(reverse)["Dishwasher"][0] == date(2028, 3, 2)


def test_the_listing_soonest_end_first_and_the_ended(tmp_path):
    b = box(tmp_path, {
        "home/log.md": ("Dishwasher, bought 2024-03-02, 2 year warranty\n"
                        "Kettle bought 2025-01-10, 1 year guarantee\n"
                        "Fridge: warranty until 2026-10-29\n"
                        "Oven: warranty until 2026-10-30\n"
                        "Toaster, bought 2025-10-30, 1 year warranty, receipt: drawer\n"),
        "receipts/dishwasher.txt": "Dishwasher 499\n"})  # fmt: skip
    got = run(SCRIPT, "--box", str(b), *NOW)
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "Kettle      ended 2026-01-10 (292 days ago)  bought 2025-01-10  receipt: not found",
        "Dishwasher  ended 2026-03-02 (241 days ago)  bought 2024-03-02  receipt: receipts/dishwasher.txt",
        "Fridge      ends 2026-10-29 (today)  receipt: not found",
        "Oven        ends 2026-10-30 (in 1 day)  receipt: not found",
        "Toaster     ends 2026-10-30 (in 1 day)  bought 2025-10-30  receipt: drawer",
        "5 warranties",
    ]
    assert run(SCRIPT, "--box", str(b), *NOW).stdout == got.stdout


def test_one_warranty_and_one_day_ago(tmp_path):
    b = box(tmp_path, {"log.md": "Kettle: warranty until 2026-10-28\n"})
    assert run(SCRIPT, "--box", str(b), *NOW).stdout.splitlines() == [
        "Kettle  ended 2026-10-28 (1 day ago)  receipt: not found",
        "1 warranty",
    ]


def test_nothing_is_42_and_refusals(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(SCRIPT, "--box", str(b), *NOW)
    assert got.returncode == 42 and "a warranty with a day it ends" in got.stdout
    for argv in (
        [],
        ["--box", str(tmp_path)],
        ["--box", str(b), "stray"],
        ["--box", str(b), "--now", "soon"],
        ["--box", str(b), "--now", "2026-13-45"],
    ):
        assert run(SCRIPT, *argv).returncode == 2, argv
    assert "warranties.py" in run(SCRIPT).stderr
    assert "not a kernel box" in run(SCRIPT, "--box", str(tmp_path)).stderr
