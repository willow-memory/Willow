"""sort: a file goes where your phrases put it, matched as the kernel matches;
a tie is said, not broken; what no phrase reaches is unsorted, never guessed;
--json is the same report."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-11-03T00:00:00Z"]
spec = importlib.util.spec_from_file_location("sort_addon", HERE / "sort.py")
so = importlib.util.module_from_spec(spec)
spec.loader.exec_module(so)

CATS = "# mine\nmoney:  invoice, receipt, bank statement\nhealth: prescription, appointment\n"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path, files: dict) -> tuple[Path, Path]:
    pile = tmp_path / "pile"
    for rel, text in files.items():
        (pile / rel).parent.mkdir(parents=True, exist_ok=True)
        (pile / rel).write_text(text)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key",
        str(tmp_path / "k"), *NOW)  # fmt: skip
    cats = tmp_path / "categories.txt"
    cats.write_text(CATS)
    return b, cats


def test_each_file_goes_where_your_phrases_put_it(tmp_path):
    b, cats = box(tmp_path, {
        "bank/may.txt": "Bank statement for May.\n\nInvoices paid. Bank statement attached.\n",
        "letters/clinic.txt": "Your appointment is Tuesday.\n\nCollect the prescription.\n",
        "notes/june.md": "An invoice came, and an appointment.\n",
        "ideas.md": "Plant beans in the north bed.\n",
    })  # fmt: skip
    got = run(str(HERE / "sort.py"), "--box", str(b), "--categories", str(cats))
    assert got.returncode == 42, got.stderr
    assert got.stdout.splitlines() == [
        "sort: populated, 4 files: 2 sorted into 2 categories, 1 in more than one, 1 unsorted",
        "## money",
        "  bank/may.txt        3 hits: bank statement 2, invoice",
        "## health",
        "  letters/clinic.txt  2 hits: appointment, prescription",
        "## more than one",
        "  notes/june.md       money 1, health 1",
        "## unsorted",
        "  ideas.md            no phrase of yours",
    ]
    doc = json.loads(run(str(HERE / "sort.py"), "--box", str(b), "--categories",
                         str(cats), "--json").stdout)  # fmt: skip
    assert doc["state"] == "populated"
    assert [g["name"] for g in doc["groups"]] == [
        "money",
        "health",
        "more than one",
        "unsorted",
    ]


def test_every_file_placed_is_0_and_a_phrase_matches_in_order_by_stem():
    toks = so.tokens
    assert (
        so.hits(
            toks("the bank statements and a statement of the bank"),
            toks("bank statement"),
        )
        == 1
    )
    assert so.hits(toks("Invoices, receipts"), toks("invoice")) == 1


def test_all_sorted_exits_0_and_nothing_to_read_is_empty(tmp_path):
    b, cats = box(tmp_path, {"a.txt": "Receipt for the boots.\n"})
    got = run(str(HERE / "sort.py"), "--box", str(b), "--categories", str(cats))
    assert got.returncode == 0
    assert (
        got.stdout.splitlines()[0]
        == "sort: populated, 1 file: 1 sorted into 1 category"
    )
    b2, cats2 = box(tmp_path / "empty", {"photo.bin": "\0\0\0"})
    got = run(str(HERE / "sort.py"), "--box", str(b2), "--categories", str(cats2))
    assert (got.returncode, got.stdout) == (
        0,
        "sort: empty, no file here the kernel reads\n",
    )


def test_refusals(tmp_path):
    b, cats = box(tmp_path, {"a.txt": "x\n"})
    script = str(HERE / "sort.py")
    assert run(script).returncode == 2
    assert run(script, "--box", str(b)).returncode == 2
    assert (
        run(
            script, "--box", str(tmp_path / "nope"), "--categories", str(cats)
        ).returncode
        == 2
    )
    (tmp_path / "none.txt").write_text(
        "# a note: with a colon, still a note\nno colon here\nempty:\n"
    )
    got = run(script, "--box", str(b), "--categories", str(tmp_path / "none.txt"))
    assert got.returncode == 2 and "no category" in got.stderr


def suggest(b: Path, path: str, category: str, tmp: Path) -> str:
    """A suggestion as sort-ask makes one: bite on the file, propose its
    category under sort/<file>.txt citing a served passage. Its subject."""
    words = (b.parent / "pile" / path).read_text().split()[:8]
    bite = json.loads(
        run(str(KERNEL), "bite", "--box", str(b), *NOW, " ".join(words)).stdout
    )
    cite = next(s["id"] for s in bite["served"] if s["where"].startswith(path + ":"))
    row = {"path": f"sort/{path}.txt", "data": category + "\n", "cites": [cite],
           "claim": "a model read it so"}  # fmt: skip
    f = tmp / f"{path}.jsonl"
    f.write_text(json.dumps(row) + "\n")
    out = run(str(KERNEL), "propose", "--box", str(b), *NOW, "--file", str(f)).stdout
    return next(w for w in out.split() if w.startswith("proposal:"))


def test_a_category_you_sealed_places_the_file_before_its_phrases(tmp_path):
    b, cats = box(tmp_path, {
        "allotment.txt": "Watered the courgettes and picked the runner beans.\n",
        "clinic.txt": "An invoice from the clinic, for the appointment.\n",
        "ideas.txt": "Plant beans in the north bed.\n",
    })  # fmt: skip
    (tmp_path / "cats2.txt").write_text(CATS + "garden: tomatoes\n")
    cats = tmp_path / "cats2.txt"
    sealed = suggest(b, "allotment.txt", "garden", tmp_path)
    over = suggest(b, "clinic.txt", "money", tmp_path)  # its phrases say health too
    suggest(b, "ideas.txt", "garden", tmp_path)  # proposed, never sealed
    for subj in (sealed, over):
        assert run(str(KERNEL), "seal", "--box", str(b), *NOW, subj).returncode == 0
    got = run(str(HERE / "sort.py"), "--box", str(b), "--categories", str(cats))
    out = got.stdout.splitlines()
    assert "  allotment.txt  sealed by you" in out
    assert out[out.index("## money") + 1] == "  clinic.txt     sealed by you", out
    assert "  ideas.txt      no phrase of yours" in out, "waiting isn't sealed"
    # a sealed suggestion whose bytes changed stands on nothing: no place
    f = next(
        p for p in (b / "proposals").glob("*.json") if "allotment" in p.read_text()
    )
    f.write_text(f.read_text().replace("garden", "money"))
    out = run(str(HERE / "sort.py"), "--box", str(b), "--categories", str(cats)).stdout
    assert "allotment.txt  sealed by you" not in out
