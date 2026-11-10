"""mirrors.py: the mirror contract's check finds each kind of break, and a
mirror that keeps it has none."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("mirrors", HERE / "mirrors.py")
mm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mm)

SOURCE = "# Beds\n\nTomatoes in bed two.\nLeeks in three.\n\nGarlic, autumn.\n"
MIRROR = "Beds\n\nTomatoes in bed two.\nLeeks in three.\n\nGarlic, autumn.\n"
GOOD = {"1": "line 1", "3": "line 3", "6": "line 6"}


def world(
    tmp_path: Path, places=GOOD, mirror: str = MIRROR, source=None
) -> tuple[Path, Path]:
    folder, out = tmp_path / "folder", tmp_path / "mirror"
    (folder / "notes").mkdir(parents=True)
    (folder / "notes" / "g.md").write_text(SOURCE)
    (out / "notes").mkdir(parents=True)
    (out / "notes" / "g.md.txt").write_text(mirror)
    if places is not None:
        (out / ".places" / "notes").mkdir(parents=True)
        doc = {"source": source or "notes/g.md", "places": places}
        (out / ".places" / "notes" / "g.md.txt.json").write_text(json.dumps(doc))
    return folder, out


def test_a_mirror_that_keeps_it_has_no_break(tmp_path):
    assert mm.check(*world(tmp_path)) == []
    folder, out = world(tmp_path / "b", {**GOOD, "3": "lines 3-4", "6": "page 2"})
    assert mm.check(folder, out) == [], "a range and a named place are places"
    folder, out = world(tmp_path / "c", {**GOOD, "4": "line 4"})
    assert mm.check(folder, out) == [], "a line inside a passage may be placed too"


def test_passages_start_after_a_blank_line_or_on_the_first():
    assert mm.starts("a\n\n\nb\nc\n\nd") == [1, 4, 7]
    assert mm.starts("\n\na\n") == [3]
    assert mm.starts("") == []


def test_each_break_is_said(tmp_path):
    cases = [
        ({"1": "line 1", "3": "line 3"}, "line 6 starts a passage the map doesn't place"),
        ({**GOOD, "5": "line 5"}, "the map places '5', which is no line with words"),
        ({**GOOD, "9": "line 6"}, "the map places '9', which is no line with words"),
        ({**GOOD, "x": "line 6"}, "the map places 'x', which is no line with words"),
        ({**GOOD, "4": "line 9"}, "line 4: line 9 is outside the source's 6 lines"),
        ({**GOOD, "6": "line 9"}, "line 6: line 9 is outside the source's 6 lines"),
        ({**GOOD, "6": "lines 0-1"}, "line 6: lines 0-1 is outside the source's 6 lines"),
        ({**GOOD, "6": "lines 6-5"}, "line 6: lines 6-5 is outside the source's 6 lines"),
        ({**GOOD, "3": "line 4"}, "line 3: no word of 'Tomatoes in bed two.' is on the source's line 4"),
        ({**GOOD, "6": "Line 6"}, "line 6: 'Line 6' is not a place"),
        ({**GOOD, "6": 6}, "its places are not a map of line to place"),
    ]  # fmt: skip
    for i, (places, why) in enumerate(cases):
        got = mm.check(*world(tmp_path / str(i), places))
        assert got == [f"notes/g.md.txt: {why}"], (places, got)


def test_a_missing_or_foreign_map_and_a_map_left_alone_are_said(tmp_path):
    assert mm.check(*world(tmp_path / "a", None)) == [
        "notes/g.md.txt: no map in .places/ that reads"
    ]
    assert mm.check(*world(tmp_path / "b", source="other.md")) == [
        "notes/g.md.txt: its map doesn't name notes/g.md as its source"
    ]
    folder, out = world(tmp_path / "c")
    (folder / "notes" / "g.md").unlink()
    assert mm.check(folder, out) == [
        "notes/g.md.txt: its source notes/g.md isn't in the folder"
    ]
    folder, out = world(tmp_path / "d")
    (out / ".places" / "gone.md.txt.json").write_text("{}")
    assert mm.check(folder, out) == [
        ".places/gone.md.txt.json: a map with no mirror file"
    ]


def test_a_line_the_kernel_would_cut_is_said(tmp_path):
    long = "Tomatoes " + "x" * 500
    folder, out = world(tmp_path, {"1": "line 3"}, mirror=long + "\n")
    assert mm.check(folder, out) == [
        f"notes/g.md.txt: line 1 is {len(long)} characters, past the kernel's 500"
    ]


def test_a_card_says_it_among_its_outputs(tmp_path):
    for said, keeps in (("mirror", True), ("report, mirror", True), ("report", False)):
        (tmp_path / "README.md").write_text(
            f"<!-- willow-addon\noutput: {said}\n-->\n# x\n"
        )
        assert mm.keeps(tmp_path / "README.md") is keeps, said
    (tmp_path / "README.md").write_text("<!-- willow-addon\nrole: reads\n-->\n# x\n")
    assert mm.keeps(tmp_path / "README.md") is False


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "mirrors.py"), *map(str, argv)],
                          capture_output=True, text=True)  # fmt: skip


def test_its_command_line_says_each_break_and_exits_42(tmp_path):
    folder, out = world(tmp_path)
    got = run("check", "--from", folder, "--mirror", out)
    assert (
        got.returncode == 0 and got.stdout == "the mirror keeps the mirror contract\n"
    )
    folder, out = world(tmp_path / "b", {"1": "line 1"})
    got = run("check", "--from", folder, "--mirror", out)
    assert got.returncode == 42
    assert got.stdout.splitlines()[-1] == "2 break(s) of the mirror contract"
    for argv in (
        [],
        ["check"],
        ["check", "--from", folder],
        ["check", "--mirror", out, "--from", folder],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "mirrors.py" in got.stderr, argv
    got = run("check", "--from", tmp_path / "none", "--mirror", out)
    assert got.returncode == 2 and got.stderr.startswith("refused: ")


def test_a_citation_line_cites_inside_its_place_and_the_next_line_is_held():
    source = ["Lead in.", "\\begin{equation}", "E = mc^2", "\\end{equation}"]
    good = "p.tex line 2, label eq:e\nLead in.\nE = mc^2"
    assert mm.check_file(good, {"1": "lines 1-4"}, source, "p.tex") == []
    assert (
        mm.cited("p.tex line 2", "p.tex") == 2
        and mm.cited("q.tex line 2", "p.tex") is None
    )
    assert mm.check_file(good, {"1": "line 3"}, source, "p.tex") == [
        "line 1: it cites line 2, outside its place, line 3"
    ]
    wrong = "p.tex line 2\nUnrelated words."
    assert mm.check_file(wrong, {"1": "lines 1-4"}, source, "p.tex") == [
        "line 1: no word of 'Unrelated words.' is on the source's lines 1-4"
    ]
    assert mm.check_file("p.tex line 2", {"1": "lines 1-4"}, source, "p.tex") == []
