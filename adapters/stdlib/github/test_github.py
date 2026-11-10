"""github: a security report's comment names the pull requests and their
authors and nothing of the report's own text; `.github/` is held to the
repo, and each way it can drift is caught."""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("willow_github", HERE / "github.py")
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)

BODY = """### Which promise

Something else

### What you did, and what happened

@someone made it do {}

### Where it is

`kernel.py:2`

kernel.py:5-6
"""


@pytest.fixture
def stand_ins(tmp_path, monkeypatch):
    """whose.py and gh stood in for: CI checks out one commit, so the real
    history isn't there to blame, and gh would ask GitHub."""
    seen = tmp_path / "seen.txt"
    whose = tmp_path / "whose.py"
    whose.write_text(
        "import sys\n"
        f"open({str(seen)!r}, 'w').write(' '.join(sys.argv[1:]) + '|' + sys.stdin.read())\n"
        "print('#4 kernel.py:2'); print('#9 kernel.py:5-6')\n"
    )
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    fake = bin_ / "gh"
    fake.write_text('#!/bin/sh\n[ "$3" = 4 ] && echo ada-example && exit 0\nexit 1\n')
    fake.chmod(0o755)
    monkeypatch.setattr(gh, "WHOSE", whose)
    monkeypatch.setenv("PATH", f"{bin_}{os.pathsep}{os.environ['PATH']}")
    return seen


def test_the_comment_names_each_pull_request_and_tags_its_author(stand_ins):
    got = gh.report(BODY)
    assert "- #4 (kernel.py:2), by @ada-example\n- #9 (kernel.py:5-6)\n" in got
    args, places = stand_ins.read_text().split("|")
    assert args == f"--host {HERE} -" and places == "`kernel.py:2`\nkernel.py:5-6"


def test_none_of_the_reports_own_text_reaches_the_comment(stand_ins):
    for body in (BODY, BODY.replace("`kernel.py:2`", "@someone ../x:1")):
        assert "someone" not in gh.report(body)


@pytest.mark.parametrize(
    "body, says",
    [
        ("### Where it is\n\n_No response_\n", "No lines were named"),
        ("### Which promise\n\nSomething else\n", "No lines were named"),
        ("### Where it is\n\n../../etc/passwd:1\n", "couldn't be looked up"),
    ],
)
def test_a_report_with_no_place_or_a_bad_one_says_so(body, says):
    assert says in gh.report(body)


def test_an_author_login_that_isnt_one_is_left_out(stand_ins, tmp_path):
    (tmp_path / "bin" / "gh").write_text("#!/bin/sh\necho 'ada; @everyone'\n")
    assert "@" not in gh.report(BODY).split("written by:")[1].split("Tagged")[0]


# ── check ────────────────────────────────────────────────────────────────────
FILES = ["kernel.py", "README.md", "FILES.md", ".github/workflows/ci.yml",
         ".github/workflows/law.yml",
         ".github/ISSUE_TEMPLATE/idea.yml", ".github/ISSUE_TEMPLATE/security.yml",
         "adapters/stdlib/readme/readme.py", "adapters/stdlib/readme/groups.py"]  # fmt: skip


def test_the_repos_github_folder_holds():
    assert gh.problems() == []


