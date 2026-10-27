"""github: a security report's comment names the pull requests and their
authors and nothing of the report's own text; `.github/` is held to the
repo, and each way it can drift is caught."""

from __future__ import annotations

import importlib.util
import os
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
         "adapters/stdlib/readme/readme.py"]  # fmt: skip


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
        # ci.py's gates cut between jobs, each run by exactly one of them
        (
            ".github/workflows/ci.yml",
            "run tests --without tests:strip --shard",
            "run tests --shard",
            "tests:strip-1 more than once",
        ),  # fmt: skip
        (
            ".github/workflows/ci.yml",
            "run tests:strip --shard",
            "run tests:kernel --shard",
            "tests:kernel more than once",
        ),  # fmt: skip
        (
            ".github/workflows/ci.yml",
            "run tests:strip --shard",
            "run tests:strpi --shard",
            "what it refuses",
        ),  # fmt: skip
        (
            ".github/workflows/ci.yml",
            "        shard: [1, 2, 3, 4]\n",
            "        shard: [1, 2, 3]\n",
            "in no job",
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
            "--shard ${{ matrix.shard }}/6",
            "--shard ${{ matrix.shard }}/5",
            "what it refuses",
        ),  # fmt: skip
        (
            ".github/workflows/ci.yml",
            "        shard: [1, 2, 3, 4, 5, 6]\n",
            "        shard: [1, 2, 3, 4, 5]\n",
            "in no job",
        ),  # fmt: skip
        (
            ".github/workflows/ci.yml",
            '"3.14"]\n        shard: [1, 2, 3, 4]\n    steps:\n      - uses: actions/checkout@v7\n      - uses: actions/setup-python@v7\n        with:\n          python-version: ${{ matrix.python-version }}\n      - run: pip install pytest\n      - run: python adapters/stdlib/ci/ci.py run tests:strip',  # fmt: skip
            '"3.13"]\n        shard: [1, 2, 3, 4]\n    steps:\n      - uses: actions/checkout@v7\n      - uses: actions/setup-python@v7\n        with:\n          python-version: ${{ matrix.python-version }}\n      - run: pip install pytest\n      - run: python adapters/stdlib/ci/ci.py run tests:strip',  # fmt: skip
            "Python matrices differ",
        ),
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
    assert got and says in got[0], got


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
