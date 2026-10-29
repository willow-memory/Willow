"""codeowners: the rule that decides a path, cited by file and line, on
GitHub's rules (last match wins, gitignore-style patterns), GitLab's
(sections, defaults) and Forgejo's (every regex that matches); an unowned path
and a missing file waiting on you; a bad command line refused; nothing written."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "codeowners.py"
KERNEL = HERE.parents[2] / "kernel.py"
mod = __import__("importlib.util").util.spec_from_file_location("codeowners", SCRIPT)
codeowners = __import__("importlib.util").util.module_from_spec(mod)
mod.loader.exec_module(codeowners)

GITHUB = """\
# everything
*       @everyone
*.js    @js-owner
/docs/  @docs-team   # a trailing comment
docs/*  @docs-top
/src/** @src-team
apps/   @apps-team
/build/ 
"""


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def repo(tmp_path: Path, where: str, text: str) -> Path:
    p = tmp_path / "repo" / where
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return tmp_path / "repo"


def who(tmp_path: Path, where: str, text: str, path: str) -> list[str]:
    got = run("--from", str(repo(tmp_path, where, text)), path)
    return (
        got.stdout.splitlines()[1:-1] if got.returncode else got.stdout.splitlines()[1:]
    )


def test_the_last_matching_rule_wins_and_is_cited_by_line(tmp_path):
    got = run("--from", str(repo(tmp_path, ".github/CODEOWNERS", GITHUB)), "web/app.js")
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines()[1] == "    .github/CODEOWNERS:3   *.js   @js-owner"


def test_a_folder_rule_covers_everything_under_it_and_a_star_only_its_top(tmp_path):
    r = repo(tmp_path, ".github/CODEOWNERS", GITHUB)
    deep = run("--from", str(r), "docs/guide/intro.md").stdout
    assert "CODEOWNERS:4   /docs/   @docs-team" in deep
    top = run("--from", str(r), "docs/intro.md").stdout
    assert "CODEOWNERS:5   docs/*   @docs-top" in top  # the later rule wins
    far = run("--from", str(r), "a/docs/intro.md").stdout
    assert "docs-team" not in far and "docs-top" not in far  # /docs/ is anchored
    assert "CODEOWNERS:2   *.js" not in far and "@everyone" in far


def test_an_unanchored_folder_matches_at_any_depth(tmp_path):
    r = repo(tmp_path, ".github/CODEOWNERS", GITHUB)
    assert "@apps-team" in run("--from", str(r), "x/y/apps/z/main.py").stdout
    assert "@apps-team" not in run("--from", str(r), "myapps/main.py").stdout


def test_a_rule_with_no_owners_clears_the_file_and_is_unowned(tmp_path):
    got = run(
        "--from", str(repo(tmp_path, ".github/CODEOWNERS", GITHUB)), "build/out.bin"
    )
    assert got.returncode == 42
    assert "CODEOWNERS:8   /build/   (no owners)" in got.stdout
    assert "1 of 1 path with no owner." in got.stdout


def test_a_path_no_rule_matches_waits_on_you(tmp_path):
    got = run(
        "--from",
        str(repo(tmp_path, "CODEOWNERS", "/src/ @a\n")),
        "README.md",
        "src/x.py",
    )
    assert got.returncode == 42
    assert (
        "no rule matches" in got.stdout and "1 of 2 paths with no owner." in got.stdout
    )


def test_gitlab_sections_each_decide_and_defaults_fill_a_rule_with_no_owners(tmp_path):
    text = "*.py @all\n[Docs] @doc-team\n*.md\n^[Optional][2]\n/src/ @src\n[Docs]\nREADME.md @readme\n"
    r = repo(tmp_path, ".gitlab/CODEOWNERS", text)
    out = run("--from", str(r), "README.md").stdout
    assert (
        "CODEOWNERS:7   README.md   @readme  [Docs]" in out
    )  # a section named twice is one
    assert "CODEOWNERS:3" not in out  # and its last match wins
    md = run("--from", str(r), "NOTES.md").stdout
    assert (
        "CODEOWNERS:3   *.md   @doc-team  [Docs]" in md
    )  # the default fills the empty rule
    both = run("--from", str(r), "src/a.py").stdout
    assert (
        "CODEOWNERS:1   *.py   @all" in both
        and "CODEOWNERS:5   /src/   @src  [Optional]" in both
    )


def test_forgejo_rules_are_regexes_and_every_match_adds_owners(tmp_path):
    text = ".*\\.go$ @gophers\n^cmd/ @cli-team\n"
    r = repo(tmp_path, ".forgejo/CODEOWNERS", text)
    out = run("--from", str(r), "cmd/main.go").stdout
    assert (
        "CODEOWNERS:1" in out
        and "@gophers" in out
        and "CODEOWNERS:2" in out
        and "@cli-team" in out
    )


def test_a_bad_regex_is_noted_and_skipped(tmp_path):
    got = run("--from", str(repo(tmp_path, ".gitea/CODEOWNERS", "( @a\n.* @b\n")), "x")
    assert (
        got.returncode == 0
        and "note: .gitea/CODEOWNERS:1" in got.stderr
        and "@b" in got.stdout
    )


def test_the_places_are_tried_in_order_and_none_is_unowned(tmp_path):
    r = repo(tmp_path, "docs/CODEOWNERS", "* @docs\n")
    (r / "CODEOWNERS").write_text("* @top\n")
    assert "@top" in run("--from", str(r), "a").stdout
    got = run("--from", str(tmp_path / "empty-nothing-here-yet"), "a")
    assert got.returncode == 2
    (tmp_path / "bare").mkdir()
    bare = run("--from", str(tmp_path / "bare"), "a")
    assert bare.returncode == 42 and "No CODEOWNERS file here" in bare.stdout


def test_a_dot_slash_and_a_leading_slash_on_the_path_are_the_same_path(tmp_path):
    r = repo(tmp_path, "CODEOWNERS", "/src/ @src\n")
    for p in ("./src/a.py", "/src/a.py", "src\\a.py"):
        assert "@src" in run("--from", str(r), p).stdout


def test_a_box_is_read_through_its_pile(tmp_path):
    pile = repo(tmp_path, "CODEOWNERS", "* @everyone\n")
    box = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), "--now", "2026-10-29T00:00:00Z"],
                   check=True, capture_output=True)  # fmt: skip
    assert run("--box", str(box), "a/b").returncode == 0


def test_matching_does_not_need_the_path_to_exist_and_writes_nothing(tmp_path):
    r = repo(tmp_path, "CODEOWNERS", "* @x\n")
    before = sorted(p.name for p in tmp_path.rglob("*"))
    run("--from", str(r), "no/such/file")
    assert sorted(p.name for p in tmp_path.rglob("*")) == before


def test_the_glob_translation(tmp_path):
    g = codeowners.glob_regex
    assert g("**/logs").match("a/b/logs") and g("**/logs").match("logs/x")
    assert g("/a/**/b").match("a/b") and g("/a/**/b").match("a/x/y/b")
    assert g("?.md").match("a.md") and not g("?.md").match("ab.md")
    assert g("\\#x").match("#x")


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    for argv in ([], ["--from"], ["--from", str(tmp_path)], ["x"],
                 ["--from", str(tmp_path), "--box", str(tmp_path), "x"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "codeowners.py" in got.stderr
    assert run("--box", str(tmp_path), "x").returncode == 2
