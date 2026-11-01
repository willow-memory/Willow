"""rules: each section of a rules file proposed as the answer to "rule NAME",
answered word for word by the kernel only once the person seals it, and found
stale when the folder's words change."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "rules.py"
spec = importlib.util.spec_from_file_location("rules", SCRIPT)
rl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rl)
NOW = ["--now", "2026-11-01T09:00:00Z"]
HOUSE = """# House rules

## Hand limit

You may hold seven cards.
Discard down at the end of your turn.

## Trading ##

Trade only on your own turn.
"""


def run(*argv: str, script: Path = SCRIPT) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *argv],
                          capture_output=True, text=True)  # fmt: skip


def make(tmp_path: Path, text: str = HOUSE) -> Path:
    pile = tmp_path / "pile"
    (pile / "games").mkdir(parents=True)
    (pile / "games" / "house.md").write_text(text)
    box = tmp_path / "box"
    got = run("init", "--box", str(box), "--pile", str(pile),
              "--key", str(tmp_path / "key"), *NOW, script=KERNEL)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return box


def rows(box: Path) -> list[dict]:
    got, breaks = rl.kernel.read(box / "record.jsonl")
    assert breaks == []
    return got


def propose(box: Path) -> subprocess.CompletedProcess:
    return run("propose", "--box", str(box), *NOW, "games/house.md")


def seal_all(box: Path) -> None:
    for r in rows(box):
        if r.get("verdict") == "pass":
            got = run("seal", "--box", str(box), r["subject"], *NOW, script=KERNEL)
            assert got.returncode == 0, got.stderr  # the person's act, with their key


def test_sections_run_heading_to_heading_word_for_word():
    found, skipped = rl.sections(HOUSE)
    assert [(s["name"], s["start"], s["end"]) for s in found] == [
        ("Hand limit", 3, 7), ("Trading", 8, 10),
    ]  # fmt: skip
    assert found[0]["body"] == (
        "You may hold seven cards.\nDiscard down at the end of your turn."
    )
    assert skipped == {"House rules": "the section is empty"}
    _, skipped = rl.sections(
        "## Hand limit\nA\n## hand LIMIT!\nB\n## Long\n" + "x" * 20001
    )
    assert skipped == {"Hand limit": "another section has the same name",
                       "hand LIMIT!": "another section has the same name",
                       "Long": "the section is over 20000 characters"}  # fmt: skip
    assert rl.sections("no headings at all\n") == ([], {})
    assert rl.in_folder(Path("/nowhere"), "rules/x.md") is None
    assert rl.in_folder(Path("/nowhere"), "rules/../../etc/x.md/a.md") is None
    assert rl.slug("Hand limit!", 3) == "hand-limit" and rl.slug("!!", 3) == "3"


def test_each_section_waits_on_the_seal_and_cites_its_own_passages(tmp_path):
    box = make(tmp_path)
    got = propose(box)
    assert got.returncode == 42, got.stderr
    assert "skipped  House rules: the section is empty" in got.stdout
    assert got.stdout.count("waiting  ") == 2
    props = rl.proposals(box, rows(box))
    assert [(p["path"], p["sealed"]) for p in props] == [
        ("rules/games/house.md/hand-limit.md", False),
        ("rules/games/house.md/trading.md", False),
    ]
    f = box / "proposals" / f"{props[0]['subject'][9:]}.json"
    cited = json.loads(f.read_text())["cites"]
    assert cited, "the section's own passages are its sources"
    got = run("ask", "--box", str(box), *NOW, "hand", "limit")
    assert got.returncode == 42 and "no rule named hand limit is sealed" in got.stdout
    assert run("list", "--box", str(box)).returncode == 42
    pile = Path(rl.kernel.config(box)["pile"])
    (pile / "games" / "house.md").write_text(HOUSE.replace("Trade only", "Trade"))
    assert "outdated the rule Trading" in run("list", "--box", str(box)).stdout
    (pile / "games" / "house.md").write_text(HOUSE)
    again = propose(box)
    assert again.returncode == 42 and again.stdout.count("waiting  ") == 2
    assert len(rl.proposals(box, rows(box))) == 2, "proposed once, not again"
    assert not any(r["kind"] == "seal" for r in rows(box)), "code never seals"


def test_once_sealed_the_kernel_answers_with_the_exact_section(tmp_path):
    box = make(tmp_path)
    propose(box)
    seal_all(box)
    got = run("ask", "--box", str(box), *NOW, "Hand", "Limit?")
    assert got.returncode == 0
    assert (
        got.stdout
        == "You may hold seven cards.\nDiscard down at the end of your turn.\n"
    )
    got = run("bite", "--box", str(box), *NOW, "rule: trading", script=KERNEL)
    assert json.loads(got.stdout)["answer"] == "Trade only on your own turn."
    got = propose(box)
    assert got.returncode == 0 and got.stdout.count("sealed   ") == 2
    got = run("list", "--box", str(box))
    assert got.returncode == 0 and got.stdout.splitlines() == [
        "sealed   the rule Hand limit, as games/house.md writes it",
        "sealed   the rule Trading, as games/house.md writes it",
    ]


def test_a_changed_section_is_said_and_not_proposed_over_the_seal(tmp_path):
    box = make(tmp_path)
    propose(box)
    seal_all(box)
    f = Path(rl.kernel.config(box)["pile"]) / "games" / "house.md"
    f.write_text(HOUSE.replace("seven", "eight"))
    got = run("list", "--box", str(box))
    assert got.returncode == 42 and got.stdout.splitlines() == [
        "changed  the rule Hand limit, as games/house.md writes it",
        "sealed   the rule Trading, as games/house.md writes it",
    ]
    f.write_text(HOUSE.replace("## Trading ##", "## Swaps"))
    assert "changed  the rule Trading" in run("list", "--box", str(box)).stdout
    f.unlink()
    assert run("list", "--box", str(box)).stdout.count("changed") == 2
    f.write_text(HOUSE.replace("seven", "eight"))
    got = propose(box)
    assert got.returncode == 0
    assert "differs  Hand limit: another text is sealed for it" in got.stdout
    got = run("ask", "--box", str(box), *NOW, "hand limit")
    assert "seven" in got.stdout, "the kernel answers with what you sealed"


def test_a_file_outside_the_folder_or_with_no_sections_is_refused(tmp_path):
    box = make(tmp_path)
    (tmp_path / "outside.md").write_text("## A\nB\n")
    for rel in ("../outside.md", "games", "nope.md"):
        got = run("propose", "--box", str(box), rel)
        assert got.returncode == 2 and "is not a file in your folder" in got.stderr
    pile = Path(rl.kernel.config(box)["pile"])
    (pile / "plain.md").write_text("Just words.\n")
    got = run("propose", "--box", str(box), "plain.md")
    assert got.returncode == 42 and "no section of plain.md to propose" in got.stdout
    (pile / "bad.md").write_bytes(b"## A\n\xff\xfe\n")
    got = run("propose", "--box", str(box), "bad.md")
    assert got.returncode == 2 and "can't be read as text" in got.stderr
    assert run("list", "--box", str(box)).stdout.startswith("no rules proposed yet")
    run("bite", "--box", str(box), *NOW, "seven cards", script=KERNEL)
    other = {"path": "notes/cards.md", "data": "Seven.", "cites": [], "claim": "mine"}
    (tmp_path / "rows.jsonl").write_text(json.dumps(other) + "\n")
    got = run("propose", "--box", str(box), "--file", str(tmp_path / "rows.jsonl"),
              *NOW, script=KERNEL)  # fmt: skip
    assert any(r.get("verdict") == "pass" for r in rows(box)), got.stdout + got.stderr
    assert rl.proposals(box, rows(box)) == [], "another add-on's proposal isn't a rule"


def test_a_bad_command_line_or_box_is_refused(tmp_path):
    box = make(tmp_path)
    b = str(box)
    for argv in ([], ["fly"], ["propose", "--box", b], ["propose", "--box", b, "a", "b"],
                 ["ask", "--box", b], ["list", "--box", b, "x"],
                 ["list", "--box", b, *NOW], ["ask", "--box", "", "x"],
                 ["ask", "--box", b, "--now", "", "x"],
                 ["ask", "--box", b, "--top", "3", "x"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "rules.py" in got.stderr, argv
    assert len(rows(box)) == 1, "nothing written by a refusal"
    got = run("list", "--box", str(tmp_path / "nobox"))
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    propose(box)
    rec = box / "record.jsonl"
    rec.write_text(rec.read_text().replace('"bite"', '"bitt"', 1))
    got = run("list", "--box", b)
    assert got.returncode == 2 and "doesn't verify" in got.stderr
