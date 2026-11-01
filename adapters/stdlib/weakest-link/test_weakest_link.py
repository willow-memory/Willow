"""weakest-link: an approval is worth its weakest cited input, never an
average; unmarked is its own value, not assumed; gone and broken are flagged."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-11-01T00:00:00Z"]
Q = "how much sun do tomatoes want"


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def wl(b: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "weakest_link.py"), "--box", str(b)],
                          capture_output=True, text=True)  # fmt: skip


def subject(row: dict) -> str:
    body = json.dumps({x: row[x] for x in ("path", "data", "cites", "claim")},
                      sort_keys=True, separators=(",", ":"), ensure_ascii=False)  # fmt: skip
    return "proposal:" + hashlib.sha256(body.encode()).hexdigest()


def approved(
    tmp_path: Path, files: dict[str, str], n: int | None = None
) -> tuple[Path, Path]:
    """A box over `files`, with one approval citing every passage the bite served (or the first n)."""
    pile = tmp_path / "pile"
    pile.mkdir()
    for name, text in files.items():
        (pile / name).write_text(text)
    b = tmp_path / "box"
    k("init", "--box", str(b), "--pile", str(pile), "--key", str(tmp_path / "k"), *NOW)
    got = json.loads(k("bite", "--box", str(b), *NOW, Q).stdout)
    cites = [s["id"] for s in got["served"]][:n]
    row = {
        "path": "sun.md",
        "data": "Six hours.",
        "cites": cites,
        "claim": "the garden notes",
    }
    (tmp_path / "rows.jsonl").write_text(json.dumps(row) + "\n")
    k("propose", "--box", str(b), "--file", str(tmp_path / "rows.jsonl"), *NOW)
    assert k("seal", "--box", str(b), subject(row), *NOW).returncode == 0
    return b, pile


def test_all_measured_is_measured_and_holds(tmp_path):
    b, _ = approved(
        tmp_path,
        {
            "a.md": "Tomatoes want six hours of sun.\nprovenance: measured\n",
            "b.md": "Six hours of sun is what tomatoes want.\nProvenance = MEASURED\n",
        },
    )
    got = wl(b)
    assert got.returncode == 0, got.stdout + got.stderr
    assert (
        got.stdout.startswith("measured ")
        and "1 measured, 0 fitted, 0 assumed, 0 unmarked" in got.stdout
    )
    assert "fix this first" not in got.stdout


def test_one_assumed_input_makes_the_answer_assumed_never_an_average(tmp_path):
    b, _ = approved(
        tmp_path,
        {
            "a.md": "Tomatoes want six hours of sun.\nprovenance: measured\n",
            "b.md": "Tomatoes want sun, six hours, I think.\nprovenance: assumed\n",
            "c.md": "Tomatoes want six hours of sun, from the trial plots.\nprovenance: measured\n",
        },
    )
    got = wl(b)
    assert got.returncode == 42
    assert got.stdout.startswith("assumed ")
    flagged = [line for line in got.stdout.splitlines() if "fix this first" in line]
    assert len(flagged) == 1 and "b.md" in flagged[0] and "assumed" in flagged[0]


def test_fitted_beside_measured_is_fitted(tmp_path):
    b, _ = approved(
        tmp_path,
        {
            "a.md": "Tomatoes want six hours of sun.\nprovenance: measured\n",
            "b.md": "Tomatoes want six hours of sun, by the growth model.\nprovenance: fitted\n",
        },
    )
    got = wl(b)
    assert got.returncode == 42 and got.stdout.startswith("fitted ")


def test_unmarked_is_its_own_value_not_assumed(tmp_path):
    b, _ = approved(
        tmp_path,
        {
            "a.md": "Tomatoes want six hours of sun.\nprovenance: measured\n",
            "b.md": "Tomatoes want six hours of sun.\n",
        },
    )
    got = wl(b)
    assert got.returncode == 42 and got.stdout.startswith("unmarked ")
    assert "0 assumed, 1 unmarked" in got.stdout


def test_the_word_assumed_in_prose_is_not_a_mark(tmp_path):
    b, _ = approved(
        tmp_path, {"a.md": "Tomatoes want six hours of sun, it was assumed.\n"}
    )
    assert wl(b).stdout.startswith("unmarked ")


def test_a_passage_marked_twice_is_worth_the_weaker_mark(tmp_path):
    b, _ = approved(
        tmp_path,
        {
            "a.md": "Tomatoes want six hours of sun.\nprovenance: measured\nprovenance: assumed\n"
        },
    )
    assert wl(b).stdout.startswith("assumed ")


def test_a_cited_passage_that_changed_is_gone_and_the_answer_unmarked(tmp_path):
    b, pile = approved(
        tmp_path, {"a.md": "Tomatoes want six hours of sun.\nprovenance: measured\n"}
    )
    assert wl(b).returncode == 0
    (pile / "a.md").write_text(
        "Tomatoes want seven hours of sun.\nprovenance: measured\n"
    )
    got = wl(b)
    assert got.returncode == 42 and got.stdout.startswith("unmarked ")
    assert "no longer in your folder" in got.stdout


def test_a_broken_proposal_file_is_shown_and_counted(tmp_path):
    b, _ = approved(
        tmp_path, {"a.md": "Tomatoes want six hours of sun.\nprovenance: measured\n"}
    )
    for p in (b / "proposals").iterdir():
        p.write_text(p.read_text().replace("Six hours.", "Seven hours."))
    got = wl(b)
    assert (
        got.returncode == 42
        and got.stdout.startswith("broken ")
        and "1 broken" in got.stdout
    )


def test_no_approvals_is_alive(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("Tomatoes want six hours of sun.\nprovenance: assumed\n")
    b = tmp_path / "box"
    k("init", "--box", str(b), "--pile", str(pile), "--key", str(tmp_path / "k"), *NOW)
    got = wl(b)
    assert got.returncode == 0 and "0 approved" in got.stdout


def test_refuses_a_record_that_does_not_verify_and_a_folder_that_is_not_a_box(tmp_path):
    b, _ = approved(
        tmp_path, {"a.md": "Tomatoes want six hours of sun.\nprovenance: measured\n"}
    )
    rec = b / "record.jsonl"
    lines = rec.read_text().splitlines()
    lines[1] = lines[1].replace('"bite"', '"bitE"', 1)
    rec.write_text("\n".join(lines) + "\n")
    assert wl(b).returncode == 2
    assert wl(tmp_path / "nowhere").returncode == 2
    assert (
        subprocess.run(
            [sys.executable, str(HERE / "weakest_link.py")], capture_output=True
        ).returncode
        == 2
    )


def test_it_writes_nothing(tmp_path):
    b, pile = approved(
        tmp_path, {"a.md": "Tomatoes want six hours of sun.\nprovenance: assumed\n"}
    )
    before = {p: p.read_bytes() for d in (b, pile) for p in d.rglob("*") if p.is_file()}
    wl(b)
    after = {p: p.read_bytes() for d in (b, pile) for p in d.rglob("*") if p.is_file()}
    assert before == after
