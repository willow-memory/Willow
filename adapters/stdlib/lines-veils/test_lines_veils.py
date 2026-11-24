"""lines-veils: a table's page of lines and veils read as written under its two
headings; a line touched by its meaning words, a plural or a possessive the
same word; the X-card and the pause on the record with no one named; and each
command line it hasn't refused with its usage."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "lines_veils.py"
spec = importlib.util.spec_from_file_location("lines_veils", SCRIPT)
lv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lv)
NOW = ["--now", "2026-11-23T20:00:00Z"]
PAGE_TEXT = "- before any heading\n# Our lines\n- spiders\n* a pet getting hurt\n-ghosts\n-x\n-\n- \n## Veils\n- kissing\n## Other\n- not a line\n"  # fmt: skip


def run(*argv: str, script: Path = SCRIPT) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *argv], capture_output=True, text=True)  # fmt: skip


def page(tmp_path: Path, text: str = PAGE_TEXT) -> Path:
    (tmp_path / "pile").mkdir(exist_ok=True)
    p = tmp_path / "pile" / lv.PAGE
    p.write_text(text)
    return p


def make(tmp_path: Path) -> Path:
    pile = tmp_path / "boxpile"
    pile.mkdir()
    (pile / "notes.md").write_text("The fair opens at dusk.\n")
    box = tmp_path / "box"
    got = run("init", "--box", str(box), "--pile", str(pile), "--key", str(tmp_path / "key"), *NOW, script=KERNEL)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return box


def rows(box: Path) -> list[dict]:
    got, breaks = lv.kernel.read(box / "record.jsonl")
    assert breaks == []
    return got


# ── the page ────────────────────────────────────────────────────────────────


def test_the_page_is_read_as_written_under_its_two_headings(tmp_path):
    p = page(tmp_path)
    want = (["spiders", "a pet getting hurt", "ghosts", "x"], ["kissing"])
    assert lv.read_page(p) == want  # a dash with no space too, an empty one not
    assert lv.read(tmp_path) == want  # a table folder: its pile's page


def test_no_page_is_no_lines(tmp_path):
    assert lv.read(tmp_path) == ([], [])
    assert lv.read_page(tmp_path / "none.md") == ([], [])


def test_a_line_needs_its_meaning_words_not_its_little_ones():
    assert lv.touches(["a pet getting hurt"], "The pet is hurt badly.") == "a pet getting hurt"  # fmt: skip
    assert lv.touches(["a pet getting hurt"], "A cat getting fed.") is None
    assert lv.touches(["a pet getting hurt"], "The pet sleeps.") is None


def test_a_line_of_only_little_words_needs_them_all():
    assert lv.touches(["being"], "Being alone in the dark.") == "being"
    assert lv.touches(["being"], "Alone in the dark.") is None


def test_a_plural_or_a_possessive_is_the_same_word():
    assert lv.touches(["spiders"], "A spider drops from the beam.") == "spiders"
    assert lv.touches(["hook"], "Tamsin climbs to the stall's hooks.") == "hook"
    assert lv.touches(["box"], "Two boxes.") == "box"
    assert lv.words("The stall's HOOKS") == ["the", "stall", "hooks"]


def test_the_first_entry_touched_is_the_one_named():
    assert lv.touches(["ghosts", "spiders"], "spiders and ghosts") == "ghosts"


# ── on the command line ─────────────────────────────────────────────────────


def test_show_prints_the_page_as_read(tmp_path):
    got = run("--page", str(page(tmp_path)), "show")
    assert got.returncode == 0
    assert got.stdout.splitlines() == ["line  spiders", "line  a pet getting hurt", "line  ghosts", "line  x", "veil  kissing"]  # fmt: skip
    none = run("--page", str(tmp_path / "none.md"), "show")
    assert none.returncode == 0 and "no lines or veils" in none.stdout
    only = run("--page", str(page(tmp_path, "## Lines\n- spiders\n")), "show")
    assert only.stdout.splitlines() == ["line  spiders"]  # lines and no veils is not "no lines or veils"  # fmt: skip


def test_touches_names_the_line_or_the_veil_and_says_what_to_do(tmp_path):
    p = str(page(tmp_path))
    line = run("--page", p, "touches", "A spider on the beam.")
    assert line.returncode == 0 and line.stdout.startswith("line  spiders: it doesn't happen")  # fmt: skip
    veil = run("--page", p, "touches", "They are kissing by the lanterns.")
    assert veil.returncode == 0 and veil.stdout.startswith("veil  kissing: it happens off-screen")  # fmt: skip
    neither = run("--page", p, "touches", "The fair opens.")
    assert neither.returncode == 42 and "no line and no veil" in neither.stdout


def test_the_x_card_is_kept_with_where_and_never_who(tmp_path):
    box = make(tmp_path)
    got = run("--box", str(box), "x", "--game", "3", "--at", "2", *NOW)
    assert got.returncode == 0, got.stderr
    assert "no reason asked and no one named" in got.stdout
    r = rows(box)[-1]
    assert (r["kind"], r["game"], r["at"], r["who"]) == (lv.X, 3, 2, lv.WHO)
    assert "part" not in r and "why" not in r
    part = run("--box", str(box), "x", "--game", "3", "--part", "call", *NOW)
    assert part.returncode == 0 and rows(box)[-1]["part"] == "call"


def test_the_pause_is_kept_with_no_one_named(tmp_path):
    box = make(tmp_path)
    got = run("--box", str(box), "pause", "--game", "1", "--at", "0", *NOW)
    assert got.returncode == 0 and got.stdout.startswith("paused")
    r = rows(box)[-1]
    assert (r["kind"], r["game"], r["at"]) == (lv.PAUSE, 1, 0)
    bare = run("--box", str(box), "pause", *NOW)
    assert bare.returncode == 0 and "game" not in rows(box)[-1]


def test_a_folder_that_isnt_a_box_and_a_place_that_isnt_a_number_are_refused(tmp_path):  # fmt: skip
    got = run("--box", str(tmp_path), "x")
    assert got.returncode == 2 and "isn't a box" in got.stderr
    box = make(tmp_path)
    before = len(rows(box))
    bad = run("--box", str(box), "x", "--game", "three")
    assert bad.returncode == 2 and "whole number" in bad.stderr
    assert len(rows(box)) == before


def test_a_record_that_doesnt_verify_is_refused(tmp_path):
    box = make(tmp_path)
    path = box / "record.jsonl"
    path.write_text(path.read_text().replace('"kind":"', '"kind":"x', 1))
    got = run("--box", str(box), "x")
    assert got.returncode == 2 and "doesn't verify" in got.stderr


def test_a_command_line_it_hasnt_is_refused_with_its_usage(tmp_path):
    box = str(make(tmp_path))
    p = str(page(tmp_path))
    for argv in ([], ["show"], ["--page", p], ["--page", p, "touches"], ["--page", p, "show", "x"],
                 ["x"], ["--box", box, "x", "y"], ["--box", box, "pause", "--part", "call"], ["--box", box, "roll"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2, argv
        assert "lines_veils.py --page PAGE show" in got.stderr, argv
