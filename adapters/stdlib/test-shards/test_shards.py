"""test-shards: every test lands in exactly one part, the split is longest
first and the same every time, a test with no past time is placed and said,
and a suite that can't be learned is refused, not guessed."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("willow_shards", HERE / "shards.py")
sh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sh)


def xml(*cases: tuple[str, str, float], name: str = "past.xml", where: Path) -> str:
    body = "".join(
        f'<testcase classname="{c}" name="{n}" time="{t}"/>' for c, n, t in cases
    )
    p = where / name
    p.write_text(
        f'<?xml version="1.0"?><testsuites><testsuite>{body}</testsuite></testsuites>'
    )
    return str(p)


def ids(where: Path, *lines: str) -> str:
    p = where / "ids.txt"
    p.write_text("\n".join(lines) + "\n\n3 tests collected in 0.01s\n")
    return str(p)


def run(*argv: str, stdin: str | None = None, cwd: Path | None = None):
    return subprocess.run([sys.executable, str(HERE / "shards.py"), *argv], input=stdin,
                          capture_output=True, text=True, cwd=cwd)  # fmt: skip


def test_a_bad_command_line_is_refused_and_names_the_script():
    for argv in ([], ["--shards", "2", "--stray", "more"], ["--shards", "0", "x"]):
        got = run(*argv)
        assert got.returncode == 2 and "shards.py" in got.stderr, argv


@pytest.mark.parametrize(
    "argv",
    [
        ["--shards", "2"],
        ["--shards", "2", "--tests", "a", "x"],
        ["--shards", "two", "x"],
        ["--shards", "2", "--shard", "1/3", "x"],
        ["--shard", "0/3", "x"],
        ["--shard", "4/3", "x"],
        ["--shard", "1-3", "x"],
        ["--shards", "2", "--by", "class", "x"],
        ["--shards", "2", "--default", "soon", "x"],
        ["--shards", "2", "--default", "-1", "x"],
        ["--shards", "2", "--past"],
        ["--past", "nowhere.xml", "--shards", "2", "--tests", "nowhere.txt"],
    ],
)
def test_each_wrong_command_line_is_refused(argv):
    got = run(*argv)
    assert got.returncode == 2 and got.stderr.startswith("refused"), (argv, got.stderr)
    assert got.stdout == ""


def test_the_key_pytest_writes_is_read_from_a_node_id():
    assert sh.key_of("a/b/test_x.py::test_one") == ("a.b.test_x", "test_one")
    assert sh.key_of("t.py::TestC::test_one[a-b]") == ("t.TestC", "test_one[a-b]")
    assert sh.key_of("t.py::TestC::Inner::test[x::y/z]") == (
        "t.TestC.Inner",
        "test[x::y/z]",
    )


def test_ids_are_read_from_collect_output_and_its_other_lines_are_not():
    text = "a/test_x.py::test_1\nb/test_y.py::T::test_2[1 2]\n\n2 tests collected in 0.1s\nERROR x.py\n"
    assert sh.parse_ids(text) == ["a/test_x.py::test_1", "b/test_y.py::T::test_2[1 2]"]


def test_the_longest_goes_first_and_ties_go_to_the_lowest_part():
    got = sh.split({"a": 7, "b": 5, "c": 4, "d": 3, "e": 1}, 2)
    assert got == [["a", "d"], ["b", "c", "e"]]
    assert sh.split({"x": 1, "y": 1, "z": 1}, 2) == [["x", "z"], ["y"]]


def test_the_median_of_nothing_is_one_second():
    assert (
        sh.median([]) == 1000 and sh.median([3, 1, 2]) == 2 and sh.median([1, 4]) == 2
    )
    assert sh.median([5, 1, 4, 2, 3]) == 3 and sh.median([20, 1, 10, 2]) == 6
    assert sh.median([7]) == 7


def test_every_test_lands_in_exactly_one_part(tmp_path):
    names = [f"t{i}.py::test_{j}" for i in range(7) for j in range(3)]
    past = xml(*[(f"t{i}", f"test_{j}", 0.1 * (i + 1)) for i in range(7) for j in range(3)],
               where=tmp_path)  # fmt: skip
    for n in (1, 2, 3, 5, 9):
        placed = []
        for k in range(1, n + 1):
            got = run(
                "--past", past, "--shard", f"{k}/{n}", "--tests", ids(tmp_path, *names)
            )
            assert got.returncode == 0, got.stderr
            placed += got.stdout.split()
        assert sorted(placed) == sorted({n.split("::")[0] for n in names}), n


def test_the_summary_says_each_part_its_time_and_the_spread(tmp_path):
    past = xml(
        ("a", "test_x", 4.0), ("b", "test_x", 3.0), ("c", "test_x", 2.0), where=tmp_path
    )
    got = run("--past", past, "--shards", "2", "--tests",
              ids(tmp_path, "a.py::test_x", "b.py::test_x", "c.py::test_x"))  # fmt: skip
    assert got.returncode == 0, got.stderr
    assert got.stdout == (
        "2 parts, 3 files, 3 tests, expected 9.000 s in all\n"
        "part 1/2  4.000 s  1 files\n"
        "  a.py  4.000 s\n"
        "part 2/2  5.000 s  2 files\n"
        "  b.py  3.000 s\n"
        "  c.py  2.000 s\n"
        "spread: slowest 5.000 s, fastest 4.000 s, 1.000 s apart\n"
        "every test has a past time\n"
        "0 tests in the past run are no longer in the suite, left out\n"
    )


def test_the_same_input_gives_the_same_bytes_whatever_the_order_given(tmp_path):
    names = [f"t{i}.py::test_{j}" for i in range(5) for j in range(4)]
    past = xml(*[(f"t{i}", f"test_{j}", 0.05 * ((i * 7 + j) % 5)) for i in range(5)
                 for j in range(4)], where=tmp_path)  # fmt: skip
    a = run("--past", past, "--shards", "3", "--tests", ids(tmp_path, *names))
    b = run("--past", past, "--shards", "3", "--tests", ids(tmp_path, *reversed(names)))
    assert a.returncode == 0 and a.stdout == b.stdout


def test_a_test_with_no_past_time_is_placed_and_said(tmp_path):
    past = xml(("a", "test_x", 2.0), ("a", "test_y", 4.0), where=tmp_path)
    got = run("--past", past, "--shards", "2", "--tests",
              ids(tmp_path, "a.py::test_x", "a.py::test_y", "b.py::test_new"))  # fmt: skip
    assert got.returncode == 0, got.stderr
    assert (
        "1 tests with no past time, counted as 3.000 s each (the median" in got.stdout
    )
    assert "  b.py  3.000 s  (1 of 1 tests with no past time)" in got.stdout
    assert "  a.py  6.000 s\n" in got.stdout


def test_with_no_past_run_at_all_every_test_counts_one_second(tmp_path):
    got = run(
        "--shards", "2", "--tests", ids(tmp_path, "a.py::t1", "b.py::t2", "b.py::t3")
    )
    assert got.returncode == 0, got.stderr
    assert (
        "3 tests with no past time, counted as 1.000 s each (no test has one"
        in got.stdout
    )
    assert "part 1/2  2.000 s" in got.stdout and "part 2/2  1.000 s" in got.stdout


def test_default_says_what_an_unknown_test_counts_as(tmp_path):
    got = run("--default", "0.5", "--shards", "1", "--tests", ids(tmp_path, "a.py::t1"))
    assert "counted as 0.500 s each (from --default)" in got.stdout


def test_a_test_gone_from_the_suite_is_left_out_and_said(tmp_path):
    past = xml(("a", "test_x", 2.0), ("old", "test_gone", 90.0), where=tmp_path)
    got = run("--past", past, "--shards", "2", "--tests", ids(tmp_path, "a.py::test_x"))
    assert "1 tests in the past run are no longer in the suite, left out" in got.stdout
    assert "expected 2.000 s in all" in got.stdout


def test_more_parts_than_pieces_leaves_some_empty_and_says_so(tmp_path):
    got = run("--shards", "3", "--tests", ids(tmp_path, "a.py::t1"))
    assert got.returncode == 0
    assert "part 2/3  0.000 s  empty: fewer pieces than parts" in got.stdout
    assert run("--shard", "3/3", "--tests", ids(tmp_path, "a.py::t1")).stdout == ""


def test_several_past_runs_are_averaged(tmp_path):
    one = xml(("a", "test_x", 2.0), name="one.xml", where=tmp_path)
    two = xml(("a", "test_x", 4.0), name="two.xml", where=tmp_path)
    got = run("--past", one, "--past", two, "--shards", "1", "--tests",
              ids(tmp_path, "a.py::test_x"))  # fmt: skip
    assert "expected 3.000 s in all" in got.stdout


def test_by_test_splits_inside_a_file_and_lists_only_the_parts(tmp_path):
    past = xml(("a", "test_x", 5.0), ("a", "test_y", 5.0), where=tmp_path)
    names = ids(tmp_path, "a.py::test_x", "a.py::test_y")
    got = run("--past", past, "--shards", "2", "--by", "test", "--tests", names)
    assert got.returncode == 0 and "part 1/2  5.000 s  1 tests" in got.stdout
    assert "spread: slowest 5.000 s, fastest 5.000 s, 0.000 s apart" in got.stdout
    assert "a.py::test_x" not in got.stdout
    one = run("--past", past, "--shard", "2/2", "--by", "test", "--tests", names)
    assert one.stdout == "a.py::test_y\n"


def test_test_ids_with_classes_and_brackets_match_their_past_times(tmp_path):
    past = xml(("pkg.test_m.TestC", "test_p[1-a b]", 8.0), where=tmp_path)
    got = run("--past", past, "--shards", "1", "--tests",
              ids(tmp_path, "pkg/test_m.py::TestC::test_p[1-a b]"))  # fmt: skip
    assert (
        "every test has a past time" in got.stdout and "expected 8.000 s" in got.stdout
    )


def test_the_ids_can_come_on_standard_input():
    got = run("--shards", "1", "--tests", "-", stdin="a.py::t1\n")
    assert got.returncode == 0 and "1 tests" in got.stdout


def test_an_empty_suite_is_42_not_a_split(tmp_path):
    got = run("--shards", "2", "--tests", ids(tmp_path))
    assert got.returncode == 42 and "holds no test" in got.stdout


def test_a_past_file_that_is_not_junit_xml_is_refused_and_named(tmp_path):
    bad = tmp_path / "bad.xml"
    bad.write_text("<testsuites><testcase")
    for past in (str(bad), str(tmp_path / "missing.xml")):
        got = run("--past", past, "--shards", "2", "--tests", ids(tmp_path, "a.py::t"))
        assert got.returncode == 2 and past in got.stderr and got.stdout == ""
    worse = tmp_path / "worse.xml"
    worse.write_text(
        '<testsuite><testcase classname="a" name="t" time="slow"/></testsuite>'
    )
    got = run(
        "--past", str(worse), "--shards", "2", "--tests", ids(tmp_path, "a.py::t")
    )
    assert got.returncode == 2 and "isn't a number" in got.stderr


def test_the_suite_is_learned_by_collecting_and_nothing_is_written(tmp_path):
    suite = tmp_path / "suite"
    (suite / "pkg").mkdir(parents=True)
    (suite / "pkg" / "test_one.py").write_text(
        "import pytest\n\n\n@pytest.mark.parametrize('n', [1, 2])\ndef test_a(n):\n    pass\n"
    )
    (suite / "test_two.py").write_text(
        "class TestC:\n    def test_b(self):\n        pass\n"
    )
    past = xml(("pkg.test_one", "test_a[1]", 1.0), ("pkg.test_one", "test_a[2]", 2.0),
               ("test_two.TestC", "test_b", 4.0), where=tmp_path)  # fmt: skip
    before = sorted(p.relative_to(suite).as_posix() for p in suite.rglob("*"))
    got = run("--past", past, "--shards", "2", "pkg", "test_two.py", cwd=suite)
    assert got.returncode == 0, got.stderr
    assert "part 1/2  4.000 s  1 files\n  test_two.py  4.000 s\n" in got.stdout
    assert "  pkg/test_one.py  3.000 s\n" in got.stdout
    assert "every test has a past time" in got.stdout
    assert sorted(p.relative_to(suite).as_posix() for p in suite.rglob("*")) == before


def test_a_suite_that_fails_to_collect_is_refused_not_guessed(tmp_path):
    (tmp_path / "test_broken.py").write_text("import not_a_module_anywhere\n")
    got = run("--shards", "2", "test_broken.py", cwd=tmp_path)
    assert got.returncode == 2 and "couldn't collect" in got.stderr and got.stdout == ""
    assert got.stderr.count(" | ") == 4, "the last five lines of what pytest said"


def test_no_test_found_by_collecting_is_42(tmp_path):
    (tmp_path / "test_none.py").write_text("x = 1\n")
    got = run("--shards", "2", "test_none.py", cwd=tmp_path)
    assert got.returncode == 42


def test_default_takes_seconds_and_zero_is_allowed(tmp_path):
    names = ids(tmp_path, "a.py::t1")
    assert (
        "counted as 2.000 s each"
        in run("--default", "2", "--shards", "1", "--tests", names).stdout
    )
    got = run("--default", "0", "--shards", "1", "--tests", names)
    assert got.returncode == 0 and "counted as 0.000 s each" in got.stdout


def test_shard_and_shards_may_name_the_same_number_of_parts(tmp_path):
    names = ids(tmp_path, "a.py::t1")
    got = run("--shards", "3", "--shard", "1/3", "--tests", names)
    assert got.returncode == 0 and got.stdout == "a.py\n"
    assert run("--shards", "3", "--shard", "3/3", "--tests", names).stdout == ""


@pytest.mark.parametrize("shard", ["0/3", "4/3", "1-3", "x"])
def test_a_shard_out_of_range_is_refused_for_that_reason(shard, tmp_path):
    got = run("--shard", shard, "--tests", ids(tmp_path, "a.py::t1"))
    assert got.returncode == 2 and "--shard is K/N" in got.stderr
