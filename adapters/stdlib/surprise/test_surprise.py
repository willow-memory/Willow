"""surprise: one passage drawn by willow-bot's seeded stream, the same for the
same seed, and on the record as an id and a place, never words."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("surprise", HERE / "surprise.py")
sp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sp)
NOW = ["--now", "2026-10-23T09:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    for i in range(30):
        (pile / f"note-{i:02d}.md").write_text(
            f"Note {i}: the garden, the bees, the van and the long winter.\n"
        )
    (pile / "short.md").write_text("Too short.\n")
    b = tmp_path / "box"
    run(
        str(KERNEL),
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    )
    return b


def test_the_stream_is_willow_bots_draw_for_draw():
    """Draws taken from willow-bot's onescript/stream.py, pinned."""
    s = sp.Stream(bytes.fromhex("00ff") + b"willow surprise")
    assert [s.below(10) for _ in range(8)] == [2, 9, 9, 3, 3, 3, 8, 0]
    seed = "9d48982a1c2fc7b8c63697a8d04cbc3512af886a0bb945fba18942442ca6e8f9"
    s = sp.Stream(bytes.fromhex(seed) + b"willow surprise")
    assert [s.below(1000) for _ in range(4)] == [170, 444, 488, 575]


def test_the_same_seed_draws_the_same_passage_and_seeds_spread(tmp_path):
    b = box(tmp_path)
    one = run(str(HERE / "surprise.py"), "--box", str(b), "--seed", "abcd", *NOW).stdout
    two = run(str(HERE / "surprise.py"), "--box", str(b), "--seed", "abcd", *NOW).stdout
    assert one == two and "Too short" not in one
    picks = {run(str(HERE / "surprise.py"), "--box", str(b), "--seed", f"{i:04x}", *NOW).stdout
             for i in range(12)}  # fmt: skip
    assert len(picks) > 5


def test_the_day_is_the_seed_when_none_is_given(tmp_path):
    b = box(tmp_path)
    today = run(str(HERE / "surprise.py"), "--box", str(b), *NOW).stdout
    again = run(
        str(HERE / "surprise.py"), "--box", str(b), "--now", "2026-10-23T22:00:00Z"
    ).stdout
    assert today.split("seed")[0] == again.split("seed")[0]
    assert sp.day_seed("2026-10-23T09:00:00Z") in today


def test_the_draw_is_on_the_record_without_its_words(tmp_path):
    b = box(tmp_path)
    run(str(HERE / "surprise.py"), "--box", str(b), "--seed", "abcd", *NOW)
    row = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    assert (
        row["kind"] == "surprise"
        and row["seed"] == "abcd"
        and row["generator"] == sp.GENERATOR
    )
    assert "garden" not in json.dumps(row) and row["served"][0]["where"].startswith(
        "note-"
    )
    assert run(str(KERNEL), "verify", "--box", str(b)).returncode == 0


def test_a_folder_with_nothing_long_enough_says_so(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("Short.\n")
    b = tmp_path / "box"
    run(
        str(KERNEL),
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    )
    assert run(str(HERE / "surprise.py"), "--box", str(b), *NOW).returncode == 42


def test_a_passage_of_exactly_eight_words_can_be_drawn(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("One two three four five six seven eight.\n")
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key",
        str(tmp_path / "k"), *NOW)  # fmt: skip
    got = run(str(HERE / "surprise.py"), "--box", str(b), *NOW)
    assert got.returncode == 0 and "seven eight" in got.stdout
