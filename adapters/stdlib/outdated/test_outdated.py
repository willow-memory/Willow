"""outdated: ages each locked dependency from a downloaded registry index and
flags the yanked, deprecated and long-unmaintained; repeatable with --now;
refuses, never crashes, on a bad command line; and writes nothing."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "outdated.py"
NOW = ["--now", "2026-10-24"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(OUT), *argv], capture_output=True, text=True
    )


def idx(root: Path, eco: str, name: str, doc: dict) -> None:
    p = root / eco / f"{name}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc), encoding="utf-8")


def npm_doc(latest, times, deprecated=None):
    versions = {
        v: ({"deprecated": deprecated} if v == latest and deprecated else {})
        for v in times
    }
    return {"dist-tags": {"latest": latest}, "time": times, "versions": versions}


def lock(folder: Path, deps: dict[str, str]) -> None:
    pkgs = {f"node_modules/{n}": {"version": v} for n, v in deps.items()}
    (folder).mkdir(parents=True, exist_ok=True)
    (folder / "package-lock.json").write_text(json.dumps({"packages": pkgs}))


def test_age_and_latest_without_a_flag_is_clean(tmp_path):
    db, src = tmp_path / "db", tmp_path / "src"
    idx(
        db,
        "npm",
        "lodash",
        npm_doc(
            "4.17.21",
            {"4.17.21": "2021-02-20T00:00:00Z", "4.17.4": "2017-02-20T00:00:00Z"},
        ),
    )
    lock(
        src, {"lodash": "4.17.21"}
    )  # on the latest, released < 2y before --now? no: 2021
    got = run("--from", str(src), "--index", str(db), *NOW)
    # released 2021-02, latest release 2021-02: >2y before 2026-10 -> stale -> 42
    assert got.returncode == 42, got.stdout + got.stderr
    assert "lodash 4.17.21" in got.stdout and "released 2021-02-20" in got.stdout
    assert "no release in" in got.stdout


def test_a_fresh_maintained_package_is_not_flagged(tmp_path):
    db, src = tmp_path / "db", tmp_path / "src"
    idx(
        db,
        "npm",
        "lodash",
        npm_doc(
            "4.18.0",
            {"4.17.4": "2017-02-20T00:00:00Z", "4.18.0": "2026-06-01T00:00:00Z"},
        ),
    )
    lock(src, {"lodash": "4.17.4"})  # old locked version, but project still releasing
    got = run("--from", str(src), "--index", str(db), *NOW)
    assert got.returncode == 0, got.stdout + got.stderr
    assert "released 2017-02-20" in got.stdout and "latest 4.18.0" in got.stdout
    assert "need attention" in got.stdout and "0 of 1" in got.stdout


def test_pypi_yanked_is_flagged(tmp_path):
    db, src = tmp_path / "db", tmp_path / "src"
    idx(
        db,
        "PyPI",
        "demo-pkg",
        {
            "info": {"version": "1.0.1"},
            "releases": {
                "1.0.0": [
                    {"upload_time_iso_8601": "2024-01-01T00:00:00Z", "yanked": True}
                ],
                "1.0.1": [
                    {"upload_time_iso_8601": "2024-02-01T00:00:00Z", "yanked": False}
                ],
            },
        },
    )
    (src).mkdir()
    (src / "requirements.txt").write_text("demo-pkg==1.0.0\n")
    got = run("--from", str(src), "--index", str(db), *NOW)
    assert got.returncode == 42, got.stdout + got.stderr
    assert "yanked" in got.stdout and "1 of 1" in got.stdout


def test_npm_deprecated_is_flagged(tmp_path):
    db, src = tmp_path / "db", tmp_path / "src"
    idx(
        db,
        "npm",
        "old-pkg",
        npm_doc(
            "2.0.0", {"2.0.0": "2026-09-01T00:00:00Z"}, deprecated="use new-pkg instead"
        ),
    )
    lock(src, {"old-pkg": "2.0.0"})
    got = run("--from", str(src), "--index", str(db), *NOW)
    assert got.returncode == 42, got.stdout + got.stderr
    assert "deprecated: use new-pkg instead" in got.stdout


def test_crates_yanked_and_stale(tmp_path):
    db, src = tmp_path / "db", tmp_path / "src"
    idx(
        db,
        "crates.io",
        "oldcrate",
        {
            "crate": {"max_stable_version": "1.2.0"},
            "versions": [
                {"num": "1.0.0", "created_at": "2019-01-01T00:00:00Z", "yanked": True},
                {"num": "1.2.0", "created_at": "2020-01-01T00:00:00Z", "yanked": False},
            ],
        },
    )
    (src).mkdir()
    (src / "Cargo.lock").write_text(
        '[[package]]\nname = "oldcrate"\nversion = "1.0.0"\n'
    )
    got = run("--from", str(src), "--index", str(db), *NOW)
    assert got.returncode == 42, got.stdout + got.stderr
    assert "oldcrate 1.0.0" in got.stdout and "no release in" in got.stdout


def test_the_stale_line_is_exactly_two_years(tmp_path):
    from datetime import date, timedelta

    now = date(2026, 10, 24)
    just_over = (
        now - timedelta(days=731)
    ).isoformat() + "T00:00:00Z"  # >= 730 -> stale
    just_under = (
        now - timedelta(days=729)
    ).isoformat() + "T00:00:00Z"  # < 730 -> fresh
    for stamp, stale in ((just_over, True), (just_under, False)):
        db, src = tmp_path / f"db{stale}", tmp_path / f"src{stale}"
        idx(db, "npm", "p", npm_doc("1.0.0", {"1.0.0": stamp}))
        lock(src, {"p": "1.0.0"})
        got = run("--from", str(src), "--index", str(db), *NOW)
        assert got.returncode == (42 if stale else 0), (stamp, got.stdout)
        assert ("no release in" in got.stdout) == stale, (stamp, got.stdout)


def test_npm_time_meta_keys_are_not_counted_as_releases(tmp_path):
    # `created` and `modified` are not versions; a recent `modified` must not
    # make a package whose last real release was years ago look fresh
    db, src = tmp_path / "db", tmp_path / "src"
    idx(db, "npm", "p", {"dist-tags": {"latest": "1.0.0"}, "versions": {"1.0.0": {}},
        "time": {"created": "2019-01-01T00:00:00Z", "1.0.0": "2020-01-01T00:00:00Z",
                 "modified": "2026-06-01T00:00:00Z"}})  # fmt: skip
    lock(src, {"p": "1.0.0"})
    got = run("--from", str(src), "--index", str(db), *NOW)
    assert got.returncode == 42 and "no release in" in got.stdout, got.stdout


def test_an_unknown_version_is_said_not_judged(tmp_path):
    db, src = tmp_path / "db", tmp_path / "src"
    idx(db, "npm", "lodash", npm_doc("4.18.0", {"4.18.0": "2026-06-01T00:00:00Z"}))
    lock(src, {"lodash": "9.9.9"})  # a version the index doesn't have
    got = run("--from", str(src), "--index", str(db), *NOW)
    assert got.returncode == 0, got.stdout + got.stderr
    assert "not found in the registry index" in got.stdout


def test_now_must_be_a_date(tmp_path):
    (tmp_path / "s").mkdir()
    got = run("--from", str(tmp_path / "s"), "--now", "last-tuesday")
    assert got.returncode == 2 and got.stderr.startswith("refused")


def test_without_an_index_it_lists_dependencies(tmp_path):
    src = tmp_path / "src"
    lock(src, {"a": "1.0.0", "b": "2.0.0"})
    got = run("--from", str(src))
    assert got.returncode == 0 and "2 locked dependencies" in got.stdout


def test_no_lockfiles_is_clean(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "notes.md").write_text("tomatoes\n")
    got = run("--from", str(src), "--index", str(tmp_path))
    assert got.returncode == 0 and "No lockfiles found" in got.stdout


def test_it_writes_nothing(tmp_path):
    db, src = tmp_path / "db", tmp_path / "src"
    idx(db, "npm", "lodash", npm_doc("4.17.21", {"4.17.21": "2021-02-20T00:00:00Z"}))
    lock(src, {"lodash": "4.17.21"})
    before = {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}
    run("--from", str(src), "--index", str(db), *NOW)
    assert {p: p.read_bytes() for p in src.rglob("*") if p.is_file()} == before


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    for argv in ([], ["--from", "x", "--extra"], ["--box", "b", "--from", "c"]):
        got = run(*argv)
        assert got.returncode == 2 and "outdated.py" in got.stderr, (argv, got.stderr)


def test_a_bad_target_is_refused(tmp_path):
    (tmp_path / "f").mkdir()
    for argv in (["--from", str(tmp_path / "missing")],
                 ["--from", str(tmp_path / "f"), "--index", str(tmp_path / "nope")],
                 ["--box", str(tmp_path / "f")]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and got.stderr.startswith("refused"), (
            argv,
            got.stderr,
        )
