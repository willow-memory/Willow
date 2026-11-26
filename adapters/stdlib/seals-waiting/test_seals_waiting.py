"""seals-waiting: what waits on the seal, said as kernel.py out says it, with
the record the same bytes after; a seal and a decline each taken out of what
waits; --json; refusals, a record that doesn't read among them."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "seals_waiting.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = "2026-10-24T09:30:00Z"


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def subject(row: dict) -> str:
    canon = json.dumps({x: row[x] for x in ("path", "data", "cites", "claim")},
                       sort_keys=True, separators=(",", ":"), ensure_ascii=False)  # fmt: skip
    return "proposal:" + hashlib.sha256(canon.encode()).hexdigest()


def a_box(tmp_path: Path, n: int = 3) -> tuple[Path, list[str]]:
    """A box with n suggestions waiting on the seal."""
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want six hours of sun.\n")
    b = tmp_path / "box"
    assert k("init", "--box", str(b), "--pile", str(pile), "--key", str(tmp_path / "key"),
             "--now", NOW).returncode == 0  # fmt: skip
    served = json.loads(k("bite", "--box", str(b), "--now", NOW,
                          "how much sun do tomatoes want").stdout)["served"]  # fmt: skip
    rows = [{"path": f"a{i}.md", "data": f"Six hours of sun {i}.",
             "cites": [served[0]["id"]], "claim": "the garden notes"} for i in range(n)]  # fmt: skip
    (tmp_path / "r.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    assert k("propose", "--box", str(b), "--file", str(tmp_path / "r.jsonl"),
             "--now", NOW).returncode == 42  # fmt: skip
    return b, [subject(r) for r in rows]


def test_it_says_what_out_says_and_writes_nothing(tmp_path):
    b, subjects = a_box(tmp_path)
    before = (b / "record.jsonl").read_bytes()
    got = run("--box", str(b))
    assert got.returncode == 42, got.stderr
    assert (b / "record.jsonl").read_bytes() == before  # not a row more
    out = k("out", "--box", str(b), "--now", NOW)
    assert out.returncode == 42
    waits = [
        ln for ln in got.stdout.splitlines() if ln.startswith("waiting on your seal: ")
    ]
    assert waits == [
        ln for ln in out.stdout.splitlines() if ln.startswith("waiting on your seal: ")
    ]
    assert sorted(w.split(": ", 1)[1] for w in waits) == sorted(subjects)
    n = len(before.decode().splitlines())
    assert got.stdout.splitlines()[-1] == f"{n} rows; 0 sealed; 3 waiting"
    assert (
        out.stdout.splitlines()[-1] == f"{n + 1} rows; 0 sealed; 3 waiting"
    )  # out's own


def test_a_seal_and_a_decline_each_stop_waiting(tmp_path):
    b, subjects = a_box(tmp_path)
    assert k("seal", "--box", str(b), subjects[0], "--now", NOW).returncode == 0
    assert k("decline", "--box", str(b), subjects[1], "--now", NOW).returncode == 0
    doc = json.loads(run("--box", str(b), "--json").stdout)
    assert doc["state"] == "waiting" and doc["waiting"] == [subjects[2]]
    assert doc["sealed"] == [subjects[0]]
    k("seal", "--box", str(b), subjects[2], "--now", NOW)
    got = run("--box", str(b), "--json")
    assert got.returncode == 0 and json.loads(got.stdout)["state"] == "empty"


def test_a_record_that_does_not_read_is_refused(tmp_path):
    b, _ = a_box(tmp_path, n=1)
    rec = b / "record.jsonl"
    rec.write_text(rec.read_text().replace("2026-10-24", "2025-10-24", 1))
    got = run("--box", str(b))
    assert got.returncode == 2 and got.stderr.startswith("refused:")


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    for argv in ([], ["--box"], ["--box", ""], ["--box", str(tmp_path), "stray"]):
        got = run(*argv)
        assert got.returncode == 2 and "seals_waiting.py" in got.stderr, argv
    got = run("--box", str(tmp_path))  # no box there
    assert got.returncode == 2 and "not a kernel box" in got.stderr
