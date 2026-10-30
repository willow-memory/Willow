"""ripgrep: exact hits from rg, each shown with the id of the kernel's own
passage that holds it, and counted, never shown, where the kernel doesn't
read the line as written; nothing written; and a refusal, never a quiet
skip, without rg."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "ripgrep.py"
NOW = ["--now", "2026-10-30T09:00:00Z"]


def run(*argv: str, env=None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv],
                          capture_output=True, text=True, env=env)  # fmt: skip


@pytest.fixture
def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    (pile / "letters").mkdir(parents=True)
    (pile / "letters" / "county.txt").write_text(
        "Notice of determination.\n\nDear Ms Varga,\nYou may file a response within 180 days.\n"
    )
    (pile / "notes.md").write_text("Ring the county: file a response by Friday.\n")
    (pile / "page.html").write_text("<p>Nothing here</p>\n<!-- file a response -->\n")
    (pile / "scan.bin").write_bytes(b"\0\0binary file a response\n")
    (pile / ".hidden").mkdir()
    (pile / ".hidden" / "x.txt").write_text("file a response\n")
    (pile / ".gitignore").write_text("notes.md\n")  # the kernel doesn't obey it
    b = tmp_path / "box"
    got = subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile",
                          str(pile), "--key", str(tmp_path / "key"), *NOW],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return b


def kernel_ids(box: Path) -> dict[str, str]:
    """{where: id} for the kernel's own passages."""
    sys.path.insert(0, str(HERE.parents[2]))
    import kernel

    pile = Path(kernel.config(box)["pile"])
    return {f"{c['path']}:{c['line']}": c["id"] for c in kernel.chunks(pile)}


def test_each_hit_names_the_kernels_own_passage(box):
    got = run("--box", str(box), "file a response")
    assert got.returncode == 0, got.stderr
    ids = kernel_ids(box)
    assert got.stdout.splitlines() == [
        f"letters/county.txt:4  {ids['letters/county.txt:3'][:12]}  "
        "You may file a response within 180 days.",
        f"notes.md:1  {ids['notes.md:1'][:12]}  Ring the county: file a response by Friday.",
        "2 hits in 2 passages; 1 not as the kernel reads it",
    ]  # the page's comment is markup the kernel drops; the binary and the
    # hidden folder rg skips itself, as the kernel does


def test_exact_unless_told_to_ignore_case(box):
    assert run("--box", str(box), "FILE A RESPONSE").returncode == 42
    got = run("--box", str(box), "--ignore-case", "FILE A RESPONSE")
    assert got.returncode == 0 and got.stdout.splitlines()[-1].startswith("2 hits")


def test_text_is_not_a_pattern(box):
    assert run("--box", str(box), "f.le a response").returncode == 42
    assert run("--box", str(box), "180 days.").returncode == 0


def test_nothing_is_written(box, tmp_path):
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    run("--box", str(box), "file a response")
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_refusals(box, tmp_path):
    for argv in ([], ["--box", str(box)], ["--box", str(box), "a", "b"],
                 ["--box", str(box), "  "], ["--box", str(tmp_path), "x"]):  # fmt: skip
        assert run(*argv).returncode == 2, argv
    rec = box / "record.jsonl"
    rec.write_text(rec.read_text().replace('"boot"', '"b00t"'))
    assert run("--box", str(box), "x").returncode == 2


def test_without_rg_it_refuses_and_names_the_install(box, tmp_path):
    """No rg beside this Python and none on PATH: a refusal, never 0 or 42."""
    lone = tmp_path / "lone"
    lone.mkdir()
    (lone / "python").symlink_to(sys.executable)
    got = subprocess.run([str(lone / "python"), str(SCRIPT), "--box", str(box), "x"],
                         capture_output=True, text=True,
                         env={"PATH": str(lone), "PYTHONPATH": ":".join(sys.path)})  # fmt: skip
    assert got.returncode == 2 and "requirements.txt" in got.stderr
