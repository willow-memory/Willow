"""The Annex skeleton plays as scene.py tells it. The files are made in a
temporary folder, as CI's demo gate makes them."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


def py(*argv, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *map(str, argv)], capture_output=True,
                          text=True, cwd=cwd)  # fmt: skip


@pytest.fixture(scope="module")
def played(tmp_path_factory) -> dict:
    tmp = tmp_path_factory.mktemp("annex")
    shutil.copy(HERE / "make_life.py", tmp / "make_life.py")
    assert py(tmp / "make_life.py", cwd=tmp).returncode == 0
    assert py(tmp / "make_life.py", "--check", cwd=tmp).returncode == 0
    to = tmp / "scene"
    got = py(HERE / "scene.py", "run", "--life", tmp / "life", "--to", to)
    return {"got": got, "doc": json.loads((to / "scene.json").read_text()), "tmp": tmp}


def test_the_scene_plays_as_told(played):
    assert played["got"].returncode == 0, played["got"].stdout + played["got"].stderr
    assert played["doc"]["wrong"] == []


def test_every_chain_holds_and_only_vask_and_lumen_sealed(played):
    boxes = played["doc"]["boxes"]
    assert len(boxes) == 8
    assert all(b["held"] for b in boxes.values())
    assert {k for k, b in boxes.items() if b["seals"]} == {"vask", "lumen"}


def test_the_wall_holds(played):
    out = played["got"].stdout
    assert "vask     exit 42, 0 served" in out
    assert "counter  exit 0, 2 served" in out
    assert "broken" in out


def test_the_scene_refuses_a_folder_that_is_there(played):
    got = py(HERE / "scene.py", "run", "--life", played["tmp"] / "life",
             "--to", played["tmp"] / "scene")  # fmt: skip
    assert got.returncode == 2
