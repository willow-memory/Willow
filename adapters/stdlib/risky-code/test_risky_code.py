"""risky-code: lines matching a known-dangerous pattern, by file and line,
across languages; clean when nothing matches; refuses a bad command line;
writes nothing."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RC = HERE / "risky_code.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def on(tmp: Path, files: dict[str, str]) -> subprocess.CompletedProcess:
    pile = tmp / "pile"
    pile.mkdir(exist_ok=True)
    for name, text in files.items():
        p = pile / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return run(str(RC), "--from", str(pile))


def test_sinks_across_languages_are_found_by_file_and_line(tmp_path):
    got = on(tmp_path, {
        "a.py": "import subprocess\nsubprocess.run(cmd, shell=True)\nr = pickle.loads(blob)\n",
        "b.php": "<?php $x = shell_exec($_GET['c']); $o = unserialize($_POST['d']); ?>\n",
        "c.js": "const r = eval(userInput);\nfetch(u, {rejectUnauthorized: false});\n",
        "d.go": 'c := &tls.Config{InsecureSkipVerify: true}\n',
    })  # fmt: skip
    assert got.returncode == 42, got.stdout + got.stderr
    out = got.stdout
    assert "command injection" in out and "a.py:2" in out and "b.php:1" in out
    assert "insecure deserialization" in out and "a.py:3" in out
    assert "code injection" in out and "c.js:1" in out
    assert "broken tls" in out and "c.js:2" in out and "d.go:1" in out
    assert "match a risky-code pattern" in out


def test_sql_injection_is_grouped(tmp_path):
    got = on(
        tmp_path, {"q.py": "db.execute(\"SELECT * FROM u WHERE n='%s'\" % name)\n"}
    )
    assert got.returncode == 42 and "sql injection" in got.stdout
    assert "q.py:1" in got.stdout


def test_clean_code_matches_nothing(tmp_path):
    got = on(tmp_path, {
        "ok.py": "def add(a, b):\n    return a + b\n",
        "notes.md": "The tomatoes want sun and the frost comes in October.\n",
    })  # fmt: skip
    assert got.returncode == 0 and "No lines matched" in got.stdout


def test_the_class_label_is_a_hint_bare_exec_reads_as_code_injection(tmp_path):
    # a bare exec( is ambiguous across languages; it surfaces, under code injection
    got = on(
        tmp_path,
        {"x.js": "const { exec } = require('child_process');\nexec(req.query.host);\n"},
    )
    assert (
        got.returncode == 42
        and "code injection" in got.stdout
        and "x.js:2" in got.stdout
    )


def test_a_long_line_is_cut_to_exactly_ninety(tmp_path):
    got = on(tmp_path, {"l.py": "x = eval(" + "a" * 200 + ")\n"})
    row = [ln for ln in got.stdout.splitlines() if "l.py:1" in ln][0]
    # one file, so no padding: "    l.py:1  " then the text, trimmed to 90 chars
    shown = row.split("l.py:1", 1)[1][2:]
    assert len(shown) == 90


def test_the_counts_are_exact(tmp_path):
    got = on(tmp_path, {
        "a.py": "eval(x)\nos.system(y)\n",   # code injection, command injection
        "b.py": "pickle.loads(z)\n",          # insecure deserialization
    })  # fmt: skip
    assert got.returncode == 42, got.stdout
    # three matching lines, each a distinct place; the summary says so exactly
    assert "3 lines in 3 places match a risky-code pattern" in got.stdout


def test_one_match_is_singular(tmp_path):
    got = on(tmp_path, {"a.py": "eval(x)\n"})
    assert "1 line in 1 place match" in got.stdout


def test_it_writes_nothing(tmp_path):
    files = {"a.py": "eval(x)\n"}
    got = on(tmp_path, files)
    pile = tmp_path / "pile"
    before = {p: p.read_bytes() for p in pile.rglob("*") if p.is_file()}
    run(str(RC), "--from", str(pile))
    assert {p: p.read_bytes() for p in pile.rglob("*") if p.is_file()} == before
    assert got.returncode == 42


def test_box_mode_reads_the_box_pile(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "v.py").write_text("os.system(user_input)\n")
    box = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(box), "--pile", str(pile),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    got = run(str(RC), "--box", str(box))
    assert (
        got.returncode == 42
        and "command injection" in got.stdout
        and "v.py:1" in got.stdout
    )


def test_a_bad_command_line_is_refused(tmp_path):
    (tmp_path / "f").mkdir()
    for argv in ([], ["--box"], ["--from", str(tmp_path / "missing")],
                 ["--from", str(tmp_path / "f"), "--extra"], ["--bad", str(tmp_path / "f")]):  # fmt: skip
        got = run(str(RC), *argv)
        assert got.returncode == 2, (argv, got.stdout, got.stderr)


def test_not_a_kernel_box_is_refused(tmp_path):
    (tmp_path / "b").mkdir()
    got = run(str(RC), "--box", str(tmp_path / "b"))
    assert got.returncode == 2 and got.stderr.startswith("refused")
