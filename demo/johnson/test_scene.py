"""The Johnson scene: one report passed between five people's willows plays as
README.md tells it. The files are made in a temporary folder, as CI's demo
gate makes them."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SHARE = HERE.parents[1] / "adapters" / "stdlib" / "share" / "share.py"


def py(*argv, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *map(str, argv)], capture_output=True,
                          text=True, cwd=cwd)  # fmt: skip


@pytest.fixture(scope="module")
def played(tmp_path_factory) -> dict:
    tmp = tmp_path_factory.mktemp("johnson")
    shutil.copy(HERE / "make_life.py", tmp / "make_life.py")
    assert py(tmp / "make_life.py", cwd=tmp).returncode == 0
    to = tmp / "scene"
    got = py(HERE / "scene.py", "run", "--life", tmp / "life", "--to", to)
    doc = json.loads((to / "scene.json").read_text())
    return {"got": got, "doc": doc, "to": to, "life": tmp / "life"}


def test_the_scene_plays_as_told(played):
    assert played["got"].returncode == 0, played["got"].stdout + played["got"].stderr
    assert played["doc"]["wrong"] == []


def test_every_chain_holds_and_only_ines_sealed(played):
    people = played["doc"]["people"]
    assert list(people) == ["ines", "walt", "aurelie", "tamsin", "harold"]
    for who, p in people.items():
        assert p["verify"].startswith("the chain holds"), (who, p["verify"])
        assert p["seals"] == (5 if who == "ines" else 0), who


def test_each_hop_is_on_both_chains(played):
    people, pk = played["doc"]["people"], played["doc"]["packages"]
    assert people["ines"]["sent"] == [pk["report"], pk["report-v2"]]
    for who, got, sent in (("walt", "report", "walt-to-aurelie"),
                           ("aurelie", "walt-to-aurelie", "aurelie-to-tamsin"),
                           ("tamsin", "aurelie-to-tamsin", "tamsin-to-harold")):  # fmt: skip
        assert [pk[got], "good"] in people[who]["received"]
        assert [pk[got + "-v2" if got != "report" else "report-v2"], "good"] in people[
            who
        ]["received"]
        assert people[who]["sent"] == [pk[sent], pk[sent + "-v2"]]
    assert people["harold"]["received"] == [[pk["tamsin-to-harold"], "good"],
                                            [pk["tamsin-to-harold-v2"], "good"]]  # fmt: skip
    assert people["harold"]["sent"] == []


def test_the_edited_copy_is_refused_and_on_tamsins_chain(played):
    received = played["doc"]["people"]["tamsin"]["received"]
    assert [v for _, v in received] == ["broken", "good", "good"]
    out = played["got"].stdout
    assert "$21,400" not in out.split("── 5.")[1], "the edit never reaches Harold"


def test_harold_holds_four_layers_and_the_correction(played):
    to, pk = played["to"], played["doc"]["packages"]
    got = py(SHARE, "check", "--package", to / "tamsin-to-harold-v2.pkg")
    assert got.returncode == 0 and got.stdout.count("└ from ") == 3
    assert "reported the leak on 2026-03-06" in got.stdout
    inner = json.loads((to / "report-v2.pkg").read_text())
    assert inner["replaces"] == pk["report"]
    v1 = json.loads((to / "report.pkg").read_text())
    assert "reported the leak on 2026-03-04" in json.dumps(v1["answers"])


def test_every_kept_package_tells_her_real_record_from_a_rewritten_one(played):
    """Her own verify can't see the rewrite; each person's packages can."""
    assert "her own verify: the chain holds" in played["got"].stdout
    witness = played["doc"]["witness"]
    assert list(witness) == ["walt", "aurelie", "tamsin", "harold"]
    for who, said in witness.items():
        assert said == {
            "real": ["holds", "holds"],
            "rewritten": ["rewritten", "rewritten"],
        }, who


def test_no_package_holds_a_line_of_anyones_files(played):
    lines = {line.strip() for p in played["life"].rglob("*.md")
             for line in p.read_text().splitlines() if len(line.strip()) > 30}  # fmt: skip
    for pkg in played["to"].glob("*.pkg"):
        text = pkg.read_text()
        assert not [line for line in lines if line in text], pkg.name


def test_a_bad_command_line_is_refused(tmp_path):
    for argv in (
        [],
        ["run"],
        ["run", "--life", tmp_path],
        ["go", "--life", "a", "--to", "b"],
    ):
        got = py(HERE / "scene.py", *argv)
        assert got.returncode == 2 and "scene.py run" in got.stderr
    got = py(HERE / "scene.py", "run", "--life", tmp_path, "--to", tmp_path / "s")
    assert got.returncode == 2 and "what make_life.py wrote" in got.stderr
