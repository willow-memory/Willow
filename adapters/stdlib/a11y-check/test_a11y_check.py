"""a11y-check: an empty image bracket and a missing alt are problems, an
HTML alt="" is the author's decoration, a heading may not skip a level, and
code fences are code, not document."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("a11y_check", HERE / "a11y_check.py")
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def check(*argv: str) -> subprocess.CompletedProcess:
    return run(str(HERE / "a11y_check.py"), *argv)


def folder(tmp_path: Path, files: dict) -> Path:
    root = tmp_path / "docs"
    for name, text in files.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return root


def test_markdown_images_an_empty_bracket_is_a_problem_a_described_one_is_not():
    lines = ["![](beach.jpg) and ![the beach at low tide](beach.jpg)",
             "![  ](dog.png)"]  # fmt: skip
    got = list(ac.md_problems(lines))
    assert [(n, w.split(":")[0]) for n, w in got] == [
        (1, "image without a description"),
        (2, "image without a description"),
    ]


def test_html_images_only_a_missing_alt_is_a_problem():
    text = ('<img src="a.png">\n<img src="b.png" alt="">\n'
            "<img src='c.png' alt='the cat'>\n<img\n  src=\"d.png\">\n")  # fmt: skip
    got = list(ac.html_problems(text))
    assert [n for n, w in got if "image" in w] == [1, 4], (
        'alt="" is the author saying decoration; across lines the tag is line 4'
    )


def test_a_heading_may_not_skip_a_level_but_may_start_anywhere():
    good = ["# one", "## two", "### three", "## back up", "### down again"]
    assert list(ac.md_problems(good)) == []
    assert list(ac.md_problems(["### notes start deep", "#### fine"])) == []
    got = list(ac.md_problems(["# one", "### three"]))
    assert got and got[0][0] == 2 and "h1 to h3" in got[0][1]
    text = "<h1>a</h1>\n<h2>b</h2>\n<h4>d</h4>\n"
    got = list(ac.html_problems(text))
    assert [(3, "heading jumps from h2 to h4")] == got


def test_fenced_code_is_not_document_and_setext_is_not_read():
    lines = ["```", "# not a heading", "![](not-an-image.png)", "```",
             "underlined", "======"]  # fmt: skip
    assert list(ac.md_problems(lines)) == []


def test_a_raw_img_in_markdown_counts_but_its_headings_do_not(tmp_path):
    root = folder(tmp_path, {"n.md": '## two\n<img src="x.png">\n<h4>not read</h4>\n'})
    got = check("--from", str(root))
    assert got.returncode == 42
    assert "n.md:2" in got.stdout and "image without a description" in got.stdout
    assert "h4" not in got.stdout, "HTML headings in Markdown are the page's business"


def test_problems_come_in_file_order_with_a_tally(tmp_path):
    root = folder(tmp_path, {
        "b.md": "# one\n### three\n",
        "a.html": '<img src="x.png">',
        "c.txt": "![](ignored.png) not a document\n",
    })  # fmt: skip
    got = check("--from", str(root))
    lines = got.stdout.splitlines()
    assert got.returncode == 42
    assert lines[0].startswith("a.html:1") and lines[1].startswith("b.md:2")
    assert lines[-1] == "2 problems in 2 of 2 documents"
    assert got.stdout == check("--from", str(root)).stdout


def test_clean_documents_are_0_and_none_at_all_is_42(tmp_path):
    root = folder(tmp_path, {"a.md": "# fine\n## also fine\n"})
    got = check("--from", str(root))
    assert (
        got.returncode == 0 and "No screen-reader problems in 1 document." in got.stdout
    )
    empty = folder(tmp_path / "e", {"notes.txt": "no documents here\n"})
    got = check("--from", str(empty))
    assert got.returncode == 42 and "No documents" in got.stdout


def test_hidden_files_are_never_read(tmp_path):
    root = folder(tmp_path, {".hidden/a.md": "# one\n### three\n",
                             ".b.md": "![](x.png)\n", "ok.md": "# fine\n"})  # fmt: skip
    got = check("--from", str(root))
    assert got.returncode == 0 and "in 1 document." in got.stdout


def test_a_box_names_its_pile(tmp_path):
    pile = folder(tmp_path, {"trip.md": "# day\n### dinner\n"})
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    got = check("--box", str(b))
    assert got.returncode == 42 and "trip.md:2" in got.stdout


def test_a_bad_command_line_and_bad_places_are_refused(tmp_path):
    got = check()
    assert got.returncode == 2 and "a11y_check.py" in got.stderr
    got = check("--box", str(tmp_path), "--from", str(tmp_path))
    assert got.returncode == 2, "one place, not two"
    got = check("--box", str(tmp_path))
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    got = check("--from", str(tmp_path / "gone"))
    assert got.returncode == 2 and "isn't a folder" in got.stderr
