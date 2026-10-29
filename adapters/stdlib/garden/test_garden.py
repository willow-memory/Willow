"""garden: a planting or a harvest on a day in a garden, the plant without its
amount, its place, a season by the year of the planting."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("garden", HERE / "garden.py")
gd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gd)
NOW = ["--now", "2026-10-23T00:00:00Z"]
SCRIPT = str(HERE / "garden.py")


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
        f"s = importlib.util.spec_from_file_location('m', {str(HERE / 'garden.py')!r})\n"
        "m = importlib.util.module_from_spec(s)\n"
        "s.loader.exec_module(m)\n"
        "print(json.dumps(sys.path))\n"
    )
    got = json.loads(
        subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True
        ).stdout
    )
    here = got.index(str(HERE.parent / "habits"))
    root = str(HERE.parents[2])
    assert got[here - 1] == root and got[here + 1] == root, (
        "the sibling is put at the front, so nothing else answers to its name"
    )


def test_the_plant_is_what_follows_the_verb_without_its_amount():
    w = gd.what
    assert w("tomatoes in bed 2") == "tomatoes"
    assert w("2kg tomatoes from bed 2") == "tomatoes"
    assert w("2 kg Tomatoes from bed 2") == "tomatoes"
    assert w("the first runner beans, lots") == "runner beans"
    assert w("some more rocket and lettuce") == "rocket"
    assert w("12 x leeks.") == "leeks"
    assert w("new potatoes (Charlotte)") == "potatoes"
    assert w("Sweet Peas at the fence") == "sweet peas"
    assert w("") == ""
    assert w("in bed 2") == ""


def test_the_place_follows_in_at_or_on():
    p = gd.place_of
    assert p("tomatoes in bed 2") == "bed 2"
    assert p("beans at the fence, again") == "the fence"
    assert p("peas on the south wall.") == "the south wall"
    assert p("beans in the greenhouse (cold)") == "the greenhouse"
    assert p("tomatoes") == ""
    assert p("tomatoes into bed 2") == "bed 2"
    assert p("tomatoes from bed 2") == ""


def test_a_garden_line_is_a_planting_or_a_harvest_and_a_season_is_a_year():
    pile = [
        {"path": "garden/log.md", "line": 1, "text": (
            "2026-04-12 planted tomatoes in bed 2\n"
            "2026-04-20 planted tomatoes in bed 3\n"
            "2026-07-20 harvested 2kg tomatoes\n"
            "2026-09-30 picked tomatoes\n"
            "2026-05-01 sowed beans at the fence\n"
            "2026-08-01 harvest runner beans\n"
            "2025-07-28 picked tomatoes from bed 1\n"
            "2025-04-20 transplanted tomatoes into bed 1\n"
        )},
        {"path": "mail/a.eml", "line": 1, "text": "2026-05-02 planted a seed of doubt\n2026-05-02 picked up the kids\n"},
        {"path": "hives/log.txt", "line": 1, "text": "2026-05-03 cut the grass\n"},
    ]  # fmt: skip
    got = gd.seasons(pile)
    assert set(got) == {"2026", "2025"}
    t = got["2026"]["tomatoes"]
    assert t["planted"] == ("20260412", "bed 2"), "the first planting that year"
    assert t["harvests"] == ["20260720", "20260930"]
    assert got["2026"]["beans"]["planted"] == ("20260501", "the fence")
    assert got["2026"]["runner beans"]["planted"] is None
    assert got["2025"]["tomatoes"]["planted"] == ("20250420", "bed 1")
    assert got["2025"]["tomatoes"]["harvests"] == ["20250728"]


def test_the_listing_newest_season_first(tmp_path):
    b = box(tmp_path, {"garden/log.md": (
        "2026-04-12 planted tomatoes in bed 2\n2026-07-20 harvested tomatoes\n"
        "2026-09-30 picked tomatoes\n2026-05-01 sowed beans at the fence\n"
        "2025-04-20 planted tomatoes in bed 1\n2025-07-28 picked tomatoes\n"
        "2025-08-30 harvest chard\n")})  # fmt: skip
    got = run(SCRIPT, "--box", str(b))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "2026",
        "  tomatoes  planted 2026-04-12 (bed 2)  harvested 2 times, 2026-07-20 to 2026-09-30",
        "  beans     planted 2026-05-01 (the fence)  not harvested yet",
        "2025",
        "  tomatoes  planted 2025-04-20 (bed 1)  harvested 1 time, 2025-07-28 to 2025-07-28",
        "  chard     (no planting written)  harvested 1 time, 2025-08-30 to 2025-08-30",
        "3 plantings in 2 seasons",
    ]
    assert run(SCRIPT, "--box", str(b)).stdout == got.stdout


def test_one_planting_one_season_is_singular(tmp_path):
    b = box(tmp_path, {"garden/log.md": "2026-04-12 planted peas\n"})
    assert run(SCRIPT, "--box", str(b)).stdout.splitlines() == [
        "2026",
        "  peas  planted 2026-04-12  not harvested yet",
        "1 planting in 1 season",
    ]


def test_nothing_is_42_and_refusals(tmp_path):
    b = box(tmp_path, {"notes.md": "Tomatoes want sun.\n"})
    got = run(SCRIPT, "--box", str(b))
    assert got.returncode == 42 and "planted or harvested in a garden" in got.stdout
    for argv in ([], ["--box", str(tmp_path)], ["--box", str(b), "stray"]):
        assert run(SCRIPT, *argv).returncode == 2, argv
    assert "garden.py" in run(SCRIPT).stderr
    assert "not a kernel box" in run(SCRIPT, "--box", str(tmp_path)).stderr
