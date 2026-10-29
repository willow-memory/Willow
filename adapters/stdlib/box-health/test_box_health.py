"""box-health: a box's health in one line: the chain, approvals and waiting
suggestions, files the bite can't read with the add-on that reads each kind,
the words list, and when the record last had an out row; broken, needs you or
ok; nothing written; a bad command line refused."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "box_health.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]
spec = importlib.util.spec_from_file_location("kernel_for_box_health", KERNEL)
kernel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kernel)


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def subject(row: dict) -> str:
    canon = json.dumps(
        {x: row[x] for x in ("path", "data", "cites", "claim")},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return "proposal:" + hashlib.sha256(canon.encode()).hexdigest()


def box(
    tmp_path: Path, files: dict[str, bytes] | None = None, words: str | None = None
) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(exist_ok=True)
    for name, data in (
        files or {"garden.txt": b"Tomatoes want six hours of sun.\n"}
    ).items():
        (pile / name).parent.mkdir(parents=True, exist_ok=True)
        (pile / name).write_bytes(data)
    b = tmp_path / "box"
    argv = [
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    ]
    if words is not None:
        (tmp_path / "w.txt").write_text(words)
        (tmp_path / "w.txt").chmod(0o600)
        argv += ["--words", str(tmp_path / "w.txt")]
    assert k(*argv).returncode == 0
    return b


def propose(tmp_path: Path, b: Path) -> str:
    served = json.loads(
        k("bite", "--box", str(b), *NOW, "how much sun do tomatoes want").stdout
    )["served"]
    row = {
        "path": "sun.md",
        "data": "Six hours.",
        "cites": [served[0]["id"]],
        "claim": "the garden notes",
    }
    (tmp_path / "r.jsonl").write_text(json.dumps(row) + "\n")
    assert (
        k(
            "propose", "--box", str(b), "--file", str(tmp_path / "r.jsonl"), *NOW
        ).returncode
        == 42
    )
    return subject(row)


def test_a_fresh_box_with_an_out_row_is_ok_in_one_line(tmp_path):
    b = box(tmp_path)
    k("out", "--box", str(b), "--now", "2026-10-20T00:00:00Z")
    got = run("--box", str(b), *NOW)
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "box ok: 2 rows hold; 0 approved, 0 waiting; every file readable; last out row 2026-10-20 (4 days ago)"
    ]


def test_one_row_holds_in_the_singular(tmp_path):
    b = box(tmp_path)
    assert "1 row holds" in run("--box", str(b), *NOW).stdout


def test_no_out_row_yet_needs_you(tmp_path):
    got = run("--box", str(box(tmp_path)), *NOW)
    assert (
        got.returncode == 42
        and "no out row yet" in got.stdout
        and got.stdout.startswith("box needs you: no out row yet;")
    )


def test_the_out_row_of_today_and_of_the_future_are_said(tmp_path):
    b = box(tmp_path)
    k("out", "--box", str(b), *NOW)
    assert "last out row 2026-10-24 (today)" in run("--box", str(b), *NOW).stdout
    assert (
        "(in the future)"
        in run("--box", str(b), "--now", "2026-10-01T00:00:00Z").stdout
    )


def test_a_waiting_suggestion_and_an_approval_are_counted(tmp_path):
    b = box(tmp_path)
    subj = propose(tmp_path, b)
    k("out", "--box", str(b), *NOW)
    got = run("--box", str(b), *NOW)
    assert (
        got.returncode == 42
        and "1 suggestion waiting for you" in got.stdout
        and "0 approved, 1 waiting" in got.stdout
    )
    assert k("seal", "--box", str(b), subj, *NOW).returncode == 0
    k("out", "--box", str(b), *NOW)
    got = run("--box", str(b), *NOW)
    assert got.returncode == 0 and "1 approved, 0 waiting" in got.stdout


def test_a_forged_seal_and_a_changed_proposal_file_need_you(tmp_path):
    b = box(tmp_path)
    subj = propose(tmp_path, b)
    kernel.append(
        b,
        "2026-10-24T00:00:00Z",
        "seal",
        who="human",
        subject="proposal:" + "0" * 64,
        proof="0" * 64,
    )
    k("seal", "--box", str(b), subj, *NOW)
    f = b / "proposals" / f"{subj[9:]}.json"
    f.write_text(f.read_text().replace("Six", "Ten"))
    out = run("--box", str(b), *NOW).stdout
    assert (
        "don't prove under your key" in out
        and "1 approved answer whose proposal file is not what you approved" in out
    )


def test_files_the_bite_cant_read_are_counted_by_extension_with_the_add_on_that_reads_them(
    tmp_path,
):
    files = {"a.pdf": b"%PDF-\0\0", "b.pdf": b"%PDF-\0\0", "c.docx": b"PK\0\0", "d.bin": b"\0\1", "e.txt": b"\xff\xfe not utf8",
             "f": b"\0", ".hidden/x.pdf": b"\0", "ok.txt": b"fine\n"}  # fmt: skip
    got = run("--box", str(box(tmp_path, files)), *NOW)
    assert got.returncode == 42
    assert (
        "6 files can't be read (2 .pdf, read by pdf; 1 (no extension); 1 .bin; 1 .docx, read by office; 1 .txt)"
        in got.stdout
    )


def test_a_file_too_large_is_unreadable(tmp_path):
    big = b"x" * (kernel.MAX_FILE + 1)
    got = run("--box", str(box(tmp_path, {"big.txt": big})), *NOW)
    assert "1 file can't be read (1 .txt)" in got.stdout


def test_the_words_list_changed_since_the_last_question_needs_you(tmp_path):
    b = box(tmp_path, words="sun = sunshine\n")
    k("bite", "--box", str(b), *NOW, "how much sun do tomatoes want")
    k("out", "--box", str(b), *NOW)
    assert "words list as last used" in run("--box", str(b), *NOW).stdout
    (tmp_path / "w.txt").write_text("sun = sunlight\n")
    out = run("--box", str(b), *NOW)
    assert (
        out.returncode == 42
        and "the words list changed since the last question" in out.stdout
    )


def test_a_words_list_that_does_not_read_needs_you(tmp_path):
    b = box(tmp_path, words="sun = sunshine\n")
    (tmp_path / "w.txt").write_text("not a list line\n")
    assert "the words list can't be read" in run("--box", str(b), *NOW).stdout


def test_a_broken_chain_is_broken_and_nothing_else_is_said(tmp_path):
    b = box(tmp_path)
    rec = b / "record.jsonl"
    rec.write_text(rec.read_text().replace("2026", "2025", 1))
    got = run("--box", str(b), *NOW)
    assert (
        got.returncode == 2
        and got.stdout == ""
        and "box broken: the chain doesn't hold" in got.stderr
    )
    assert "more)" not in got.stderr, "one break is one break"


def test_long_puts_each_part_on_its_own_line(tmp_path):
    b = box(tmp_path)
    propose(tmp_path, b)
    k("out", "--box", str(b), *NOW)
    out = run("--box", str(b), "--long", *NOW).stdout.splitlines()
    assert out[0] == "box needs you"
    assert (
        "  needs you: 1 suggestion waiting for you" in out
        and "  fine: every file readable" in out
    )


def test_it_writes_nothing_not_even_an_out_row(tmp_path):
    b = box(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    run("--box", str(b), *NOW)
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    b = box(tmp_path)
    for argv in (
        [],
        ["--box"],
        ["--box", str(b), "stray"],
        ["--box", str(b), "--now", "soon"],
        ["--box", str(tmp_path)],
    ):
        assert run(*argv).returncode == 2, argv
    assert "box_health.py" in run().stderr


def test_several_breaks_are_counted_after_the_first(tmp_path):
    b = box(tmp_path)
    k("bite", "--box", str(b), *NOW, "how much sun do tomatoes want")
    k("out", "--box", str(b), *NOW)
    rec = b / "record.jsonl"
    rec.write_text(rec.read_text().replace("2026-10-24", "2025-10-24"))
    got = run("--box", str(b), *NOW)
    assert got.returncode == 2 and "(and 2 more)" in got.stderr
