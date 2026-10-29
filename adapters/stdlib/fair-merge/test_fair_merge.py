"""fair-merge: each source ranked on its own and the lists dealt out in turns,
so a large source can't crowd a small one out; a source with nothing says so;
the echo of the question is no answer; --from takes folders, --box takes the
pile's folders; nothing is written; a bad command line is refused."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "fair_merge.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]


def pile(tmp_path: Path) -> Path:
    p = tmp_path / "pile"
    (p / "logs").mkdir(parents=True)
    (p / "notes").mkdir()
    (p / "archive").mkdir()
    (p / "logs" / "syslog").write_text(
        "\n\n".join(f"frost-check cron {i} ran frost" for i in range(30))
    )
    (p / "notes" / "garden.md").write_text(
        "Frost is due the first week of November.\n\nThe frost took the beans.\n"
    )
    (p / "archive" / "old.txt").write_text("Nothing about weather.\n")
    (p / "loose.txt").write_text("A frost warning came by post.\n")
    return p


def box(tmp_path: Path, p: Path) -> Path:
    b = tmp_path / "box"
    subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "init",
            "--box",
            str(b),
            "--pile",
            str(p),
            "--key",
            str(tmp_path / "k"),
            *NOW,
        ],
        check=True,
        capture_output=True,
    )
    return b


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def places(out: str) -> list[str]:
    return [line.split()[1] for line in out.splitlines() if line[:1].isdigit()]


def test_sources_take_turns_so_the_large_one_cannot_crowd_out_the_small(tmp_path):
    got = run("--box", str(box(tmp_path, pile(tmp_path))), "frost")
    assert got.returncode == 0, got.stderr
    assert [r.split(".")[0] for r in got.stdout.splitlines()[:6]] == list("123456")
    assert places(got.stdout) == [
        "loose.txt:1",
        "logs/syslog:1",
        "notes/garden.md:1",
        "logs/syslog:3",
        "notes/garden.md:3",
        "logs/syslog:5",
    ]


def test_a_source_that_found_nothing_says_so_and_more_held_is_counted(tmp_path):
    got = run("--box", str(box(tmp_path, pile(tmp_path))), "--top", "3", "frost")
    assert "archive: found nothing" in got.stdout
    assert "logs: 2 more that held it, not shown" in got.stdout
    assert "notes: 1 more that held it, not shown" in got.stdout


def test_the_top_shows_that_many(tmp_path):
    b = box(tmp_path, pile(tmp_path))
    assert len(places(run("--box", str(b), "--top", "2", "frost").stdout)) == 2
    assert (
        len(places(run("--box", str(b), "--top", "20", "frost").stdout)) == 6
    )  # the most any source holds is three


def test_from_takes_folders_in_the_order_given(tmp_path):
    p = pile(tmp_path)
    got = run(
        "--from", str(p / "notes"), "--from", str(p / "logs"), "--top", "3", "frost"
    )
    assert got.returncode == 0
    assert places(got.stdout) == [
        "notes/garden.md:1",
        "logs/syslog:1",
        "notes/garden.md:3",
    ]
    flipped = run(
        "--from", str(p / "logs"), "--from", str(p / "notes"), "--top", "2", "frost"
    )
    assert places(flipped.stdout) == ["logs/syslog:1", "notes/garden.md:1"]


def test_each_source_is_ranked_on_its_own_not_across_them(tmp_path):
    p = tmp_path / "p"
    (p / "a").mkdir(parents=True)
    (p / "b").mkdir()
    (p / "a" / "x.txt").write_text("frost beans\n\nfrost\n")
    (p / "b" / "y.txt").write_text("beans\n\nfrost beans compost\n")
    got = run("--from", str(p / "a"), "--from", str(p / "b"), "frost beans")
    assert places(got.stdout)[0] == "a/x.txt:1" and places(got.stdout)[1].startswith(
        "b/y.txt"
    )


def test_nothing_held_waits_on_you_and_says_which_sources_found_nothing(tmp_path):
    got = run("--box", str(box(tmp_path, pile(tmp_path))), "zebra giraffe")
    assert got.returncode == 42
    assert (
        "logs: found nothing" in got.stdout
        and "notes: found nothing" in got.stdout
        and "archive: found nothing" in got.stdout
    )


def test_the_question_asked_back_is_not_an_answer(tmp_path):
    p = tmp_path / "p"
    (p / "a").mkdir(parents=True)
    (p / "a" / "q.txt").write_text("when does the frost come\n")
    got = run("--from", str(p / "a"), "when does the frost come")
    assert got.returncode == 42 and "a: found nothing" in got.stdout


def test_a_long_passage_is_cut_short(tmp_path):
    p = tmp_path / "p"
    (p / "a").mkdir(parents=True)
    (p / "a" / "t.txt").write_text("frost " + "word " * 40)
    line = run("--from", str(p / "a"), "frost").stdout.splitlines()[0]
    assert line.endswith("…") and len(line.split("    ")[-1]) == 90


def test_it_writes_nothing_not_even_a_record_row(tmp_path):
    b = box(tmp_path, pile(tmp_path))
    before = {q: q.read_bytes() for q in tmp_path.rglob("*") if q.is_file()}
    run("--box", str(b), "frost")
    assert {q: q.read_bytes() for q in tmp_path.rglob("*") if q.is_file()} == before


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    p = pile(tmp_path)
    b = box(tmp_path, p)
    for argv in ([], ["frost"], ["--box", str(b)], ["--box", str(b), "--from", str(p), "frost"], ["--box", str(b), "frost", "x"],
                 ["--box", str(b), "--top", "0", "frost"], ["--box", str(b), "--top", "x", "frost"], ["--from", "", "frost"],
                 ["--from", str(p / "missing"), "frost"], ["--box", str(tmp_path), "frost"], ["--box", "", "frost"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2, argv
    assert "fair_merge.py" in run().stderr
