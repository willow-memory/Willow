"""slow-tests: each test's time over several runs, the slowest named, and any
that got slower flagged by a fixed rule."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "slow_tests.py"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )


def junit(cases: list[tuple], wrap: bool = False) -> str:
    """cases: (classname, name, seconds[, state]) with state passed|skipped|failed|error."""
    body = ""
    for c in cases:
        cls, name, t = c[:3]
        state = c[3] if len(c) > 3 else "passed"
        inner = {
            "passed": "",
            "skipped": '<skipped type="pytest.skip" message="x"/>',
            "failed": '<failure message="boom">trace</failure>',
            "error": '<error message="boom">trace</error>',
        }[state]
        body += (
            f'<testcase classname="{cls}" name="{name}" time="{t}">{inner}</testcase>'
        )
    suite = f'<testsuite name="pytest" tests="{len(cases)}">{body}</testsuite>'
    return f"<testsuites>{suite}</testsuites>" if wrap else suite


def folder(tmp_path: Path, runs: dict[str, list[tuple]]) -> Path:
    d = tmp_path / "runs"
    d.mkdir()
    for name, cases in runs.items():
        (d / f"{name}.xml").write_text(junit(cases))
    return d


def lines(out: str, title: str) -> list[str]:
    """The lines under the heading that starts with `title`, up to the blank line."""
    got, on = [], False
    for ln in out.splitlines():
        if on:
            if not ln.strip():
                break
            got.append(ln)
        elif ln.startswith(title):
            on = True
    return got


def test_no_arguments_or_a_stray_one_is_refused_and_says_how_to_run_it(tmp_path):
    d = folder(tmp_path, {"a": [("m", "t", 1)]})
    for argv in ([], [str(d)], ["--runs", str(d), "--stray", "x"], ["--runs"]):
        got = run(*argv)
        assert got.returncode == 2 and "slow_tests.py" in got.stderr, argv
        assert got.stdout == ""


def test_bad_option_values_are_refused(tmp_path):
    d = folder(tmp_path, {"a": [("m", "t", 1)]})
    for extra in (
        ["--top", "0"],
        ["--top", "x"],
        ["--times", "0.5"],
        ["--times", "nan"],
        ["--seconds", "-1"],
        ["--seconds", "inf"],
    ):
        got = run("--runs", str(d), *extra)
        assert got.returncode == 2 and "slow_tests.py" in got.stderr, extra


def test_a_missing_folder_is_refused_and_an_empty_one_is_42(tmp_path):
    got = run("--runs", str(tmp_path / "nope"))
    assert got.returncode == 2 and got.stderr.startswith("refused"), got.stderr
    empty = tmp_path / "empty"
    empty.mkdir()
    (empty / "garden.md").write_text("Tomatoes want sun.\n")
    (empty / ".hidden.xml").write_text(junit([("m", "t", 1)]))
    got = run("--runs", str(empty))
    assert got.returncode == 42 and "no JUnit XML run" in got.stdout


def test_runs_with_no_tests_in_any_say_so_instead_of_reporting(tmp_path):
    d = folder(tmp_path, {"a": [], "b": []})
    assert run("--runs", str(d)).returncode == 42


def test_a_file_that_is_not_junit_or_has_no_time_is_refused_naming_it(tmp_path):
    d = folder(tmp_path, {"a": [("m", "t", 1)]})
    (d / "b.xml").write_text("not xml at all")
    got = run("--runs", str(d))
    assert got.returncode == 2 and "b.xml" in got.stderr and got.stdout == ""
    (d / "b.xml").write_text(
        '<testsuite><testcase classname="m" name="t"/></testsuite>'
    )
    got = run("--runs", str(d))
    assert got.returncode == 2 and "m::t" in got.stderr
    (d / "b.xml").write_text(
        '<testsuite><testcase classname="m" name="t" time="-2"/></testsuite>'
    )
    assert run("--runs", str(d)).returncode == 2
    (d / "b.xml").write_text(
        '<testsuite><testcase classname="m" name="t" time="nan"/></testsuite>'
    )
    assert run("--runs", str(d)).returncode == 2


def test_the_slowest_come_first_by_time_then_name_with_times_to_two_places(tmp_path):
    d = folder(
        tmp_path,
        {
            "a": [
                ("m", "t_b", 2.0),
                ("m", "t_a", 2.0),
                ("m", "t_c", 9.456),
                ("m", "t_d", 0.004),
            ]
        },
    )
    got = run("--runs", str(d))
    assert got.returncode == 0, got.stderr
    rows = lines(got.stdout, "Slowest in a")
    assert [r.split()[0] for r in rows] == ["9.46", "2.00", "2.00", "0.00"]
    assert [r.split()[1] for r in rows] == ["m::t_c", "m::t_a", "m::t_b", "m::t_d"]
    assert "no earlier time" in rows[0]
    assert "One run: nothing earlier to compare with." in got.stdout
    assert "SLOWER" not in got.stdout


def test_files_are_added_up_and_ranked(tmp_path):
    d = folder(
        tmp_path,
        {
            "a": [
                ("x.one", "t1", 3),
                ("x.one", "t2", 3),
                ("y.two", "t1", 5),
                ("y.two", "s", 99, "skipped"),
            ]
        },
    )
    rows = lines(run("--runs", str(d)).stdout, "Slowest files")
    assert [r.split() for r in rows] == [["6.00", "x.one"], ["5.00", "y.two"]]


def test_runs_go_by_name_with_numbers_as_numbers_never_by_file_time(tmp_path):
    d = folder(
        tmp_path,
        {
            "run-10": [("m", "t", 30)],
            "run-9": [("m", "t", 3)],
            "run-2": [("m", "t", 3)],
        },
    )
    # written order and file times point the other way
    for i, n in enumerate(("run-10", "run-9", "run-2")):
        os.utime(d / f"{n}.xml", (1000 + i, 1000 + i))
    got = run("--runs", str(d))
    head = [ln.split()[0] for ln in got.stdout.splitlines()[1:4]]
    assert head == ["run-2", "run-9", "run-10"]
    assert "Slowest in run-10" in got.stdout
    assert "m::t  27.00" not in got.stdout
    assert (
        "m::t  30.00 s now, 3.00 s median of 2 earlier  (+27.00 s, 10.0x)" in got.stdout
    )


def test_a_test_slower_by_the_rule_is_flagged_with_its_median(tmp_path):
    d = folder(
        tmp_path,
        {
            "r1": [("m", "t", 4), ("m", "u", 4)],
            "r2": [("m", "t", 6), ("m", "u", 4)],
            "r3": [("m", "t", 5), ("m", "u", 4)],
            "r4": [("m", "t", 12.5), ("m", "u", 4.2)],
        },
    )
    got = run("--runs", str(d))
    assert lines(got.stdout, "SLOWER") == [
        "  m::t  12.50 s now, 5.00 s median of 3 earlier  (+7.50 s, 2.5x)"
    ]


def test_the_rule_needs_both_more_times_and_more_seconds_and_exactly_on_it_is_not_enough(
    tmp_path,
):
    for latest, flagged in (
        (10.01, True),
        (10.0, False),  # exactly 2x over 5 s: not more than 2x
        (0.5, False),  # 10x over 0.05 s but under a second more
        (1.05, False),  # exactly 1 s over 0.05: not more than 1 s
        (1.06, True),
    ):
        base = 0.05 if latest < 2 else 5
        sub = tmp_path / f"c{latest}"
        sub.mkdir()
        d = folder(sub, {"r1": [("m", "t", base)], "r2": [("m", "t", latest)]})
        got = run("--runs", str(d))
        assert ("m::t" in "".join(lines(got.stdout, "SLOWER"))) is flagged, (
            latest,
            got.stdout,
        )


def test_the_rule_can_be_moved_from_the_command_line(tmp_path):
    d = folder(tmp_path, {"r1": [("m", "t", 5)], "r2": [("m", "t", 8)]})
    assert lines(run("--runs", str(d)).stdout, "SLOWER")[0].strip() == "none"
    got = run("--runs", str(d), "--times", "1.5", "--seconds", "2")
    assert "m::t" in lines(got.stdout, "SLOWER")[0]
    got = run("--runs", str(d), "--times", "1.5", "--seconds", "3")
    assert lines(got.stdout, "SLOWER")[0].strip() == "none"
    assert "more than 1.5x and 3 s" in got.stdout


def test_the_median_not_the_one_slow_earlier_run_is_the_yardstick(tmp_path):
    d = folder(
        tmp_path,
        {
            "r1": [("m", "t", 2)],
            "r2": [("m", "t", 40)],  # one bad earlier run
            "r3": [("m", "t", 2)],
            "r4": [("m", "t", 10)],
        },
    )
    assert "m::t" in lines(run("--runs", str(d)).stdout, "SLOWER")[0]


def test_a_test_missing_from_this_run_is_said_with_when_it_last_passed(tmp_path):
    d = folder(
        tmp_path,
        {
            "r1": [("m", "gone", 7), ("m", "keep", 1)],
            "r2": [("m", "gone", 8), ("m", "keep", 1)],
            "r3": [("m", "keep", 1), ("m", "new", 2)],
        },
    )
    got = run("--runs", str(d))
    assert lines(got.stdout, "NOT RUN") == [
        "  m::gone  not in this run; last passed in r2 at 8.00 s"
    ]
    assert "(1 passed with no earlier pass, so not compared)" in got.stdout


def test_a_skipped_test_is_not_fast_and_not_ranked_and_says_so(tmp_path):
    d = folder(
        tmp_path,
        {
            "r1": [("m", "t", 30), ("m", "u", 1)],
            "r2": [("m", "t", 0.01, "skipped"), ("m", "u", 1)],
        },
    )
    got = run("--runs", str(d))
    assert lines(got.stdout, "NOT RUN") == [
        "  m::t  skipped; last passed in r1 at 30.00 s"
    ]
    assert [r.split()[1] for r in lines(got.stdout, "Slowest in r2")] == ["m::u"]
    assert "skipped 1" in got.stdout


def test_a_failed_test_is_listed_and_its_time_is_not_a_time(tmp_path):
    d = folder(
        tmp_path,
        {
            "r1": [("m", "t", 3), ("m", "u", 3)],
            "r2": [("m", "t", 90, "failed"), ("m", "u", 0.1, "error")],
            "r3": [("m", "t", 3.5), ("m", "u", 3)],
        },
    )
    got = run("--runs", str(d))
    assert "failed 0" in got.stdout.splitlines()[3]  # r3
    assert "failed 2" in got.stdout.splitlines()[2]  # r2
    # r2's 90 s failure is not in t's yardstick: median of r1 only
    assert "m::t  3.50 s" not in got.stdout and lines(got.stdout, "SLOWER") == [
        "  none"
    ]
    (tmp_path / "x").mkdir()
    d2 = folder(
        tmp_path / "x",
        {
            "r1": [("m", "t", 3)],
            "r2": [("m", "t", 1, "failed"), ("m", "k", 1, "error")],
        },
    )
    out = run("--runs", str(d2)).stdout
    assert lines(out, "FAILED") == ["  m::k  error", "  m::t  failed"]
    assert lines(out, "Slowest in r2") == ["  nothing passed in this run"]


def test_the_same_test_twice_in_a_run_adds_its_times_and_keeps_the_worse_state(
    tmp_path,
):
    d = tmp_path / "runs"
    d.mkdir()
    (d / "a.xml").write_text(
        junit([("m", "t", 2), ("m", "t", 3), ("m", "s", 1), ("m", "s", 1, "skipped")])
    )
    got = run("--runs", str(d))
    rows = lines(got.stdout, "Slowest in a")
    assert [r.split()[:2] for r in rows] == [["5.00", "m::t"], ["2.00", "m::s"]]


def test_both_junit_shapes_and_other_files_are_read_as_they_should(tmp_path):
    d = tmp_path / "runs"
    d.mkdir()
    (d / "a.xml").write_text(junit([("m", "t", 1)], wrap=True))
    (d / "b.xml").write_text(junit([("m", "t", 1)]))
    (d / "notes.txt").write_text("<testcase/>")
    (d / ".c.xml").write_text("garbage")
    got = run("--runs", str(d))
    assert got.returncode == 0 and got.stdout.startswith("2 runs, oldest first:")


def test_a_testcase_with_no_class_is_named_by_its_name(tmp_path):
    d = tmp_path / "runs"
    d.mkdir()
    (d / "a.xml").write_text('<testsuite><testcase name="loose" time="1"/></testsuite>')
    rows = lines(run("--runs", str(d)).stdout, "Slowest in a")
    assert rows[0].split() == ["1.00", "loose", "(no", "earlier", "time)"]
    assert lines(run("--runs", str(d)).stdout, "Slowest files") == [
        "       1.00  loose"
    ]


def test_each_list_stops_at_top_and_says_how_many_more(tmp_path):
    cases = [("m", f"t{i}", 10 - i) for i in range(5)]
    d = folder(tmp_path, {"a": cases})
    out = run("--runs", str(d), "--top", "2").stdout
    rows = lines(out, "Slowest in a")
    assert [r.split()[1] for r in rows[:2]] == ["m::t0", "m::t1"]
    assert rows[2].strip() == "... and 3 more (--top shows more)"
    assert len(rows) == 3
    assert len(lines(run("--runs", str(d), "--top", "5").stdout, "Slowest in a")) == 5


def test_same_input_same_bytes_and_it_writes_nothing(tmp_path):
    d = folder(
        tmp_path,
        {
            "r1": [("m", "t", 1.234), ("m", "u", 5)],
            "r2": [("m", "t", 9.876), ("m", "v", 5)],
        },
    )
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in d.iterdir()}
    first, second = run("--runs", str(d)), run("--runs", str(d))
    assert first.stdout == second.stdout and first.returncode == 0
    assert {
        p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in d.iterdir()
    } == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["runs"]
    assert str(tmp_path) not in first.stdout


def test_a_test_twice_in_one_run_keeps_the_worst_state_whichever_came_first(tmp_path):
    cases = []
    for name, first, second in (
        ("pf", "passed", "failed"),
        ("fp", "failed", "passed"),
        ("fe", "failed", "error"),
        ("ef", "error", "failed"),
        ("sp", "skipped", "passed"),
        ("ps", "passed", "skipped"),
    ):
        cases += [("m", name, 1, first), ("m", name, 1, second)]
    d = tmp_path / "runs"
    d.mkdir()
    (d / "a.xml").write_text(junit(cases))
    out = run("--runs", str(d)).stdout
    assert lines(out, "Slowest in a")[0].split()[:2] == ["2.00", "m::ps"]
    assert [r.split()[1] for r in lines(out, "Slowest in a")] == ["m::ps", "m::sp"]


def test_one_more_than_the_cap_is_said_too(tmp_path):
    d = folder(tmp_path, {"a": [("m", "t1", 2), ("m", "t2", 1)]})
    rows = lines(run("--runs", str(d), "--top", "1").stdout, "Slowest in a")
    assert rows[1].strip() == "... and 1 more (--top shows more)"


def test_names_with_numbers_and_words_sort_numbers_first_then_by_text(tmp_path):
    d = folder(
        tmp_path,
        {
            "b": [("m", "t", 1)],
            "10": [("m", "t", 1)],
            "a": [("m", "t", 1)],
            "2": [("m", "t", 1)],
        },
    )
    heads = [ln.split()[0] for ln in run("--runs", str(d)).stdout.splitlines()[1:5]]
    assert heads == ["2", "10", "a", "b"]


def test_the_totals_count_only_passed_time(tmp_path):
    d = folder(
        tmp_path,
        {"a": [("m", "t", 2), ("m", "u", 50, "failed"), ("m", "v", 7, "skipped")]},
    )
    assert "passed time 2.00 s" in run("--runs", str(d)).stdout


def test_ties_in_how_much_slower_and_in_how_long_ago_go_by_name(tmp_path):
    d = folder(
        tmp_path,
        {
            "r1": [("m", "a", 4), ("m", "b", 2), ("m", "g1", 5), ("m", "g2", 5)],
            "r2": [("m", "a", 4), ("m", "b", 2), ("m", "g1", 9), ("m", "g2", 9)],
            "r3": [("m", "a", 9), ("m", "b", 7), ("m", "g2", 9)],
        },
    )
    # r3: a and b are both +5 s, a ending longer; g1 has not passed since r2
    out = run("--runs", str(d), "--seconds", "1").stdout
    rows = lines(out, "SLOWER")
    assert [r.split()[0] for r in rows] == ["m::a", "m::b"]
    assert lines(out, "NOT RUN") == [
        "  m::g1  not in this run; last passed in r2 at 9.00 s"
    ]


def test_a_test_missing_from_a_middle_run_still_counts_where_it_passed(tmp_path):
    d = folder(
        tmp_path,
        {
            "r1": [("m", "t", 2), ("m", "other", 1)],
            "r2": [("m", "other", 1)],
            "r3": [("m", "t", 9), ("m", "other", 1)],
        },
    )
    got = run("--runs", str(d))
    assert got.returncode == 0
    assert "m::t  9.00 s now, 2.00 s median of 1 earlier" in got.stdout


def test_equally_long_gone_tests_go_by_name_not_by_when_they_last_passed(tmp_path):
    d = folder(
        tmp_path,
        {
            "r1": [("m", "b", 3), ("m", "a", 3), ("m", "keep", 1)],
            "r2": [("m", "a", 3), ("m", "keep", 1)],
            "r3": [("m", "keep", 1)],
        },
    )
    got = lines(run("--runs", str(d)).stdout, "NOT RUN")
    assert [r.split()[0] for r in got] == ["m::a", "m::b"]


def test_files_with_equal_totals_go_by_name(tmp_path):
    d = folder(
        tmp_path,
        {
            "a": [
                ("b.m", "t1", 2),
                ("a.m", "t1", 1.5),
                ("a.m", "t2", 1.5),
                ("b.m", "t2", 1),
            ]
        },
    )
    rows = lines(run("--runs", str(d)).stdout, "Slowest files")
    assert [r.split()[1] for r in rows] == ["a.m", "b.m"]
