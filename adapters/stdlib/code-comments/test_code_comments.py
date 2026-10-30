"""code-comments: a source file's comments and docstrings on the lines they were on; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "code_comments.py"
spec = importlib.util.spec_from_file_location("code_comments", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = b'"""Module docstring.\n\nSecond line."""\n# A cache of parsed answers.\nTTL = 60  # seconds an entry lives\ns = "# not a comment"\n\n\ndef f():\n    """Do the thing."""\n    return 1\n'


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


def test_python_comments_and_docstrings_sit_on_their_own_source_lines():
    assert mod.convert(SAMPLE, "cache.py") == (
        "Module docstring.\n\nSecond line.\nA cache of parsed answers.\nseconds an entry lives\n\n\n\n\nDo the thing.\n\n"
    )


def test_the_mirror_has_as_many_lines_as_the_source():
    for src in (
        SAMPLE,
        b"x = 1  # c\n",
        b"# only\n\n\n",
        b"x = 1\n# c",
        b"# a\r\n\r\ny = 2\r\n",
    ):
        out = mod.convert(src, "a.py")
        want = len(src.decode().replace("\r\n", "\n").split("\n")) - (
            1 if src.endswith(b"\n") else 0
        )
        assert out.count("\n") == want and out.endswith("\n"), src


def test_a_hash_inside_a_string_or_a_shebang_is_not_a_comment():
    assert mod.python_comments(
        "s = \"a # b\"\nt = '# c'\nu = 1  # real\n#!/usr/bin/env python\n"
    ) == {3: ["real"]}
    assert mod.c_like_comments(
        '#!/bin/sh\n# real\necho "# not"  # also real\n', ".sh"
    ) == {2: ["real"], 3: ["also real"]}


def test_c_like_line_block_and_doc_comments_with_their_marks_off():
    src = "// one\n/// doc\nint x; // trailing\n/*\n * block line\n * another\n */\nint y; /* inline */ int z;\n/** javadoc */\n"
    assert mod.c_like_comments(src, ".c") == {
        1: ["one"],
        2: ["doc"],
        3: ["trailing"],
        5: ["block line"],
        6: ["another"],
        8: ["inline"],
        9: ["javadoc"],
    }


def test_strings_template_strings_and_character_literals_are_stepped_over():
    c = mod.c_like_comments
    assert c('s = "// not"; // yes\n', ".c") == {1: ["yes"]}
    assert c('s = "esc \\" // still string"; // yes\n', ".c") == {1: ["yes"]}
    assert c("c = '/'; d = '\\\\'; // yes\n", ".c") == {1: ["yes"]}
    assert c("s = 'a // b'; // yes\n", ".js") == {1: ["yes"]}
    assert c("t = `line one\nline // two`; // yes\n", ".js") == {2: ["yes"]}
    assert c("fn f<'a>(x: &'a str) {} // yes\n", ".rs") == {1: ["yes"]}
    assert c("// a\n/* b\nc */ d // e\n", ".java") == {
        1: ["a"],
        2: ["b"],
        3: ["c", "e"],
    }


def test_a_block_comment_that_never_ends_runs_to_the_end_and_php_and_ruby_hash_comments():
    assert mod.c_like_comments("x;\n/* open\nstill", ".c") == {
        2: ["open"],
        3: ["still"],
    }
    assert mod.c_like_comments("$a = 1; # note\n// slash\n", ".php") == {
        1: ["note"],
        2: ["slash"],
    }
    assert mod.c_like_comments("puts 1 # note\n", ".rb") == {1: ["note"]}


def test_a_file_with_no_comment_an_unknown_extension_or_that_does_not_parse_is_not_a_result_or_an_error():
    assert (
        mod.convert(b"x = 1\n", "a.py") is None
        and mod.convert(b"int x;\n", "a.c") is None
        and mod.convert(b"# c\n", "notes.txt") is None
    )
    assert mod.convert(b"# c\n", "") is None
    try:
        mod.convert(b"def (:\n# c\n", "bad.py")
    except (SyntaxError, mod.tokenize.TokenError):
        pass
    else:
        raise AssertionError("bad python")


def test_a_file_that_cannot_be_read_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(
        tmp_path, {"a.py": SAMPLE, "nocomment.c": b"int x;\n", "bad.py": b"def (:\n"}
    )
    assert "wrote 1 files" in got.stdout and "skipped 2" in got.stdout
    assert (out / "a.py.txt").is_file()


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"src/cache.py": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "src/cache.py.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {"src/cache.py": SAMPLE, ".hid/src/cache.py": SAMPLE, ".src/cache.py": SAMPLE},
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["src/cache.py.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"src/cache.py": SAMPLE})
    before = (tmp_path / "src" / "src/cache.py").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "src/cache.py.txt").read_bytes() == (
        out / "src/cache.py.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "src/cache.py").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(tmp_path, {"good.py": SAMPLE, "bad.py": b"def (:\n"})
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.py.txt").is_file() and not (out / "bad.py.txt").exists()


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
        assert got.returncode == 2 and "code_comments.py" in got.stderr
