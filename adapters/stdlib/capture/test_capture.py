"""capture: one paragraph per note that the kernel's chunks and bite find by its
words, type or tags; two captures never overwrite each other; nothing is written
but that one file, and a missing folder, a box or a bad word is refused."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
KERNEL = ROOT / "kernel.py"
SCRIPT = HERE / "capture.py"
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

NOW = "2026-11-01T09:30:00Z"


def cap(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_a_note_is_one_paragraph_with_its_type_and_tags(tmp_path):
    d = tmp_path
    got = cap("--to", str(d), "--type", "idea", "--tags", "garden,veg",
              "--now", NOW, "Plant  out\nthe tomatoes.")  # fmt: skip
    assert got.returncode == 0, got.stderr
    [f] = d.iterdir()
    assert f.name.startswith("20261101T093000Z-") and f.suffix == ".txt"
    assert f.read_text(encoding="utf-8") == (
        "Plant out the tomatoes.\ntype: idea\ntags: garden, veg\n"
        "captured: 2026-11-01T09:30:00Z\n"
    )
    assert got.stdout == f"written: {f}\n"
    [chunk] = kernel.chunks(d)
    assert chunk["path"] == f.name and chunk["line"] == 1
    assert chunk["text"].count("\n") == 3


def test_the_default_type_is_note_and_no_tags_leaves_the_line_out(tmp_path):
    assert cap("--to", str(tmp_path), "--now", NOW, "Bin day.").returncode == 0
    [f] = tmp_path.iterdir()
    assert f.read_text(encoding="utf-8") == (
        "Bin day.\ntype: note\ncaptured: 2026-11-01T09:30:00Z\n"
    )


def test_the_kernels_bite_finds_a_note_by_its_words_its_type_and_its_tags(tmp_path):
    pile, box = tmp_path / "pile", tmp_path / "box"
    pile.mkdir()
    cap("--to", str(pile), "--type", "observation", "--tags", "garden,frost",
        "--now", NOW, "Swallows were back over the allotment.")  # fmt: skip
    cap("--to", str(pile), "--type", "task", "--now", "2026-11-01T09:31:00Z",
        "Order seed potatoes.")  # fmt: skip
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), "--pile",
                    str(pile), "--key", str(tmp_path / "key"), "--now", NOW],
                   check=True, capture_output=True)  # fmt: skip
    for question, first in [
        ("swallows allotment", "Swallows"),
        ("observation", "Swallows"),
        ("garden frost", "Swallows"),
        ("task seed potatoes", "Order seed"),
    ]:
        got = subprocess.run(
            [sys.executable, str(KERNEL), "bite", "--box", str(box), "--now", NOW, question],
            capture_output=True, text=True,
        )  # fmt: skip
        assert got.returncode == 0, (question, got.stdout, got.stderr)
        top = json.loads(got.stdout)["served"][0]["text"]
        assert top.startswith(first), (question, top)


def test_two_captures_never_overwrite_each_other(tmp_path):
    a = cap("--to", str(tmp_path), "--now", NOW, "First thing.")
    b = cap("--to", str(tmp_path), "--now", NOW, "Second thing.")
    again = cap("--to", str(tmp_path), "--now", NOW, "First thing.")
    again2 = cap("--to", str(tmp_path), "--now", NOW, "First thing.")
    assert {a.returncode, b.returncode, again.returncode, again2.returncode} == {0}
    files = sorted(tmp_path.iterdir())
    assert len(files) == 4 and len({f.name for f in files}) == 4
    texts = sorted(f.read_text(encoding="utf-8").splitlines()[0] for f in files)
    assert texts == ["First thing."] * 3 + ["Second thing."]
    assert sum(f.name.endswith("-2.txt") for f in files) == 1
    assert sum(f.name.endswith("-3.txt") for f in files) == 1


def test_an_existing_note_is_left_byte_for_byte(tmp_path):
    cap("--to", str(tmp_path), "--now", NOW, "Keep me.")
    before = snapshot(tmp_path)
    cap("--to", str(tmp_path), "--now", NOW, "Keep me.")
    after = snapshot(tmp_path)
    assert all(after[k] == v for k, v in before.items()) and len(after) == 2


def test_it_writes_that_one_file_and_nothing_else(tmp_path):
    pile = tmp_path / "pile"
    (pile / "sub").mkdir(parents=True)
    (pile / "garden.md").write_text("Tomatoes want sun.\n", encoding="utf-8")
    before = snapshot(tmp_path)
    assert cap("--to", str(pile), "--now", NOW, "One more.").returncode == 0
    added = set(snapshot(tmp_path)) - set(before)
    assert len(added) == 1 and next(iter(added)).startswith("pile/")
    assert all(snapshot(tmp_path)[k] == v for k, v in before.items())


def test_a_missing_folder_is_refused_not_made(tmp_path):
    got = cap("--to", str(tmp_path / "new" / "deeper"), "--now", NOW, "Hello.")
    assert got.returncode == 2 and "isn't a folder" in got.stderr
    assert not (tmp_path / "new").exists()


def test_a_file_in_place_of_the_folder_is_refused(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("x", encoding="utf-8")
    assert cap("--to", str(f), "Hello.").returncode == 2
    assert f.read_text(encoding="utf-8") == "x"


def test_a_box_is_refused_and_left_alone(tmp_path):
    pile, box = tmp_path / "pile", tmp_path / "box"
    pile.mkdir()
    (pile / "g.md").write_text("Tomatoes want sun.\n", encoding="utf-8")
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), "--pile",
                    str(pile), "--key", str(tmp_path / "key"), "--now", NOW],
                   check=True, capture_output=True)  # fmt: skip
    before = snapshot(box)
    got = cap("--to", str(box), "--now", NOW, "Hello.")
    assert got.returncode == 2 and "box" in got.stderr
    assert snapshot(box) == before


@pytest.mark.parametrize(
    "argv",
    [
        ["--type", "Idea"],
        ["--type", "two words"],
        ["--type", ""],
        ["--tags", "Garden"],
        ["--tags", "a b"],
        ["--tags", ""],
        ["--tags", ",,"],
        ["--now", "yesterday"],
        ["--now", "2026-11-01"],
    ],
)
def test_a_bad_word_or_time_is_refused_and_writes_nothing(argv, tmp_path):
    got = cap("--to", str(tmp_path), *argv, "Hello.")
    assert got.returncode == 2 and got.stderr.startswith("refused:"), got.stderr
    assert list(tmp_path.iterdir()) == []


def test_an_empty_note_is_refused(tmp_path):
    assert cap("--to", str(tmp_path), " \n ").returncode == 2
    assert list(tmp_path.iterdir()) == []


def test_a_note_too_long_for_one_passage_is_refused_at_the_edge(tmp_path):
    fixed = len("\ntype: note\ncaptured: 2026-11-01T09:30:00Z")
    fits = "x" * (kernel.MAX_CHUNK - 1 - fixed)
    assert cap("--to", str(tmp_path), "--now", NOW, fits).returncode == 0
    [f] = tmp_path.iterdir()
    assert len(kernel.chunks(tmp_path)) == 1
    got = cap("--to", str(tmp_path), "--now", NOW, fits + "y")
    assert got.returncode == 2 and "one passage holds" in got.stderr
    assert list(tmp_path.iterdir()) == [f]


def test_repeated_tags_are_kept_once_in_the_order_given(tmp_path):
    cap("--to", str(tmp_path), "--tags", "b, a ,b,a-1", "--now", NOW, "Hi.")
    [f] = tmp_path.iterdir()
    assert "tags: b, a, a-1\n" in f.read_text(encoding="utf-8")


def test_the_time_defaults_to_now_and_fits_the_name(tmp_path):
    assert cap("--to", str(tmp_path), "Hello.").returncode == 0
    [f] = tmp_path.iterdir()
    text = f.read_text(encoding="utf-8")
    stamp = text.rsplit("captured: ", 1)[1].strip()
    assert f.name.startswith(stamp.replace("-", "").replace(":", ""))


@pytest.mark.parametrize(
    "argv",
    [[], ["Hello."], ["--to"], ["--stray", "x", "--to", "."], ["--to", ".", "a", "b"],
     ["--to", ".", "--bogus"]],
)  # fmt: skip
def test_a_bad_command_line_is_refused_and_says_how_to_run_it(argv, tmp_path):
    got = cap(*argv)
    assert got.returncode == 2 and "capture.py" in got.stderr
    assert not any(tmp_path.iterdir())
