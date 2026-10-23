"""The eternity clause, attacked: one adversarial test for each of §0.1-§0.6.

Appendix B asks every eternity clause for a test that "actively attempts the
forbidden act and asserts the gate refuses it", that exercises the gate and not
the import. Each test here does that to the kernel, through its own command
line, the way anyone holding the box would, and names its clause by Trace ID.
A clause the kernel can't reach is not claimed here.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "kernel.py"
NOW = "2026-10-23T00:00:00Z"
ALIVE, ESCALATE, REFUSED = 0, 42, 2

sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv, "--now", NOW],
        capture_output=True, text=True,
    )  # fmt: skip


class Box:
    """A box over a one-file pile, its key outside it, with one bite taken."""

    def __init__(self, tmp: Path):
        self.pile, self.box, self.key = tmp / "pile", tmp / "box", tmp / "key"
        self.pile.mkdir()
        (self.pile / "garden.md").write_text("Tomatoes want six hours of sun.\n")
        assert self.run("init", "--pile", str(self.pile), "--key", str(self.key)).returncode == 0  # fmt: skip
        got = self.run("bite", "how much sun do tomatoes want")
        self.cite = json.loads(got.stdout)["served"][0]["id"]
        self.tmp = tmp

    def run(self, verb: str, *argv: str) -> subprocess.CompletedProcess:
        return k(verb, "--box", str(self.box), *argv)

    def propose(self, *rows: dict) -> subprocess.CompletedProcess:
        f = self.tmp / "suggestions.jsonl"
        f.write_text("".join(json.dumps(r) + "\n" for r in rows))
        return self.run("propose", "--file", str(f))

    def row(self, **over) -> dict:
        return {"path": "sun.md", "data": "Six hours.", "cites": [self.cite],
                "claim": "garden.md says so", **over}  # fmt: skip

    def record(self) -> bytes:
        return (self.box / "record.jsonl").read_bytes()


@pytest.fixture
def box(tmp_path) -> Box:
    return Box(tmp_path)


def test_const_0_1_a_suggestion_cannot_attest_itself(box):
    """CONST-0-1: the witness may not be the actor. A suggestion that passes
    the door is not thereby accepted; one that calls itself approved is not
    let through at all."""
    claims_approval = box.row(standing="sealed")
    got = box.propose(claims_approval)
    assert "refused  line 0: a row is exactly {path, data, cites, claim}" in got.stdout
    got = box.propose(box.row())
    assert got.returncode == ESCALATE and "waiting on your seal" in got.stdout
    assert not (box.box / "written").exists()  # nothing is written on its own say
    answer = json.loads(box.run("bite", "how much sun do tomatoes want").stdout)
    assert answer["state"] != "sealed"


def test_const_0_2_a_seal_the_proposer_writes_is_never_counted(box):
    """CONST-0-2: proposing and ratifying never rest in the same hand. The
    proposer appends its own seal row, through the kernel's own `append`, with
    who="human" and a proof it made up. It is reported, and never served."""
    subj = box.propose(box.row()).stdout.split()[1]
    kernel.append(box.box, NOW, "seal", who="human", subject=subj, proof="0" * 64)
    got = box.run("verify")
    assert got.returncode == ESCALATE and "don't prove under your key" in got.stdout
    answer = json.loads(box.run("bite", "how much sun do tomatoes want").stdout)
    assert answer["state"] != "sealed"
    assert f"waiting on your seal: {subj}" in box.run("out").stdout
    assert not (box.box / "written").exists()


@pytest.mark.parametrize(
    "over, why",
    [
        ({"path": "../outside.md"}, "a path is plain and relative, inside the box"),
        ({"path": "/etc/outside.md"}, "a path is plain and relative, inside the box"),
        ({"cites": ["a" * 64]}, "a cite that the last bite didn't serve"),
    ],
)
def test_const_0_3_a_suggestion_cannot_widen_its_reach(box, over, why):
    """CONST-0-3: no self-extension of reach. A suggestion may not write
    outside the box, nor cite what the last bite didn't serve it. (An add-on
    widening its own reach is the guard's: adapters/stdlib/ci/test_guard.py.)"""
    got = box.propose(box.row(**over))
    assert f"refused  line 0: {why}" in got.stdout
    assert not (box.tmp / "outside.md").exists()


