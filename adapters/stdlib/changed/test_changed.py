"""changed: every file fingerprinted on the first check, then only what's
new, edited or deleted, each check one `changed` row through the kernel;
the folder's state rebuilt from the record alone; never a file's words."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("changed", HERE / "changed.py")
ch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ch)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "changed.py"), *argv],
        capture_output=True,
        text=True,
    )


def make(tmp_path: Path) -> tuple[Path, Path]:
    pile = tmp_path / "pile"
    (pile / "care").mkdir(parents=True)
    (pile / "care" / "log.txt").write_text("Pills at 8.\n")
    (pile / "insurance.txt").write_text("Renews in May.\n")
    (pile / "scan.pdf").write_bytes(b"%PDF\0binary")
    (pile / ".hidden").mkdir()
    (pile / ".hidden" / "x.txt").write_text("not counted\n")
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key", str(tmp_path / "k"),
                    "--now", "2026-10-20T09:12:00Z"], check=True, capture_output=True)  # fmt: skip
    return pile, b


def rows(b: Path) -> list[dict]:
    return [json.loads(x) for x in (b / "record.jsonl").read_text().splitlines()]


def test_the_first_check_fingerprints_every_file_even_a_pdf(tmp_path):
    pile, b = make(tmp_path)
    got = run("--box", str(b), "--now", "2026-10-20T09:12:00Z")
    assert got.returncode == 0 and "First check: 3 files" in got.stdout
    row = rows(b)[-1]
    assert row["kind"] == "changed" and row["who"] == "changed" and row["first"] is True
    assert sorted(row["files"]) == ["care/log.txt", "insurance.txt", "scan.pdf"]


def test_a_later_check_says_what_changed_and_keeps_only_that(tmp_path):
    pile, b = make(tmp_path)
    run("--box", str(b), "--now", "2026-10-20T09:12:00Z")
    (pile / "care" / "log.txt").write_text("Pills at 9 now.\n")
    (pile / "insurance.txt").unlink()
    (pile / "bank.txt").write_text("Statement.\n")
    got = run("--box", str(b), "--now", "2026-10-22T10:00:00Z")
    assert got.returncode == 42
    assert got.stdout.splitlines()[:4] == [
        "Since the last check (2026-10-20 09:12):",
        "  new      bank.txt",
        "  edited   care/log.txt",
        "  deleted  insurance.txt",
    ]
    assert "the stale add-on says which" in got.stdout
    row = rows(b)[-1]
    assert sorted(row["new"]) == ["bank.txt"] and sorted(row["edited"]) == [
        "care/log.txt"
    ]
    assert row["deleted"] == ["insurance.txt"] and "files" not in row
    again = run("--box", str(b), "--now", "2026-10-23T10:00:00Z")
    assert (
        again.returncode == 0
        and "Nothing changed since the last check (2026-10-22 10:00)." in again.stdout
    )


def test_the_state_is_rebuilt_from_the_record_alone(tmp_path):
    pile, b = make(tmp_path)
    run("--box", str(b), "--now", "2026-10-20T09:12:00Z")
    (pile / "insurance.txt").unlink()
    (pile / "new.txt").write_text("x\n")
    run("--box", str(b), "--now", "2026-10-21T00:00:00Z")
    state, when = ch.last_state(rows(b))
    assert state == ch.fingerprints(pile) and when == "2026-10-21T00:00:00Z"
    assert ch.last_state([]) == (None, "")


def test_no_words_of_a_file_reach_the_record_and_the_chain_holds(tmp_path):
    pile, b = make(tmp_path)
    run("--box", str(b), "--now", "2026-10-20T09:12:00Z")
    text = (b / "record.jsonl").read_text()
    assert "Pills" not in text and "Renews" not in text
    assert (
        subprocess.run(
            [sys.executable, str(KERNEL), "verify", "--box", str(b)],
            capture_output=True,
        ).returncode
        == 0
    )


def test_a_broken_record_is_refused(tmp_path):
    pile, b = make(tmp_path)
    rec = b / "record.jsonl"
    rec.write_bytes(rec.read_bytes().replace(b'"boot"', b'"booT"', 1))
    got = run("--box", str(b))
    assert got.returncode == 2 and "doesn't verify" in got.stderr


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    for argv in ([], ["--box"], ["--box", str(tmp_path), "x"]):
        got = run(*argv)
        assert got.returncode == 2 and "changed.py" in got.stderr
    assert "not a kernel box" in run("--box", str(tmp_path)).stderr
