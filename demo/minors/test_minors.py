"""demo/minors: the made-up files are what make_life.py writes, and the
scene plays as its page tells it: who holds each box, what a held box
cannot find, whose key proves whose seal, and what a handover leaves."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_life  # noqa: E402
import scene  # noqa: E402

make_life.main(
    []
)  # life/ is not kept in git: the files are made, the same bytes each time


def test_the_made_up_files_are_as_written_and_his_words_are_in_no_box_marit_holds():
    assert make_life.check() == []
    assert sorted({name.split("/")[0] for name in make_life.FILES}) == sorted(
        scene.BOXES
    )
    wrong = dict(make_life.FILES)
    wrong["tobias/checkups.md"] += "\nAsk him about the counselling.\n"
    old, make_life.FILES = make_life.FILES, wrong
    try:
        assert any("says 'counselling'" in w for w in make_life.check())
    finally:
        make_life.FILES = old


def test_the_scene_plays_as_told(tmp_path, capsys):
    to = tmp_path / "scene"
    assert scene.main(["run", "--life", str(HERE / "life"), "--to", str(to)]) == 0
    said = json.loads((to / "scene.json").read_text())
    assert said["wrong"] == []
    boxes = said["boxes"]
    assert {n: b["holder"] for n, b in boxes.items()} == {
        "marit": "marit", "wren": "marit", "tobias": "marit", "imani": "marit",
        "tobias-own": "tobias", "imani-own": "imani", "leo": "dana", "ravi": "ravi",
    }  # fmt: skip
    assert all(b["verify"].startswith("the chain holds") for b in boxes.values())
    assert {n for n, b in boxes.items() if b["held_for"]} == {
        "wren",
        "tobias",
        "imani",
        "leo",
    }
    assert said["said"]["wren"] == {"seals": 1, "same_key": True}
    tobias = said["said"]["tobias"]
    assert set(tobias["found"].values()) == {"empty"} and len(tobias["found"]) == 4
    assert tobias["named_by"] == [] and (tobias["his_key"], tobias["her_key"]) == (1, 0)
    assert said["said"]["imani"] == {
        "held_box_seals": 2, "own_box_seals": 1, "received": 1, "held_box_ends": "handed-over",
    }  # fmt: skip
    assert said["said"]["leo"] == {"received": 1, "ravis_notes_travelled": False, "leo_box_seals": 0}  # fmt: skip
    printed = capsys.readouterr().out
    assert "received, not sealed by you" in printed and "went otherwise" not in printed


def test_a_scene_is_played_outside_the_repository_and_never_over_another(tmp_path):
    life = str(HERE / "life")
    assert scene.main(["run", "--life", life, "--to", str(HERE / "out")]) == 2
    assert scene.main(["run", "--life", life, "--to", str(tmp_path)]) == 2
    assert (
        scene.main(["run", "--life", str(tmp_path), "--to", str(tmp_path / "x")]) == 2
    )
    assert scene.main(["run"]) == 2 and scene.main([]) == 2
    assert not (HERE / "out").exists()