@pytest.mark.parametrize(
    "rel, old, new, says",
    [
        (
            ".github/workflows/ci.yml",
            '["3.9", ',
            '["3.10", ',
            "not at the Python kernel.py names",
        ),  # fmt: skip
        (".github/workflows/ci.yml", ', "3.14"]', "]", "README.md doesn't say"),
        (
            "FILES.md",
            "tests on Python 3.9 to",
            "tests on Python 3.8 to",
            "FILES.md's ci.yml line",
        ),  # fmt: skip
        (
            ".github/ISSUE_TEMPLATE/idea.yml",
            "        - Play\n",
            "        - Games\n",
            "sections",
        ),  # fmt: skip
        (
            ".github/ISSUE_TEMPLATE/idea.yml",
            "        - record",
            "        - recorded",
            "writes",
        ),  # fmt: skip
        (
            ".github/ISSUE_TEMPLATE/security.yml",
            "label: Where it is",
            "label: Where",
            "security.yml",
        ),  # fmt: skip
        (
            "README.md",
            "python-3.9%20to%203.14",
            "python-3.9%20to%203.13",
            "Python badge",
        ),
        (
            "README.md",
            "workflows/ci.yml/badge.svg",
            "workflows/tests.yml/badge.svg",
            "CI badge",
        ),
        (
            ".github/workflows/ci.yml",
            " && github.event.pull_request.user.login != 'dependabot[bot]'",
            "",
            "changelog job",
        ),
        (
            ".github/workflows/ci.yml",
            "login != 'dependabot[bot]'",
            "login != 'someone'",
            "changelog job",
        ),
        # willow-bot reads the similar job's list from its artifact
        (
            ".github/workflows/ci.yml",
            "          name: similar\n",
            "          name: near\n",
            "similar job",
        ),
        (
            ".github/workflows/ci.yml",
            '> "$RUNNER_TEMP/similar.md"',
            '>> "$GITHUB_STEP_SUMMARY"',
            "similar job",
        ),
        # one run per change: no second run from the branch's push, and a
        # newer commit cancels the older run, but never one of main's
        (".github/workflows/ci.yml", "    branches: [main]\n", "", "runs twice"),
        (
            ".github/workflows/ci.yml",
            "cancel-in-progress: ${{ github.event_name == 'pull_request' }}",
            "cancel-in-progress: true",
            "doesn't cancel",
        ),
        (
            ".github/workflows/ci.yml",
            "group: ci-${{ github.event.pull_request.number || github.ref }}",
            "group: ci",
            "doesn't cancel",
        ),
        # ci.py's gates cut between jobs, each run by exactly one of them; a
        # cores.py line runs every gate select names for it, uncut
        (
            ".github/workflows/ci.yml",
            "tests --without tests:strip | tee",
            "tests | tee",
            "tests:strip-1 more than once",
        ),  # fmt: skip
        (
            ".github/workflows/ci.yml",
            "tests --without tests:strip | tee",
            "tests --without tests:strip --without tests:kernel | tee",
            "tests:kernel in no job",
        ),  # fmt: skip
        (
            ".github/workflows/ci.yml",
            "ci-record tests:strip | tee",
            "ci-record tests:kernel | tee",
            "tests:kernel more than once",
        ),  # fmt: skip
        (
            ".github/workflows/ci.yml",
            "ci-record tests:strip | tee",
            "ci-record tests:strpi | tee",
            "what it refuses",
        ),  # fmt: skip
        (
            ".github/workflows/ci.yml",
            "run mutants --shard ${{ matrix.shard }}/4",
            "run mutants --shard ${{ matrix.shard }}/5",
            "in no job",
        ),  # fmt: skip
        (
            ".github/workflows/ci.yml",
            "--shard ${{ matrix.shard }}/4",
            "--shard 1/4",
            "more than once",
        ),  # fmt: skip
        (
            ".github/workflows/ci.yml",
            "        shard: [1, 2, 3, 4]\n",
            "        shard: [1, 2, 3]\n",
            "in no job",
        ),  # fmt: skip
        (
            ".github/workflows/ci.yml",
            '{"python-version":"3.13"}]\') || fromJSON(\'[]\') }}\n    steps:\n      - uses: actions/checkout@v7\n      - uses: actions/setup-python@v7\n        with:\n          python-version: ${{ matrix.python-version }}\n      - run: pip install pytest\n      - run: python adapters/stdlib/ci/cores.py --jobs 4 --box ${{ runner.temp }}/ci-record tests:strip',  # fmt: skip
            '{"python-version":"3.12"}]\') || fromJSON(\'[]\') }}\n    steps:\n      - uses: actions/checkout@v7\n      - uses: actions/setup-python@v7\n        with:\n          python-version: ${{ matrix.python-version }}\n      - run: pip install pytest\n      - run: python adapters/stdlib/ci/cores.py --jobs 4 --box ${{ runner.temp }}/ci-record tests:strip',  # fmt: skip
            "Python matrices differ",
        ),
        # mutants run in full on a push and, on a pull request, by what
        # ci-memo says a change reaches: its plan names the same gates, and
        # it falls back to all of them
        (
            ".github/workflows/ci.yml",
            'plan --pin "$RUNNER_TEMP/ci.pin" mutants > "$RUNNER_TEMP/plan.txt"',
            'plan --pin "$RUNNER_TEMP/ci.pin" mutants:accents > "$RUNNER_TEMP/plan.txt"',
            "mutants job is skipped on pull requests",
        ),  # fmt: skip
        (
            ".github/workflows/ci.yml",
            "cores.py --jobs 4 --box ${{ runner.temp }}/ci-record mutants | tee",
            "cores.py --jobs 4 --box ${{ runner.temp }}/ci-record mutants:accents | tee",
            "mutants job is skipped on pull requests",
        ),  # fmt: skip
        (
            ".github/workflows/ci.yml",
            "    if: github.event_name == 'pull_request'\n    runs-on: ubuntu-24.04\n    permissions:",
            "    if: github.event_name != 'push'\n    runs-on: ubuntu-24.04\n    permissions:",
            "what it refuses",
        ),  # fmt: skip
        # CONST-VIII-2: the weekly run that reaches a person when an
        # emergency amendment expires in a quiet repo
        (".github/workflows/law.yml", "  schedule:\n", "  scheduled:\n", "law.yml"),
        (
            ".github/workflows/law.yml",
            "run: python constitution/amend.py check",
            "run: python constitution/amend.py write",
            "law.yml",
        ),
    ],
)
def test_each_way_github_can_drift_is_caught(
    rel, old, new, says, tmp_path, monkeypatch
):
    for f in FILES:
        (tmp_path / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / f, tmp_path / f)
    text = (tmp_path / rel).read_text(encoding="utf-8")
    assert old in text, f"the plant's anchor {old!r} is gone from {rel}"
    (tmp_path / rel).write_text(text.replace(old, new, 1), encoding="utf-8")
    monkeypatch.setattr(gh, "ROOT", tmp_path)
    monkeypatch.setattr(gh, "DOT", tmp_path / ".github")
    got = gh.problems()
    assert got and any(says in g for g in got), got


