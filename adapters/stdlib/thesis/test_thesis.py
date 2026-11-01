"""thesis: each sentence of a document against the folder, claim-check's way,
and the ones no passage holds listed last."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import thesis  # noqa: E402

KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "thesis.py"
NOW = ["--now", "2026-11-01T00:00:00Z"]

DOC = """# Notes

Tomatoes want six hours of sun. Water goes at the root, never the leaves.

- Basil likes shade and cold.
- Yes.

```
Slugs eat lettuce overnight.
```

Slugs eat the lettuce overnight.
"""


def box(tmp_path: Path, words: str | None = None) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text(
        "Tomatoes want six hours of sun.\n\nWater at the root.\n\nBasil likes shade.\n"
    )
    extra = []
    if words is not None:
        wl = tmp_path / "words.txt"
        wl.write_text(words)
        os.chmod(wl, 0o600)
        extra = ["--words", str(wl)]
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), *extra, *NOW],
                   check=True, capture_output=True)  # fmt: skip
    return b


def run(b: Path, doc: Path, *more: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--box", str(b), str(doc), *more],
                          capture_output=True, text=True)  # fmt: skip


def doc_of(tmp_path: Path, text: str = DOC) -> Path:
    d = tmp_path / "thesis.md"
    d.write_text(text)
    return d


def test_claims_are_sentences_placed_at_their_line():
    got = thesis.claims(DOC)
    assert got == [
        (3, "Tomatoes want six hours of sun."),
        (3, "Water goes at the root, never the leaves."),
        (5, "Basil likes shade and cold."),
        (6, "Yes."),
        (12, "Slugs eat the lettuce overnight."),
    ]


def test_a_sentence_runs_over_lines_and_starts_where_it_starts():
    got = thesis.claims("First one.\nSecond starts here\nand ends here.\n")
    assert got == [(1, "First one."), (2, "Second starts here and ends here.")]


def test_held_short_and_the_part_no_file_has(tmp_path):
    got = run(box(tmp_path), doc_of(tmp_path))
    assert got.returncode == 42
    out = got.stdout
    assert "line 3    held   garden.md:1   Tomatoes want six hours of sun." in out
    assert "Water goes at the root" in out and "lacks goes, never, leaves" in out
    assert "line 5    short  garden.md:5 lacks cold" in out
    assert "line 12   short  no part held" in out
    assert "5 claims" not in out and "4 claims; 1 held, 3 short; 1 skipped" in out
    tail = out.split("without a passage holding every part:")[1]
    assert "line 3    no file has: goes, never, leaves" in tail  # the second sentence
    assert "line 5    no file has: cold" in tail
    assert "line 12   no file has: slugs, eat, lettuce, overnight" in tail


def test_every_claim_held_exits_zero(tmp_path):
    d = doc_of(tmp_path, "Tomatoes want six hours of sun.\n\nBasil likes shade.\n")
    got = run(box(tmp_path), d)
    assert got.returncode == 0 and "2 claims; 2 held, 0 short" in got.stdout
    assert "without" not in got.stdout


def test_a_one_part_sentence_is_skipped_not_judged(tmp_path):
    d = doc_of(tmp_path, "Yes. Basil likes shade.\n")
    got = run(box(tmp_path), d)
    assert got.returncode == 0 and "1 claims; 1 held, 0 short; 1 skipped" in got.stdout


def test_a_part_each_in_another_passage_says_so(tmp_path):
    d = doc_of(tmp_path, "Basil wants six hours.\n")
    got = run(box(tmp_path), d)
    assert got.returncode == 42
    assert "every part is somewhere, none in one place" in got.stdout


def test_the_words_list_is_read_as_claim_check_reads_it(tmp_path):
    d = doc_of(tmp_path, "Tomatoes want daylight.\n")
    assert run(box(tmp_path), d).returncode == 42
    (tmp_path / "w").mkdir()
    got = run(box(tmp_path / "w", "daylight = sun\n"), d)
    assert got.returncode == 0 and "garden.md:1" in got.stdout


def test_top_sets_how_many_near_passages_a_short_claim_shows(tmp_path):
    d = doc_of(tmp_path, "Tomatoes and basil need water and shade.\n")
    b = box(tmp_path)
    one, two = run(b, d).stdout, run(b, d, "--top", "2").stdout
    assert one.count(" lacks ") == 1 and two.count(" lacks ") == 2


def test_the_empty_document_and_the_refusals(tmp_path):
    b = box(tmp_path)
    got = run(b, doc_of(tmp_path, "# Only a heading\n"))
    assert got.returncode == 0 and "No claims to check" in got.stdout
    for argv in ([str(tmp_path / "nope.md")], [str(tmp_path)]):
        assert run(b, Path(argv[0])).returncode == 2
    bin_doc = tmp_path / "x.bin"
    bin_doc.write_bytes(b"\xff\xfe\x00")
    assert run(b, bin_doc).returncode == 2
    assert run(tmp_path / "nobox", doc_of(tmp_path)).returncode == 2
    assert run(b, doc_of(tmp_path), "--top", "0").returncode == 2
    bare = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    assert bare.returncode == 2 and "thesis.py --box DIR FILE" in bare.stderr


def test_it_writes_nothing(tmp_path):
    b, d = box(tmp_path), doc_of(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    run(b, d)
    assert before == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
