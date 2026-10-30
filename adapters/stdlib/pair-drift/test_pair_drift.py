"""pair-drift: a summary's figures looked for in its full text; ranges as
one figure, scale words kept, years and small counts left out."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("pair_drift", HERE / "pair_drift.py")
pd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pd)
NOW = ["--now", "2026-10-29T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(parents=True)
    for name, text in files.items():
        p = pile / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    return b


def ask(b: Path, *extra: str) -> subprocess.CompletedProcess:
    return run(str(HERE / "pair_drift.py"), "--box", str(b), *extra)


def test_a_figure_only_the_summary_says_is_drift(tmp_path):
    b = box(tmp_path, {
        "paper/DRAFT.md": "Google moves its guide toward $180 to $190 billion.\n",
        "paper/README.md": "Google guides $195-205B for 2026.\n",
    })  # fmt: skip
    got = ask(b)
    lines = got.stdout.splitlines()
    assert got.returncode == 0
    assert lines[0] == "paper  summary 1 figures, full 1, 1 only in the summary"
    assert lines[1].startswith("  README.md:1  $195-205B")
    assert lines[-1] == "1 pair read, 1 with drift"


def test_the_same_range_written_two_ways_agrees(tmp_path):
    b = box(tmp_path, {
        "p/DRAFT.md": "A guide of $180 to $190 billion, and 39% growth.\n",
        "p/README.md": "The guide: $180-190B. Growth: 39 percent.\n",
    })  # fmt: skip
    got = ask(b)
    assert got.returncode == 42
    assert "0 only in the summary" in got.stdout


def test_a_billion_is_never_a_dollar(tmp_path):
    assert pd.figures("$5 billion and $5 million") == ["$5B", "$5M"]
    b = box(
        tmp_path,
        {
            "p/DRAFT.md": "a loan of $5 million\n",
            "p/README.md": "a loan of $5 billion\n",
        },
    )
    assert ask(b).returncode == 0


def test_years_months_and_small_counts_are_not_figures():
    assert pd.figures("chapter 12 of the 2025 report, as of 2026-03") == []
    assert pd.figures("from 1990 to 2010, 40 to 60 people") == []
    assert pd.figures("117 firms and 10,000 A100s") == ["117", "10000"]
    assert pd.figures("121 MW and 1.5 GW") == ["121MW", "1.5GW"]


def test_named_pair_files(tmp_path):
    b = box(tmp_path, {"t/full.md": "it cost $10\n", "t/short.md": "it cost $12\n"})
    assert ask(b).returncode == 42
    got = ask(b, "--full", "full.md", "--summary", "short.md")
    assert got.returncode == 0 and "$12" in got.stdout


def test_a_summary_without_its_full_text_is_no_pair(tmp_path):
    got = ask(box(tmp_path, {"t/README.md": "it cost $12\n"}))
    assert got.returncode == 42
    assert "No folder holds both DRAFT.md and README.md." in got.stdout


def test_refusals(tmp_path):
    assert ask(tmp_path / "nobox").returncode == 2
    b = box(tmp_path, {"t/README.md": "x\n"})
    assert ask(b, "--full", "README.md").returncode == 2
    assert ask(b, "--full", "").returncode == 2
    assert ask(b, "stray").returncode == 2
    assert run(str(HERE / "pair_drift.py")).returncode == 2


def test_a_bare_range_reaching_three_digits_is_a_figure():
    assert pd.figures("40 to 99 people") == []
    assert pd.figures("40 to 100 people") == ["40-100"]
    assert pd.figures("99 to 40 people") == []


def test_a_long_summary_line_is_cut_to_a_hundred_characters(tmp_path):
    line = "It cost $12 " + "x" * 200
    b = box(tmp_path, {"t/DRAFT.md": "it cost $10\n", "t/README.md": line + "\n"})
    row = ask(b).stdout.splitlines()[1]
    assert row.endswith(line[:100]) and not row.endswith(line[:101])
