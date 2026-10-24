"""stack.py on Bernadette's files: every layer runs, nothing is approved but by
the person, and the answers are still the ones STRIP.md scores.

Her files are made in a temporary folder, as CI's demo gate makes them."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[1] / "kernel.py"
NOW = "2026-10-24T09:00:00Z"
#: What each of the twenty questions came to on the mirror, as STRIP.md has it
STATES = ["populated"] * 18 + ["empty"] * 2


def py(*argv: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True,
                          cwd=cwd)  # fmt: skip


@pytest.fixture(scope="module")
def ran(tmp_path_factory) -> dict:
    tmp = tmp_path_factory.mktemp("bernie")
    shutil.copy(HERE / "make_life.py", tmp / "make_life.py")
    assert py(str(tmp / "make_life.py"), cwd=tmp).returncode == 0
    to = tmp / "out"
    got = py(str(HERE / "stack.py"), "run", "--to", str(to), "--life",
             str(tmp / "life"), "--now", NOW)  # fmt: skip
    assert got.returncode == 42, got.stdout + got.stderr  # waits on the person
    doc = json.loads((to / "stack.json").read_text())
    return {"to": to, "doc": doc, "out": got.stdout}


def step(doc: dict, piece: str) -> list[dict]:
    return [s for s in doc["steps"] if s["piece"] == piece]


def test_every_reader_reads_her_files(ran):
    for piece in ("mail", "calendar", "chats", "notes", "office", "books"):
        [s] = step(ran["doc"], piece)
        assert s["state"] == "said" and s["said"].startswith("wrote "), s
    [pdf] = step(ran["doc"], "pdf")  # a deps add-on: unreachable without pypdf
    assert pdf["state"] in ("said", "unreachable"), pdf


def test_the_questions_come_to_what_strip_scores(ran):
    asked = ran["doc"]["asked"]
    if step(ran["doc"], "pdf")[0]["state"] == "unreachable":
        pytest.skip("the scores were made with the pdf reader")
    assert [a["state"] for a in asked] == STATES
    by = {a["n"]: a for a in asked}
    assert by[5]["served"][0] == "Calendar/Home.ics.txt:150"  # N6, TAX DUE
    assert by[2]["served"][0] == "Documents/Household budget 2026.xlsx.txt:3"  # T2
    assert (
        "Documents/Scans/Referral - Dr Tolley 11-02-2026.pdf.txt:13"
        in (by[3]["served"])
    )  # N2
    assert [n for n, a in by.items() if a["raw_state"] != a["state"]] == [6, 9, 18]


def test_nothing_is_approved_until_the_person_seals(ran):
    rows, breaks = load(ran["to"] / "willow" / "box")
    assert breaks == [] and not [r for r in rows if r["kind"] == "seal"]
    [*_, last] = step(ran["doc"], "mcp-lite")
    assert len(last["waiting"]) == 1
    assert "WAITING ON THE PERSON" in ran["out"]
    assert not (ran["to"] / "willow" / "box" / "written").exists()


def test_after_the_seal_the_trust_layer_holds(ran):
    box = ran["to"] / "willow" / "box"
    [subj] = step(ran["doc"], "mcp-lite")[-1]["waiting"]
    sealed = py(str(KERNEL), "seal", "--box", str(box), subj, "--now", NOW)
    assert sealed.returncode == 0, sealed.stderr  # the person's act, with her key
    got = py(str(HERE / "stack.py"), "after", "--to", str(ran["to"]), "--now", NOW)
    assert got.returncode == 0, got.stdout + got.stderr
    after = {s["piece"]: s for s in json.loads(
        (ran["to"] / "stack.json").read_text())["after"]}  # fmt: skip
    assert after["stale"]["said"] == "1 approved; 0 stale"
    assert after["diverge"]["said"].startswith("The same")
    assert after["kernel"]["said"].startswith("the chain holds")
    assert after["session-seal"]["state"] == "for you", "one seal, still theirs"


def test_a_bad_command_line_or_a_folder_inside_the_repo_is_refused(tmp_path):
    for argv in ([], ["run"], ["fly", "--to", str(tmp_path)]):
        got = py(str(HERE / "stack.py"), *argv)
        assert got.returncode == 2 and "stack.py" in got.stderr
    got = py(str(HERE / "stack.py"), "run", "--to", str(HERE / "out"),
             "--life", str(tmp_path))  # fmt: skip
    assert got.returncode == 2 and "outside the repo" in got.stderr


def load(box: Path) -> tuple[list[dict], list[str]]:
    sys.path.insert(0, str(KERNEL.parent))
    import kernel

    return kernel.read(box / "record.jsonl")
