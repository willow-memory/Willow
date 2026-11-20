"""gh-json: gh --json output as dated lines of issues, pull requests and runs; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "gh_json.py"
spec = importlib.util.spec_from_file_location("gh_json", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'[{"number":14,"title":"Move tomatoes to bed 2","state":"MERGED","createdAt":"2024-03-04T09:00:00Z","author":{"login":"ben"},"headRefName":"bed-2","mergedAt":"2024-03-05T10:00:00Z"},'
    b'{"number":12,"title":"Tomatoes want more sun","state":"OPEN","createdAt":"2024-03-02T08:15:00Z","author":{"login":"ana"},"body":"The bed by the  fence\\nis shaded.",'
    b'"labels":[{"name":"bug"},{"name":"garden"}],"comments":[{"author":{"login":"ben"},"createdAt":"2024-03-03T10:00:00Z","body":"Move them."},{"body":" "}]},'
    b'{"databaseId":1234,"name":"ci","workflowName":"CI","conclusion":"failure","headBranch":"main","createdAt":"2024-03-04T09:30:00Z","displayTitle":"Move tomatoes"}]'
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


def test_issues_pull_requests_and_runs_come_oldest_first():
    assert mod.convert(SAMPLE) == (
        "issue #12 (open) 2024-03-02 ana: Tomatoes want more sun [bug, garden]\n"
        "  The bed by the fence is shaded.\n  comment 2024-03-03 ben: Move them.\n"
        "pull request #14 (merged) 2024-03-04 ben: Move tomatoes to bed 2 (branch bed-2)\n"
        "run 1234 (failure) 2024-03-04 CI on main: Move tomatoes\n"
    )


def test_a_pull_request_is_known_by_its_fields_and_merged_needs_a_merge_time():
    t = lambda **k: mod.item({"number": 1, "title": "T", **k}).splitlines()[0]  # noqa: E731
    assert t(state="OPEN") == "issue #1 (open) T"
    assert t(state="OPEN", isDraft=True) == "pull request #1 (open) T"
    assert t(state="CLOSED", mergedAt=None) == "pull request #1 (closed) T"
    assert (
        t(state="CLOSED", mergedAt="2024-01-01T00:00:00Z")
        == "pull request #1 (merged) T"
    )
    assert (
        t(state="CLOSED", mergedAt="2024-01-01T00:00:00Z", headRefName="x")
        == "pull request #1 (merged) T (branch x)"
    )
    assert t() == "issue #1 (unknown) T" and t(state="MERGED") == "issue #1 (merged) T"


def test_a_run_uses_its_workflow_else_its_name_and_says_what_it_has():
    assert mod.run({"databaseId": 7, "conclusion": "success"}) == "run 7 (success)"
    assert (
        mod.run(
            {
                "databaseId": 7,
                "status": "in_progress",
                "name": "build",
                "createdAt": "2024-01-01T00:00:00Z",
            }
        )
        == "run 7 (in_progress) 2024-01-01 build"
    )
    assert (
        mod.run(
            {
                "databaseId": 7,
                "conclusion": "failure",
                "workflowName": "CI",
                "name": "other",
                "headBranch": "main",
                "displayTitle": "t",
            }
        )
        == "run 7 (failure) CI on main: t"
    )
    assert (
        mod.run({"databaseId": 7, "conclusion": "failure", "headBranch": "main"})
        == "run 7 (failure) on main"
    )


def test_the_order_is_by_day_undated_first_and_the_same_day_keeps_the_files_order():
    doc = b'[{"number":2,"title":"Zed","createdAt":"2024-03-02T00:00:00Z"},{"number":1,"title":"Alpha","createdAt":"2024-03-02T09:00:00Z"},{"number":3,"title":"Undated"}]'
    assert [x.split()[1] for x in mod.convert(doc).splitlines()] == ["#3", "#2", "#1"]


def test_items_that_are_neither_an_issue_nor_a_run_are_ignored():
    mixed = b'[5, {"number": "7", "title": "string number"}, {"number": true, "title": "t"}, {"number": 1}, {"databaseId": 1}, {"number": 3, "title": "kept"}]'
    assert mod.convert(mixed) == "issue #3 (unknown) kept\n"


def test_json_that_is_not_gh_output_is_not_a_result_and_bad_json_is_an_error():
    for other in (
        b"{}",
        b"[]",
        b"5",
        b"null",
        b'{"number":1,"title":"t"}',
        b"[1, 2]",
        b'[{"other": 1}]',
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"[nope")
    except ValueError:
        pass
    else:
        raise AssertionError("bad json")


def test_a_json_file_that_is_no_gh_output_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"a.json": SAMPLE, "b.json": b'{"other": 1}'})
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"gh/issues.json": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "gh/issues.json.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "gh/issues.json": SAMPLE,
            ".hid/gh/issues.json": SAMPLE,
            ".gh/issues.json": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["gh/issues.json.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"gh/issues.json": SAMPLE})
    before = (tmp_path / "src" / "gh/issues.json").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "gh/issues.json.txt").read_bytes() == (
        out / "gh/issues.json.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "gh/issues.json").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(tmp_path, {"good.json": SAMPLE, "bad.json": b"[nope"})
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.json.txt").is_file() and not (out / "bad.json.txt").exists()


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
        assert got.returncode == 2 and "gh_json.py" in got.stderr


def test_the_rest_apis_shape_reads_as_gh_prints_it():
    """GitHub's REST API, and an MCP server over it, name things their own
    way and wrap a list in an object: read the same as gh's --json."""
    issues = (
        b'{"issues":[{"number":91,"title":"hook-guard: seal is allowed","state":"OPEN",'
        b'"user":{"login":"ana"},"created_at":"2026-10-30T05:19:56Z","labels":["bug"],"comments":1}]}'
    )
    assert (
        mod.convert(issues)
        == "issue #91 (open) 2026-10-30 ana: hook-guard: seal is allowed [bug]\n"
    )
    prs = (
        b'[{"number":380,"title":"main green","state":"closed","merged":true,'
        b'"merged_at":"2026-11-20T02:23:07Z","draft":false,"head":{"ref":"ccr-x"},'
        b'"user":{"login":"ben"},"created_at":"2026-11-19T21:38:28Z"},'
        b'{"number":382,"title":"forge: blind","state":"open","draft":false,"head":{"ref":"forge-blind"},'
        b'"user":{"login":"ben"},"created_at":"2026-11-20T05:57:02Z"},'
        b'{"number":7,"title":"from the issues list","state":"open","pull_request":{"merged_at":null}}]'
    )
    assert mod.convert(prs) == (
        "pull request #7 (open) from the issues list\n"
        "pull request #380 (merged) 2026-11-19 ben: main green (branch ccr-x)\n"
        "pull request #382 (open) 2026-11-20 ben: forge: blind (branch forge-blind)\n"
    )
    runs = (
        b'{"total_count":2,"workflow_runs":[{"id":44690843012,"name":"ci","status":"in_progress",'
        b'"conclusion":null,"head_branch":"main","created_at":"2026-11-20T07:01:00Z","display_title":"forge (#382)"}]}'
    )
    assert (
        mod.convert(runs)
        == "run 44690843012 (in_progress) 2026-11-20 ci on main: forge (#382)\n"
    )


