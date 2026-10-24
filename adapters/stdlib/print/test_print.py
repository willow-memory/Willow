"""print: the kernel's own bite, written as one page to print: the answer
or the passages with their file and line, the record's row at the foot,
escaped, scriptless, never overwriting."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("print_addon", HERE / "print.py")
pr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr)
NOW = ["--now", "2026-10-24T09:30:00Z"]


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "print.py"), *argv], capture_output=True, text=True
    )


def make_box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "dentist.txt").write_text(
        "The dentist is on Tuesday at 3pm. <script>x</script>\n"
    )
    b = tmp_path / "box"
    k(
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "key"),
        *NOW,
    )
    return b


def test_the_page_holds_the_passages_with_file_and_line_and_the_records_row(tmp_path):
    b = make_box(tmp_path)
    page_at = [
        "--box",
        str(b),
        "--to",
        str(tmp_path / "out" / "a.html"),
        *NOW,
        "when is the dentist",
    ]
    got = run(*page_at)
    assert got.returncode == 2 and "isn't a folder" in got.stderr  # no folder is made
    assert not (tmp_path / "out").exists()
    (tmp_path / "out").mkdir()
    got = run(*page_at)
    assert got.returncode == 0, got.stderr
    page = (tmp_path / "out" / "a.html").read_text()
    assert "What your files say" in page and "dentist.txt:1" in page
    assert "&lt;script&gt;" in page and "<script>" not in page
    assert "Asked 2026-10-24</p>" in page and "<h1>when is the dentist</h1>" in page
    row = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    assert (
        row["kind"] == "bite"
        and f"row {row['n']}, fingerprint {row['hash'][:16]}" in page
    )
    assert "default-src 'none'" in page and "Verdana" not in page


def test_large_is_large_high_contrast_type(tmp_path):
    b = make_box(tmp_path)
    assert (
        run(
            "--box",
            str(b),
            "--to",
            str(tmp_path / "l.html"),
            "--large",
            *NOW,
            "when is the dentist",
        ).returncode
        == 0
    )
    page = (tmp_path / "l.html").read_text()
    assert "font: 24pt" in page and "color: #000" in page


def test_an_approved_answer_comes_first(tmp_path):
    b = make_box(tmp_path)
    served = json.loads(k("bite", "--box", str(b), *NOW, "when is the dentist").stdout)[
        "served"
    ]
    (tmp_path / "s.jsonl").write_text(
        json.dumps(
            {
                "path": "d.md",
                "data": "Tuesday, 3pm",
                "cites": [served[0]["id"]],
                "claim": "note",
            }
        )
        + "\n"
    )
    k("propose", "--box", str(b), "--file", str(tmp_path / "s.jsonl"), *NOW)
    subj = json.loads((b / "record.jsonl").read_text().splitlines()[-1])["subject"]
    k("seal", "--box", str(b), subj, *NOW)
    assert (
        run(
            "--box",
            str(b),
            "--to",
            str(tmp_path / "s.html"),
            *NOW,
            "when is the dentist",
        ).returncode
        == 0
    )
    page = (tmp_path / "s.html").read_text()
    assert (
        "Your approved answer" in page
        and "Tuesday, 3pm" in page
        and "dentist.txt:1" not in page
    )


def test_nothing_found_says_so_and_exits_42(tmp_path):
    b = make_box(tmp_path)
    got = run(
        "--box",
        str(b),
        "--to",
        str(tmp_path / "n.html"),
        *NOW,
        "passport renewal office",
    )
    assert got.returncode == 42
    page = (tmp_path / "n.html").read_text()
    assert "Nothing in your folder holds this" in page and "words list" in page


def test_it_never_overwrites_and_a_refusal_writes_nothing(tmp_path):
    b = make_box(tmp_path)
    (tmp_path / "x.html").write_text("mine")
    got = run("--box", str(b), "--to", str(tmp_path / "x.html"), *NOW, "dentist")
    assert got.returncode == 2 and "isn't overwritten" in got.stderr
    assert (tmp_path / "x.html").read_text() == "mine"
    got = run("--box", str(b), "--to", str(tmp_path / "y.html"), *NOW, "!!!")
    assert got.returncode == 2 and not (tmp_path / "y.html").exists()


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    b = make_box(tmp_path)
    for argv in (
        [],
        ["--box", str(b), "q"],
        ["--to", "x.html", "q"],
        ["--box", str(b), "--to", str(tmp_path / "z.html")],
        ["--box", str(b), "--to", str(tmp_path / "z.html"), "a", "b"],
        ["--box", str(b), "--to", str(tmp_path / "z.html"), "--stray"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "print.py" in got.stderr
    got = run("--box", str(tmp_path), "--to", str(tmp_path / "z.html"), "q")
    assert got.returncode == 2 and "not a kernel box" in got.stderr
