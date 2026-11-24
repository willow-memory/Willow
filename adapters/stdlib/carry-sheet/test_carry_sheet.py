"""carry-sheet: a sheet line read as a name, a change and a thing; a sheet read
in order from every row, a thing used by its words, a wound lasting until
healed; written and read back on the record through the command line; and
each line or command line it can't read refused, nothing written."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "carry_sheet.py"
spec = importlib.util.spec_from_file_location("carry_sheet", SCRIPT)
cs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cs)
NOW = ["--now", "2026-11-23T20:00:00Z"]
NAMES = ["Tamsin", "Oro", "Old Vell"]


def run(*argv: str, script: Path = SCRIPT) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *argv], capture_output=True, text=True)  # fmt: skip


def make(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "notes.md").write_text("The fair opens at dusk.\n")
    box = tmp_path / "box"
    got = run("init", "--box", str(box), "--pile", str(pile), "--key", str(tmp_path / "key"), *NOW, script=KERNEL)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return box


def rows_of(box: Path) -> list[dict]:
    got, breaks = cs.kernel.read(box / "record.jsonl")
    assert breaks == []
    return got


def write(box: Path, line: str, names: str = ",".join(NAMES)) -> subprocess.CompletedProcess:  # fmt: skip
    return run("--box", str(box), "write", "--names", names, line, *NOW)


# ── reading a line ──────────────────────────────────────────────────────────


def test_a_sheet_line_is_a_name_a_change_and_a_thing():
    assert cs.read("Tamsin finds a rope.", NAMES) == {"char": "Tamsin", "change": "carry", "what": "a rope"}  # fmt: skip
    assert cs.read("Old Vell gives away the lantern", NAMES) == {"char": "Old Vell", "change": "spend", "what": "the lantern"}  # fmt: skip
    assert cs.read("Oro is hurt by a club", NAMES) == {"char": "Oro", "change": "hurt", "what": "by a club"}  # fmt: skip
    assert cs.read("Oro is healed", NAMES) == {
        "char": "Oro",
        "change": "heal",
        "what": "",
    }
    assert cs.read("oro uses up the rope!", NAMES) == {"char": "Oro", "change": "spend", "what": "the rope"}  # fmt: skip


def test_a_sheet_line_it_cant_read_is_none():
    for line in ("Mira finds a key", "Tamsin finds", "Tamsin finds the", "Tamsin sings", "Tamsinfinds a rope"):  # fmt: skip
        assert cs.read(line, NAMES) is None, line


def test_the_longest_name_is_read_first():
    assert cs.read("Old Vell finds a coin", ["Old", "Old Vell"])["char"] == "Old Vell"


# ── a sheet, from the rows ──────────────────────────────────────────────────


def rows(*changes) -> list[dict]:
    return [{"kind": cs.KIND, "char": c, "change": ch, "what": w} for c, ch, w in changes]  # fmt: skip


def test_a_sheet_is_every_row_in_order_a_thing_used_by_its_words():
    got = rows(("Oro", "carry", "a rope"), ("Oro", "carry", "a lantern"), ("Tamsin", "carry", "a rope"), ("oro", "spend", "the ropes"), ("Oro", "spend", "a kite"))  # fmt: skip
    assert cs.sheet(got, "Oro") == (["a lantern"], [])
    assert cs.sheet(got, "Tamsin") == (["a rope"], [])


def test_a_thing_is_the_same_but_for_an_article_or_a_plural():
    assert cs.same_thing("a rope", "the ropes") and cs.same_thing("Some boxes", "a box")
    assert not cs.same_thing("a rope", "a red rope")
    assert not cs.same_thing("a rope", "a kite")


def test_a_wound_lasts_until_healed_and_heals_all_at_once():
    got = rows(("Oro", "hurt", "by a club"), ("Oro", "hurt", ""), ("Oro", "heal", ""), ("Oro", "hurt", "stung"))  # fmt: skip
    assert cs.sheet(got, "Oro") == ([], ["stung"])
    assert cs.sheet(got[:2], "Oro") == ([], ["by a club", ""])


def test_rows_of_another_kind_are_not_a_sheet():
    got = [{"kind": "note", "char": "Oro", "change": "carry", "what": "a rope"}]
    assert cs.sheet(got, "Oro") == ([], [])


def test_what_is_said_aloud():
    assert cs.said("Oro", ["a lantern", "a kite"], ["by a club", ""]) == "Oro carries a lantern, a kite and is still hurt (by a club)"  # fmt: skip
    assert cs.said("Oro", [], [""]) == "Oro is still hurt"
    assert cs.said("Oro", [], []) == ""


# ── on the record ───────────────────────────────────────────────────────────


def test_a_line_written_is_a_row_and_the_sheet_as_it_stands(tmp_path):
    box = make(tmp_path)
    got = write(box, "Tamsin finds a rope")
    assert got.returncode == 0, got.stderr
    assert got.stdout.startswith("Tamsin carries a rope   (row ")
    r = rows_of(box)[-1]
    assert (r["kind"], r["who"], r["char"], r["change"], r["what"]) == (cs.KIND, cs.WHO, "Tamsin", "carry", "a rope")  # fmt: skip
    assert r["ts"] == NOW[1]  # the time given, not the clock's
    assert write(box, "Tamsin uses the ropes").stdout.startswith("Tamsin carries nothing and isn't hurt")  # fmt: skip


def test_the_sheet_carries_over_and_names_everyone_with_a_change(tmp_path):
    box = make(tmp_path)
    for line in ("Oro picks up a lantern", "Tamsin is hurt by a club", "Oro finds a kite", "Oro uses the kite"):  # fmt: skip
        assert write(box, line).returncode == 0
    got = run("--box", str(box), "sheet")
    assert got.returncode == 0
    assert got.stdout.splitlines() == ["Oro carries a lantern", "Tamsin is still hurt (by a club)"]  # fmt: skip
    one = run("--box", str(box), "sheet", "--name", "Old Vell")
    assert one.stdout.strip() == "Old Vell carries nothing and isn't hurt"


def test_an_empty_record_has_no_sheet(tmp_path):
    got = run("--box", str(make(tmp_path)), "sheet")
    assert (
        got.returncode == 0 and got.stdout.strip() == "no one's sheet is on the record"
    )


def test_a_line_it_cant_read_is_refused_and_nothing_written(tmp_path):
    box = make(tmp_path)
    before = len(rows_of(box))
    got = write(box, "Mira finds a key")
    assert got.returncode == 2 and "isn't a line this reads" in got.stderr
    assert len(rows_of(box)) == before


def test_a_folder_that_isnt_a_box_and_a_record_that_doesnt_verify_are_refused(tmp_path):  # fmt: skip
    got = run("--box", str(tmp_path), "sheet")
    assert got.returncode == 2 and "isn't a box" in got.stderr
    box = make(tmp_path)
    path = box / "record.jsonl"
    path.write_text(path.read_text().replace('"kind":"', '"kind":"x', 1))
    bad = run("--box", str(box), "sheet")
    assert bad.returncode == 2 and "doesn't verify" in bad.stderr


def test_a_command_line_it_hasnt_is_refused_with_its_usage(tmp_path):
    box = str(make(tmp_path))
    for argv in ([], ["sheet"], ["--box", box], ["--box", box, "write", "Oro finds a rope"],
                 ["--box", box, "write", "--names", "Oro"], ["--box", box, "sheet", "--names", "Oro"], ["--box", box, "sheet", "Oro"], ["--box", box, "sheet", "--name", ""],
                 ["--box", box, "write", "--names", "Oro", "--name", "Oro", "Oro finds a rope"],
                 ["--box", box, "roll"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2, argv
        assert "carry_sheet.py --box DIR sheet" in got.stderr, argv
