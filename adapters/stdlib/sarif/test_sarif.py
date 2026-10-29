"""sarif: a SARIF report finding by finding with tool, rule, level and place; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "sarif.py"
spec = importlib.util.spec_from_file_location("sarif", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'{"version":"2.1.0","runs":[{"tool":{"driver":{"name":"CodeQL","rules":[{"id":"py/sql-injection","shortDescription":{"text":"SQL injection"}}]}},"results":['
    b'{"ruleId":"py/xss","level":"warning","message":{"text":"Reflected   XSS."},"locations":[{"physicalLocation":{"artifactLocation":{"uri":"src/web.py"},"region":{"startLine":7}}}]},'
    b'{"ruleId":"py/sql-injection","level":"error","message":{"text":"This query depends on a user-provided value."},"locations":[{"physicalLocation":{"artifactLocation":{"uri":"src/db.py"},"region":{"startLine":42}}}]},'
    b'{"ruleId":"py/other","message":{"markdown":"Plain **md**"}}]}]}'
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


def test_findings_come_in_file_line_rule_order_with_tool_rule_level_and_place():
    assert mod.convert(SAMPLE) == (
        "CodeQL: py/other (warning)\nPlain **md**\n\n"
        "CodeQL: py/sql-injection (error) at src/db.py:42\nSQL injection: This query depends on a user-provided value.\n\n"
        "CodeQL: py/xss (warning) at src/web.py:7\nReflected XSS.\n"
    )


def test_a_place_is_the_first_location_with_a_file_and_a_positive_line():
    p = mod.place
    assert p(
        {
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": "a.py"},
                        "region": {"startLine": 3},
                    }
                }
            ]
        }
    ) == ("a.py", 3)
    assert p(
        {"locations": [{"physicalLocation": {"artifactLocation": {"uri": "a.py"}}}]}
    ) == ("a.py", 0)
    assert p(
        {
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": "a.py"},
                        "region": {"startLine": 0},
                    }
                }
            ]
        }
    ) == ("a.py", 0)
    assert p(
        {
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": "a.py"},
                        "region": {"startLine": True},
                    }
                }
            ]
        }
    ) == ("a.py", 0)
    assert p(
        {"locations": [{}, {"physicalLocation": {"artifactLocation": {"uri": "b.py"}}}]}
    ) == ("b.py", 0)
    assert (
        p({"locations": []}) == ("", 0)
        and p({}) == ("", 0)
        and p({"locations": [5]}) == ("", 0)
    )


def test_a_rule_with_no_description_and_a_tool_with_no_name_still_read():
    doc = b'{"version":"2.1.0","runs":[{"tool":{"driver":{}},"results":[{"ruleId":"r1","message":{"text":"m"}}]}]}'
    assert mod.convert(doc) == "scanner: r1 (warning)\nm\n"
    nameless = b'{"version":"2.1.0","runs":[{"results":[{"message":{"text":"m"}}]}]}'
    assert mod.convert(nameless) == "scanner: (no rule) (warning)\nm\n"
    short_only = b'{"version":"2.1.0","runs":[{"tool":{"driver":{"name":"T","rules":[{"id":"r","shortDescription":{"text":"S"}}]}},"results":[{"ruleId":"r"}]}]}'
    assert mod.convert(short_only) == "T: r (warning)\nS\n"


def test_a_report_with_no_findings_or_that_is_no_report_is_not_a_result_and_bad_json_is_an_error():
    for other in (
        b"[]",
        b"{}",
        b'{"runs":[]}',
        b'{"version":"2.1.0","runs":{}}',
        b'{"version":2,"runs":[]}',
        b'{"version":"2.1.0","runs":[{"results":[]},5]}',
        b'{"version":"2.1.0","runs":[{"results":[7]}]}',
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"{nope")
    except ValueError:
        pass
    else:
        raise AssertionError("bad json")


def test_a_file_that_is_no_report_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {"a.sarif": SAMPLE, "b.sarif": b'{"other": 1}', "c.sarif.json": SAMPLE},
    )
    assert "wrote 2 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "c.sarif.json.txt").is_file()


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"scans/codeql.sarif": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "scans/codeql.sarif.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "scans/codeql.sarif": SAMPLE,
            ".hid/scans/codeql.sarif": SAMPLE,
            ".scans/codeql.sarif": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["scans/codeql.sarif.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"scans/codeql.sarif": SAMPLE})
    before = (tmp_path / "src" / "scans/codeql.sarif").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "scans/codeql.sarif.txt").read_bytes() == (
        out / "scans/codeql.sarif.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "scans/codeql.sarif").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(tmp_path, {"good.sarif": SAMPLE, "bad.sarif": b"{not json"})
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.sarif.txt").is_file() and not (out / "bad.sarif.txt").exists()


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
        assert got.returncode == 2 and "sarif.py" in got.stderr
