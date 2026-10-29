"""pile-poetry: pairs of words your files put side by side at least twice, a
poem walked along them with the seeded stream, nothing in it your files do not
have, the same folder and seed giving the same poem."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "pile_poetry.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]
spec = importlib.util.spec_from_file_location("pile_poetry", SCRIPT)
pp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pp)

LINES = (
    "tomatoes want six hours of sun\n" * 3
    + "bins go out on thursday night\n" * 3
    + "hours of sun and bins go out\n" * 2
    + "the garden wants water\n" * 2
    + "a once only pair\n"
)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def box(tmp_path: Path, text: str = LINES) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "notes.txt").write_text(text)
    b = tmp_path / "box"
    got = subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "init",
            "--box",
            str(b),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "k"),
            *NOW,
        ],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 0, got.stderr
    return b


def chunk(text: str, path: str = "a.txt") -> list[dict]:
    return [{"path": path, "line": 1, "text": text}]


def test_a_pair_is_two_words_side_by_side_on_a_line_seen_twice():
    got = pp.pairs(chunk("red door\nred door\nred door open\nopen red\n"))
    assert got == {("red", "door"): 3}
    assert pp.pairs(chunk("red door\n")) == {}, "once is not a pair"
    assert pp.pairs(chunk("red door\nred door\n")) == {("red", "door"): 2}, "twice is"
    across = pp.pairs(chunk("one red\ndoor two\none red\ndoor two\n"))
    assert ("red", "door") not in across, "a pair never crosses the end of a line"
    two_files = chunk("red door\n", "a.txt") + chunk("red door\n", "b.txt")
    assert pp.pairs(two_files) == {("red", "door"): 2}


def test_a_word_with_a_digit_is_left_out_and_its_neighbours_close_up():
    got = pp.pairs(chunk("red 2026 door\nred 2026 door\n"))
    assert ("red", "door") in got, (
        "a date or an id never gets in, and the words round it meet"
    )
    assert not any("2026" in w for pair in got for w in pair)


def test_a_line_you_wrote_is_not_a_machines():
    y = pp.yours
    assert y("tomatoes want sun")
    assert not y("DTSTART;VALUE=DATE:20261028")
    assert not y("BEGIN:VEVENT")
    assert not y("From: Ana <ana@example.org> sent")
    assert not y("UID=abc some words")
    assert not y("<p>words here</p>")
    assert not y("DD HARBOUR PENSIONS")
    assert y("  indented but yours")
    assert y("Mixed CASE words")
    assert not y("")


def test_followers_are_in_a_fixed_order_and_a_draw_follows_the_weights():
    f = pp.follows({("b", "z"): 1, ("a", "y"): 2, ("a", "x"): 3})
    assert f == {"a": [("x", 3), ("y", 2)], "b": [("z", 1)]}

    class Fixed:
        def __init__(self, k):
            self.k = k

        def below(self, n):
            assert n == 5
            return self.k

    opts = f["a"]
    assert [pp.draw(opts, Fixed(k)) for k in range(5)] == ["x", "x", "x", "y", "y"]


def test_a_poem_is_made_only_of_pairs_the_files_have_and_is_repeatable():
    counts = pp.pairs(chunk(LINES))
    verse = pp.poem(counts, "s", 8)
    assert verse == pp.poem(counts, "s", 8)
    assert verse != pp.poem(counts, "t", 8)
    for line in verse:
        ws = line.lower().split()
        assert 1 <= len(ws) <= pp.LONGEST
        assert line[0].isupper()
        assert all((a, b) in counts for a, b in zip(ws, ws[1:])), line
    assert len(pp.poem(counts, "s", 3)) == 3


def test_a_line_of_verse_runs_to_eight_words_and_no_further():
    words = [f"w{chr(97 + i)}" for i in range(20)]
    long_chain = {(a, b): 2 for a, b in zip(words, words[1:])}
    lengths = [len(line.split()) for line in pp.poem(long_chain, "chain", 40)]
    assert max(lengths) == 8 and all(1 <= n <= 8 for n in lengths)
    assert 8 in lengths and min(lengths) < 8, "a line stops early at the end of a chain"


def test_the_poem_by_hand(tmp_path):
    b = box(tmp_path)
    got = run("--box", str(b))
    assert got.returncode == 0, got.stderr
    stanzas = got.stdout.rstrip("\n").split("\n\n")
    assert [len(s.splitlines()) for s in stanzas] == [4, 4]
    assert run("--box", str(b)).stdout == got.stdout
    assert run("--box", str(b), "--seed", "other").stdout != got.stdout
    ten = run("--box", str(b), "--lines", "10").stdout.rstrip("\n").split("\n\n")
    assert [len(s.splitlines()) for s in ten] == [4, 4, 2]
    one = run("--box", str(b), "--lines", "1").stdout
    assert len(one.splitlines()) == 1 and "\n\n" not in one


def test_too_little_repeated_is_42_and_says_so(tmp_path):
    b = box(tmp_path, "red door\nred door\nblue sky\nblue sky\n")
    got = run("--box", str(b))
    assert (
        got.returncode == 42
        and got.stdout
        == "Too little to write from: 2 word pairs seen twice, 12 needed.\n"
    )


def test_a_bad_command_line_is_refused_and_nothing_is_written(tmp_path):
    b = box(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    for argv in (
        [],
        ["--box"],
        ["--box", str(b), "stray"],
        ["--box", str(b), "--lines", "0"],
        ["--box", str(b), "--lines", "41"],
        ["--box", str(b), "--lines", "x"],
        ["--box", str(b), "--seed", ""],
        ["--box", str(tmp_path)],
    ):
        assert run(*argv).returncode == 2, argv
    assert run("--box", str(b), "--lines", "40").returncode == 0
    assert "pile_poetry.py" in run().stderr
    assert "not a kernel box" in run("--box", str(tmp_path)).stderr
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_the_sibling_it_reads_through_is_put_at_the_front():
    """In a process of its own, so another test's imports can't move the path."""
    code = (
        "import importlib.util, json, sys\n"
        f"s = importlib.util.spec_from_file_location('m', {str(HERE / 'pile_poetry.py')!r})\n"
        "m = importlib.util.module_from_spec(s)\n"
        "s.loader.exec_module(m)\n"
        "print(json.dumps(sys.path))\n"
    )
    got = json.loads(
        subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True
        ).stdout
    )
    here = got.index(str(HERE.parent / "tarot"))
    root = str(HERE.parents[2])
    assert got[here - 1] == root and got[here + 1] == root, (
        "the sibling is put at the front, so nothing else answers to its name"
    )
