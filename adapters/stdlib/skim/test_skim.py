"""skim's tests: a list held to a screen, a width and a name to jump to,
each failing at its edge and holding just inside it."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("skim", HERE / "skim.py")
sk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sk)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "skim.py"), *argv],
                          capture_output=True, text=True)  # fmt: skip


def checks(text: str, screen: int = 5, width: int = 20) -> list[tuple[int, str]]:
    return [(n, c) for n, c, _ in sk.skim(text, screen, width)]


# ── screen ───────────────────────────────────────────────────────────────────
def test_a_run_longer_than_a_screen_is_said_once_where_it_starts():
    text = "# a\n" + "x\n" * 6 + "## b\n" + "y\n" * 5
    assert checks(text) == [(2, "screen")]
    said = sk.skim(text, 5, 20)[0][2]
    assert said == "lines 2 to 7, 6 with no heading (a screen is 5)"


def test_a_run_of_exactly_a_screen_holds_and_the_file_end_closes_one():
    assert checks("# a\n" + "x\n" * 5) == []
    assert checks("# a\n" + "x\n" * 6) == [(2, "screen")], "the last run counts too"
    assert checks("x\n" * 6) == [(1, "screen")], "a file with no heading at all"


def test_a_code_block_is_read_too_and_a_heading_in_one_is_no_heading():
    text = "# a\n```\n" + "# not a heading\n" * 4 + "```\n"
    assert checks(text) == [(2, "screen")]
    assert checks("# a\n~~~\nx\n~~~\n# b\n") == [], "~~~ fences too"


# ── width ────────────────────────────────────────────────────────────────────
def test_a_line_past_the_width_is_said_and_one_at_it_holds():
    assert checks("# a\n" + "x" * 20 + "\n") == []
    got = sk.skim("# a\n" + "x" * 21 + "\n", 5, 20)
    assert got == [(2, "width", "21 characters (the most is 20)")]


def test_a_table_row_is_read_by_its_columns_not_its_width():
    assert checks("# a\n| " + "x" * 30 + " |\n  | " + "y" * 30 + " |\n") == []


def test_a_long_line_in_a_tree_counts():
    assert checks("# a\n```\n├── " + "x" * 30 + "\n```\n") == [(3, "width")]


# ── jump ─────────────────────────────────────────────────────────────────────
def test_an_add_on_entry_needs_an_anchor_its_own_or_a_headings():
    text = ("# list\n- [**pdf**](x/) — PDFs.\n- **mail** — mail.\n"
            '<a id="mail"></a>\n## ocr\n- **ocr** — scans.\n')  # fmt: skip
    got = sk.skim(text, 60, 160)
    assert got == [(2, "jump", "`pdf` has no anchor to jump to")]


def test_a_bold_lead_in_sentence_is_emphasis_not_a_name():
    assert checks("# a\n- **Never the key.** No add-on reads it.\n", width=99) == []
    assert checks("# a\n- **Ask** first.\n", width=99) == [], "a capital: not a name"
    assert checks("# a\n* **pdf** x\n", width=99) == [(2, "jump")], "* lists too"


def test_a_tree_s_top_folder_needs_a_heading_and_a_deeper_one_doesnt():
    tree = "```\nwillow/\n├── ui/\n│   ├── deep/\n└── docs/\n```\n"
    assert checks("# Every file\n" + tree, 99, 99) == [(4, "jump"), (6, "jump")]
    headed = "# Every file\n## ui/\n" + tree + "## docs\n"
    assert checks(headed, 99, 99) == [], "a heading naming it, with its slash or not"
    assert checks("# a\n├── ui/\n", width=99) == [], "outside a code block: not a tree"


def test_a_heading_s_anchor_is_github_s():
    assert sk.slug("Reading more kinds of files") == "reading-more-kinds-of-files"
    assert sk.slug("`ready`: its *steps*") == "ready-its-steps"
    assert sk.slug("[pdf](adapters/deps/pdf/)") == "pdf"


# ── the command line ─────────────────────────────────────────────────────────
def test_check_says_each_place_and_a_count_and_exits_42(tmp_path):
    f = tmp_path / "list.md"
    f.write_text("# a\n- **pdf** x\n" + "y" * 30 + "\n", encoding="utf-8")
    got = run("check", str(f), "--width", "20")
    assert got.returncode == 42, got.stderr
    lines = got.stdout.splitlines()
    assert lines[0] == f"{f}:2: jump: `pdf` has no anchor to jump to"
    assert lines[1] == f"{f}:3: width: 30 characters (the most is 20)"
    assert lines[2] == f"{f}: 0 screen, 1 width, 1 jump"


def test_a_list_that_reads_well_is_0_and_says_so(tmp_path):
    f = tmp_path / "ok.md"
    f.write_text("# a\nshort.\n", encoding="utf-8")
    got = run("check", str(f))
    assert got.returncode == 0 and got.stdout == f"{f}: reads within the bounds\n"


def test_the_screen_and_width_are_options(tmp_path):
    f = tmp_path / "list.md"
    f.write_text("# a\n" + "x\n" * 61, encoding="utf-8")
    assert run("check", str(f)).returncode == 42
    assert run("check", str(f), "--screen", "61").returncode == 0


def test_with_no_file_it_reads_the_two_made_lists():
    got = run("check")
    assert got.returncode in (0, 42), got.stderr
    tails = [
        x for x in got.stdout.splitlines() if not x.split(":")[1].strip().isdigit()
    ]
    assert [t.split(":")[0] for t in tails] == ["FILES.md", "ADDONS.md"]


@pytest.mark.parametrize("argv", [[], ["read"], ["check", "--screen"], ["check", "--screen", "0"],
                                  ["check", "--width", "wide"], ["check", "--stray"]])  # fmt: skip
def test_a_bad_command_line_is_refused_and_names_the_script(argv):
    got = run(*argv)
    assert got.returncode == 2 and "skim.py" in got.stderr


def test_a_file_that_isnt_there_is_refused_before_anything_is_read(tmp_path):
    good = tmp_path / "ok.md"
    good.write_text("# a\n", encoding="utf-8")
    got = run("check", str(good), str(tmp_path / "gone.md"))
    assert got.returncode == 2 and "refused: no file" in got.stderr and got.stdout == ""
