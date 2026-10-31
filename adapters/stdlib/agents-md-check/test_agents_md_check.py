"""agents-md-check: a path, link, script, make target, npm script or import an
instruction file names that the repo lacks is listed by file and line; what is
there, a placeholder, a URL and an absolute path are left alone; a clean repo
is clean; a bad command line is refused; and nothing is written."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "agents_md_check.py"
KERNEL = HERE.parents[2] / "kernel.py"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def repo(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        p = tmp_path / "repo" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return tmp_path / "repo"


def lines(got: subprocess.CompletedProcess) -> list[str]:
    return [" ".join(row.split()) for row in got.stdout.splitlines() if row.strip()][
        :-1
    ]


def test_a_missing_path_in_backticks_is_cited_by_file_and_line(tmp_path):
    r = repo(
        tmp_path,
        {
            "AGENTS.md": "# x\n\nSee `src/gone.py` and `src/here.py`.\n",
            "src/here.py": "",
        },
    )
    got = run("--from", str(r))
    assert got.returncode == 42, got.stderr
    assert lines(got) == ["AGENTS.md:3 src/gone.py path: no such file"]
    assert "1 thing named in 1 instruction file not found." in got.stdout


def test_a_path_is_looked_for_from_the_top_and_from_the_files_own_folder(tmp_path):
    r = repo(
        tmp_path,
        {
            "docs/CLAUDE.md": "`notes.md` and `docs/other.md`\n",
            "docs/notes.md": "",
            "docs/other.md": "",
        },
    )
    assert run("--from", str(r)).returncode == 0


def test_a_missing_script_a_command_runs_is_listed(tmp_path):
    text = "```\npython tools/gone.py --flag\nnode build.js\n./run.sh\n```\n"
    r = repo(tmp_path, {"AGENTS.md": text, "build.js": ""})
    got = run("--from", str(r))
    assert got.returncode == 42
    assert lines(got) == [
        "AGENTS.md:2 tools/gone.py path: no such file",
        "AGENTS.md:4 ./run.sh path: no such file",
    ]


def test_an_environment_prefix_and_a_dollar_prompt_are_read_through(tmp_path):
    r = repo(tmp_path, {"AGENTS.md": "```\n$ CI=1 python gone.py\n```\n"})
    assert lines(run("--from", str(r))) == ["AGENTS.md:2 gone.py path: no such file"]


def test_a_make_target_and_an_npm_script_are_checked_against_their_files(tmp_path):
    r = repo(tmp_path, {
        "AGENTS.md": "Run `make lint`, `make nope`, `npm run build` and `npm run nope`.\n",
        "Makefile": "lint: deps\n\tx\n.PHONY: lint\n",
        "package.json": '{"scripts": {"build": "tsc"}}',
    })  # fmt: skip
    got = run("--from", str(r))
    assert lines(got) == [
        "AGENTS.md:1 make nope make target: not in the Makefile",
        "AGENTS.md:1 npm run nope script: not in package.json",
    ]


def test_without_a_makefile_or_package_json_nothing_is_said_about_targets(tmp_path):
    r = repo(tmp_path, {"AGENTS.md": "Run `make lint` or `npm run build`.\n"})
    assert run("--from", str(r)).returncode == 0


def test_a_relative_link_and_an_import_are_checked_and_a_fragment_is_dropped(tmp_path):
    text = "@RULES.md\n[a](docs/a.md#top) [b](docs/b.md) [c](https://x.org/y.md)\n"
    r = repo(tmp_path, {"CLAUDE.md": text, "docs/a.md": ""})
    assert lines(run("--from", str(r))) == [
        "CLAUDE.md:1 RULES.md import: no such file",
        "CLAUDE.md:2 docs/b.md path: no such file",
    ]


def test_placeholders_urls_globs_and_absolute_paths_are_left_alone(tmp_path):
    text = ("`DIR/file.txt` `VENV/bin/python` `MIRROR/<same path>.txt` `/tmp/x.json` `~/a/b.py` "
            "`src/*.py` `$HOME/x.sh` `https://e.org/a.md` `a/b...c` `3.13` `sys.argv` `kernel.rank`\n")  # fmt: skip
    assert run("--from", str(repo(tmp_path, {"AGENTS.md": text}))).returncode == 0


def test_a_path_inside_a_code_block_prose_is_not_a_command_but_a_fence_still_toggles(
    tmp_path,
):
    text = "```\nsome prose words here\n```\nthen `gone/x.py` after\n"
    assert lines(run("--from", str(repo(tmp_path, {"AGENTS.md": text})))) == [
        "AGENTS.md:4 gone/x.py path: no such file"
    ]


def test_instruction_files_under_node_modules_are_not_read(tmp_path):
    r = repo(
        tmp_path, {"node_modules/p/AGENTS.md": "`gone/x.py`\n", "AGENTS.md": "ok\n"}
    )
    got = run("--from", str(r))
    assert got.returncode == 0 and "1 instruction file is there" in got.stdout


def test_no_instruction_file_is_clean(tmp_path):
    got = run("--from", str(repo(tmp_path, {"README.md": "`gone/x.py`"})))
    assert got.returncode == 0 and "No AGENTS.md or CLAUDE.md" in got.stdout


def test_a_box_is_read_through_its_pile_and_nothing_is_written(tmp_path):
    pile = repo(tmp_path, {"AGENTS.md": "`gone/x.py`\n"})
    box = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), "--now", "2026-10-29T00:00:00Z"],
                   check=True, capture_output=True)  # fmt: skip
    before = {p: p.read_bytes() for p in pile.rglob("*") if p.is_file()}
    got = run("--box", str(box))
    assert got.returncode == 42 and "gone/x.py" in got.stdout
    assert before == {p: p.read_bytes() for p in pile.rglob("*") if p.is_file()}


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    for argv in ([], ["--from"], ["--from", str(tmp_path), "stray"],
                 ["--from", str(tmp_path), "--box", str(tmp_path)]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "agents_md_check.py" in got.stderr
    assert run("--from", str(tmp_path / "missing")).returncode == 2
    assert run("--box", str(tmp_path)).returncode == 2


def test_a_runner_given_by_its_path_is_still_a_runner(tmp_path):
    text = "```\n.venv/bin/python gone1.py\n/usr/bin/python3 gone2.py\n```\n"
    got = run("--from", str(repo(tmp_path, {"AGENTS.md": text})))
    assert lines(got) == [
        "AGENTS.md:2 gone1.py path: no such file",
        "AGENTS.md:3 gone2.py path: no such file",
    ]


def test_a_name_the_line_calls_a_repo_is_not_a_missing_path(tmp_path):
    r = repo(
        tmp_path,
        {"AGENTS.md": "# x\n\nLessons live in the `Emerging-Rule/community` repo.\n"},
    )
    got = run("--from", str(r))
    assert got.returncode == 0, got.stdout


def test_a_real_missing_path_is_still_reported_when_the_line_says_repo(tmp_path):
    r = repo(tmp_path, {"AGENTS.md": "This repo still needs `src/gone.py`.\n"})
    got = run("--from", str(r))
    assert got.returncode == 42
    assert lines(got) == ["AGENTS.md:1 src/gone.py path: no such file"]
