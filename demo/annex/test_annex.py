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


def test_every_chain_holds_and_only_the_five_who_sealed_have_seals(played):
    boxes = played["doc"]["boxes"]
    assert len(boxes) == 8
    assert all(b["held"] for b in boxes.values())
    assert {k: b["seals"] for k, b in boxes.items() if b["seals"]} == {
        "vask": 2, "lumen": 3, "karst": 2, "program": 2, "intake": 2, "counter": 2,
    }  # fmt: skip
    # oversight only received; prior never left its wall
    assert boxes["oversight"]["seals"] == boxes["prior"]["seals"] == 0


def test_each_box_alone_sees_no_clash_and_oversight_sees_both(played):
    out = played["got"].stdout
    assert out.count("0 of 1 steps flagged") == 4
    assert "OPERATOR   Karst: an operator is a running process" in out
    assert "Lumen: an operator is the person" in out
    assert "CLOCK      Program: 08:00    Intake: 09:00" in out


def test_the_wall_holds(played):
    out = played["got"].stdout
    assert "vask     exit 42, 0 served" in out
    assert "counter  exit 0, 2 served" in out
    assert "broken" in out


def test_the_scene_refuses_a_folder_that_is_there(played):
    got = py(HERE / "scene.py", "run", "--life", played["tmp"] / "life",
             "--to", played["tmp"] / "scene")  # fmt: skip
    assert got.returncode == 2


def test_the_witness_names_exactly_the_rewritten_chain(played):
    found = played["doc"]["found"]
    assert set(found["real"].values()) == {"holds"}
    assert found["rewritten"] == ["rewritten"]
    assert (
        "the chain holds"
        in played["got"].stdout.split("rewritten copy, by its own verify: ")[1]
    )


def test_the_rumour_is_in_no_package(played):
    assert not any(
        "Halvern" in p.read_text() for p in (played["tmp"] / "scene").glob("*.pkg")
    )


def test_annex_os_builds_one_page_without_the_rumour(played, tmp_path):
    page = tmp_path / "annex-os.html"
    got = py(
        HERE / "annex_os.py", "build", "--scene", played["tmp"] / "scene", "--to", page
    )
    assert got.returncode == 0, got.stderr
    html = page.read_text(encoding="utf-8")
    assert "ANNEX-OS" in html and html.count('id="data"') == 1
    data = json.loads(html.split('type="application/json">')[1].split("</script>")[0])
    assert len(data["boxes"]) == 8
    assert data["clocks"] == {"program": "08:00", "intake": "09:00"}
    assert data["found"]["rewritten"] == ["rewritten"]
    for rumour in ("Halvern", "affairs", "intelligence service"):
        assert rumour not in html
    assert "review" in data["served"] and "affairs" not in data["served"]
    assert "src=" not in html and "http" not in html  # no network, nothing fetched


def test_annex_os_refuses_a_bad_command_line(tmp_path):
    assert py(HERE / "annex_os.py", "build").returncode == 2
