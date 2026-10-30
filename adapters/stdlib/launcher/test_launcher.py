"""launcher: the passages a question holds as Alfred Script Filter JSON or as
tab-separated lines, with file and line; nothing written, no key read; a bad
command line refused."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "launcher.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]
spec = importlib.util.spec_from_file_location("launcher", SCRIPT)
lc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lc)
GARDEN = "Notes\n\nTomatoes want six hours of sun.\nWater them daily.\n\nThe bins go out on Thursday night.\n"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def box(tmp_path: Path, words: str | None = None) -> tuple[Path, Path]:
    pile = tmp_path / "pile"
    (pile / "notes").mkdir(parents=True)
    (pile / "notes" / "garden.md").write_text(GARDEN)
    b = tmp_path / "box"
    argv = [
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    ]
    if words is not None:
        (tmp_path / "w.txt").write_text(words)
        (tmp_path / "w.txt").chmod(0o600)
        argv += ["--words", str(tmp_path / "w.txt")]
    got = subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )
    assert got.returncode == 0, got.stderr
    return b, pile


def test_a_question_gives_alfred_items_with_title_file_line_path_and_the_passage_to_copy(
    tmp_path,
):
    b, pile = box(tmp_path)
    got = run("--box", str(b), "how much sun do tomatoes want")
    assert got.returncode == 0, got.stderr
    items = json.loads(got.stdout)["items"]
    top = items[0]
    full = (pile / "notes" / "garden.md").resolve()
    assert top["title"] == "Tomatoes want six hours of sun."
    assert (
        top["subtitle"] == "notes/garden.md:3"
        and top["arg"] == str(full)
        and top["quicklookurl"] == full.as_uri()
    )
    assert top["text"] == {
        "copy": "Tomatoes want six hours of sun. Water them daily.",
        "largetype": "Tomatoes want six hours of sun. Water them daily.",
    }
    assert top["variables"] == {"line": "3", "path": "notes/garden.md"} and top["uid"]
    assert "valid" not in top


def test_nothing_held_and_no_question_are_items_that_do_nothing(tmp_path):
    b, _ = box(tmp_path)
    none = json.loads(run("--box", str(b), "zzz qqq unknown words").stdout)["items"]
    assert none == [
        {
            "title": "No passage holds that",
            "subtitle": "your files don't say, so nothing is guessed",
            "valid": False,
        }
    ]
    empty = json.loads(run("--box", str(b)).stdout)["items"]
    assert empty == [
        {
            "title": "Type a question",
            "subtitle": "the passages your folder holds for it appear here",
            "valid": False,
        }
    ]
    assert (
        json.loads(run("--box", str(b), "   ").stdout)["items"][0]["title"]
        == "Type a question"
    )


def test_lines_are_tab_separated_and_nothing_found_is_42(tmp_path):
    b, pile = box(tmp_path)
    got = run("--box", str(b), "--format", "lines", "how much sun do tomatoes want")
    full = (pile / "notes" / "garden.md").resolve()
    assert (
        got.returncode == 0
        and got.stdout.splitlines()[0]
        == f"Tomatoes want six hours of sun.\tnotes/garden.md:3\t{full}"
    )
    none = run("--box", str(b), "--format", "lines", "zzz qqq unknown words")
    assert none.returncode == 42 and none.stdout == ""
    assert run("--box", str(b), "--format", "lines").returncode == 42


def test_the_limit_caps_the_items_and_a_long_first_line_is_cut():
    assert (
        lc.short("a" * 100) == "a" * 100
        and lc.short("a" * 101) == "a" * 99 + "…"
        and lc.short("  a   b  ") == "a b"
    )
    p = {"id": "x", "path": "n.md", "line": 1, "text": "\n\n" + "w " * 80 + "\nsecond"}
    assert (
        lc.item(p, Path("/tmp"))["title"].endswith("…")
        and len(lc.item(p, Path("/tmp"))["title"]) == 100
    )


def test_a_limit_of_one_gives_one_item(tmp_path):
    b, _ = box(tmp_path)
    many = json.loads(run("--box", str(b), "tomatoes sun daily thursday bins").stdout)[
        "items"
    ]
    one = json.loads(
        run("--box", str(b), "--limit", "1", "tomatoes sun daily thursday bins").stdout
    )["items"]
    assert len(one) == 1 and one[0] == many[0]


def test_the_boxs_words_list_is_used_and_a_list_that_does_not_read_is_refused(tmp_path):
    b, _ = box(tmp_path, words="sunshine = sun\n")
    got = json.loads(run("--box", str(b), "how much sunshine do tomatoes want").stdout)[
        "items"
    ]
    assert got[0]["title"] == "Tomatoes want six hours of sun."
    (tmp_path / "w.txt").write_text("not a list line\n")
    bad = run("--box", str(b), "sunshine")
    assert (
        bad.returncode == 2 and bad.stderr.startswith("refused:") and bad.stdout == ""
    )


def test_it_writes_nothing_not_even_a_record_row(tmp_path):
    b, _ = box(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    run("--box", str(b), "tomatoes")
    run("--box", str(b), "--format", "lines", "tomatoes")
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_a_bad_command_line_is_refused(tmp_path):
    b, _ = box(tmp_path)
    for argv in (
        [], ["--box"], ["--box", str(b), "one", "two"], ["--box", str(b), "--stray"], ["--box", str(b), "--format", "xml", "q"],
        ["--box", str(b), "--limit", "0", "q"], ["--box", str(b), "--limit", "51", "q"], ["--box", str(b), "--limit", "x", "q"], ["--box", str(tmp_path), "q"],
    ):  # fmt: skip
        assert run(*argv).returncode == 2, argv
    assert (
        "launcher.py" in run().stderr
        and "not a kernel box" in run("--box", str(tmp_path), "q").stderr
    )
    assert (
        run("--box", str(b), "--limit", "50", "q").returncode == 0
        and run("--box", str(b), "--limit", "1", "q").returncode == 0
    )
