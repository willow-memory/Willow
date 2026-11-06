"""log-kit: the logs' engine. A spec's words and kinds pick the lines, each
line has its day, and each summary sums up a period its own way."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "log_kit.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-11-06T00:00:00Z"]
spec = importlib.util.spec_from_file_location("log_kit", SCRIPT)
lk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lk)

DIARY = (
    "2026-03-02\nRan 5 km by the river.\nLunch: soup.\n\n"
    "2026-03-03\nran 3 km, slow\nRandom thought.\n\n"
    "2026-04-10 ran 2 km\n"
)


def pile(text: str, name: str = "diary.md") -> list[dict]:
    return [{"path": name, "line": 1, "text": text, "id": "x"}]


def box(tmp_path: Path, files: dict[str, str]) -> Path:
    folder = tmp_path / "pile"
    for rel, text in files.items():
        (folder / rel).parent.mkdir(parents=True, exist_ok=True)
        (folder / rel).write_text(text)
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(folder),
                    "--key", str(tmp_path / "key"), *NOW], check=True, capture_output=True)  # fmt: skip
    return b


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, argv)],
                          capture_output=True, text=True)  # fmt: skip


def km(line: str) -> float | None:
    import re

    m = re.search(r"(\d+(?:\.\d+)?)\s*km\b", line)
    return float(m.group(1)) if m else None


def test_a_line_takes_its_own_date_else_the_one_above_else_its_files():
    got = lk.entries(pile("2026-03-02\nfirst\n2026-03-05 second\nthird\n"))
    assert [(d, n, t) for d, _, n, t in got] == [
        ("20260302", 1, "2026-03-02"), ("20260302", 2, "first"),
        ("20260305", 3, "2026-03-05 second"), ("20260305", 4, "third"),
    ]  # fmt: skip
    assert [d for d, *_ in lk.entries(pile("no date\n", "2026-01-09 notes.md"))] == [
        "20260109"
    ]
    assert lk.entries(pile("no date at all\n", "notes.md")) == []


def test_words_and_kinds_are_whole_and_case_aside():
    assert lk.holds("Ran 5 km", ["ran"]) and not lk.holds("Random thought", ["ran"])
    assert lk.holds("ran-dom", ["dom"]), "a hyphen ends a word"
    assert (
        lk.kind_of("Supper: soup", {"lunch": ["lunch"], "dinner": ["dinner", "supper"]})
        == "dinner"
    )
    assert lk.kind_of("a walk", {"lunch": ["lunch"]}) is None
    found = lk.gather(pile(DIARY), {"words": ["ran"]})
    assert [n for _, _, n, *_ in found] == [2, 6, 9], "Random is not ran"
    kinds = lk.gather(pile(DIARY), {"kinds": {"lunch": ["lunch"]}})
    assert [(n, k) for _, _, n, _, k, _ in kinds] == [(3, "lunch")]
    assert len(lk.gather(pile(DIARY), {})) == 7, "no words or kinds: every dated line"


def test_a_value_that_isnt_there_leaves_the_line_out():
    found = lk.gather(
        pile(DIARY + "2026-04-11 ran, no distance\n"), {"words": ["ran"], "value": km}
    )
    assert [v for *_, v in found] == [5.0, 3.0, 2.0]


def test_periods():
    assert [lk.period("20260302", by) for by in lk.PERIODS] == [
        "2026-03-02", "2026-W10", "2026-03", "2026"]  # fmt: skip
    assert lk.period("20210103", "week") == "2020-W53", "ISO weeks"


def test_totals_lines_and_averages_each_sum_up_a_period():
    found = lk.gather(pile(DIARY), {"words": ["ran"], "value": km})
    assert lk.totals(found, "month", "km") == [
        "2026-03  8 km  2 lines", "2026-04  2 km  1 line", "2 months, 10 km in all"]  # fmt: skip
    assert lk.summary(found, {"summary": "total", "unit": "km"}, "year") == [
        "2026  10 km  3 lines", "1 year, 10 km in all"]  # fmt: skip
    text = lk.lines(
        lk.gather(pile(DIARY), {"words": ["ran"], "kinds": {"far": ["5"]}}), "month"
    )
    assert text == [
        "2026-03",
        "  far  diary.md:2  Ran 5 km by the river.",
        "       diary.md:6  ran 3 km, slow",
        "2026-04",
        "       diary.md:9  2026-04-10 ran 2 km",
        "2 months, 3 lines",
    ]
    assert lk.lines(lk.gather(pile(DIARY), {"words": ["lunch"]}), "day") == [
        "2026-03-02", "  diary.md:3  Lunch: soup.", "1 day, 1 line"]  # fmt: skip
    avg = lk.averages(
        {"20260301": 4.0, "20260302": 8.0, "20260401": 7.0, "20260501": 7.0}, "month"
    )
    assert avg == [
        "2026-03  avg 6.0  2 days  low 4 on 2026-03-01, high 8 on 2026-03-02",
        "2026-04  avg 7.0  1 day  low 7 on 2026-04-01, high 7 on 2026-04-01  up 1.0",
        "2026-05  avg 7.0  1 day  low 7 on 2026-05-01, high 7 on 2026-05-01  same",
        "3 months, 4 days",
    ]
    days = lk.summary(lk.gather(pile("2026-03-01\nx 4\nx 8\n"), {"value": lambda s: float(s[2]) if s.startswith("x") else None}),
                      {"summary": "average"}, "month")  # fmt: skip
    assert days[0].startswith("2026-03  avg 6.0  1 day"), (
        "a day's values are averaged first"
    )


def test_on_its_own_it_is_a_log_of_any_words(tmp_path):
    b = box(tmp_path, {"diary.md": DIARY})
    got = run("--box", b, "--words", "ran, jog", "--by", "year")
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines()[0] == "2026" and got.stdout.endswith(
        "1 year, 3 lines\n"
    )
    got = run("--box", b, "--words", "tide")
    assert (
        got.returncode == 42
        and got.stdout == "No line of your folder holds those words.\n"
    )


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    b = box(tmp_path, {"diary.md": DIARY})
    for argv in ([], ["--box", b], ["--box", b, "--words", ""], ["--box", b, "--words", " , "],
                 ["--box", b, "--words", "ran", "--by", "fortnight"], ["--box", b, "--words", "ran", "x"],
                 ["--box", b, "--words", "ran", "--words", "jog"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "log_kit.py" in got.stderr, argv
    got = run("--box", tmp_path, "--words", "ran")
    assert got.returncode == 2 and got.stderr.startswith("refused: not a kernel box")


def test_the_change_is_of_the_averages_as_shown_to_a_tenth():
    got = lk.averages({"20260301": 6.04, "20260401": 6.06}, "month")
    assert got[1].endswith("  up 0.1"), "6.0 then 6.1, as shown"
