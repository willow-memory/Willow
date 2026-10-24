"""pipe: one answer a line, JSON or grep's file:line: text, and the worst
exit code of the questions asked."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("pipe", HERE / "pipe.py")
pp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pp)
NOW = ["--now", "2026-10-23T00:00:00Z"]


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "n.md").write_text(
        "The bus leaves at seven from the square.\n\nWhen does the ferry sail?\n"
    )
    b = tmp_path / "box"
    assert subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                           "--key", str(tmp_path / "k"), *NOW], capture_output=True).returncode == 0  # fmt: skip
    return b


def ask(b: Path, text: str, *more: str) -> tuple[int, list[str]]:
    out = io.StringIO()
    code = pp.main(["--box", str(b), *NOW, *more], stdin=io.StringIO(text), stdout=out)
    return code, out.getvalue().splitlines()


def test_each_question_is_one_json_line_with_its_exit(tmp_path):
    code, lines = ask(box(tmp_path), "bus square\n\nzebra\n")
    rows = [json.loads(ln) for ln in lines]
    assert [r["question"] for r in rows] == [
        "bus square",
        "zebra",
    ]  # the blank line skipped
    assert rows[0]["exit"] == 0 and rows[0]["served"][0]["where"] == "n.md:1"
    assert rows[1]["exit"] == 42 and rows[1]["state"] == "empty"
    assert code == 42  # the worst of 0 and 42


def test_grep_prints_full_path_line_and_text(tmp_path):
    b = box(tmp_path)
    code, lines = ask(b, "bus square\n", "--grep")
    assert code == 0
    assert lines == [
        f"{tmp_path / 'pile' / 'n.md'}:1: The bus leaves at seven from the square."
    ]


def test_grep_marks_a_passage_that_only_asks_back(tmp_path):
    _, lines = ask(box(tmp_path), "when does the ferry sail\n", "--grep")
    assert lines[0].endswith(
        ":3: When does the ferry sail? (only asks your question back)"
    )


def test_every_question_is_on_the_record(tmp_path):
    b = box(tmp_path)
    ask(b, "bus\nferry\n")
    rows = [json.loads(ln) for ln in (b / "record.jsonl").read_text().splitlines()]
    assert [r["kind"] for r in rows].count("bite") == 2


def test_questions_given_as_arguments_are_asked_instead_of_reading(tmp_path):
    out = io.StringIO()
    code = pp.main(["--box", str(box(tmp_path)), *NOW, "--grep", "bus square"],
                   stdin=io.StringIO("zebra\n"), stdout=out)  # fmt: skip
    assert (
        code == 0
        and out.getvalue().count("\n") == 1
        and ":1: The bus" in out.getvalue()
    )


def test_the_worst_exit_wins():
    assert pp.worst([0, 42, 2]) == 2 and pp.worst([0, 42]) == 42 and pp.worst([0]) == 0
    assert pp.worst([]) == 0


def test_a_box_that_isnt_one_is_refused(tmp_path, capsys):
    assert pp.main(["--box", str(tmp_path)], stdin=io.StringIO("x\n")) == 2
    assert "not a kernel box" in capsys.readouterr().err


def test_a_bad_command_line_is_refused():
    for argv in ([], ["--box"], ["--box", "x", "--nope"], ["--box", "x", "--now"]):
        assert pp.main(argv, stdin=io.StringIO("")) == 2
