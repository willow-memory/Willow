"""ci-logs: a CI run log as its failing steps; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "ci_logs.py"
spec = importlib.util.spec_from_file_location("ci_logs", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b"2026-10-29T03:28:14.1000000Z ##[group]Run actions/checkout@v7\n2026-10-29T03:28:14.2000000Z with:\n2026-10-29T03:28:14.3000000Z ##[endgroup]\n"
    b"2026-10-29T03:28:15.0000000Z ##[group]Run pytest\n2026-10-29T03:28:15.5000000Z \x1b[31mFAILED\x1b[0m tests/test_garden.py::test_sun - assert 5 == 6\n"
    b"2026-10-29T03:28:16.0000000Z ===== 1 failed, 40 passed in 2.31s =====\n2026-10-29T03:28:17.0000000Z ##[error]Process completed with exit code 1.\n"
    b"2026-10-29T03:28:18.0000000Z Post job cleanup.\n"
)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def mirror_of(
    tmp_path: Path, files: dict[str, bytes]
) -> tuple[subprocess.CompletedProcess, Path]:
    src = tmp_path / "src"
    for rel, data in files.items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_bytes(data)
    out = tmp_path / "out"
    return run("mirror", "--from", str(src), "--to", str(out)), out


def test_a_github_log_gives_each_failing_step_its_name_time_last_lines_and_error():
    assert mod.convert(SAMPLE) == (
        "failed step: Run pytest (2026-10-29 03:28)\n"
        "  FAILED tests/test_garden.py::test_sun - assert 5 == 6\n"
        "  ===== 1 failed, 40 passed in 2.31s =====\n"
        "  ##[error]Process completed with exit code 1.\n"
    )


def test_only_the_last_fifteen_lines_before_the_error_are_kept():
    lines = "".join(f"2026-10-29T03:28:{i % 60:02d}.0Z line {i}\n" for i in range(40))
    out = mod.convert(
        (
            "2026-10-29T03:28:00.0Z ##[group]Build\n"
            + lines
            + "2026-10-29T03:29:00.0Z ##[error]boom\n"
        ).encode()
    )
    body = out.splitlines()[1:]
    assert (
        len(body) == mod.KEEP + 1
        and body[0] == "  line 25"
        and body[-2] == "  line 39"
        and body[-1] == "  ##[error]boom"
    )


def test_gh_run_view_log_failed_names_the_step_on_every_line():
    log = b"build\tRun pytest\t2026-10-29T03:28:15.5000000Z FAILED test_sun\nbuild\tRun pytest\t2026-10-29T03:28:17.0000000Z ##[error]Process completed with exit code 1.\n"
    assert (
        mod.convert(log)
        == "failed step: Run pytest (2026-10-29 03:28)\n  FAILED test_sun\n  ##[error]Process completed with exit code 1.\n"
    )


def test_a_gitlab_log_gives_each_failing_section():
    log = (
        b"Running with gitlab-runner 16.0\nsection_start:1710000000:step_script\r\x1b[0K\x1b[36;1mRunning script\x1b[0;m\n$ pytest\nFAILED test_sun\n"
        b"section_end:1710000100:step_script\r\x1b[0K\x1b[31;1mERROR: Job failed: exit code 1\x1b[0;m\n"
    )
    assert (
        mod.convert(log)
        == "failed step: step_script\n  Running script\n  $ pytest\n  FAILED test_sun\n  ERROR: Job failed: exit code 1\n"
    )


def test_a_gitlab_log_is_known_by_either_its_sections_or_its_runner_line():
    only_sections = (
        b"section_start:1:build\r\x1b[0K$ make\nERROR: Job failed: exit code 2\n"
    )
    assert (
        mod.convert(only_sections)
        == "failed step: build\n  $ make\n  ERROR: Job failed: exit code 2\n"
    )
    only_runner = (
        b"Running with gitlab-runner 16.0\n$ make\nERROR: Job failed: exit code 2\n"
    )
    assert (
        mod.convert(only_runner)
        == "failed step: (job)\n  Running with gitlab-runner 16.0\n  $ make\n  ERROR: Job failed: exit code 2\n"
    )


def test_an_error_outside_a_step_is_the_jobs_and_a_passing_or_unknown_log_is_not_a_result():
    out = mod.convert(
        b"2026-10-29T03:28:17.0Z ##[error]The runner lost contact\n2026-10-29T03:28:18.0Z ok\n"
    )
    assert (
        out
        == "failed step: (job) (2026-10-29 03:28)\n  ##[error]The runner lost contact\n"
    )
    passing = b"2026-10-29T03:28:14.0Z ##[group]Run tests\n2026-10-29T03:28:15.0Z all good\n2026-10-29T03:28:16.0Z ##[endgroup]\n"
    for other in (
        passing,
        b"",
        b"just some text\nwith lines\n",
        b"Running with gitlab-runner 16\nall good\n",
    ):
        assert mod.convert(other) is None, other


def test_a_log_that_is_not_a_ci_log_or_has_no_failure_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "run.log": SAMPLE,
            "notes.txt": b"nothing here\n",
            "pass.log": b"2026-10-29T03:28:14.0Z ok\n2026-10-29T03:28:15.0Z fine\n",
        },
    )
    assert "wrote 1 files" in got.stdout and "skipped 2" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"logs/run.log": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "logs/run.log.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {"logs/run.log": SAMPLE, ".hid/logs/run.log": SAMPLE, ".logs/run.log": SAMPLE},
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["logs/run.log.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"logs/run.log": SAMPLE})
    before = (tmp_path / "src" / "logs/run.log").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "logs/run.log.txt").read_bytes() == (
        out / "logs/run.log.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "logs/run.log").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path, {"good.log": SAMPLE, "bad.log": b"\xff\xfe\x00 not a log"}
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.log.txt").is_file() and not (out / "bad.log.txt").exists()


def test_a_folder_with_nothing_to_read_waits_on_you(tmp_path):
    got, _ = mirror_of(tmp_path, {"notes.md": b"nothing here\n"})
    assert got.returncode == 42 and "wrote 0 files" in got.stdout


def test_a_mirror_inside_the_folder_or_the_folder_inside_it_is_refused(tmp_path):
    (tmp_path / "src").mkdir()
    for to in (tmp_path / "src" / "m", tmp_path):
        got = run("mirror", "--from", str(tmp_path / "src"), "--to", str(to))
        assert got.returncode == 2 and got.stderr.startswith("refused")
    assert (
        run(
            "mirror", "--from", str(tmp_path / "missing"), "--to", str(tmp_path / "m")
        ).returncode
        == 2
    )


def test_a_bad_command_line_says_how_to_run_it():
    for argv in (
        [],
        ["mirror"],
        ["mirror", "--from", "a"],
        ["nope", "--from", "a", "--to", "b"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "ci_logs.py" in got.stderr
