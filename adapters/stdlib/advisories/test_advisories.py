"""advisories: matches locked dependencies to a downloaded OSV database,
offline; names what it can't version-compare instead of guessing; refuses,
never crashes, on a bad command line; and writes nothing."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ADV = HERE / "advisories.py"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ADV), *argv], capture_output=True, text=True
    )


def osv(db: Path, gid: str, eco: str, name: str, *, cve="", published="2020-07-15T00:00:00Z",
        versions=None, ranges=None, summary="") -> None:  # fmt: skip
    aff: dict = {"package": {"ecosystem": eco, "name": name}}
    if versions is not None:
        aff["versions"] = versions
    if ranges is not None:
        aff["ranges"] = ranges
    doc = {"id": gid, "aliases": ([cve] if cve else []), "summary": summary,
           "published": published, "affected": [aff]}  # fmt: skip
    p = db / eco / gid[:8] / f"{gid}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc), encoding="utf-8")


def semver(introduced, fixed):
    return [
        {"type": "SEMVER", "events": [{"introduced": introduced}, {"fixed": fixed}]}
    ]


def ecosystem(introduced, fixed):  # the range type GitHub's PyPI advisories use
    return [
        {"type": "ECOSYSTEM", "events": [{"introduced": introduced}, {"fixed": fixed}]}
    ]


def test_an_ecosystem_range_without_a_versions_list(tmp_path):
    # mirrors a real record (GHSA-x84v-xcm2-53pg): ECOSYSTEM range, no versions[]
    db, src = tmp_path / "db", tmp_path / "src"
    osv(db, "GHSA-x84v-xcm2-53pg", "PyPI", "requests", cve="CVE-2018-18074",
        ranges=ecosystem("0", "2.20.0"))  # fmt: skip
    write(src, {"requirements.txt": "requests==2.19.1\ncertifi==2024.2.2\n"})
    got = run("--from", str(src), "--db", str(db))
    assert got.returncode == 42, got.stderr
    assert "requests 2.19.1" in got.stdout and "certifi" not in got.stdout
    assert "1 of 2" in got.stdout


def write(folder: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        p = folder / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def test_a_named_dependency_by_versions_and_by_range(tmp_path):
    db, src = tmp_path / "db", tmp_path / "src"
    osv(db, "GHSA-jf85-cpcp-j695", "npm", "lodash", cve="CVE-2020-8203",
        ranges=semver("0", "4.17.20"), summary="Prototype Pollution")  # fmt: skip
    osv(db, "GHSA-x84v-xcm2-53pg", "PyPI", "requests", cve="CVE-2018-18074",
        published="2018-10-09T00:00:00Z", versions=["2.19.1", "2.19.0"])  # fmt: skip
    write(
        src,
        {
            "package-lock.json": json.dumps(
                {"packages": {"node_modules/lodash": {"version": "4.17.4"}}}
            ),
            "requirements.txt": "requests==2.19.1\n",
        },
    )
    got = run("--from", str(src), "--db", str(db))
    assert got.returncode == 42, got.stderr
    assert "lodash 4.17.4" in got.stdout and "GHSA-jf85-cpcp-j695" in got.stdout
    assert "CVE-2020-8203" in got.stdout and "since 2018-10-09" in got.stdout
    assert "2018-10-09T" not in got.stdout  # the date is cut to the day, no time
    assert "requests 2.19.1" in got.stdout and "2 of 2" in got.stdout


def test_range_bounds_are_compared_not_just_touched(tmp_path):
    db, src = tmp_path / "db", tmp_path / "src"
    # introduced is a real version: a version below it is NOT affected
    osv(db, "GHSA-lo-00", "npm", "a", ranges=semver("2.0.0", "3.0.0"))
    # a shorter version equal to the fixed bound (1.2 == 1.2.0) is NOT affected
    osv(db, "GHSA-hi-00", "npm", "b", ranges=semver("0", "1.2"))
    write(
        src,
        {
            "package-lock.json": json.dumps(
                {
                    "packages": {
                        "node_modules/a": {"version": "1.5.0"},
                        "node_modules/b": {"version": "1.2.0"},
                    }
                }
            )
        },
    )
    got = run("--from", str(src), "--db", str(db))
    assert got.returncode == 0, got.stdout + got.stderr  # both outside the range
    # and the versions that ARE inside are caught
    write(
        src,
        {
            "package-lock.json": json.dumps(
                {
                    "packages": {
                        "node_modules/a": {"version": "2.5.0"},
                        "node_modules/b": {"version": "1.1.9"},
                    }
                }
            )
        },
    )
    got = run("--from", str(src), "--db", str(db))
    assert got.returncode == 42 and "2 of 2" in got.stdout, got.stdout


def test_requirements_comments_and_markers_are_stripped(tmp_path):
    db, src = tmp_path / "db", tmp_path / "src"
    osv(db, "GHSA-fl-00", "PyPI", "flask", versions=["2.0.1"])
    osv(db, "GHSA-rq-00", "PyPI", "requests", versions=["2.19.1"])
    write(
        src,
        {
            "requirements.txt": 'flask == 2.0.1 ; python_version >= "3.8"\n'
            "requests==2.19.1  # pinned, see #42\n"
        },
    )
    got = run("--from", str(src), "--db", str(db))
    assert got.returncode == 42, got.stdout + got.stderr
    assert "flask 2.0.1" in got.stdout and "requests 2.19.1" in got.stdout


def test_a_fixed_version_is_not_named(tmp_path):
    db, src = tmp_path / "db", tmp_path / "src"
    osv(db, "GHSA-jf85-cpcp-j695", "npm", "lodash", ranges=semver("0", "4.17.20"))
    write(
        src,
        {
            "package-lock.json": json.dumps(
                {"packages": {"node_modules/lodash": {"version": "4.17.21"}}}
            )
        },
    )
    got = run("--from", str(src), "--db", str(db))
    assert got.returncode == 0, got.stderr
    assert "No known advisory" in got.stdout


def test_a_version_it_cannot_compare_is_listed_apart_not_guessed(tmp_path):
    db, src = tmp_path / "db", tmp_path / "src"
    osv(db, "GHSA-aaaa-bbbb-cccc", "npm", "left-pad", ranges=semver("0", "1.3.0"))
    # a prerelease version is not plain numeric: not matched, not dropped
    write(
        src,
        {
            "package-lock.json": json.dumps(
                {"packages": {"node_modules/left-pad": {"version": "1.3.0-beta.1"}}}
            )
        },
    )
    got = run("--from", str(src), "--db", str(db))
    assert got.returncode == 42, got.stderr
    assert "couldn't compare" in got.stdout and "left-pad 1.3.0-beta.1" in got.stdout


def test_three_ecosystems_and_pypi_name_normalisation(tmp_path):
    db, src = tmp_path / "db", tmp_path / "src"
    osv(db, "GHSA-pypi-0000-0000", "PyPI", "my-pkg", versions=["1.0.0"])
    osv(
        db, "GHSA-crat-0000-0000", "crates.io", "openssl", ranges=semver("0", "0.10.55")
    )
    # lock names it My_Pkg; PyPI folds case and _ to - so it still matches
    write(
        src,
        {
            "requirements.txt": "My_Pkg==1.0.0\n",
            "Cargo.lock": '[[package]]\nname = "openssl"\nversion = "0.10.48"\n',
        },
    )
    got = run("--from", str(src), "--db", str(db))
    assert got.returncode == 42, got.stderr
    # the name is shown as the lockfile wrote it; normalisation is only for matching
    assert "My_Pkg 1.0.0" in got.stdout and "openssl 0.10.48" in got.stdout


def test_nested_lockfiles_in_node_modules_are_skipped(tmp_path):
    db, src = tmp_path / "db", tmp_path / "src"
    osv(db, "GHSA-aaaa-bbbb-cccc", "npm", "lodash", ranges=semver("0", "9.9.9"))
    write(
        src,
        {
            "package-lock.json": json.dumps({"packages": {}}),
            "node_modules/x/package-lock.json": json.dumps(
                {"packages": {"node_modules/lodash": {"version": "1.0.0"}}}
            ),
        },
    )
    got = run("--from", str(src), "--db", str(db))
    assert got.returncode == 0, got.stderr  # the vendored lockfile was not read


def test_without_a_db_it_lists_the_dependencies(tmp_path):
    src = tmp_path / "src"
    write(src, {"requirements.txt": "flask==2.0.1\nrequests==2.19.1\n"})
    got = run("--from", str(src))
    assert got.returncode == 0, got.stderr
    assert "flask 2.0.1" in got.stdout and "2 locked dependencies" in got.stdout


def test_no_lockfiles_is_clean(tmp_path):
    src = tmp_path / "src"
    write(src, {"notes.md": "tomatoes want sun\n"})
    got = run("--from", str(src))
    assert got.returncode == 0 and "No lockfiles found" in got.stdout


def test_it_writes_nothing(tmp_path):
    db, src = tmp_path / "db", tmp_path / "src"
    osv(db, "GHSA-aaaa-bbbb-cccc", "npm", "lodash", ranges=semver("0", "4.17.20"))
    write(
        src,
        {
            "package-lock.json": json.dumps(
                {"packages": {"node_modules/lodash": {"version": "4.17.4"}}}
            )
        },
    )
    before = {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}
    run("--from", str(src), "--db", str(db))
    after = {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}
    assert before == after


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    # a malformed command line prints the usage, which names the script
    for argv in ([], ["--from", str(tmp_path / "f"), "--extra"],
                 ["--box", "b", "--from", str(tmp_path / "f")],
                 ["--db", str(tmp_path / "f")]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "advisories.py" in got.stderr, (argv, got.stderr)


def test_a_bad_target_is_refused(tmp_path):
    (tmp_path / "f").mkdir()
    # a well-formed command line naming something that isn't there is refused
    for argv in (["--from", str(tmp_path / "missing")],
                 ["--from", str(tmp_path / "f"), "--db", str(tmp_path / "nodir")],
                 ["--box", str(tmp_path / "f")]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and got.stderr.startswith("refused"), (
            argv,
            got.stderr,
        )
