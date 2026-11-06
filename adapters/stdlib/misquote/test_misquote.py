"""misquote: the passage nearest a quote, and the words it drops, adds or
changes; as written when it's there, nothing close when under half."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import misquote  # noqa: E402

KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "misquote.py"
POLICY = (
    "We don't show you personalized ads based on your content from Drive, Gmail,\n"
    "or Google Photos, unless you choose to make data available.\n\n"
    "The council met on Tuesday and approved the budget.\n\n"
    "The council met on Tuesday, and after a long debate about the library, approved it.\n"
)


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "policy.txt").write_text(POLICY)
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), "--now", "2026-10-24T00:00:00Z"],
                   check=True, capture_output=True)  # fmt: skip
    return b


def run(b: Path, quote: str, *more: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--box", str(b), quote, *more],
                          capture_output=True, text=True)  # fmt: skip


def test_where_column_caps_at_sixty():
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "misquote", Path(__file__).resolve().parent / "misquote.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.WHERE_CAP == 60


def test_a_dropped_word_is_named_as_the_file_spells_it(tmp_path):
    b = box(tmp_path)
    quote = ("We don't show you personalized ads based on your content "
             "from Drive, Gmail, or Photos, unless you choose")  # fmt: skip
    got = run(b, quote)
    assert got.returncode == 42
    assert got.stdout.splitlines() == [
        "misquote: populated, closest passage holds 19 of 19 words, in order",
        "## dropped",
        "  policy.txt:1  Google: your files have it here; the quote doesn't",
    ]  # don't is two; the file's capital
    assert json.loads(run(b, quote, "--json").stdout) == {
        "addon": "misquote", "state": "populated",
        "said": "closest passage holds 19 of 19 words, in order",
        "groups": [{"name": "dropped", "rows": [{"where": "policy.txt:1",
                    "what": "Google: your files have it here; the quote doesn't"}]}],
    }  # fmt: skip


def test_added_and_changed_words(tmp_path):
    got = run(
        box(tmp_path), "The council met on Monday and quietly approved the budget"
    )
    assert got.returncode == 42
    assert got.stdout.splitlines() == [
        "misquote: populated, closest passage holds 8 of 10 words, in order",
        "## added",
        "  policy.txt:4  quietly: the quote has it; your files don't",
        "## changed",
        "  policy.txt:4  Monday -> Tuesday: the quote's words, then your files'",
    ]


def test_the_shorter_stretch_wins_a_tie(tmp_path):
    got = run(box(tmp_path), "The council met on Tuesday approved")
    assert "policy.txt:4" in got.stdout  # 6 of 6 in a stretch of 7, not of 17


def test_as_written_when_the_words_are_there_in_order(tmp_path):
    b = box(tmp_path)
    got = run(b, "drive gmail or GOOGLE photos!")
    assert got.returncode == 0
    assert got.stdout == (
        "misquote: populated, the quote is in your files as written\n"
        "  policy.txt:1  as written\n"
    )
    assert json.loads(run(b, "drive gmail or GOOGLE photos!", "--json").stdout) == {
        "addon": "misquote", "state": "populated",
        "said": "the quote is in your files as written",
        "groups": [{"name": None, "rows": [{"where": "policy.txt:1", "what": "as written"}]}],
    }  # fmt: skip


def test_nothing_close_under_half(tmp_path):
    b = box(tmp_path)
    got = run(b, "Google scans every Gmail message to serve ads")
    assert got.returncode == 0  # found nothing is empty, never 42
    assert got.stdout == (
        "misquote: empty, nothing in your folder holds even half of it, in that order\n"
    )
    assert json.loads(run(b, "Google scans every Gmail message to serve ads", "--json").stdout) == {
        "addon": "misquote", "state": "empty",
        "said": "nothing in your folder holds even half of it, in that order",
        "groups": [],
    }  # fmt: skip
    # exactly half is close: 3 of 6 words in order
    assert "closest passage holds 3 of 6" in run(b, "council met on zz yy xx").stdout


def test_refusals(tmp_path):
    b = box(tmp_path)
    assert run(b, "...").returncode == 2
    assert run(tmp_path, "the council").returncode == 2
    got = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    assert got.returncode == 2 and "misquote.py" in got.stderr


def test_closest_reads_passages_directly():
    pile = [{"path": "a.txt", "line": 1, "text": "one two three four"}]
    c, kept, diffs = misquote.closest(pile, "one two five four")
    assert kept == 3 and diffs == [("changed", ["five"], ["three"])]
    assert misquote.closest(pile, "six seven eight") is None
    assert misquote.closest(pile, "one two")[2] == []
