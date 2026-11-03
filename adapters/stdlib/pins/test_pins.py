"""pins: lists the version ranges your manifests declare that no lockfile pins,
offline; names a manifest it can't read instead of dropping it; refuses, never
crashes, on a bad command line; and writes nothing."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PINS = HERE / "pins.py"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PINS), *argv], capture_output=True, text=True
    )


def rows(got: subprocess.CompletedProcess) -> list[str]:
    """The report's lines with runs of spaces made one, so a column's width
    doesn't matter."""
    return [" ".join(line.split()) for line in got.stdout.splitlines()]


def write(folder: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        p = folder / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def lock(folder: Path, deps: dict[str, str]) -> None:
    pkgs = {f"node_modules/{n}": {"version": v} for n, v in deps.items()}
    write(folder, {"package-lock.json": json.dumps({"packages": pkgs})})


def test_a_range_no_lockfile_pins_is_listed_and_exits_42(tmp_path):
    src = tmp_path / "src"
    write(src, {"package.json": json.dumps({"dependencies": {
        "left-pad": "1.3.0", "lodash": "^4.17.0"}})})  # fmt: skip
    lock(src, {"left-pad": "1.3.0"})  # pins the exact one only
    got = run("--from", str(src))
    assert got.returncode == 42, got.stdout + got.stderr
    assert "npm lodash ^4.17.0" in rows(got)
    assert "left-pad" not in got.stdout  # already exact
    assert "1 of 1 declared ranges have no lockfile pin" in got.stdout


def test_a_lockfile_that_pins_the_range_is_clean(tmp_path):
    src = tmp_path / "src"
    write(src, {"package.json": json.dumps({"dependencies": {"lodash": "^4.17.0"}})})
    lock(src, {"lodash": "4.17.21"})  # the lockfile holds it at a version
    got = run("--from", str(src))
    assert got.returncode == 0, got.stdout + got.stderr
    assert "pins: empty, all 1 declared ranges are pinned by a lockfile" in got.stdout


def test_dev_dependencies_count_and_peer_ones_do_not(tmp_path):
    src = tmp_path / "src"
    write(src, {"package.json": json.dumps({
        "devDependencies": {"jest": "~29.0.0"},
        "peerDependencies": {"react": ">=18"}})})  # fmt: skip
    got = run("--from", str(src))
    assert got.returncode == 42, got.stdout
    assert "npm jest ~29.0.0" in rows(got)
    assert "react" not in got.stdout


def test_what_counts_as_a_range_and_what_is_exact(tmp_path):
    src = tmp_path / "src"
    specs = {
        "exact": "1.2.3",
        "pre": "1.2.3-beta.1",
        "equals": "=1.2.3",
        "partial": "1.2",
        "star": "*",
        "latest": "latest",
        "hyphen": "1.0.0 - 2.0.0",
        "url": "git+https://example.com/x.git",
        "any": "",
    }
    write(src, {"package.json": json.dumps({"dependencies": specs})})
    got = run("--from", str(src))
    assert got.returncode == 42, got.stdout + got.stderr
    listed = {n for n in specs if any(r.startswith(f"npm {n} ") for r in rows(got))}
    assert listed == {"partial", "star", "latest", "hyphen", "url", "any"}, got.stdout
    assert "npm any (any)" in rows(got)


def test_requirements_pins_ranges_and_options(tmp_path):
    src = tmp_path / "src"
    write(
        src,
        {
            "requirements.txt": (
                "# a comment\n"
                "\n"
                "-r base.txt\n"
                "requests==2.19.1  # pinned\n"
                "flask>=2.0\n"
                "requests-oauthlib~=1.3\n"
                "django\n"
                'pytest>=7; python_version >= "3.8"\n'
                "pkg @ https://example.com/pkg.tar.gz\n"
                "https://example.com/other.tar.gz\n"
            )
        },
    )
    got = run("--from", str(src))
    assert got.returncode == 42, got.stdout + got.stderr
    assert "PyPI flask >=2.0" in rows(got)
    assert "PyPI requests-oauthlib ~=1.3" in rows(got)
    assert "PyPI django (any)" in rows(got)
    assert "PyPI pytest >=7" in rows(got)
    assert "PyPI pkg @ https://example.com/pkg.tar.gz" in rows(got)
    assert "PyPI https://example.com/other.tar.gz (a url or path)" in rows(got)
    assert "PyPI  requests  " not in got.stdout  # the exact pin is not a range
    assert "base.txt" not in got.stdout  # an option line is skipped


def test_a_wildcard_pin_is_a_range(tmp_path):
    src = tmp_path / "src"
    write(src, {"requirements.txt": "requests==2.*\n"})
    got = run("--from", str(src))
    assert got.returncode == 42, got.stdout
    assert "PyPI requests ==2.*" in rows(got)


def test_a_pypi_name_is_matched_folded(tmp_path):
    src = tmp_path / "src"
    write(
        src,
        {
            "requirements.txt": "My_Pkg>=1.0\n",
            "poetry.lock": '[[package]]\nname = "my-pkg"\nversion = "1.4.0"\n',
        },
    )
    got = run("--from", str(src))
    assert got.returncode == 0, got.stdout + got.stderr


def test_a_requirements_pin_locks_a_range_of_the_same_name(tmp_path):
    src = tmp_path / "src"
    write(src, {"requirements.txt": "flask==2.0.1\nflask>=2\n"})
    got = run("--from", str(src))
    assert got.returncode == 0, got.stdout + got.stderr


def test_a_python_pin_does_not_lock_an_npm_range(tmp_path):
    # the same name in two ecosystems is two packages: a PyPI pin pins PyPI only
    src = tmp_path / "src"
    write(src, {"package.json": json.dumps({"dependencies": {"requests": "^2"}}),
                "requirements.txt": "requests==2.19.1\n"})  # fmt: skip
    got = run("--from", str(src))
    assert got.returncode == 42, got.stdout + got.stderr
    assert "npm requests ^2" in rows(got)


def test_an_unreadable_manifest_is_named_not_dropped(tmp_path):
    src = tmp_path / "src"
    write(
        src,
        {
            "package.json": "{ not json",
            "sub/package.json": '{"dependencies": {"a": "^1"}}',
        },
    )
    got = run("--from", str(src))
    assert got.returncode == 42, got.stdout + got.stderr
    assert "## couldn't read -- check by hand" in got.stdout.splitlines()
    assert "package.json" in rows(got)
    assert "npm a ^1" in rows(got)


def test_vendored_manifests_are_skipped(tmp_path):
    src = tmp_path / "src"
    write(
        src,
        {
            "node_modules/x/package.json": json.dumps({"dependencies": {"y": "^1"}}),
            "vendor/requirements.txt": "z>=1\n",
        },
    )
    got = run("--from", str(src))
    assert got.returncode == 0, got.stdout + got.stderr
    assert "pins: empty, no package.json or requirements.txt" in got.stdout


def test_no_manifests_is_clean(tmp_path):
    src = tmp_path / "src"
    write(src, {"notes.md": "tomatoes want sun\n"})
    got = run("--from", str(src))
    assert (
        got.returncode == 0
        and "pins: empty, no package.json or requirements.txt" in got.stdout
    )


def test_all_exact_is_clean(tmp_path):
    src = tmp_path / "src"
    write(src, {"package.json": json.dumps({"dependencies": {"a": "1.0.0"}})})
    got = run("--from", str(src))
    assert got.returncode == 0, got.stdout
    assert (
        "pins: empty, every declared dependency is an exact version; no ranges to check"
        in got.stdout
    )


def test_it_writes_nothing(tmp_path):
    src = tmp_path / "src"
    write(src, {"package.json": json.dumps({"dependencies": {"a": "^1"}}),
                "requirements.txt": "b>=2\n"})  # fmt: skip
    lock(src, {"a": "1.0.0"})
    before = {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}
    run("--from", str(src))
    assert {p: p.read_bytes() for p in src.rglob("*") if p.is_file()} == before


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    for argv in ([], ["--from", "x", "--extra"], ["--box", "b", "--from", "c"]):
        got = run(*argv)
        assert got.returncode == 2 and "pins.py" in got.stderr, (argv, got.stderr)


def test_a_bad_target_is_refused(tmp_path):
    (tmp_path / "f").mkdir()
    for argv in (["--from", str(tmp_path / "missing")],
                 ["--box", str(tmp_path / "f")]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and got.stderr.startswith("refused"), (
            argv,
            got.stderr,
        )


def test_the_report_is_exact_in_text_and_in_json(tmp_path):
    src = tmp_path / "src"
    write(src, {"package.json": json.dumps({"dependencies": {"lodash": "^4.17.0"}}),
                "requirements.txt": "flask>=2.0\n"})  # fmt: skip
    got = run("--from", str(src))
    assert got.returncode == 42
    assert got.stdout.splitlines() == [
        "pins: populated, 2 of 2 declared ranges have no lockfile pin",
        "## no lockfile pins it",
        "  PyPI  flask  >=2.0",
        "  npm   lodash  ^4.17.0",
    ]
    asked = run("--from", str(src), "--json")
    assert asked.returncode == 42
    assert json.loads(asked.stdout) == {
        "addon": "pins",
        "state": "populated",
        "said": "2 of 2 declared ranges have no lockfile pin",
        "groups": [{"name": "no lockfile pins it", "rows": [
            {"where": "PyPI", "what": "flask  >=2.0"},
            {"where": "npm", "what": "lodash  ^4.17.0"},
        ]}],
    }  # fmt: skip


def test_an_unreadable_manifest_is_a_group_of_its_own_in_the_report(tmp_path):
    src = tmp_path / "src"
    write(src, {"package.json": "{ not json"})
    got = run("--from", str(src))
    assert got.returncode == 42
    assert got.stdout.splitlines() == [
        "pins: populated, 0 of 0 declared ranges have no lockfile pin; 1 couldn't be read",
        "## couldn't read -- check by hand",
        "  package.json",
    ]


def test_nothing_to_check_is_empty_in_json_and_exits_0(tmp_path):
    src = tmp_path / "src"
    write(src, {"package.json": json.dumps({"dependencies": {"a": "1.0.0"}})})
    got = run("--from", str(src), "--json")
    assert got.returncode == 0
    assert json.loads(got.stdout) == {
        "addon": "pins",
        "state": "empty",
        "said": "every declared dependency is an exact version; no ranges to check",
        "groups": [],
    }
