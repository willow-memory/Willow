"""transcript-redact: each shape taken out and listed with a stub, the copy
written even clean, JSON kept JSON, and nothing ever printed whole."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "transcript_redact", HERE / "transcript_redact.py"
)
tr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tr)

KEY = "sk-abcdefghijklmnop1234"
JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.dBjftJeZ4CVPmB92K27uhbUJU1p1r_wW1gFWFOEjXk"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "transcript_redact.py"), *argv],
        capture_output=True, text=True,
    )  # fmt: skip


def test_each_shape_is_taken_out_and_listed_with_a_stub():
    line, got = tr.redact(f"auth {KEY} from /home/drew/.config, mail drew@example.org")
    assert line == ("auth [redacted:key] from /home/[redacted]/.config,"
                    " mail [redacted:email]")  # fmt: skip
    assert [g[0] for g in got] == ["a key", "a home path", "an email"]
    assert got[0][2] == "…1234" and got[1][2] == "…drew"
    assert got[2][2] == "…d@example.org"
    assert KEY not in line and "drew" not in line.replace("…", "")


def test_the_key_shapes_cover_the_families_and_leave_prose_alone():
    for token in (KEY, "ghp_" + "A1" * 10, "github_pat_" + "a" * 22,
                  "AKIA" + "A" * 16, "xoxb-12345-abcdef-ghijk",
                  "AIza" + "B" * 32, JWT):  # fmt: skip
        line, got = tr.redact(f"token {token} here")
        assert got and got[0][0] == "a key", token
        assert token not in line
    for plain in ("risk-free offer", "a skeleton key", "ask-me-anything",
                  "gh pr list", "take 5 units"):  # fmt: skip
        assert tr.redact(plain) == (plain, []), plain


def test_a_json_transcript_stays_json(tmp_path):
    page = {"cmd": f"export K={KEY}", "cwd": "C:\\Users\\bob\\repo",
            "mail": "bob@example.org"}  # fmt: skip
    src = tmp_path / "t.jsonl"
    src.write_text(json.dumps(page) + "\n")
    to = tmp_path / "out.jsonl"
    got = run("--from", str(src), "--to", str(to))
    assert got.returncode == 0
    back = json.loads(to.read_text())
    assert back["cmd"] == "export K=[redacted:key]"
    assert back["cwd"] == "C:\\Users\\[redacted]\\repo"
    assert back["mail"] == "[redacted:email]"


def test_the_copy_is_written_even_clean_and_twice_gives_the_same_bytes(tmp_path):
    src = tmp_path / "clean.txt"
    src.write_text("nothing to see here\n")
    to = tmp_path / "out.txt"
    got = run("--from", str(src), "--to", str(to))
    assert got.returncode == 0 and "0 removals on 0 lines" in got.stdout
    assert to.read_text() == "nothing to see here\n"
    assert to.stat().st_mode & 0o777 == 0o600
    again = tmp_path / "again.txt"
    run("--from", str(src), "--to", str(again))
    assert again.read_bytes() == to.read_bytes()


def test_the_listing_never_prints_a_key_whole(tmp_path):
    src = tmp_path / "t.txt"
    src.write_text(f"a {KEY} and another {KEY}\nmail drew@example.org\n")
    to = tmp_path / "out.txt"
    got = run("--from", str(src), "--to", str(to))
    assert KEY not in got.stdout and KEY not in to.read_text()
    assert "2 removals on 1 line" not in got.stdout, "an email makes it two lines"
    assert "3 removals on 2 lines" in got.stdout
    assert got.stdout.count("line 1") == 2 and "line 2" in got.stdout


def test_one_removal_is_said_in_the_singular(tmp_path):
    src = tmp_path / "t.txt"
    src.write_text("mail drew@example.org\n")
    to = tmp_path / "out.txt"
    got = run("--from", str(src), "--to", str(to))
    assert "1 removal on 1 line" in got.stdout and "removals" not in got.stdout


def test_refusals_never_write(tmp_path):
    src = tmp_path / "t.txt"
    src.write_text("x\n")
    exists = tmp_path / "taken.txt"
    exists.write_text("mine")
    got = run("--from", str(src), "--to", str(exists))
    assert got.returncode == 2 and exists.read_text() == "mine"
    got = run("--from", str(tmp_path / "gone"), "--to", str(tmp_path / "o"))
    assert got.returncode == 2 and not (tmp_path / "o").exists()
    got = run()
    assert got.returncode == 2 and "transcript_redact.py" in got.stderr
    got = run("--from", str(src), "--to", str(tmp_path / "o2"), "--stray", "x")
    assert got.returncode == 2 and not (tmp_path / "o2").exists()
