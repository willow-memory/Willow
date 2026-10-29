"""hook-compact: a PreCompact hook that prints the suggestions waiting for a
seal and the questions asked again and never answered; a quiet box prints
nothing; nothing is written; a record that doesn't verify is refused."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "hook_compact.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]
spec = importlib.util.spec_from_file_location("hook_compact", SCRIPT)
hc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hc)


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def init(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.txt").write_text("Tomatoes want six hours of sun.\n")
    (pile / "bins.txt").write_text("Bins go out on Thursday night.\n")
    b = tmp_path / "box"
    assert (
        k(
            "init",
            "--box",
            str(b),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "key"),
            *NOW,
        ).returncode
        == 0
    )
    return b


def propose(tmp_path: Path, b: Path, question: str, path: str, answer: str) -> str:
    served = json.loads(k("bite", "--box", str(b), *NOW, question).stdout)["served"]
    row = {
        "path": path,
        "data": answer,
        "cites": [served[0]["id"]],
        "claim": "the garden notes",
    }
    f = tmp_path / f"{path}.jsonl"
    f.write_text(json.dumps(row) + "\n")
    got = k("propose", "--box", str(b), "--file", str(f), *NOW)
    assert got.returncode == 42
    return got.stdout.split()[1]


def test_plurals():
    assert hc.plural(1, "question", "questions") == "1 question"
    assert hc.plural(0, "question", "questions") == "0 questions"
    assert hc.plural(2, "question", "questions") == "2 questions"


def test_a_quiet_box_prints_nothing_and_writes_nothing(tmp_path):
    b = init(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    got = run("--box", str(b))
    assert got.returncode == 0 and got.stdout == "" and got.stderr == ""
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_what_waits_for_a_seal_and_what_was_never_answered_is_printed(tmp_path):
    b = init(tmp_path)
    propose(tmp_path, b, "how much sun do tomatoes want", "sun.md", "Six hours of sun.")
    for _ in range(2):
        k("bite", "--box", str(b), *NOW, "zzz qqq unknown words")
    got = run("--box", str(b))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "Before this conversation is summarised, the person's willow box still holds open:",
        "- 1 suggestion waiting for their seal (only the person approves; an assistant never does):",
        "  - Six hours of sun. (why: the garden notes)",
        "- 1 question asked more than once and never answered (2 times).",
        "Keep these in the summary.",
    ]


def test_a_sealed_suggestion_no_longer_waits(tmp_path):
    b = init(tmp_path)
    subj = propose(
        tmp_path, b, "how much sun do tomatoes want", "sun.md", "Six hours of sun."
    )
    assert k("seal", "--box", str(b), subj, *NOW).returncode == 0
    assert run("--box", str(b)).stdout == ""


def test_more_than_five_suggestions_are_counted_not_listed():
    doc = {
        "waiting": {"items": [{"answer": f"a{i}", "why": "w"} for i in range(7)]},
        "again": {"items": [3, 2]},
    }
    out = hc.sentences(doc)
    assert out[0].startswith("- 7 suggestions waiting")
    assert len(out) == 1 + 5 + 1 + 1
    assert out[6] == "  - and 2 more"
    assert (
        out[-1]
        == "- 2 questions asked more than once and never answered (3 times, 2 times)."
    )
    assert hc.sentences({"waiting": {"items": []}, "again": {"items": []}}) == []


def test_a_bad_command_line_and_a_broken_record_are_refused(tmp_path):
    b = init(tmp_path)
    for argv in ([], ["--box"], ["--box", str(b), "stray"], ["--box", str(tmp_path)]):
        assert run(*argv).returncode == 2, argv
    assert "hook_compact.py" in run().stderr
    rec = b / "record.jsonl"
    rec.write_text(rec.read_text().replace("2026", "2025", 1))
    got = run("--box", str(b))
    assert got.returncode == 2 and got.stdout == "" and "refused:" in got.stderr


def test_the_sibling_it_reads_through_is_put_at_the_front():
    """In a process of its own, so another test's imports can't move the path."""
    code = (
        "import importlib.util, json, sys\n"
        f"s = importlib.util.spec_from_file_location('m', {str(HERE / 'hook_compact.py')!r})\n"
        "m = importlib.util.module_from_spec(s)\n"
        "s.loader.exec_module(m)\n"
        "print(json.dumps(sys.path))\n"
    )
    got = json.loads(
        subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True
        ).stdout
    )
    here = got.index(str(HERE.parent / "digest"))
    root = str(HERE.parents[2])
    assert got[here - 1] == root and got[here + 1] == root, (
        "the sibling is put at the front, so nothing else answers to its name"
    )