@pytest.mark.parametrize("argv", [[], ["reports"], ["check", "x"]])
def test_a_bad_command_line_is_refused(argv):
    assert gh.main(argv) == 2


def test_check_on_the_command_line(capsys):
    assert gh.main(["check"]) == 0
    assert "holds" in capsys.readouterr().out


def test_host_json_reads_githubs_two_merge_titles_and_nothing_else():
    spec = importlib.util.spec_from_file_location(
        "willow_whose_for_github", ROOT / "adapters" / "stdlib" / "ci" / "whose.py"
    )
    whose = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(whose)
    h = whose.host(str(HERE))

    def number(title: str):
        return next((int(m.group(1)) for t in h["titles"] for m in [t.search(title)] if m), None)  # fmt: skip

    assert number("Add-ons in stdlib/ and deps/ (#2)") == 2
    assert number("Merge pull request #11 from someone/branch") == 11
    assert number("Merge branch 'main' into feature") is None
    assert number("Fix (#2) in the middle") is None
    assert h["label"].format(n=7) == "#7"


def ci_text() -> str:
    return (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")


#: the mutants job's condition: main's commit only, on a push the queue didn't run
MUTANTS_IF = "    if: ${{ github.event_name != 'pull_request' && !failure() && !cancelled() && needs.queued.outputs.tested != 'true' }}\n"


def test_a_push_only_job_needs_a_pull_request_job_that_plans_its_gates():
    ci = ci_text()
    assert ci.count(MUTANTS_IF) == 1, (
        "the mutants job's condition, as these plants read it"
    )
    assert gh.split_problems(ci) == []
    # no reach job at all: the mutants gates are dropped from pull requests
    whole = re.sub(r"^  mutants-reach:\n.*?(?=^  \S)", "", ci, flags=re.M | re.S)
    assert "\n  mutants-reach:\n" not in whole
    got = gh.split_problems(whole)
    assert len(got) == 1 and "mutants job is skipped on pull requests" in got[0]
    # the old shape, push alone, is held the same way
    push = whole.replace(MUTANTS_IF, "    if: github.event_name == 'push' && needs.queued.outputs.tested != 'true'\n")  # fmt: skip
    assert any("mutants job is skipped on pull requests" in p for p in gh.split_problems(push))  # fmt: skip
    # a job on pull requests only, with no push side, runs its gates on no push
    only = ci.replace(MUTANTS_IF, "    if: github.event_name == 'pull_request'\n")
    assert any("mutants:again in no job" in p for p in gh.split_problems(only))
    # a job that runs on pull requests too still stands down on a queued push
    both = ci.replace(MUTANTS_IF, "    if: ${{ !failure() && !cancelled() && needs.queued.outputs.tested != 'true' }}\n")  # fmt: skip
    assert gh.split_problems(both) == []


def test_every_job_that_runs_a_gate_stands_on_the_queues_run_of_a_pushed_commit():
    ci = ci_text()
    # tests runs its gates again on a push the queue ran
    loose = ci.replace("    needs: [queued, lint, against, changelog]\n", "    needs: [lint, against, changelog]\n", 1)  # fmt: skip
    got = gh.split_problems(loose)
    assert any("tests job runs gates again on a push the merge queue" in p for p in got), got  # fmt: skip
    unasked = ci.replace("&& needs.queued.outputs.tested != 'true' }}\n    runs-on: ubuntu-24.04\n    steps:\n      - uses: actions/checkout@v7\n      - uses: actions/setup-python@v7\n        with:\n          python-version: \"3.13\"\n      - run: pip install ruff", "}}\n    runs-on: ubuntu-24.04\n    steps:\n      - uses: actions/checkout@v7\n      - uses: actions/setup-python@v7\n        with:\n          python-version: \"3.13\"\n      - run: pip install ruff", 1)  # fmt: skip
    assert unasked != ci, "the lint job's condition, as this plant reads it"
    got = gh.split_problems(unasked)
    assert any("lint job runs gates again" in p for p in got), got
    # the queued job asks for any run, not the queue's green run of this commit
    for old, new in (('--commit "$GITHUB_SHA" ', ""), ("--status success ", ""), ("--event merge_group", "--event push")):  # fmt: skip
        assert old in ci
        got = gh.split_problems(ci.replace(old, new, 1))
        assert any("no queued job" in p for p in got), (old, got)
    gone = re.sub(r"^  queued:\n.*?(?=^  \S)", "", ci, flags=re.M | re.S)
    assert any("no queued job" in p for p in gh.split_problems(gone))
