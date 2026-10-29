"""badge: an SVG badge of the record's counts: answers approved and the files
they came from, green when the chain holds and every approval stands, amber
when one doesn't, red when the chain breaks, grey when nothing is approved;
its title and description carry how to check it; the Markdown snippet with a
link; escaped, parseable, the same bytes twice, written once; refusals."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "badge.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]
NS = {"s": "http://www.w3.org/2000/svg"}
spec = importlib.util.spec_from_file_location("kernel_for_badge", KERNEL)
kernel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kernel)
spec2 = importlib.util.spec_from_file_location("badge", SCRIPT)
bd = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(bd)


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def subject(row: dict) -> str:
    canon = json.dumps(
        {x: row[x] for x in ("path", "data", "cites", "claim")},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return "proposal:" + hashlib.sha256(canon.encode()).hexdigest()


def box(
    tmp_path: Path, answers: list[tuple[str, str]], seal: bool = True
) -> tuple[Path, list[str]]:
    """A box with an answer for each (file the question finds, answer)."""
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want six hours of sun.\n")
    (pile / "bins.md").write_text("Bins go out on Thursday night.\n")
    b = tmp_path / "box"
    assert (
        k(
            "init",
            "--box",
            str(b),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "key"),
            *NOW,
        ).returncode
        == 0
    )
    subjects = []
    for question, text in answers:
        served = json.loads(k("bite", "--box", str(b), *NOW, question).stdout)["served"]
        row = {
            "path": f"a{len(subjects)}.md",
            "data": text,
            "cites": [served[0]["id"]],
            "claim": "the notes",
        }
        (tmp_path / "r.jsonl").write_text(json.dumps(row) + "\n")
        assert (
            k(
                "propose", "--box", str(b), "--file", str(tmp_path / "r.jsonl"), *NOW
            ).returncode
            == 42
        )
        if seal:
            assert k("seal", "--box", str(b), subject(row), *NOW).returncode == 0
        subjects.append(subject(row))
    return b, subjects


def badge(b: Path, tmp_path: Path, *extra: str):
    to = tmp_path / "badge.svg"
    to.unlink(missing_ok=True)
    got = run("--box", str(b), "--to", str(to), *extra)
    return got, ET.fromstring(to.read_text()) if to.exists() else None


def texts(root: ET.Element) -> list[str]:
    return [t.text for t in root.iter("{http://www.w3.org/2000/svg}text")]


def fills(root: ET.Element) -> list[str]:
    return [r.get("fill") for r in root.iter("{http://www.w3.org/2000/svg}rect")]


TWO = [
    ("how much sun do tomatoes want", "Six hours."),
    ("when do the bins go out", "Thursday night."),
]


def test_approved_answers_and_the_files_they_came_from_are_counted_in_green(tmp_path):
    b, _ = box(tmp_path, TWO)
    got, root = badge(b, tmp_path)
    assert got.returncode == 0, got.stderr
    assert texts(root) == ["willow", "2 answers from 2 files"] and fills(root) == [
        "#555",
        "#3c9a5f",
    ]
    assert (
        root.get("role") == "img"
        and root.get("aria-label") == "willow: 2 answers from 2 files"
    )
    assert f"wrote {tmp_path / 'badge.svg'}: 2 answers from 2 files" in got.stdout


def test_two_answers_from_one_file_are_one_file_and_one_answer_is_singular(tmp_path):
    b, _ = box(
        tmp_path,
        [("how much sun do tomatoes want", "A"), ("tomatoes want six hours sun", "B")],
    )
    assert texts(badge(b, tmp_path)[1])[1] == "2 answers from 1 file"
    sub = tmp_path / "one"
    sub.mkdir()
    b1, _ = box(sub, TWO[:1])
    assert texts(badge(b1, sub)[1])[1] == "1 answer from 1 file"


def test_nothing_approved_is_a_grey_badge_that_says_so(tmp_path):
    b, _ = box(tmp_path, TWO, seal=False)
    got, root = badge(b, tmp_path)
    assert (
        got.returncode == 0
        and texts(root)[1] == "no approved answers"
        and fills(root)[1] == "#9f9f9f"
    )


def test_a_changed_proposal_or_a_forged_seal_makes_it_amber_and_waits_on_you(tmp_path):
    b, subjects = box(tmp_path, TWO)
    f = b / "proposals" / f"{subjects[0][9:]}.json"
    f.write_text(f.read_text().replace("Six", "Ten"))
    got, root = badge(b, tmp_path)
    assert (
        got.returncode == 42
        and texts(root)[1] == "1 answer from 1 file, 1 not standing"
        and fills(root)[1] == "#d4a017"
    )
    kernel.append(
        b,
        "2026-10-24T00:00:00Z",
        "seal",
        who="human",
        subject="proposal:" + "0" * 64,
        proof="0" * 64,
    )
    assert texts(badge(b, tmp_path)[1])[1] == "1 answer from 1 file, 2 not standing"


def test_a_broken_chain_is_a_red_record_broken_badge(tmp_path):
    b, _ = box(tmp_path, TWO)
    rec = b / "record.jsonl"
    rec.write_text(rec.read_text().replace("garden.md", "garden.mx", 1))
    got, root = badge(b, tmp_path)
    assert (
        got.returncode == 42
        and texts(root)[1] == "record broken"
        and fills(root)[1] == "#c0392b"
    )


def test_the_title_and_description_say_how_to_check_it(tmp_path):
    b, _ = box(tmp_path, TWO)
    _, root = badge(b, tmp_path)
    rows, _ = kernel.read(b / "record.jsonl")
    desc = root.find("s:desc", NS).text
    assert root.find("s:title", NS).text == "willow: 2 answers from 2 files"
    assert (
        f"The record has {len(rows)} rows and its tip begins {rows[-1]['hash'][:8]}."
        in desc
    )
    assert (
        "python kernel.py verify --box BOX" in desc
        and "a claim, not a signature" in desc
    )


def test_a_link_prints_the_markdown_for_a_page(tmp_path):
    b, _ = box(tmp_path, TWO)
    got, _ = badge(b, tmp_path, "--link", "https://example.org/check")
    assert (
        "markdown: [![willow: 2 answers from 2 files](badge.svg)](https://example.org/check)"
        in got.stdout
    )
    assert "markdown:" not in badge(b, tmp_path)[0].stdout


def test_the_badge_is_wide_enough_for_its_words_and_text_is_escaped():
    f = {"state": "ok", "rows": 1, "tip": "ab", "answers": 1, "files": 1, "bad": 0}
    root = ET.fromstring(bd.svg(f))
    left, right = [
        r.get("width") for r in root.iter("{http://www.w3.org/2000/svg}rect")
    ][:2]
    assert (
        int(root.get("width")) == int(left) + int(right)
        and int(right) > len("1 answer from 1 file") * 6
    )
    assert bd.escape("a<b&c") == "a&lt;b&amp;c"


def test_the_same_record_gives_the_same_bytes_and_it_is_written_once_private(tmp_path):
    b, _ = box(tmp_path, TWO)
    to = tmp_path / "badge.svg"
    assert run("--box", str(b), "--to", str(to)).returncode == 0
    assert stat.S_IMODE(os.stat(to).st_mode) == 0o600
    one = to.read_bytes()
    again = run("--box", str(b), "--to", str(to))
    assert again.returncode == 2 and "could not write" in again.stderr
    to.unlink()
    run("--box", str(b), "--to", str(to))
    assert to.read_bytes() == one
    assert (
        run("--box", str(b), "--to", str(tmp_path / "nope" / "b.svg")).returncode == 2
    )


def test_the_box_is_not_changed(tmp_path):
    b, _ = box(tmp_path, TWO)
    before = {p: p.read_bytes() for p in b.rglob("*") if p.is_file()}
    run("--box", str(b), "--to", str(tmp_path / "badge.svg"))
    assert {p: p.read_bytes() for p in b.rglob("*") if p.is_file()} == before


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    b, _ = box(tmp_path, TWO[:1])
    to = str(tmp_path / "b.svg")
    for argv in ([], ["--box", str(b)], ["--to", to], ["--box", str(b), "--to", to, "stray"], ["--box", str(b), "--to", to, "--link", "ftp://x"],
                 ["--box", str(b), "--to", to, "--link"], ["--box", str(tmp_path), "--to", to]):  # fmt: skip
        assert run(*argv).returncode == 2, argv
    assert "badge.py" in run().stderr
