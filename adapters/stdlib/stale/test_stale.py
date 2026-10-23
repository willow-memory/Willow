"""stale: an approval whose cited passage changed or went is found exactly,
by the passage's content hash; an edit elsewhere is not a false alarm."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def stale(b: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "stale.py"), "--box", str(b)],
                          capture_output=True, text=True)  # fmt: skip


def approved(tmp_path: Path, data: str = "Six hours.") -> tuple[Path, Path]:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text(
        "Tomatoes want six hours of sun.\n\nWater at the root.\n"
    )
    (pile / "other.md").write_text("The shed is blue.\n")
    b = tmp_path / "box"
    k("init", "--box", str(b), "--pile", str(pile), "--key", str(tmp_path / "k"), *NOW)
    got = json.loads(
        k("bite", "--box", str(b), *NOW, "how much sun do tomatoes want").stdout
    )
    row = {"path": "sun.md", "data": data, "cites": [got["served"][0]["id"]],
           "claim": "garden.md"}  # fmt: skip
    (tmp_path / "rows.jsonl").write_text(json.dumps(row) + "\n")
    k("propose", "--box", str(b), "--file", str(tmp_path / "rows.jsonl"), *NOW)
    subj = "proposal:" + __import__("hashlib").sha256(
        json.dumps({x: row[x] for x in ("path", "data", "cites", "claim")},
                   sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()  # fmt: skip
    assert k("seal", "--box", str(b), subj, *NOW).returncode == 0
    return b, pile


def test_an_approval_holds_while_its_cited_passage_is_there(tmp_path):
    b, pile = approved(tmp_path)
    got = stale(b)
    assert got.returncode == 0 and "holds" in got.stdout and "0 stale" in got.stdout
    (pile / "other.md").write_text("The shed is green now.\n")  # an edit it didn't cite
    assert stale(b).returncode == 0


def test_a_changed_or_deleted_cited_passage_makes_it_stale(tmp_path):
    b, pile = approved(tmp_path)
    (pile / "garden.md").write_text(
        "Tomatoes want eight hours of sun.\n\nWater at the root.\n"
    )
    got = stale(b)
    assert got.returncode == 42 and "stale" in got.stdout
    assert "was at garden.md:1" in got.stdout
    (pile / "garden.md").write_text(
        "Tomatoes want six hours of sun.\n\nWater at the root.\n"
    )
    assert stale(b).returncode == 0  # put back word for word: it holds again
    (pile / "garden.md").unlink()
    assert stale(b).returncode == 42
    # the kernel still answers with the approval: finding this is stale's job
    again = json.loads(
        k("bite", "--box", str(b), *NOW, "how much sun do tomatoes want").stdout
    )
    assert again["state"] == "sealed"


def test_it_reads_and_never_writes(tmp_path):
    b, pile = approved(tmp_path)
    (pile / "garden.md").unlink()
    before = (b / "record.jsonl").read_bytes()
    stale(b)
    assert (b / "record.jsonl").read_bytes() == before


def test_a_record_that_doesnt_verify_is_refused(tmp_path):
    b, _ = approved(tmp_path)
    path = b / "record.jsonl"
    path.write_bytes(
        path.read_bytes().replace(b'"verdict":"pass"', b'"verdict":"fail"', 1)
    )
    assert stale(b).returncode == 2


def test_a_long_answer_is_shown_cut_and_its_subject_shortened(tmp_path):
    long = "Six hours of direct sun, more in a cool summer, and never less than four."
    b, _ = approved(tmp_path, long)
    line = stale(b).stdout.splitlines()[0]
    assert line.startswith("holds   proposal:") and line.split("…")[0].endswith(
        line.split()[1][:21]
    )
    assert len(line.split()[1].rstrip("…")) == 21
    assert line.endswith(repr(long[:57] + "..."))
