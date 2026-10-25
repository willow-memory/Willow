"""repo-pile: repos cloned from a source, kept only under a licence an
Apache-2.0 project can use, their docs made the pile of a box the kernel
makes, indexed by scan; then asked, checked and backed up by willow's own
add-ons. The repos here are made on this machine and cloned over file://,
so nothing goes online."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "repo_pile.py"

MIT = "MIT License\n\nPermission is hereby granted, free of charge, to any person\n"
GPL = "GNU GENERAL PUBLIC LICENSE\nVersion 3, 29 June 2007\n"
GIT = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.org",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.org",
       "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}  # fmt: skip


def repo(source: Path, name: str, files: dict[str, str]) -> None:
    """A git repo at source/name holding files, in one commit."""
    root = source / name
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    env = {**os.environ, **GIT}
    for argv in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-qm", "one"]):
        subprocess.run(["git", *argv], cwd=root, env=env, check=True)


@pytest.fixture
def source(tmp_path: Path) -> Path:
    src = tmp_path / "source"
    repo(src, "ada/paint", {
        "LICENSE": MIT,
        "README.md": "Paint reads PSD layers; write to ada@example.org.\n",
        "docs/blend.md": "Blend modes follow the ISO 32000 spec.\n",
        "src/main.rs": "fn main() { /* PSD layers are read here */ }\n",
        "tests/case.md": "A test fixture, never in the pile.\n",
    })  # fmt: skip
    repo(src, "ada/copyleft", {"COPYING": GPL, "README.md": "Copyleft notes.\n"})
    repo(src, "ada/bare", {"README.md": "No licence here.\n"})
    repo(src, "ada/dual", {"LICENSE-MIT": MIT, "LICENSE-GPL": GPL,
                           "README.md": "Dual licensed notes.\n"})  # fmt: skip
    repo(
        src, "ada/mixed", {"LICENSE": MIT + GPL, "README.md": "One file, two texts.\n"}
    )
    return src


def run(*argv, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, argv)], env=env,
                          capture_output=True, text=True)  # fmt: skip


def listing(tmp_path: Path, *names: str) -> Path:
    p = tmp_path / "repos.txt"
    p.write_text("# repos to study\n" + "".join(f"{n}\n" for n in names))
    return p


def build(tmp_path: Path, source: Path, *names: str, extra=()) -> tuple:
    base = tmp_path / "base"
    got = run("build", "--to", base, "--repos", listing(tmp_path, *names),
              "--key", tmp_path / "key", "--source", f"file://{source}", *extra)  # fmt: skip
    return base, got


def files(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}  # fmt: skip


def rows(base: Path) -> list[dict]:
    text = (base / "box" / "record.jsonl").read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines()]


def test_build_keeps_permissive_repos_and_makes_their_docs_the_pile(tmp_path, source):
    notes = tmp_path / "NOTES.md"
    notes.write_text("Our notes on paint.\n")
    base, got = build(tmp_path, source, "ada/paint", "ada/copyleft", "ada/bare",
                      "ada/dual", "ada/mixed", extra=("--notes", notes))  # fmt: skip
    assert got.returncode == 0, got.stdout + got.stderr
    assert sorted(p.name for p in (base / "repos").iterdir()) == [
        "ada-dual",
        "ada-paint",
    ]
    assert (base / "REJECTED.txt").read_text().splitlines() == [
        "ada/copyleft\tcopyleft: GPL",
        "ada/bare\tno licence it can read",
        "ada/mixed\tcopyleft: GPL",
    ]
    assert sorted(files(base / "pile")) == [
        "NOTES.md",
        "repos/ada-dual/LICENSE-GPL",
        "repos/ada-dual/LICENSE-MIT",
        "repos/ada-dual/README.md",
        "repos/ada-paint/LICENSE",
        "repos/ada-paint/README.md",
        "repos/ada-paint/docs/blend.md",
    ]
    assert "[licence] ada/paint: kept (MIT)" in got.stdout
    assert "[licence] ada/copyleft: left out (copyleft: GPL)" in got.stdout
    assert "[secrets] No passwords, keys or card numbers found" in got.stdout
    cfg = json.loads((base / "box" / "kernel.json").read_text())
    assert cfg["pile"] == str((base / "pile").resolve())
    for index in ("index-pile", "index-code"):
        assert (base / index / "index.json").exists()
    assert [r["kind"] for r in rows(base)] == ["boot", "changed"]
    assert "[verify] the chain holds" in got.stdout


def test_a_second_build_fetches_nothing_and_gives_the_same_pile(tmp_path, source):
    base, got = build(tmp_path, source, "ada/paint", extra=("--no-code-index",))
    assert got.returncode == 0, got.stderr
    first = files(base / "pile")
    os.rename(source, tmp_path / "gone")  # a second clone would now fail
    _, again = build(tmp_path, source, "ada/paint", extra=("--no-code-index",))
    assert again.returncode == 0, again.stdout + again.stderr
    assert files(base / "pile") == first
    assert "[box] already made" in again.stdout
    assert "not cloned" not in again.stdout
    assert not (base / "index-code").exists()


def test_a_secret_in_the_docs_is_found_by_place_never_shown(tmp_path, source):
    repo(source, "ada/leaky", {"LICENSE": MIT, "README.md": "password: hunter2\n"})
    base, got = build(tmp_path, source, "ada/leaky", extra=("--no-code-index",))
    assert got.returncode == 0
    assert "[secrets] repos/ada-leaky/README.md:1" in got.stdout
    assert "hunter2" not in got.stdout
    check = run("check", "--base", base)
    assert "[secrets] 1 place hold" in check.stdout and "hunter2" not in check.stdout


@pytest.mark.parametrize("name", ["COPYING.md", "apache-2.0.LICENSE", "UNLICENSE"])
def test_a_licence_file_is_known_by_its_name_wherever_the_word_is(
    tmp_path, source, name
):
    text = {"UNLICENSE": "This is free and unencumbered software released into "
            "the public domain.\n"}.get(name, MIT)  # fmt: skip
    repo(source, "ada/named", {name: text, "README.md": "Named.\n",
                               "licensedcode.toml": GPL})  # fmt: skip
    base, got = build(tmp_path, source, "ada/named", extra=("--no-code-index",))
    assert got.returncode == 0, got.stdout
    assert (base / "pile" / "repos" / "ada-named" / name).exists()
    assert not (base / "pile" / "repos" / "ada-named" / "licensedcode.toml").exists()


def test_a_repo_that_cannot_be_cloned_is_said_and_listed(tmp_path, source):
    base, got = build(tmp_path, source, "ada/paint", "ada/missing",
                      extra=("--no-code-index",))  # fmt: skip
    assert got.returncode == 0
    assert "[clone] ada/missing: not cloned" in got.stdout
    line = (base / "REJECTED.txt").read_text().splitlines()[0]
    assert line.startswith("ada/missing\tnot cloned: ")


def test_lines_that_are_not_repos_are_skipped_and_an_empty_list_builds_nothing(
    tmp_path,
):
    p = tmp_path / "list.txt"
    p.write_text("Tomatoes want sun.\n\n# a comment\nnot a/repo/at all\n")
    base = tmp_path / "base"
    got = run("build", "--to", base, "--repos", p, "--key", tmp_path / "key")
    assert got.returncode == 42, got.stderr
    assert "[list] line 1 skipped: not owner/repo" in got.stdout
    assert "[list] line 4 skipped: not owner/repo" in got.stdout
    assert "nothing to build" in got.stdout
    assert not base.exists() and not (tmp_path / "key").exists()


def test_nothing_kept_builds_nothing(tmp_path, source):
    base, got = build(tmp_path, source, "ada/copyleft")
    assert got.returncode == 42
    assert "nothing to build: no repo was kept" in got.stdout
    assert not (base / "box").exists() and not (tmp_path / "key").exists()


def test_without_git_it_refuses_and_names_git(tmp_path, source):
    empty = tmp_path / "no-programs"
    empty.mkdir()
    base = tmp_path / "base"
    got = run("build", "--to", base, "--repos", listing(tmp_path, "ada/paint"),
              "--key", tmp_path / "key", env={**os.environ, "PATH": str(empty)})  # fmt: skip
    assert got.returncode == 2 and "git" in got.stderr
    assert not base.exists()


def test_a_missing_parent_or_list_is_refused(tmp_path, source):
    got = run("build", "--to", tmp_path / "no" / "base", "--repos",
              listing(tmp_path, "ada/paint"), "--key", tmp_path / "key")  # fmt: skip
    assert got.returncode == 2 and "make it first" in got.stderr
    got = run("build", "--to", tmp_path / "base", "--repos", tmp_path / "none.txt",
              "--key", tmp_path / "key")  # fmt: skip
    assert got.returncode == 2 and "must be a file" in got.stderr
    assert not (tmp_path / "base").exists()


def questions(tmp_path: Path, *lines: str) -> Path:
    p = tmp_path / "questions.txt"
    p.write_text("".join(f"{line}\n" for line in lines))
    return p


def test_ask_answers_from_both_indexes_and_hides_what_people_left(tmp_path, source):
    base, _ = build(tmp_path, source, "ada/paint")
    q = questions(tmp_path, "psd\tpsd layers", "none\tqqqq zzzz")
    got = run("ask", "--base", base, "--questions", q)
    assert got.returncode == 0, got.stderr
    answers = [json.loads(line) for line in got.stdout.splitlines()]
    assert [(a["index"].endswith("index-pile"), a["question"], a["state"])
            for a in answers] == [
        (True, "psd", "populated"), (True, "none", "empty"),
        (False, "psd", "populated"), (False, "none", "empty"),
    ]  # fmt: skip
    where = [s["where"] for s in answers[2]["served"]]
    assert "ada-paint/src/main.rs:1" in where, "the code index holds the source"
    assert "ada@example.org" not in got.stdout and "[withheld: email]" in got.stdout
    assert json.loads(got.stderr) == {"withheld": {"email": 2}}, "once per index"
    raw = run("ask", "--base", base, "--questions", q, "--raw")
    assert "ada@example.org" in raw.stdout and raw.stderr == ""
    bm25 = run("ask", "--base", base, "--questions", q, "--rank", "bm25")
    assert all(json.loads(a)["ranked_by"] == "bm25" for a in bm25.stdout.splitlines())


def test_ask_todo_adds_the_lines_each_answer_s_file_marks_to_do(tmp_path, source):
    repo(source, "ada/next", {"LICENSE": MIT,
                              "README.md": "PSD masks are read.\n\nTODO: read PSD layers too.\n"})  # fmt: skip
    base, _ = build(tmp_path, source, "ada/next", extra=("--no-code-index",))
    q = questions(tmp_path, "masks\tpsd masks")
    plain = json.loads(run("ask", "--base", base, "--questions", q).stdout)
    assert "marked" not in plain["served"][0]
    got = json.loads(run("ask", "--base", base, "--questions", q, "--todo").stdout)
    assert [m["where"] for m in got["served"][0]["marked"]] == [
        "repos/ada-next/README.md:3"
    ]


def test_ask_uses_the_box_words_list(tmp_path, source):
    words = tmp_path / "words.txt"
    words.write_text("photoshop = psd\n")
    words.chmod(0o600)
    base, got = build(tmp_path, source, "ada/paint",
                      extra=("--words", words, "--no-code-index"))  # fmt: skip
    assert got.returncode == 0, got.stdout + got.stderr
    q = questions(tmp_path, "ps\tphotoshop")
    assert (
        json.loads(run("ask", "--base", base, "--questions", q).stdout)["state"]
        == "populated"
    )
    other = tmp_path / "other.txt"
    other.write_text("photoshop = canvas\n")
    other.chmod(0o600)
    got = run("ask", "--base", base, "--questions", q, "--words", other)
    assert json.loads(got.stdout)["state"] == "empty", "--words names another list"


def test_bite_goes_on_the_record_and_nothing_is_ever_sealed(tmp_path, source):
    base, _ = build(tmp_path, source, "ada/paint", extra=("--no-code-index",))
    got = run("bite", "--base", base, "blend modes spec")
    assert got.returncode == 0, got.stderr
    assert json.loads(got.stdout)["state"] == "populated"
    assert [r["kind"] for r in rows(base)] == ["boot", "changed", "bite"]
    nothing = run("bite", "--base", base, "weather in atlanta")
    assert nothing.returncode == 42
    assert not [r for r in rows(base) if r["kind"] == "seal"]


def test_quote_finds_an_exact_line(tmp_path, source):
    base, _ = build(tmp_path, source, "ada/paint", extra=("--no-code-index",))
    got = run("quote", "--base", base, "Blend modes follow the ISO 32000 spec.")
    assert got.returncode == 0 and "repos/ada-paint/docs/blend.md:1" in got.stdout


def test_report_check_and_backup(tmp_path, source):
    base, _ = build(tmp_path, source, "ada/paint", extra=("--no-code-index",))
    run("bite", "--base", base, "blend modes spec")
    got = run("report", "--base", base, "--days", "3")
    assert got.returncode == 0, got.stderr
    titles = [line for line in got.stdout.splitlines() if line.startswith("## ")]
    assert titles == ["## digest", "## asked again", "## stale",
                      "## questions by day", "## history", "## verify"]  # fmt: skip
    assert "the chain holds: 3 rows, 0 sealed" in got.stdout
    got = run("check", "--base", base)
    assert got.returncode == 0
    assert [line.split("]")[0] for line in got.stdout.splitlines()] == [
        "[xref",
        "[todo",
        "[secrets",
        "[each",
    ]
    assert "[todo] 0 lines marked to do" in got.stdout
    (base / "pile" / "NEXT.md").write_text("TODO: read the blend spec again\n")
    assert "[todo] 1 lines marked to do" in run("check", "--base", base).stdout
    backups = tmp_path / "backups"
    backups.mkdir()
    got = run("backup", "--base", base, "--to", backups)
    assert got.returncode == 0, got.stderr
    assert [p.suffix for p in backups.iterdir()] == [".zip"]


@pytest.mark.parametrize("argv", [
    [], ["seal"], ["build"], ["ask", "--base"], ["ask", "--base", "x"],
    ["build", "--to", "b", "--repos", "r", "--key", "k", "--stray", "more"],
    ["ask", "--base", "b", "--questions", "q", "--rank", "best"],
    ["bite", "--base", "b"], ["bite", "--base", "b", "one", "two"],
    ["quote", "--base", "b", "--todo", "x"], ["report", "--base", "b", "--base", "c"],
])  # fmt: skip
def test_a_bad_command_line_is_refused_and_says_how(argv):
    got = run(*argv)
    assert got.returncode == 2 and "repo_pile.py" in got.stderr


def test_a_base_without_a_box_is_refused(tmp_path):
    for argv in (["check"], ["report"], ["bite", "x"]):
        got = run(*argv[:1], "--base", tmp_path, *argv[1:])
        assert got.returncode == 2 and "holds no box" in got.stderr
