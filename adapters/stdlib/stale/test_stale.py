"""stale: an approval whose cited passage changed or went is found exactly,
by the passage's content hash, and said as a report (and --json the same);
an edit elsewhere is not a false alarm."""

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


def stale(b: Path, *more: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "stale.py"), "--box", str(b), *more],
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


def module():
    import importlib.util

    spec = importlib.util.spec_from_file_location("stale_under_test", HERE / "stale.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_every_id_asked_for_that_is_in_the_pile_is_found(tmp_path):
    st = module()
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("Tomatoes want six hours of sun.\n")
    (pile / "b.md").write_text("The shed is blue.\n")
    ids = {c["id"] for c in __import__("kernel").chunks(pile)}
    assert len(ids) == 2
    assert st.present(pile, ids) == ids
    assert st.present(pile, ids | {"0" * 64}) == ids


def test_it_reads_the_pile_a_folder_at_a_time_through_pieces_when_beside_it():
    # the card's looks-for: pieces is used when it is beside stale, and stale
    # reads the kernel's way without it (copied out alone, tests:alone)
    beside = (HERE.parent / "pieces" / "pieces.py").is_file()
    pc = module().pieces()
    assert (pc is not None) == beside
    assert pc is None or hasattr(pc, "passages")


def test_an_approval_holds_while_its_cited_passage_is_there(tmp_path):
    b, pile = approved(tmp_path)
    got = stale(b)
    assert got.returncode == 0 and got.stdout == "stale: empty, 1 approved; 0 stale\n"
    assert json.loads(stale(b, "--json").stdout) == {
        "addon": "stale",
        "state": "empty",
        "said": "1 approved; 0 stale",
        "groups": [],
    }
    (pile / "other.md").write_text("The shed is green now.\n")  # an edit it didn't cite
    assert stale(b).returncode == 0


def test_a_changed_or_deleted_cited_passage_makes_it_stale(tmp_path):
    b, pile = approved(tmp_path)
    (pile / "garden.md").write_text(
        "Tomatoes want eight hours of sun.\n\nWater at the root.\n"
    )
    got = stale(b)
    assert got.returncode == 42
    head, group, row = got.stdout.splitlines()
    assert head == "stale: populated, 1 approved; 1 stale"
    assert group.startswith("## proposal:") and group.endswith("…  'Six hours.'")
    cited = json.loads((next((b / "proposals").glob("*.json"))).read_text())["cites"][0]
    assert row == f"  garden.md:1  cited {cited[:12]}: no longer in your folder"
    data = stale(b, "--json")
    assert data.returncode == 42 and json.loads(data.stdout) == {
        "addon": "stale", "state": "populated", "said": "1 approved; 1 stale",
        "groups": [{"name": group[3:], "rows": [{
            "where": "garden.md:1",
            "what": f"cited {cited[:12]}: no longer in your folder"}]}],
    }  # fmt: skip
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
    b, pile = approved(tmp_path, long)
    (pile / "garden.md").unlink()
    line = stale(b).stdout.splitlines()[1]
    assert line.startswith("## proposal:")
    assert len(line.split()[1].rstrip("…")) == 21
    assert line.endswith("…  " + repr(long[:57] + "..."))


def test_an_approval_whose_proposal_file_changed_is_broken_not_trusted(tmp_path):
    """Its cited passages are read from that file, so a file that no longer
    holds the bytes the person approved can't say whether the ground moved."""
    b, _ = approved(tmp_path)
    f = next((b / "proposals").glob("*.json"))
    held = f.read_text()
    f.write_text(json.dumps({**json.loads(held), "data": "Never.", "cites": []}))
    got = stale(b)
    assert got.returncode == 42 and "Never." not in got.stdout
    head, row = got.stdout.splitlines()
    assert head == "stale: populated, 1 approved; 0 stale; 1 broken"
    subject = "proposal:" + f.stem  # its row's place: the subject's first 21, then …
    assert (
        row
        == f"  {subject[:21]}…  broken: its proposal file is not the bytes that were sealed"
    )
    doc = json.loads(stale(b, "--json").stdout)
    assert [g["name"] for g in doc["groups"]] == [None]
    f.unlink()
    got = stale(b)
    assert got.returncode == 42 and "missing or can't be read" in got.stdout
    f.write_text(held)
    assert stale(b).returncode == 0
