"""pile-sweep: the person's sealed answers asked at several passage sizes. An
answer is found at a size when a passage in the top five overlaps its lines;
each size is read with the kernel's MAX_CHUNK set to it and put back; the
best size finds the most, then reads the fewest lines, then is the kernel's
own; nothing is written; no sealed answer still in the folder is said; and a
bad command line, a broken record or an unreadable words list is refused."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PSW = HERE / "pile_sweep.py"
KERNEL = HERE.parents[2] / "kernel.py"
sys.path.insert(0, str(HERE))
import pile_sweep  # noqa: E402

kernel = pile_sweep.kernel
NOW = ["--now", "2026-10-28T00:00:00Z"]
Q = "when is the boiler serviced"


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(KERNEL), *argv, *NOW],
                          capture_output=True, text=True)  # fmt: skip


def sweep_cmd(box: Path, *more: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(PSW), "--box", str(box), *more],
                          capture_output=True, text=True)  # fmt: skip


HOUSE = (
    "2026-03-01 The boiler is serviced every March by Tamsin.\n"
    "She brings the spare valve and checks the flue.\n"
    "The gutter needs clearing before the rains, and the shed roof leaks.\n"
)


def a_box(tmp: Path, words: Path | None = None) -> tuple[Path, Path]:
    pile = tmp / "pile"
    pile.mkdir()
    (pile / "house.md").write_text(HOUSE)
    (pile / "garden.md").write_text("Tomatoes want sun.\n")
    box = tmp / "box"
    more = ["--words", str(words)] if words else []
    assert k("init", "--box", str(box), "--pile", str(pile),
             "--key", str(tmp / "key"), *more).returncode == 0  # fmt: skip
    return box, pile


def seal(box: Path, tmp: Path, question: str) -> None:
    """Ask, propose an answer citing what was served first, and seal it."""
    served = json.loads(k("bite", "--box", str(box), question).stdout)["served"]
    prop = {"path": "a.md", "data": "March.\n", "cites": [served[0]["id"]],
            "claim": "the house notes say so"}  # fmt: skip
    f = tmp / "prop.jsonl"
    f.write_text(json.dumps(prop) + "\n")
    subj = k("propose", "--box", str(box), "--file", str(f)).stdout.split()[1]
    assert k("seal", "--box", str(box), subj).returncode == 0


def questions(tmp: Path, *lines: str) -> Path:
    f = tmp / "questions.txt"
    f.write_text("".join(x + "\n" for x in lines))
    return f


def test_each_size_is_asked_and_the_best_is_named_writing_nothing(tmp_path):
    box, _ = a_box(tmp_path)
    seal(box, tmp_path, Q)
    before = {p: p.read_bytes() for p in box.rglob("*") if p.is_file()}
    got = sweep_cmd(box, "--questions", str(questions(tmp_path, Q, "kayak")),
                    "--sizes", "60,500")  # fmt: skip
    assert got.returncode == 0, got.stdout + got.stderr
    lines = got.stdout.splitlines()
    assert lines[0] == "1 questions, 1 approved passages, top 5"
    assert lines[1].split() == ["size", "kernel", "pile-rank"]
    assert lines[2].split()[:4] == ["60", "1", "of", "1,"], lines
    assert lines[3].startswith("  500  1 of 1, 3 lines") and "the kernel's" in lines[3]
    assert lines[-1] == "best for the kernel: 60; for pile-rank: 60"
    assert {p: p.read_bytes() for p in box.rglob("*") if p.is_file()} == before


def test_a_passage_is_a_file_and_its_lines(tmp_path):
    c = {"path": "a.md", "line": 4, "text": "one\ntwo\nthree"}
    assert pile_sweep.span(c) == ("a.md", 4, 6)
    assert pile_sweep.overlaps(("a.md", 4, 6), ("a.md", 6, 9))
    assert not pile_sweep.overlaps(("a.md", 4, 6), ("a.md", 7, 9))
    assert not pile_sweep.overlaps(("a.md", 4, 6), ("b.md", 4, 6))


def test_each_size_is_read_at_that_size_and_the_kernels_put_back(tmp_path):
    _, pile = a_box(tmp_path)
    small = pile_sweep.at_size(pile, 60)
    assert kernel.MAX_CHUNK == 500
    assert all(len(c["text"]) <= 60 for c in small) and len(small) > 2
    assert pile_sweep.at_size(pile, 500) == kernel.chunks(pile)


def test_the_best_finds_most_then_reads_least_then_is_the_kernels():
    t = {200: {"k": (2, 10)}, 500: {"k": (3, 40)}, 800: {"k": (3, 30)}}
    assert pile_sweep.best(t, "k") == 800, "more found beats fewer lines"
    t[500] = {"k": (3, 30)}
    assert pile_sweep.best(t, "k") == 500, "equal: the kernel's own"
    t = {300: {"k": (1, 5)}, 900: {"k": (1, 5)}}
    assert pile_sweep.best(t, "k") == 300, "then the smaller"


def test_no_sealed_answer_still_in_the_folder_says_so(tmp_path):
    box, pile = a_box(tmp_path)
    qs = questions(tmp_path, Q)
    got = sweep_cmd(box, "--questions", str(qs))
    assert got.returncode == 42 and "none of 1 questions" in got.stdout
    seal(box, tmp_path, Q)
    (pile / "house.md").write_text("The boiler was replaced.\n")
    got = sweep_cmd(box, "--questions", str(qs))
    assert got.returncode == 42 and "still in the folder" in got.stdout


def test_a_words_list_is_read_as_the_kernel_reads_it(tmp_path):
    words = tmp_path / "words.txt"
    words.write_text("furnace = boiler\n")
    words.chmod(0o600)
    box, _ = a_box(tmp_path, words)
    seal(box, tmp_path, "boiler serviced")
    qs = questions(tmp_path, "furnace serviced")
    assert sweep_cmd(box, "--questions", str(qs)).returncode == 42
    seal(box, tmp_path, "furnace serviced")
    got = sweep_cmd(box, "--questions", str(qs), "--sizes", "500")
    assert got.returncode == 0 and "  500  1 of 1" in got.stdout, got
    words.chmod(0o644)
    got = sweep_cmd(box, "--questions", str(qs))
    assert got.returncode == 2 and "chmod 600" in got.stderr


def test_a_bad_command_line_or_a_broken_record_is_refused(tmp_path):
    box, _ = a_box(tmp_path)
    qs = questions(tmp_path, Q)
    good = ["--box", str(box), "--questions", str(qs)]
    for argv in ([], ["--box", str(box)], ["--questions", str(qs)],
                 [*good, "--stray"], [*good, "--sizes", ""],
                 [*good, "--sizes", "x"], [*good, "--sizes", "10,500"],
                 [*good, "--sizes", "2000000"],
                 ["--box", str(tmp_path), "--questions", str(qs)],
                 ["--box", str(box), "--questions", str(tmp_path / "none")]):  # fmt: skip
        got = subprocess.run([sys.executable, str(PSW), *argv],
                             capture_output=True, text=True)  # fmt: skip
        assert got.returncode == 2 and got.stdout == "", (argv, got.stdout)
    assert (
        "pile_sweep.py"
        in subprocess.run(
            [sys.executable, str(PSW)], capture_output=True, text=True
        ).stderr
    )
    record = box / "record.jsonl"
    record.write_text(record.read_text().replace('"boot"', '"btoo"', 1))
    assert sweep_cmd(box, "--questions", str(qs)).returncode == 2


def test_without_sizes_it_sweeps_the_documented_five(tmp_path):
    box, _ = a_box(tmp_path)
    seal(box, tmp_path, Q)
    got = sweep_cmd(box, "--questions", str(questions(tmp_path, Q)))
    assert got.returncode == 0, got.stderr
    rows = [line.split()[0] for line in got.stdout.splitlines()[2:-1]]
    assert rows == ["200", "350", "500", "800", "1200"]
    assert "--sizes 200,350,500,800,1200" in pile_sweep.__doc__
