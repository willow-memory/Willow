"""pets: care by pet and kind, a pet named only by what the line says, a line
about a person's own vaccine left out, and the car add-on's reading of cost
and due dates."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("pets", HERE / "pets.py")
pt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pt)
NOW = ["--now", "2026-10-29T00:00:00Z"]
SCRIPT = str(HERE / "pets.py")


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(parents=True)
    for name, text in files.items():
        p = pile / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    return b


def test_the_sibling_it_reads_through_is_put_at_the_front():
    here = sys.path.index(str(HERE.parent / "car"))
    root = str(HERE.parents[2])
    assert sys.path[here - 1] == root and sys.path[here + 1] == root


def test_a_pet_is_named_only_by_what_the_line_says():
    w = pt.who_of
    assert w("Biscuit: booster, £38") == "Biscuit"
    assert w("2026-02-03 Biscuit: booster") == "Biscuit", "after a date"
    assert w("03/02/2026  Rex Junior - jab") == "Rex Junior"
    assert w("Biscuit - worming tablet") == "Biscuit"
    assert w("Rex Junior: jab") == "Rex Junior"
    assert w("booster for Biscuit at the vet") == "Biscuit"
    assert w("Biscuit's booster was done") == "Biscuit"
    assert w("took Pickle's worming tablet") == "Pickle"
    assert w("Vet: booster for Pickle") == "Pickle", "Vet is not a name"
    assert w("Note: annual booster") == pt.NO_PET
    assert w("annual booster at the vet") == pt.NO_PET
    assert w("Dr Smith's practice did the booster") == pt.NO_PET
    assert w("Subject: vet reminder") == pt.NO_PET


def test_kinds_and_the_pet_context():
    pile = [
        {"path": "pets/log.md", "line": 1, "text": (
            "2026-02-03 Biscuit: booster £38\n"
            "2026-09-01 Biscuit: flea and worming tablet £10\n"
            "2026-09-02 Biscuit: antibiotics for the ear\n"
            "2025-05-20 Pickle: vet check-up\n"
        )},
        {"path": "health/me.md", "line": 1, "text": "2026-03-01 my flu jab\n2026-03-02 dental check\n"},
    ]  # fmt: skip
    got = pt.car.register(pile, pt.PETS, pt.who_of, pt.CONTEXT)
    assert set(got) == {
        ("Biscuit", "vaccine"), ("Biscuit", "worming"), ("Biscuit", "medicine"), ("Pickle", "vet"),
    }  # fmt: skip
    assert got[("Biscuit", "vaccine")]["cost"] == {"£": 38.0}
    assert pt.car.register(pile[1:], pt.PETS, pt.who_of, pt.CONTEXT) == {}, (
        "a person's own jab is no pet's"
    )


def test_the_listing_soonest_due_first(tmp_path):
    b = box(tmp_path, {"pets/log.md": (
        "2026-02-03 Biscuit: booster £38, yearly\n"
        "2025-02-03 Biscuit: booster £38\n"
        "2026-09-01 Biscuit: worming tablet £10, every 3 months\n"
        "2025-05-20 Pickle: vet check-up\n")})  # fmt: skip
    got = run(SCRIPT, "--box", str(b), *NOW)
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "Biscuit  worming  last 2026-09-01  1 time    £10.00      due 2026-12-01 (in 33 days)",
        "Biscuit  vaccine  last 2026-02-03  2 times   £76.00      due 2027-02-03 (in 97 days)",
        "Pickle   vet      last 2025-05-20  1 time    -           no due date written",
        "3 pet records, 4 entries",
    ]
    assert run(SCRIPT, "--box", str(b), *NOW).stdout == got.stdout


def test_nothing_is_42_and_refusals(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(SCRIPT, "--box", str(b), *NOW)
    assert got.returncode == 42 and "care given to a pet" in got.stdout
    for argv in (
        [],
        ["--box", str(tmp_path)],
        ["--box", str(b), "stray"],
        ["--box", str(b), "--now", "soon"],
    ):
        assert run(SCRIPT, *argv).returncode == 2, argv
    assert "pets.py" in run(SCRIPT).stderr
    assert "not a kernel box" in run(SCRIPT, "--box", str(tmp_path)).stderr
