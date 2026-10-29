"""deep-links: each approved answer, or each passage a question holds, as a
file link with an RFC 5147 line fragment and, with --base, a web link with a
text fragment; encoded as the standards ask; nothing opened or written; an
approval that doesn't stand or a vanished citation left out and said."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "deep_links.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]
spec = importlib.util.spec_from_file_location("kernel_for_deep_links", KERNEL)
kernel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kernel)
spec2 = importlib.util.spec_from_file_location("deep_links", SCRIPT)
dl = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(dl)
GARDEN = "Notes\n\nTomatoes want six hours of sun.\nWater them daily.\n\nA well-known frost, the first, arrives in the second week of November & stays.\n"


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


def box(tmp_path: Path, seal: bool = True, folder: str = "notes") -> tuple[Path, str]:
    pile = tmp_path / "pile"
    (pile / folder).mkdir(parents=True)
    (pile / folder / "garden.md").write_text(GARDEN)
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
    served = json.loads(
        k("bite", "--box", str(b), *NOW, "how much sun do tomatoes want water").stdout
    )["served"]
    row = {
        "path": "sun.md",
        "data": "Six hours, and water daily.",
        "cites": [s["id"] for s in served],
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
    return b, subject(row)


def test_an_approved_answer_is_followed_by_a_file_link_for_each_cited_passage(tmp_path):
    b, _ = box(tmp_path)
    got = run("--box", str(b))
    assert got.returncode == 0, got.stderr
    lines = got.stdout.splitlines()
    assert lines[0] == "Six hours, and water daily."
    uri = (tmp_path / "pile" / "notes" / "garden.md").resolve().as_uri()
    assert f"  notes/garden.md:3   {uri}#line=2,4" in lines


def test_lines_are_counted_from_zero_over_the_whole_passage():
    assert dl.lines_fragment({"line": 1, "text": "one"}) == "line=0,1"
    assert dl.lines_fragment({"line": 3, "text": "a\nb\nc"}) == "line=2,5"


def test_with_a_base_a_web_link_carries_a_text_fragment(tmp_path):
    b, _ = box(tmp_path)
    out = run("--box", str(b), "--base", "https://example.org/files/").stdout
    assert (
        "https://example.org/files/notes/garden.md#:~:text=Tomatoes%20want%20six%20hours%20of%20sun."
        in out
    )


def test_a_long_first_line_is_a_start_and_an_end_and_the_special_characters_are_encoded():
    p = {
        "path": "a b/c.md",
        "line": 1,
        "text": "A well-known frost, the first, arrives in the second week of November & stays.",
    }
    assert (
        dl.text_fragment(p)
        == ":~:text=A%20well%2Dknown%20frost%2C%20the,of%20November%20%26%20stays."
    )
    assert dl.encode("a-b,c&d e") == "a%2Db%2Cc%26d%20e"
    assert dl.links(p, Path("/tmp"), "https://x.org")[
        1
    ] == "https://x.org/a%20b/c.md#" + dl.text_fragment(p)
    assert (
        dl.text_fragment({"text": "one two three four five six seven eight"})
        == ":~:text=one%20two%20three%20four%20five%20six%20seven%20eight"
    )
    assert (
        dl.text_fragment({"text": "one two three four five six seven eight nine"})
        == ":~:text=one%20two%20three%20four,six%20seven%20eight%20nine"
    )
    assert (
        dl.text_fragment({"text": "\n\n  first line here\nsecond"})
        == ":~:text=first%20line%20here"
    )


def test_a_question_gives_links_for_the_passages_held_and_writes_nothing(tmp_path):
    b, _ = box(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    got = run("--box", str(b), "how much sun do tomatoes want")
    assert got.returncode == 0 and got.stdout.splitlines()[0].startswith(
        "Tomatoes want six hours of sun. Water them daily."
    )
    assert "#line=2,4" in got.stdout
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_a_question_nothing_holds_says_so_and_waits_on_you(tmp_path):
    b, _ = box(tmp_path)
    got = run("--box", str(b), "zebra giraffe")
    assert got.returncode == 42 and "nothing to link" in got.stdout


def test_no_approved_answer_waits_on_you(tmp_path):
    b, _ = box(tmp_path, seal=False)
    got = run("--box", str(b))
    assert got.returncode == 42 and "No approved answer to link." in got.stdout


def test_a_changed_proposal_is_left_out_and_said(tmp_path):
    b, subj = box(tmp_path)
    f = b / "proposals" / f"{subj[9:]}.json"
    f.write_text(f.read_text().replace("Six", "Ten"))
    got = run("--box", str(b))
    assert (
        got.returncode == 42
        and "1 approval left out" in got.stderr
        and "Ten" not in got.stdout
    )


def test_a_passage_that_changed_has_no_link_and_is_said(tmp_path):
    b, _ = box(tmp_path)
    (tmp_path / "pile" / "notes" / "garden.md").write_text(
        GARDEN.replace("six", "eight")
    )
    got = run("--box", str(b))
    assert got.returncode == 42 and "no longer in your files" in got.stderr
    assert "notes/garden.md:3" not in got.stdout


def test_a_path_with_a_space_is_a_safe_link(tmp_path):
    b, _ = box(tmp_path, folder="my notes")
    out = run("--box", str(b), "--base", "https://x.org/f").stdout
    assert "garden.md#line=2,4" in out and "my%20notes/garden.md" in out


def test_a_record_that_does_not_verify_is_refused(tmp_path):
    b, _ = box(tmp_path)
    rec = b / "record.jsonl"
    rec.write_text(rec.read_text().replace("garden.md", "garden.mx", 1))
    assert run("--box", str(b)).returncode == 2


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    b, _ = box(tmp_path)
    for argv in ([], ["--box"], ["--box", str(b), "a", "b"], ["--box", str(b), "--base", "ftp://x"], ["--box", str(b), "--base"], ["--box", str(b), "--stray"],
                 ["--box", str(tmp_path)]):  # fmt: skip
        assert run(*argv).returncode == 2, argv
    assert (
        run().stderr.strip()
        == "python adapters/stdlib/deep-links/deep_links.py --box DIR [--base URL]"
    )


def test_a_long_passage_is_cut_at_a_hundred_characters(tmp_path):
    b, _ = box(tmp_path)
    (tmp_path / "pile" / "notes" / "garden.md").write_text(
        "Tomatoes " + "want sun " * 30 + "\n"
    )
    got = run("--box", str(b), "tomatoes want sun")
    first = got.stdout.splitlines()[0]
    assert len(first) == 100 and first.startswith("Tomatoes want sun want sun")
