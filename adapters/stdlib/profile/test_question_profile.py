"""profile: how long reading the folder and ranking took, and the functions the
time went to, biggest own time first; the kernel's version and release named;
--top and --repeat; nothing written, not even a record row, and no word of the
question printed; a words list that doesn't read, or a bad command line, refused."""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "question_profile.py"
KERNEL = HERE.parents[2] / "kernel.py"
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

spec = importlib.util.spec_from_file_location("question_profile", SCRIPT)
qp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qp)
NOW = ["--now", "2026-10-24T00:00:00Z"]


def box(tmp_path: Path, words: str | None = None) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.txt").write_text(
        "Tomatoes want six hours of sun.\n\nFrost came early on 2026-10-02.\n"
    )
    (pile / "bins.txt").write_text("Bins go out on Thursday night.\n")
    b = tmp_path / "box"
    argv = [
        sys.executable,
        str(KERNEL),
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    ]
    if words is not None:
        (tmp_path / "w.txt").write_text(words)
        (tmp_path / "w.txt").chmod(0o600)
        argv += ["--words", str(tmp_path / "w.txt")]
    subprocess.run(argv, check=True, capture_output=True)
    return b


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def test_it_names_the_kernel_the_folder_the_two_steps_and_the_biggest_functions(
    tmp_path,
):
    got = run(
        "--box", str(box(tmp_path)), "--top", "5", "how much sun do tomatoes want"
    )
    assert got.returncode == 0, got.stderr
    lines = got.stdout.splitlines()
    assert re.fullmatch(
        rf"kernel {kernel.VERSION[:12]}, release (v\d+\.\d+\.\d+|unreleased)", lines[0]
    )
    assert lines[1] == "folder: 3 passages from 2 files; the question has 6 words"
    assert re.fullmatch(r"read and cut the folder\s+\d+\.\d{3} s", lines[2])
    assert re.fullmatch(r"rank\s+\d+\.\d{3} s", lines[3])
    assert lines[4] == "own time, the 5 biggest" and "function" in lines[5]
    assert len(lines) == 6 + 5


def test_the_functions_are_listed_biggest_own_time_first_and_are_the_kernels(tmp_path):
    rows = run(
        "--box", str(box(tmp_path)), "--top", "8", "frost sun bins"
    ).stdout.splitlines()[6:]
    own = [float(r.split()[1]) for r in rows]
    assert own == sorted(own, reverse=True)
    assert all(
        re.match(r"\s*\d+\s+\d+\.\d{3}\s+\d+\.\d{3}\s+\S+:\d+ \S", r) for r in rows
    )
    assert any("kernel.py:" in r for r in rows)


def test_top_and_repeat_are_taken(tmp_path):
    b = box(tmp_path)
    assert len(run("--box", str(b), "--top", "1", "sun").stdout.splitlines()) == 7
    assert run("--box", str(b), "--repeat", "3", "sun").returncode == 0


def test_the_question_s_words_are_not_printed_only_counted(tmp_path):
    out = run("--box", str(box(tmp_path)), "tomatoes frost secretword").stdout
    assert "secretword" not in out and "the question has 3 words" in out


def test_one_file_and_one_word_use_the_singular_where_it_matters(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.txt").write_text("one\n")
    b = tmp_path / "box"
    subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "init",
            "--box",
            str(b),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "k"),
            *NOW,
        ],
        check=True,
        capture_output=True,
    )
    assert "1 passage from 1 file;" in run("--box", str(b), "one").stdout


def test_it_writes_nothing_not_even_a_record_row(tmp_path):
    b = box(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    run("--box", str(b), "how much sun do tomatoes want")
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_a_boxs_words_list_is_used_and_one_that_does_not_read_is_refused(tmp_path):
    assert run("--box", str(box(tmp_path, "sun = sunshine\n")), "sun").returncode == 0
    (tmp_path / "w.txt").write_text("not a list line\n")
    assert run("--box", str(tmp_path / "box"), "sun").returncode == 2


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    b = box(tmp_path)
    for argv in ([], ["--box", str(b)], ["--box", str(b), "a", "b"], ["--box", str(b), "--top", "0", "a"], ["--box", str(b), "--top", "x", "a"],
                 ["--box", str(b), "--repeat", "0", "a"], ["--box", str(tmp_path), "a"], ["--box", str(b), "--stray"]):  # fmt: skip
        assert run(*argv).returncode == 2, argv
    assert "question_profile.py" in run().stderr


def test_the_shortest_of_the_repeats_is_the_one_reported(monkeypatch):
    clock = iter([0.0, 3.0, 10.0, 11.0, 20.0, 22.0])  # three runs of 3, 1 and 2 seconds
    monkeypatch.setattr(qp.time, "perf_counter", lambda: next(clock))
    calls = []
    result, best = qp.timed(lambda: calls.append(1) or len(calls), 3)
    assert best == 1.0 and result == 3 and len(calls) == 3
    clock2 = iter([0.0, 1.0, 5.0, 8.0])  # 1 then 3: the first stays
    monkeypatch.setattr(qp.time, "perf_counter", lambda: next(clock2))
    assert qp.timed(lambda: None, 2)[1] == 1.0
