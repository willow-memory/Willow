"""pypi_dates.py: each deps floor pin's PyPI date and the rule's release's,
kept in a file; PyPI asked only for what the file lacks; what it lacks or
holds for no add-on named; and the repo's file holds every floor pin."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pypi_dates", HERE / "pypi_dates.py")
dates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dates)
CI = dates._ci()

#: what PyPI would say, by package: a release before 2021, the floor's after
PYPI = {
    "old": {"1.0": "2019-03-01T00:00:00Z", "1.1": "2020-06-01T00:00:00Z",
            "2.0": "2023-01-01T00:00:00Z"},
    "new": {"0.1": "2025-01-01T00:00:00Z", "0.2": "2025-06-01T00:00:00Z"},
}  # fmt: skip


@pytest.fixture
def repo():
    """Two deps add-ons with floor pins, in scratch made with tempfile."""
    with tempfile.TemporaryDirectory() as tmp:
        r = Path(tmp)
        for name, pins in (
            ("a", "old==2.0\nnew==0.2\n"),
            ("b", "Old==1.1  # its rule\n"),
        ):
            (r / "adapters/deps" / name).mkdir(parents=True)
            (r / "adapters/deps" / name / "requirements-floor.txt").write_text(pins)
        yield r


def asked_of(log: list):
    def releases(package):
        log.append(package)
        return PYPI[package]

    return releases


def test_write_keeps_each_floor_and_the_rules_release_with_pypis_dates(repo):
    path, log = repo / "dates.json", []
    assert dates.write(CI, repo, path, asked_of(log)) == ["new", "old"]
    assert json.loads(path.read_text()) == {
        "new": {"0.1": "2025-01-01T00:00:00Z", "0.2": "2025-06-01T00:00:00Z"},
        "old": {"1.1": "2020-06-01T00:00:00Z", "2.0": "2023-01-01T00:00:00Z"},
    }
    kept = json.loads(path.read_text())
    for package, versions in kept.items():
        assert CI.rule_floor(versions) == CI.rule_floor(PYPI[package]), (
            "the two kept give the rule the release all of them give"
        )


def test_with_nothing_new_pypi_isnt_asked_and_nothing_is_written(repo):
    path = repo / "dates.json"
    dates.write(CI, repo, path, asked_of([]))
    before, log = path.stat().st_mtime_ns, []
    assert dates.write(CI, repo, path, asked_of(log)) == [] and log == []
    assert path.stat().st_mtime_ns == before


def test_a_new_pin_is_asked_alone_and_one_no_add_on_pins_is_named(repo):
    path = repo / "dates.json"
    dates.write(CI, repo, path, asked_of([]))
    (repo / "adapters/deps/b/requirements-floor.txt").write_text("old==1.0\n")
    kept = json.loads(path.read_text())
    assert dates.missing(kept, dates.pinned(CI, repo)) == (["old==1.0"], [])
    log = []
    dates.write(CI, repo, path, asked_of(log))
    assert log == ["old"]
    assert dates.missing({**kept, "gone": {}}, dates.pinned(CI, repo))[1] == ["gone"]


def test_a_pin_pypi_doesnt_have_is_refused_and_nothing_is_written(repo):
    (repo / "adapters/deps/b/requirements-floor.txt").write_text("old==9.9\n")
    with pytest.raises(ValueError, match="old==9.9 is not on PyPI"):
        dates.write(CI, repo, repo / "dates.json", asked_of([]))
    assert not (repo / "dates.json").exists()


def test_the_repos_file_holds_every_floor_pin():
    kept = json.loads(dates.DATES.read_text(encoding="utf-8"))
    assert dates.missing(kept, dates.pinned(CI, dates.ROOT)) == ([], []), (
        "python adapters/stdlib/ci/pypi_dates.py write"
    )


@pytest.mark.parametrize("argv", [[], ["writ"], ["check", "more"]])
def test_a_bad_command_line_is_refused_and_names_the_script(argv):
    got = subprocess.run(
        [sys.executable, str(HERE / "pypi_dates.py"), *argv],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 2 and "pypi_dates.py" in got.stderr
