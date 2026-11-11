"""fair-merge: each source ranked on its own and the lists dealt out in turns,
so a large source can't crowd a small one out; a source with nothing says so;
the echo of the question is no answer; --from takes folders, --box takes the
pile's folders, --index takes scan's indexes and names the words none of
their passages hold; a passage two sources hold is shown once, with both;
nothing is written; a bad command line is refused."""

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


SCAN = HERE.parent / "scan" / "scan.py"


def index(tmp_path: Path, folder: Path, name: str) -> Path:
    to = tmp_path / name
    subprocess.run(
        [sys.executable, str(SCAN), "index", "--from", str(folder), "--to", str(to)],
        capture_output=True,
    )
    return to


def indexes(tmp_path: Path) -> tuple[Path, Path, Path]:
    p = pile(tmp_path)
    return tuple(index(tmp_path, p / n, n + "-ix") for n in ("logs", "notes", "archive"))  # fmt: skip


def test_indexes_take_turns_as_folders_do_in_the_order_given(tmp_path):
    logs, notes, archive = indexes(tmp_path)
    got = run("--index", str(notes), "--index", str(logs), "--index", str(archive), "--top", "3", "frost")  # fmt: skip
    assert got.returncode == 0, got.stderr
    assert places(got.stdout) == [
        "notes-ix/garden.md:1",
        "logs-ix/syslog:1",
        "notes-ix/garden.md:3",
    ]
    assert "[notes-ix]" in got.stdout.splitlines()[0]
    assert "logs-ix: 2 more that held it, not shown" in got.stdout
    p = tmp_path / "pile"
    same = run("--from", str(p / "notes"), "--from", str(p / "logs"), "--top", "3", "frost")  # fmt: skip
    assert [x.split("/", 1)[1] for x in places(same.stdout)] == [
        x.split("/", 1)[1] for x in places(got.stdout)
    ]


def test_an_index_names_the_words_none_of_its_passages_hold(tmp_path):
    logs, notes, archive = indexes(tmp_path)
    got = run("--index", str(notes), "--index", str(archive), "frost violin")
    assert got.returncode == 0
    lines = got.stdout.splitlines()
    assert "archive-ix: found nothing; no passage holds: frost, violin" in lines
    # found, on half the words, and still said to lack the other
    assert "notes-ix: no passage holds: violin" in lines
    whole = run("--index", str(notes), "frost beans")
    assert "no passage holds" not in whole.stdout


def test_an_absent_word_is_held_as_the_kernel_holds_one(tmp_path):
    logs, notes, archive = indexes(tmp_path)
    words = tmp_path / "words.txt"
    words.write_text("rime = frost\n")
    plain = run("--index", str(notes), "rime")
    assert plain.returncode == 42
    assert "notes-ix: found nothing; no passage holds: rime" in plain.stdout
    got = run("--index", str(notes), "--words", str(words), "rime")
    assert got.returncode == 0 and "no passage holds" not in got.stdout
    # a plural is the word: "beans" is held, so "bean" is
    assert "no passage holds" not in run("--index", str(notes), "bean").stdout


def test_a_passage_two_sources_hold_is_shown_once_with_both(tmp_path):
    p = tmp_path / "p"
    for name in ("a", "b"):
        (p / name).mkdir(parents=True)
        (p / name / "x.txt").write_text("Frost is due in November.\n")
    (p / "b" / "y.txt").write_text("The frost took the beans.\n")
    got = run("--from", str(p / "a"), "--from", str(p / "b"), "frost")
    assert places(got.stdout) == ["a/x.txt:1", "b/y.txt:1"]
    assert "[a, b]" in got.stdout.splitlines()[0]
    assert "[b]" in got.stdout.splitlines()[1]
    assert "found nothing" not in got.stdout and "more" not in got.stdout
    ia, ib = index(tmp_path, p / "a", "ia"), index(tmp_path, p / "b", "ib")
    got = run("--index", str(ib), "--index", str(ia), "frost")
    assert len(places(got.stdout)) == 2 and "[ib, ia]" in got.stdout
    assert "ia: found nothing" not in got.stdout  # it found one; ib showed it


def test_what_is_not_an_index_is_refused_and_two_of_one_name(tmp_path):
    logs, notes, archive = indexes(tmp_path)
    p = tmp_path / "pile"
    assert run("--index", str(p / "notes"), "frost").returncode == 2
    assert "not an index" in run("--index", str(p / "notes"), "frost").stderr
    (tmp_path / "other").mkdir()
    twin = index(tmp_path / "other", p / "logs", "notes-ix")
    got = run("--index", str(notes), "--index", str(twin), "frost")
    assert got.returncode == 2 and "same folder name" in got.stderr
    bad = tmp_path / "bad.txt"
    bad.write_text("no equals sign here\n")
    for argv in (["--index", str(notes), "--from", str(p / "logs"), "frost"], ["--index", "", "frost"],
                 ["--from", str(p / "logs"), "--words", str(bad), "frost"], ["--index", str(notes), "--words", "", "frost"],
                 ["--index", str(notes), "--words", str(tmp_path / "missing"), "frost"]):  # fmt: skip
        assert run(*argv).returncode == 2, argv


def test_indexes_are_read_and_nothing_is_written(tmp_path):
    logs, notes, archive = indexes(tmp_path)
    before = {q: q.read_bytes() for q in tmp_path.rglob("*") if q.is_file()}
    run("--index", str(logs), "--index", str(notes), "frost")
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


def test_a_refusal_says_the_first_line_of_how_it_is_run():
    said = run().stderr.strip()
    assert (
        said
        == 'python adapters/stdlib/fair-merge/fair_merge.py --box DIR [--top N] "question"'
    )
    assert run("--top", "0", "frost").stderr.strip() == said
