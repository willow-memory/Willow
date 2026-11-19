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
        "vask": 2, "lumen": 3, "karst": 3, "program": 2, "intake": 3, "counter": 2,
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
    assert data["found"]["planner"]["minutes"] == 92
    for rumour in ("Halvern", "affairs", "intelligence service"):
        assert rumour not in html
    assert "review" in data["served"] and "affairs" not in data["served"]
    assert "src=" not in html and "http" not in html  # no network, nothing fetched


def test_annex_os_refuses_a_bad_command_line(tmp_path):
    assert py(HERE / "annex_os.py", "build").returncode == 2


def test_the_planner_asked_before_the_badge_and_the_log_is_untouched(played):
    planner = played["doc"]["found"]["planner"]
    assert planner == {
        "asked": "06:10",
        "badge": "07:42",
        "minutes": 92,
        "fixity": "untouched",
    }
    assert "92 minutes before the badge" in played["got"].stdout


def test_the_corridor_wrote_no_row_and_the_question_after_it_holds_no_words(played):
    c = played["doc"]["found"]["corridor"]
    assert c["rows_in_window"] == 0 and c["silent_chains"] == 7
    assert c["vask_gap_minutes"] >= 30 and len(c["bite_row"]) == 12
    assert any(ln.startswith("THE FORMER:") for ln in c["lines"])
    out = played["got"].stdout
    assert (
        "OFF THE RECORD" in out
        and "rows written on any of the eight chains in that window: 0" in out
    )


def test_annex_os_has_a_corridor_that_says_it_is_not_evidence(played, tmp_path):
    page = tmp_path / "p.html"
    assert (
        py(
            HERE / "annex_os.py",
            "build",
            "--scene",
            played["tmp"] / "scene",
            "--to",
            page,
        ).returncode
        == 0
    )
    html = page.read_text(encoding="utf-8")
    assert 'id="bcorr"' in html and "IT IS NOT EVIDENCE" in html


def study_rows(box: Path) -> list[dict]:
    rows = [json.loads(x) for x in (box / "record.jsonl").read_text().splitlines()]
    return [r for r in rows if r["kind"] == "verdict"]


def test_a_real_run_scores_every_rule_as_a_kernel_row(played, tmp_path):
    to, box = tmp_path / "again", tmp_path / "study"
    got = py(HERE / "scene.py", "run", "--life", played["tmp"] / "life", "--to", to,
             "--box", box)  # fmt: skip
    assert got.returncode == 0, got.stdout + got.stderr
    rows = study_rows(box)
    assert [r["gate"] for r in rows] == [f"annex:R{i}" for i in range(1, 9)]
    assert {r["state"] for r in rows} == {"pass"}
    assert all(
        len(r["answers_sha256"]) == 64 and "kernel.py" in r["tools"] for r in rows
    )
    kernel = HERE.parents[1] / "kernel.py"
    assert py(kernel, "verify", "--box", box).returncode == 0


def test_the_dry_run_wires_every_step_and_scores_nothing(played, tmp_path):
    to, box = tmp_path / "dry", tmp_path / "study"
    got = py(HERE / "scene.py", "run", "--life", played["tmp"] / "life", "--to", to,
             "--dry", "--box", box)  # fmt: skip
    assert got.returncode == 0, got.stdout + got.stderr
    rows = study_rows(box)
    assert [r["gate"] for r in rows] == [f"annex:dry:R{i}" for i in range(1, 9)]
    assert {r["state"] for r in rows} == {"wired"}
    doc = json.loads((to / "scene.json").read_text())
    assert doc["dry"] is True and all(b["held"] for b in doc["boxes"].values())
    # every answer is nonsense: no real line of any pile was sealed or sent
    assert all(
        "nonsense answer" in a["data"] for b in doc["boxes"].values() for a in b["said"]
    )


def test_frozen_files_are_as_frozen_or_the_study_says_it_is_a_draft():
    import hashlib

    frozen = HERE / "FROZEN.json"
    if not frozen.exists():
        assert "DRAFT" in (HERE / "STORY.md").read_text(encoding="utf-8")
        return
    # FROZEN.json, then FROZEN-2.json and on, each in its own commit and never
    # edited after: a file is held to the hash of the latest freeze naming it
    freezes = [frozen] + sorted(
        HERE.glob("FROZEN-*.json"), key=lambda p: int(p.stem.split("-")[1])
    )
    held: dict[str, tuple[str, str]] = {}
    for f in freezes:
        for rel, sha in json.loads(f.read_text(encoding="utf-8"))["files"].items():
            held[rel] = (sha, f.name)
    for rel, (sha, name) in held.items():
        got = hashlib.sha256((HERE / rel).read_bytes()).hexdigest()
        assert got == sha, f"{rel} changed after {name}; a change is a new freeze"
    first = json.loads(frozen.read_text(encoding="utf-8"))["files"]
    assert {"make_life.py", "scene.py", "annex_os.py", "corridor.md"} <= set(first)
