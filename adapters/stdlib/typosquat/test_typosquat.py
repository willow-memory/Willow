"""typosquat: flags a locked name one letter off a popular one, not the popular
name itself, not a name two letters off; respects ecosystems; refuses, never
crashes, on a bad command line; and writes nothing."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TS = HERE / "typosquat.py"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TS), *argv], capture_output=True, text=True
    )


def write(folder: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        p = folder / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def npm_lock(**pkgs: str) -> str:
    return json.dumps(
        {"packages": {f"node_modules/{n}": {"version": v} for n, v in pkgs.items()}}
    )


def test_a_name_one_letter_off_a_popular_one_is_flagged(tmp_path):
    src = tmp_path / "src"
    top = tmp_path / "top.txt"
    top.write_text("requests\nlodash\n", encoding="utf-8")
    write(src, {"package-lock.json": npm_lock(reqests="1.0.0", lodash="4.17.21")})
    got = run("--from", str(src), "--top", str(top))
    assert got.returncode == 42, got.stdout + got.stderr
    assert "reqests -> looks like requests" in got.stdout
    assert "lodash" not in got.stdout  # the popular name itself is not flagged
    assert "1 of 2" in got.stdout


def test_an_exact_popular_name_is_not_flagged(tmp_path):
    src = tmp_path / "src"
    top = tmp_path / "top.txt"
    top.write_text("requests\nlodash\n", encoding="utf-8")
    write(src, {"package-lock.json": npm_lock(requests="2.31.0", lodash="4.17.21")})
    got = run("--from", str(src), "--top", str(top))
    assert got.returncode == 0, got.stdout + got.stderr
    assert "No locked dependency" in got.stdout


def test_a_name_two_letters_off_is_not_flagged(tmp_path):
    src = tmp_path / "src"
    top = tmp_path / "top.txt"
    top.write_text("requests\n", encoding="utf-8")
    # reqsts drops two letters from requests; requestz2 changes one and adds one
    write(src, {"package-lock.json": npm_lock(reqsts="1.0.0", requestz2="1.0.0")})
    got = run("--from", str(src), "--top", str(top))
    assert got.returncode == 0, got.stdout + got.stderr
    assert "No locked dependency" in got.stdout


def test_a_substitution_insertion_and_deletion_are_each_one_letter(tmp_path):
    src = tmp_path / "src"
    top = tmp_path / "top.txt"
    top.write_text("requests\n", encoding="utf-8")
    # one substitution (requesta), one deletion (reqests), one insertion (requestss)
    # and one deletion at the start (equests)
    for bad in ("requesta", "reqests", "requestss", "equests"):
        write(src, {"package-lock.json": npm_lock(**{bad: "1.0.0"})})
        got = run("--from", str(src), "--top", str(top))
        assert got.returncode == 42 and f"{bad} -> looks like requests" in got.stdout, (
            bad, got.stdout, got.stderr)  # fmt: skip


def test_an_ecosystem_on_the_top_line_limits_the_comparison(tmp_path):
    src = tmp_path / "src"
    top = tmp_path / "top.txt"
    top.write_text("npm requests\n", encoding="utf-8")
    # reqeusts is a PyPI package here; the npm popular name does not apply to it
    write(src, {"requirements.txt": "reqests==1.0.0\n"})
    got = run("--from", str(src), "--top", str(top))
    assert got.returncode == 0, got.stdout + got.stderr
    write(src, {"package-lock.json": npm_lock(reqests="1.0.0")})
    got = run("--from", str(src), "--top", str(top))
    assert got.returncode == 42, got.stdout + got.stderr


def test_a_bare_name_on_the_top_list_applies_to_any_ecosystem(tmp_path):
    src = tmp_path / "src"
    top = tmp_path / "top.txt"
    top.write_text("# popular names\nrequests\n", encoding="utf-8")
    write(src, {"requirements.txt": "reqests==1.0.0\n"})
    got = run("--from", str(src), "--top", str(top))
    assert got.returncode == 42 and "reqests -> looks like requests" in got.stdout


def test_pypi_names_fold_before_they_are_compared(tmp_path):
    src = tmp_path / "src"
    top = tmp_path / "top.txt"
    top.write_text("PyPI python-dateutil\n", encoding="utf-8")
    # Python_Dateutil is the same package, folded: not a typosquat of itself
    write(src, {"requirements.txt": "Python_Dateutil==2.8.2\n"})
    got = run("--from", str(src), "--top", str(top))
    assert got.returncode == 0, got.stdout + got.stderr
    # python_dateutl is one letter off once folded
    write(src, {"requirements.txt": "python_dateutl==2.8.2\n"})
    got = run("--from", str(src), "--top", str(top))
    assert got.returncode == 42 and "looks like python-dateutil" in got.stdout


def test_no_lockfiles_is_clean(tmp_path):
    src = tmp_path / "src"
    write(src, {"garden.md": "tomatoes want sun\n"})
    top = tmp_path / "top.txt"
    top.write_text("requests\n", encoding="utf-8")
    for argv in (["--from", str(src)], ["--from", str(src), "--top", str(top)]):
        got = run(*argv)
        assert got.returncode == 0 and "No lockfiles found" in got.stdout, got.stdout


def test_without_a_top_it_lists_the_dependencies(tmp_path):
    src = tmp_path / "src"
    write(src, {"requirements.txt": "flask==2.0.1\nrequests==2.19.1\n"})
    got = run("--from", str(src))
    assert got.returncode == 0, got.stderr
    assert "flask 2.0.1" in got.stdout and "2 locked dependencies" in got.stdout


def test_it_writes_nothing(tmp_path):
    src = tmp_path / "src"
    top = tmp_path / "top.txt"
    top.write_text("requests\n", encoding="utf-8")
    write(src, {"package-lock.json": npm_lock(reqeusts="1.0.0")})
    before = {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}
    run("--from", str(src), "--top", str(top))
    after = {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}
    assert before == after and set(after) == set(before)


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    # a malformed command line prints the usage, which names the script
    for argv in ([], ["--from", str(tmp_path / "f"), "--extra"],
                 ["--box", "b", "--from", str(tmp_path / "f")],
                 ["--top", str(tmp_path / "t")]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "typosquat.py" in got.stderr, (argv, got.stderr)


def test_a_bad_target_is_refused(tmp_path):
    (tmp_path / "f").mkdir()
    top = tmp_path / "top.txt"
    top.write_text("requests\n", encoding="utf-8")
    crowded = tmp_path / "crowded.txt"
    crowded.write_text("npm requests extra\n", encoding="utf-8")
    # a well-formed command line naming something that isn't there is refused
    for argv in (["--from", str(tmp_path / "missing")],
                 ["--from", str(tmp_path / "f"), "--top", str(tmp_path / "nofile")],
                 ["--from", str(tmp_path / "f"), "--top", str(crowded)],
                 ["--box", str(tmp_path / "f")]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and got.stderr.startswith("refused"), (
            argv,
            got.stderr,
        )


def test_edit_distance_is_optimal_string_alignment(tmp_path):
    import typosquat

    assert typosquat.edit_distance("requests", "requests") == 0
    assert typosquat.edit_distance("reqeusts", "requests") == 1  # one adjacent swap
    assert typosquat.edit_distance("ba", "ab") == 1  # a bare swap is one edit
    assert typosquat.edit_distance("reqests", "requests") == 1  # one deletion
    assert typosquat.edit_distance("", "abc") == 3
    assert typosquat.edit_distance("kitten", "sitting") == 3  # no swaps: same as before


def test_an_adjacent_swap_is_flagged(tmp_path):
    src = tmp_path / "src"
    top = tmp_path / "top.txt"
    top.write_text("requests\nlodash\n", encoding="utf-8")
    # reqeusts (swap) and lodahs (swap) are each one edit from the popular name
    write(src, {"package-lock.json": npm_lock(reqeusts="1.0.0", lodahs="4.17.4")})
    got = run("--from", str(src), "--top", str(top))
    assert got.returncode == 42, got.stdout + got.stderr
    assert "reqeusts -> looks like requests" in got.stdout
    assert "lodahs -> looks like lodash" in got.stdout and "2 of 2" in got.stdout