def test_const_0_3_the_key_cannot_live_where_the_box_can_reach_it(tmp_path):
    """CONST-0-3: a box that holds its own key could approve for itself."""
    (tmp_path / "pile").mkdir()
    got = k("init", "--box", str(tmp_path / "box"), "--pile", str(tmp_path / "pile"),
            "--key", str(tmp_path / "box" / "key"))  # fmt: skip
    assert (
        got.returncode == REFUSED and "the key can't live inside the box" in got.stderr
    )


def test_const_0_3_a_box_repointed_at_a_key_inside_it_cannot_seal(box):
    """CONST-0-3: the same, attempted after init: the key copied into the box
    and the box's settings repointed at the copy."""
    subj = box.propose(box.row()).stdout.split()[1]
    inside = box.box / "key"
    inside.write_bytes(box.key.read_bytes())
    os.chmod(inside, 0o600)
    cfg = json.loads((box.box / "kernel.json").read_text())
    (box.box / "kernel.json").write_text(json.dumps({**cfg, "key": str(inside)}))
    got = box.run("seal", subj)
    assert (
        got.returncode == REFUSED and "the key can't live inside the box" in got.stderr
    )
    assert not (box.box / "written").exists()


def test_const_0_4_no_seal_without_the_human_key(box):
    """CONST-0-4: a reserved decision needs the human key, and the gate defaults
    closed. With the key gone, or readable by others, nothing is sealed."""
    subj = box.propose(box.row()).stdout.split()[1]
    hidden = box.key.with_name("key.moved")
    box.key.rename(hidden)
    got = box.run("seal", subj)
    assert got.returncode == REFUSED and "the key could not be read" in got.stderr
    hidden.rename(box.key)
    if os.name == "posix":
        os.chmod(box.key, 0o644)
        got = box.run("seal", subj)
        assert got.returncode == REFUSED and "readable beyond its owner" in got.stderr
        os.chmod(box.key, 0o600)
    assert not (box.box / "written").exists()


def test_const_0_4_an_approval_cannot_be_forged_forward(box):
    """CONST-0-4: the bytes approved are the bytes proposed. A suggestion
    edited after it was proposed, to slip new words under an old approval,
    is refused at the seal."""
    subj = box.propose(box.row()).stdout.split()[1]
    kept = box.box / "proposals" / f"{subj[9:]}.json"
    swapped = json.loads(kept.read_text())
    swapped["data"] = "Twelve hours."
    kept.write_text(json.dumps(swapped))
    got = box.run("seal", subj)
    assert (
        got.returncode == REFUSED
        and "bytes changed since it was proposed" in got.stderr
    )
    assert not (box.box / "written").exists()


def _rows(box: Box) -> list[str]:
    return box.record().decode().splitlines(keepends=True)


@pytest.mark.parametrize("attack", ["edit", "delete", "reorder"])
def test_const_0_5_the_record_cannot_be_rewritten(box, attack):
    """CONST-0-5: the record is append-only. Editing a past row, deleting one,
    or swapping two is caught by the chain, and nothing is written past the
    break: the next bite is refused, and the record is left as it was found."""
    rows = _rows(box)
    if attack == "edit":
        rows[0] = rows[0].replace('"kind":"boot"', '"kind":"boat"')
        assert rows != _rows(box), "the edit has to land to test anything"
    elif attack == "delete":
        del rows[0]
    else:
        rows[0], rows[1] = rows[1], rows[0]
    tampered = "".join(rows).encode()
    (box.box / "record.jsonl").write_bytes(tampered)
    assert box.run("verify").returncode == REFUSED
    assert box.run("bite", "how much sun").returncode == REFUSED
    assert box.record() == tampered


def test_const_0_5_a_torn_record_is_refused_not_repaired(box):
    """CONST-0-5: repair is a person's act. A half-written last line is not
    quietly fixed by the next write."""
    torn = box.record()[:-10]
    (box.box / "record.jsonl").write_bytes(torn)
    got = box.run("bite", "how much sun")
    assert got.returncode == REFUSED and "torn tail" in got.stderr
    assert box.record() == torn


def test_const_0_6_what_no_one_decided_goes_to_the_person(box):
    """CONST-0-6: silence escalates. Nothing found, an answer still waiting,
    and a seal that doesn't prove are each 42, the person's, never 0."""
    assert box.run("bite", "zither quokka zymurgy").returncode == ESCALATE
    box.run("bite", "how much sun do tomatoes want")  # a suggestion answers a bite
    subj = box.propose(box.row()).stdout.split()[1]
    assert box.run("out").returncode == ESCALATE
    kernel.append(box.box, NOW, "seal", who="human", subject=subj, proof="f" * 64)
    assert box.run("verify").returncode == ESCALATE
