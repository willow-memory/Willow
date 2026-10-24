"""Each test holds one promise in adapters/stdlib/ci-why/README.md.

The logs below are cut from real red runs of `ci.py run` made on purpose
(a command left out of test_contract.py's list, a bogus id in accepted.json,
an unused import and an unformatted line), then put back.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
KERNEL = ROOT / "kernel.py"
SCRIPT = HERE / "ci_why.py"
spec = importlib.util.spec_from_file_location("ci_why", SCRIPT)
ci_why = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci_why)
k = ci_why.kernel
NOW = "2026-10-24T00:00:00Z"

PYTEST_RED = """
── tests:kernel
................                                                         [100%]
16 passed in 2.27s

── tests:adapters
........................................................................ [ 10%]
..............................................F......................... [ 21%]
=================================== FAILURES ===================================
________________ test_every_add_on_a_person_runs_is_listed_here ________________

    def test_every_add_on_a_person_runs_is_listed_here():
        \"\"\"A new add-on with a command line can't slip past these checks.\"\"\"
        run_by_people = {1}
>       assert run_by_people == set(COMMANDS)
E       AssertionError: assert {'again', 'ai...'browse', ...} == {'aider', 'al...alendar', ...}
E
E         Extra items in the left set:
E         'again'
E         Use -v to get more diff

adapters/stdlib/ci/test_contract.py:144: AssertionError
=========================== short test summary info ============================
FAILED adapters/stdlib/ci/test_contract.py::test_every_add_on_a_person_runs_is_listed_here
1 failed, 681 passed, 1 skipped in 128.26s (0:02:08)

── tests:coverage
const-coverage: undeclared 81, a note and not a failure

tests:kernel       satisfied
tests:adapters     failing  (exit 1)
tests:coverage     satisfied
"""

MUTANTS_RED = """
── mutants:again
again: 6 of 6 killed, 0 accepted
  stale 1b9ac0201051: accepted, but no longer made or no longer surviving; take it out of accepted.json

── mutants:backup
backup: 6 of 6 killed, 0 accepted

── mutants:odds
odds: 5 of 6 killed, 0 accepted
  survived 0123456789ab  adapters/stdlib/odds/odds.py:40  compare: n > 0
  couldn't run fedcba987654 (no tests collected)

mutants:again      failing  (exit 2)
mutants:backup     satisfied
mutants:odds       failing  (exit 2)
"""

LINT_RED = """
── lint:check
E402 Module level import not at top of file
   --> adapters/stdlib/dice/dice.py:169:1
    |
167 | if __name__ == "__main__":
168 |     raise SystemExit(main(sys.argv[1:]))
169 | import os
    | ^^^^^^^^^
170 | x=1
    |
help: Move module level imports to top of file

F401 [*] `os` imported but unused
   --> adapters/stdlib/dice/dice.py:169:8
    |
169 | import os
    |        ^^
170 | x=1
    |
help: Remove unused import: `os`
    |
168 |     raise SystemExit(main(sys.argv[1:]))
    - import os
169 | x=1
    |

Found 2 errors.

── lint:format
unformatted: File would be reformatted
   --> adapters/stdlib/dice/dice.py:170:1
    |
169 | import os
    - x=1
170 + 
171 + x = 1
    |

1 file would be reformatted, 262 files already formatted

lint:check         failing  (exit 1)
lint:format        failing  (exit 1)
"""


def cli(*argv: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv], input=stdin or "",
                          capture_output=True, text=True)  # fmt: skip


def log(tmp: Path, text: str, name: str = "run.log") -> str:
    path = tmp / name
    path.write_text(text, encoding="utf-8")
    return str(path)


def record(tmp: Path, states: dict[str, tuple[str, str | None]]) -> str:
    """A real CI record: a kernel box with one ci verdict row per gate."""
    pile, box = tmp / "pile", tmp / "box"
    pile.mkdir()
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), "--pile",
                    str(pile), "--key", str(tmp / "key"), "--now", NOW],
                   check=True, capture_output=True)  # fmt: skip
    for gate, (state, why) in states.items():
        row = {"gate": gate, "state": state, "files_sha256": "0" * 64,
               "said_sha256": "0" * 64, "python": "3.13"}  # fmt: skip
        if why:
            row["why"] = why
        k.append(box, NOW, "verdict", who="ci", **row)
    return str(box / "record.jsonl")


def test_a_pytest_failure_is_the_test_the_line_and_the_assertion(tmp_path):
    got = cli(log(tmp_path, PYTEST_RED))
    assert got.returncode == 0, got.stderr
    out = got.stdout
    assert out.startswith("ci-why: 1 failing (tests:adapters); 1 block found\n")
    assert "adapters/stdlib/ci/test_contract.py::test_every_add_on_a_person_runs_is_listed_here" in out  # fmt: skip
    assert ">       assert run_by_people == set(COMMANDS)" in out
    assert "E         'again'" in out
    assert "adapters/stdlib/ci/test_contract.py:144: AssertionError" in out
    # nothing else: no source around the line, no dots, no timings, no other gate
    assert "def test_every" not in out and '"""' not in out
    assert "100%" not in out and "passed in" not in out
    assert "tests:kernel" not in out and "undeclared" not in out


def test_a_stale_or_surviving_mutant_names_the_line_to_act_on(tmp_path):
    got = cli(log(tmp_path, MUTANTS_RED))
    assert got.returncode == 0, got.stderr
    out = got.stdout
    assert out.startswith("ci-why: 2 failing (mutants:again, mutants:odds); 2 blocks found")  # fmt: skip
    assert "stale 1b9ac0201051: accepted, but no longer made or no longer surviving; take it out of accepted.json" in out  # fmt: skip
    assert "survived 0123456789ab  adapters/stdlib/odds/odds.py:40  compare: n > 0" in out  # fmt: skip
    assert "couldn't run fedcba987654 (no tests collected)" in out
    assert "odds: 5 of 6 killed, 0 accepted" in out
    assert "backup" not in out


def test_ruff_gives_the_rule_the_place_the_line_and_the_format_diff(tmp_path):
    got = cli(log(tmp_path, LINT_RED))
    assert got.returncode == 0, got.stderr
    assert (
        got.stdout
        == """ci-why: 2 failing (lint:check, lint:format); 3 blocks found

── lint:check  failing  (exit 1)
   adapters/stdlib/dice/dice.py:169  E402 Module level import not at top of file
      import os
   adapters/stdlib/dice/dice.py:169  F401 [*] `os` imported but unused
      import os

── lint:format  failing  (exit 1)
   adapters/stdlib/dice/dice.py:170  unformatted: File would be reformatted
      - x=1
      + x = 1
"""
    )


def test_a_line_that_only_looks_like_a_rule_is_not_a_block(tmp_path):
    text = "── lint:check\nE501 is the rule for long lines\nF401"
    assert cli(log(tmp_path, text)).returncode == 42


def test_a_traceback_is_its_last_frame_and_its_error(tmp_path):
    text = (
        "── demo:odile\nTraceback (most recent call last):\n"
        '  File "make_life.py", line 9, in <module>\n    main()\n'
        '  File "make_life.py", line 4, in main\n    return 1 / 0\n'
        "ZeroDivisionError: division by zero\n\ndemo:odile         failing  (exit 1)\n"
    )
    got = cli(log(tmp_path, text))
    assert got.returncode == 0
    assert got.stdout.splitlines()[3:] == [
        "   a traceback",
        '      File "make_life.py", line 4, in main',
        "      return 1 / 0",
        "      ZeroDivisionError: division by zero",
    ]


def test_a_long_assertion_keeps_both_ends_and_says_what_it_left_out(tmp_path):
    es = "".join(f"E   line {i}\n" for i in range(60))
    text = ("── tests:docs\n=== FAILURES ===\n".replace("=== FAILURES ===", "=" * 20 + " FAILURES " + "=" * 20)
            + "_____ test_big _____\n> assert False\n" + es + "x.py:1: AssertionError\n"
            + "\ntests:docs         failing  (exit 1)\n")  # fmt: skip
    out = cli(log(tmp_path, text)).stdout
    got = [x.strip() for x in out.splitlines()[3:]]
    want = ["> assert False", *(f"E   line {i}" for i in range(15)),
            "E   ... 37 E lines left out ...",
            *(f"E   line {i}" for i in range(52, 60)), "x.py:1: AssertionError"]  # fmt: skip
    assert got[1:] == want  # 60 - 15 - 8 = 37, in the middle


def test_many_failing_gates_are_counted_not_listed(tmp_path):
    gates = ["lint:check", "lint:format", "tests:docs", "tests:kernel"]
    text = "".join(f"── {g}\nTraceback (most recent call last):\nValueError: x\n" for g in gates)  # fmt: skip
    text += "".join(f"{g}  failing  (exit 1)\n" for g in gates)
    out = cli(log(tmp_path, text)).stdout
    assert out.startswith("ci-why: 4 failing; 4 blocks found\n")


def test_unreachable_is_not_failing_and_nothing_failed_is_exit_0(tmp_path):
    text = "── ports:java\n\nports:java         unreachable  (javac not on PATH)\ntests:kernel       satisfied\n"  # fmt: skip
    got = cli(log(tmp_path, text))
    assert got.returncode == 0
    assert got.stdout == "ci-why: nothing failed: 0 satisfied, 1 couldn't run (not a failure)\n"  # fmt: skip


def test_the_record_decides_which_gates_failed_and_the_log_is_read_only_there(tmp_path):
    path = log(tmp_path, PYTEST_RED + MUTANTS_RED)
    rec = record(tmp_path, {"tests:kernel": ("satisfied", None),
                            "tests:adapters": ("satisfied", None),
                            "mutants:again": ("failing", "exit 2"),
                            "tests:coverage": ("unreachable", "x")})  # fmt: skip
    got = cli(path, "--record", rec)
    assert got.returncode == 0, got.stderr
    assert got.stdout.startswith("ci-why: 1 failing (mutants:again); 1 block found")
    assert "── mutants:again  failing  (exit 2)" in got.stdout
    assert "test_every_add_on" not in got.stdout, (
        "the record says tests:adapters passed"
    )


def test_a_later_verdict_for_a_gate_replaces_an_earlier_one(tmp_path):
    rec = record(tmp_path, {"lint:check": ("failing", "exit 1")})
    k.append(Path(rec).parent, NOW, "verdict", who="ci", gate="lint:check",
             state="satisfied", files_sha256="0" * 64, said_sha256="0" * 64,
             python="3.13")  # fmt: skip
    got = cli("--record", rec)
    assert got.returncode == 0 and "nothing failed: 1 satisfied" in got.stdout


def test_a_record_alone_names_the_failing_gates_but_has_no_block_to_show(tmp_path):
    rec = record(tmp_path, {"lint:check": ("failing", "exit 1")})
    got = cli("--record", rec)
    assert got.returncode == 42
    assert "lint:check  failing  (exit 1)" in got.stdout
    assert "no log was given" in got.stdout


def test_a_failing_gate_with_no_known_shape_says_so_and_guesses_nothing(tmp_path):
    text = "── demo:hollis\nmade 3 files\nthe planted file is wrong\n\ndemo:hollis        failing  (make_life.py --check: exit 1)\n"  # fmt: skip
    got = cli(log(tmp_path, text))
    assert got.returncode == 42
    assert got.stdout.startswith("ci-why: 1 failing (demo:hollis); 0 blocks found; couldn't find one for 1")  # fmt: skip
    assert "no failure shape this knows; the section's last lines, as printed:" in got.stdout  # fmt: skip
    assert "the planted file is wrong" in got.stdout


def test_a_failing_gate_the_log_has_no_section_for_is_said(tmp_path):
    rec = record(tmp_path, {"lint:check": ("failing", "exit 1")})
    got = cli(log(tmp_path, PYTEST_RED), "--record", rec)
    assert got.returncode == 42
    assert "the log has no section for this gate" in got.stdout


def test_a_raw_job_log_loses_its_stamps_colours_and_markers(tmp_path):
    stamped = (
        "".join(
            f"2026-10-24T08:38:{i % 60:02d}.1234567Z \x1b[31m{line}\x1b[0m\n"
            for i, line in enumerate(PYTEST_RED.splitlines())
        )
        + "2026-10-24T08:39:00.0000000Z ##[error]Process completed with exit code 2.\n"
    )
    got = cli(log(tmp_path, stamped))
    assert got.returncode == 0
    assert got.stdout == cli(log(tmp_path, PYTEST_RED, "b.log")).stdout
    assert "##[error]" not in got.stdout and "2026-10-24" not in got.stdout


def test_a_bare_pytest_log_works_without_any_gate_headers(tmp_path):
    body = PYTEST_RED.split("── tests:adapters\n")[1].split("\n── tests:coverage")[0]
    got = cli(log(tmp_path, body))
    assert got.returncode == 0
    assert got.stdout.startswith("ci-why: 1 failing (log); 1 block found")
    assert "E         'again'" in got.stdout


def test_a_log_that_says_it_passed_is_not_couldnt_find(tmp_path):
    passed = cli(log(tmp_path, "......\n6 passed in 0.10s\n"))
    assert (passed.returncode, passed.stdout) == (0, "ci-why: nothing failed: the log says it passed\n")  # fmt: skip
    nothing = cli(log(tmp_path, "hello\nworld\n", "n.log"))
    assert nothing.returncode == 42
    assert nothing.stdout.startswith("ci-why: couldn't find a failing block")


def test_the_log_comes_from_standard_input_with_a_dash(tmp_path):
    got = cli("-", stdin=LINT_RED)
    assert got.returncode == 0 and got.stdout.startswith("ci-why: 2 failing")


def test_the_same_log_gives_the_same_bytes_and_is_left_alone(tmp_path):
    path = log(tmp_path, PYTEST_RED + MUTANTS_RED + LINT_RED)
    before = Path(path).read_bytes()
    a, b = cli(path), cli(path)
    assert a.stdout == b.stdout and a.stdout
    assert Path(path).read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["run.log"]


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    path = log(tmp_path, PYTEST_RED)
    for argv in ([], [path, "--stray"], [path, "more"], ["--record"], ["--nope"],
                 [path, "--record", path, "--record", path]):  # fmt: skip
        got = cli(*argv)
        assert got.returncode == 2 and "ci_why.py" in got.stderr, (argv, got.stderr)
        assert got.stdout == ""


def test_a_missing_file_or_a_record_that_does_not_verify_is_refused(tmp_path):
    assert cli(str(tmp_path / "nope.log")).returncode == 2
    path = log(tmp_path, PYTEST_RED)
    assert cli(path, "--record", str(tmp_path / "nope.jsonl")).returncode == 2
    rec = Path(record(tmp_path, {"lint:check": ("failing", "exit 1")}))
    rec.write_text(rec.read_text().replace('"failing"', '"satisfied"'), encoding="utf-8")  # fmt: skip
    got = cli(path, "--record", str(rec))
    assert got.returncode == 2 and got.stderr.startswith("refused: the record doesn't verify")  # fmt: skip
    assert got.stdout == ""


def test_an_empty_record_is_not_enough_to_say(tmp_path):
    rec = record(tmp_path, {})
    got = cli("--record", rec)
    assert got.returncode == 42 and "no verdicts" in got.stdout
