"""The handoff zip: a reviewer can do every step from it alone and get the
proposal it says they will, with nothing of anyone's key or documents in it."""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ZIP = HERE / "marisol-handoff.zip"
HASH = "d53f9c12aee372ef1548a90a996c6d0999018466d8ed7c4c0f396e0b7e65ff75"
QUESTION = "Maria made landfall on Puerto Rico on Wednesday, September 20, near the Yabucoa municipality"
PRIVATE = (
    "Trader Joe",
    "UFCW",
    "Stansbury",
    "medical",
    "resume",
    "curriculum vitae",
    " CV",
)


def kernel(where: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "kernel.py", *args], cwd=where, capture_output=True, text=True
    )


def test_the_zip_is_what_make_handoff_writes():
    got = subprocess.run(
        [sys.executable, str(HERE / "make_handoff.py"), "--check"],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 0, "run: python3 demo/marisol/handoff/make_handoff.py"


def test_it_holds_its_five_files_and_no_key_box_or_personal_document():
    with zipfile.ZipFile(ZIP) as z:
        names = z.namelist()
    assert sorted(n.split("/", 1)[1] for n in names) == [
        "FOR-FELIPE.md", "README.md", "kernel.py",
        "pile/hurricane-maria-landfall.txt", "suggestions.jsonl",
    ]  # fmt: skip
    assert not [
        n for n in names if n.endswith((".key", ".pdf", ".docx", ".jpg", ".png"))
    ]


def test_its_instructions_are_the_repos_and_name_nothing_private():
    with zipfile.ZipFile(ZIP) as z:
        for doc in ("README.md", "FOR-FELIPE.md"):
            text = z.read(f"marisol-handoff/{doc}").decode("utf-8")
            assert text == (HERE / doc).read_text(encoding="utf-8")
            assert not [w for w in PRIVATE if w in text], doc


def test_every_step_works_from_the_zip_and_gives_the_proposal_it_says(tmp_path):
    with zipfile.ZipFile(ZIP) as z:
        z.extractall(tmp_path)
    where = tmp_path / "marisol-handoff"
    assert (
        kernel(
            where, "init", "--box", "box", "--pile", "pile", "--key", "my.key"
        ).returncode
        == 0
    )
    bite = kernel(where, "bite", "--box", "box", QUESTION)
    assert (
        '"state": "echo"' in bite.stdout and bite.returncode == 42
    )  # as the README says
    got = kernel(where, "propose", "--box", "box", "--file", "suggestions.jsonl")
    assert f"pass  proposal:{HASH}" in got.stdout
    assert kernel(where, "seal", "--box", "box", f"proposal:{HASH}").returncode == 0
    assert "1 sealed" in kernel(where, "verify", "--box", "box").stdout
    sealed = where / "box/written/translations/maria-landfall.es.md"
    assert sealed.read_text(encoding="utf-8").startswith("La tormenta tocó tierra")
