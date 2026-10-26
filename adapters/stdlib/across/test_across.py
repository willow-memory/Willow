"""across: one document composed across several boxes. It runs a document
add-on (digest, export, timeline, readings) over every box, heads each box's
part, and refuses a bad command line, a folder that isn't a box, or an
unknown document. It writes nothing of its own."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACROSS = HERE / "across.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ACROSS), *argv], capture_output=True, text=True
    )


def box(tmp: Path, name: str, files: dict[str, str]) -> Path:
    """A real kernel box over a little pile; returns the box folder."""
    pile = tmp / f"{name}-pile"
    pile.mkdir()
    for rel, text in files.items():
        p = pile / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    b = tmp / f"{name}-box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile",
                    str(pile), "--key", str(tmp / f"{name}.key"), *NOW],
                   check=True, capture_output=True)  # fmt: skip
    return b


def two_boxes(tmp: Path) -> tuple[Path, Path]:
    a = box(
        tmp, "alice", {"garden.md": "2026-03-01 Reported the mould in the bedroom.\n"}
    )
    b = box(tmp, "bob", {"log.md": "2026-04-02 The mould came back in the kitchen.\n"})
    return a, b


def test_digest_is_composed_across_every_box(tmp_path):
    a, b = two_boxes(tmp_path)
    got = run("--box", str(a), "--box", str(b), "digest")
    assert got.returncode in (0, 42), got.stderr
    assert "across 2 boxes, digest" in got.stdout
    assert f"══ {a} ══" in got.stdout and f"══ {b} ══" in got.stdout
    assert "of 2 boxes flagged by digest" in got.stdout


def test_a_boxes_list_file_names_the_boxes(tmp_path):
    a, b = two_boxes(tmp_path)
    lst = tmp_path / "boxes.txt"
    lst.write_text(f"# my boxes\n{a}\n\n{b}\n")
    got = run("--boxes", str(lst), "digest")
    assert got.returncode in (0, 42), got.stderr
    assert f"══ {a} ══" in got.stdout and f"══ {b} ══" in got.stdout


def test_a_relative_path_in_the_list_is_read_from_the_lists_folder(tmp_path):
    a, _ = two_boxes(tmp_path)
    lst = tmp_path / "boxes.txt"
    lst.write_text(f"{a.name}\n")  # relative to tmp_path, where the box sits
    got = run("--boxes", str(lst), "digest")
    assert got.returncode in (0, 42), got.stderr
    assert a.name in got.stdout


def test_timeline_traces_a_matter_across_the_boxes_and_writes_nothing(tmp_path):
    a, b = two_boxes(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    got = run("--box", str(a), "--box", str(b), "timeline", "--", "mould")
    assert got.returncode in (0, 42), got.stderr
    assert "mould" in got.stdout  # each box's dated line about the matter
    after = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert after == before, "across and its add-ons wrote nothing outside their scratch"


def test_export_runs_over_every_box(tmp_path):
    a, b = two_boxes(tmp_path)
    got = run("--box", str(a), "--box", str(b), "export")
    assert got.returncode in (0, 42), got.stderr
    assert f"══ {a} ══" in got.stdout and f"══ {b} ══" in got.stdout


def test_readings_passes_the_words_through(tmp_path):
    a, b = two_boxes(tmp_path)
    got = run("--box", str(a), "--box", str(b), "readings", "--", "mould")
    assert got.returncode in (0, 42), got.stderr
    assert f"══ {a} ══" in got.stdout


def test_a_box_with_a_flag_from_the_doc_lifts_the_exit(tmp_path):
    # timeline exits 42 when a matter is only common words; across lifts to 42
    a, b = two_boxes(tmp_path)
    got = run("--box", str(a), "--box", str(b), "timeline", "--", "the of and")
    assert got.returncode == 42, got.stdout + got.stderr
    assert "2 of 2 boxes flagged by timeline" in got.stdout


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    a, _ = two_boxes(tmp_path)
    for argv in (
        [],  # nothing
        ["--box", str(a)],  # no DOC
        ["--box", str(a), "digest", "--stray", "x"],  # junk after DOC, no `--`
        ["--box", str(a), "nonsense"],  # unknown DOC
        ["digest"],  # no boxes
        ["--boxes", str(a), "--box", str(a), "digest"],  # both sources
    ):
        got = run(*argv)
        assert got.returncode == 2 and "across.py" in got.stderr, (argv, got.stderr)


def test_a_folder_that_isnt_a_box_is_refused(tmp_path):
    (tmp_path / "plain").mkdir()
    got = run("--box", str(tmp_path / "plain"), "digest")
    assert got.returncode == 2 and "isn't a kernel box" in got.stderr


def test_an_unreadable_box_list_is_refused(tmp_path):
    got = run("--boxes", str(tmp_path / "missing.txt"), "digest")
    assert got.returncode == 2 and "box list" in got.stderr
