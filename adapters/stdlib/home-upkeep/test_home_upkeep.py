"""home-upkeep: jobs to a house by kind, a car's oil filter not the house's,
cost and due dates read as the car add-on reads them."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("home_upkeep", HERE / "home_upkeep.py")
hu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hu)
NOW = ["--now", "2026-10-29T00:00:00Z"]
SCRIPT = str(HERE / "home_upkeep.py")


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
    """In a process of its own, so another test's imports can't move the path."""
    code = (
        "import importlib.util, json, sys\n"
        f"s = importlib.util.spec_from_file_location('m', {str(HERE / 'home_upkeep.py')!r})\n"
        "m = importlib.util.module_from_spec(s)\n"
        "s.loader.exec_module(m)\n"
        "print(json.dumps(sys.path))\n"
    )
    got = json.loads(
        subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True
        ).stdout
    )
    here = got.index(str(HERE.parent / "car"))
    root = str(HERE.parents[2])
    assert got[here - 1] == root and got[here + 1] == root, (
        "the sibling is put at the front, so nothing else answers to its name"
    )


def test_kinds_and_the_house_context():
    pile = [
        {"path": "house/log.md", "line": 1, "text": (
            "2025-11-20 boiler service £240, every 12 months\n"
            "2025-04-12 gutters cleared £90\n"
            "2026-05-01 smoke alarm batteries\n"
            "2026-06-01 chimney swept\n"
            "2026-06-02 roof tiles fixed\n"
            "2026-06-03 drain unblocked\n"
            "2026-06-04 pest control for the loft\n"
            "2026-06-05 changed the filters\n"
        )},
        {"path": "van/history.txt", "line": 1, "text": "2026-06-06 Oil + filter\n"},
    ]  # fmt: skip
    kinds = lambda pl: {k[1] for k in hu.car.register(pl, hu.HOME, None, hu.CONTEXT)}  # noqa: E731
    assert kinds(pile) == {
        "boiler",
        "gutters",
        "smoke alarm",
        "chimney",
        "roof",
        "drains",
        "pest",
        "filters",
    }
    assert kinds(pile[1:]) == set(), "a van's filter is not the house's"
    assert kinds(
        [
            {
                "path": "x.md",
                "line": 1,
                "text": "2026-06-06 changed the filters at home\n",
            }
        ]
    ) == {"filters"}


def test_the_listing_soonest_due_first(tmp_path):
    b = box(tmp_path, {"house/log.md": (
        "2025-11-20 boiler service £240, every 12 months\n"
        "2024-11-20 boiler service £230\n"
        "2025-04-12 gutters cleared £90\n"
        "2026-05-01 smoke alarm tested, every 6 months\n")})  # fmt: skip
    got = run(SCRIPT, "--box", str(b), *NOW)
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "smoke alarm  last 2026-05-01  1 time    -           due 2026-11-01 (in 3 days)",
        "boiler       last 2025-11-20  2 times   £470.00     due 2026-11-20 (in 22 days)",
        "gutters      last 2025-04-12  1 time    £90.00      no due date written",
        "3 kinds of job, 4 entries",
    ]
    assert run(SCRIPT, "--box", str(b), *NOW).stdout == got.stdout


def test_nothing_is_42_and_refusals(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(SCRIPT, "--box", str(b), *NOW)
    assert got.returncode == 42 and "job done to the house" in got.stdout
    for argv in (
        [],
        ["--box", str(tmp_path)],
        ["--box", str(b), "stray"],
        ["--box", str(b), "--now", "soon"],
    ):
        assert run(SCRIPT, *argv).returncode == 2, argv
    assert "home_upkeep.py" in run(SCRIPT).stderr
    assert "not a kernel box" in run(SCRIPT, "--box", str(tmp_path)).stderr
