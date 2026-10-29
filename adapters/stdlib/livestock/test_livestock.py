"""livestock: a named or tagged animal's birth, treatments and end from lines
about farm stock; a herd-wide line is no animal's; the latest end counts."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "livestock.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]
spec = importlib.util.spec_from_file_location("livestock", SCRIPT)
lv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lv)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    for name, text in files.items():
        (pile / name).parent.mkdir(parents=True, exist_ok=True)
        (pile / name).write_text(text)
    b = tmp_path / "box"
    got = subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "init",
            "--box",
            str(b),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "k"),
            *NOW,
        ],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 0, got.stderr
    return b


def test_an_animal_is_a_tag_or_the_name_a_line_starts_with():
    a = lv.animal_of
    assert a("cow tag 412 calved") == "#412"
    assert a("ear tag #412 treated") == "#412"
    assert a("#412 drenched") == "#412"
    assert a("Tag 7: sold") == "#7"
    assert a("Daisy: treated for mastitis") == "Daisy"
    assert a("2026-05-01 Daisy - wormed") == "Daisy"
    assert a("Big Bess: died") == "Big Bess"
    assert a("Note: drenched the whole flock") == ""
    assert a("Farm: sold ten lambs") == ""
    assert a("the herd was drenched") == ""
    assert a("tag") == ""


def test_the_story_of_each_animal():
    pile = [{"path": "farm/log.md", "line": 1, "text": (
        "2024-03-02 Daisy: calved\n"
        "2026-02-02 Daisy: treated for mastitis\n"
        "2026-05-01 Daisy: wormed\n"
        "2026-09-15 Daisy: sold $1,200.00 at the sale\n"
        "2025-04-10 cow tag 412 born\n"
        "2026-01-20 tag 388 died\n"
        "2026-03-01 drenched the whole herd\n"
        "2026-03-02 Bella: calved\n2026-04-02 Bella: calved\n"
        "2026-06-02 Bella: sold\n2026-07-02 Bella: died\n"
        )},
        {"path": "notes.md", "line": 1, "text": "2026-02-02 Rex: treated\n2026-06-03 Mum: vaccinated\n"}]  # fmt: skip
    got = lv.herd(pile)
    assert set(got) == {"Daisy", "#412", "#388", "Bella"}, (
        "Rex and Mum are not farm stock"
    )
    d = got["Daisy"]
    assert d["birth"] == "20240302" and d["treats"] == ["20260202", "20260501"]
    assert d["end"] == ("20260915", "sold", "$1,200.00")
    assert got["#412"] == {"birth": "20250410", "treats": [], "end": None}
    assert got["#388"]["end"] == ("20260120", "died", "")
    assert got["Bella"]["birth"] == "20260402", "the latest birth"
    assert got["Bella"]["end"] == ("20260702", "died", ""), "the latest end"


def test_the_listing_tags_first_and_the_tally(tmp_path):
    b = box(tmp_path, {"farm/log.md": (
        "2024-03-02 Daisy: calved\n2026-02-02 Daisy: treated\n2026-05-01 Daisy: wormed\n2026-09-15 Daisy: sold $1,200.00\n"
        "2025-04-10 cow tag 412 born\n2026-02-02 tag 412 vaccinated\n"
        "2026-01-20 tag 388 died\n")})  # fmt: skip
    got = run("--box", str(b))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "#388   born not written  treated 0 times  died 2026-01-20",
        "#412   born 2025-04-10  treated 1 time, last 2026-02-02  alive",
        "Daisy  born 2024-03-02  treated 2 times, last 2026-05-01  sold 2026-09-15 ($1,200.00)",
        "3 animals: 1 alive, 1 sold, 1 died",
    ]
    assert run("--box", str(b)).stdout == got.stdout


def test_tags_sort_as_numbers_and_one_animal_is_singular(tmp_path):
    b = box(
        tmp_path, {"farm/log.md": "2026-01-01 tag 9 born\n2026-01-01 tag 100 born\n"}
    )
    out = run("--box", str(b)).stdout.splitlines()
    assert [row.split()[0] for row in out[:2]] == ["#9", "#100"]
    (tmp_path / "x").mkdir()
    one = box(tmp_path / "x", {"farm/log.md": "2026-01-01 tag 9 culled\n"})
    assert run("--box", str(one)).stdout.splitlines()[-1] == "1 animal: 1 culled"


def test_nothing_is_42_and_a_bad_command_line_is_refused(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run("--box", str(b))
    assert got.returncode == 42 and "named animal" in got.stdout
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    for argv in ([], ["--box"], ["--box", str(b), "stray"], ["--box", str(tmp_path)]):
        assert run(*argv).returncode == 2, argv
    assert "livestock.py" in run().stderr
    assert "not a kernel box" in run("--box", str(tmp_path)).stderr
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_the_sibling_it_reads_through_is_put_at_the_front():
    """In a process of its own, so another test's imports can't move the path."""
    code = (
        "import importlib.util, json, sys\n"
        f"s = importlib.util.spec_from_file_location('m', {str(HERE / 'livestock.py')!r})\n"
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