def test_gh_s_own_names_win_over_the_rest_apis():
    both = b'[{"number":1,"title":"t","createdAt":"2024-01-01","created_at":"2026-01-01","author":{"login":"gh"},"user":{"login":"rest"}}]'
    assert mod.convert(both) == "issue #1 (unknown) 2024-01-01 gh: t\n"


def test_an_object_with_no_list_gh_or_the_api_would_send_is_still_not_a_result():
    for other in (
        b'{"issues": 5}',
        b'{"other": [{"number": 1, "title": "t"}]}',
        b'{"items": []}',
    ):
        assert mod.convert(other) is None, other


def test_a_merge_queues_run_is_said_as_the_pull_request_it_holds():
    queued = (
        b'[{"databaseId":9,"workflowName":"ci","status":"in_progress",'
        b'"headBranch":"gh-readonly-queue/main/pr-382-6b0e27e69f28d214b0c82b1e5a54cf1c5273616d"},'
        b'{"databaseId":8,"workflowName":"ci","conclusion":"success","headBranch":"gh-readonly-queue/release/1.x/pr-7-abcdef1"},'
        b'{"databaseId":7,"workflowName":"ci","conclusion":"success","headBranch":"gh-readonly-queue/main/not-a-pr"}]'
    )
    assert mod.convert(queued).splitlines() == [
        "run 9 (in_progress) ci in the merge queue for pull request #382, into main",
        "run 8 (success) ci in the merge queue for pull request #7, into release/1.x",
        "run 7 (success) ci on gh-readonly-queue/main/not-a-pr",
    ]
