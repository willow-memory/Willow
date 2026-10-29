"""hook-stop: a Stop hook that won't let a turn end while the record doesn't
verify or the repository has uncommitted work, and says which; it lets go when
it has already stopped the turn once, and on what it can't read."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "hook_stop.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.org"]


def run(*argv: str, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv],
        input=stdin,
        capture_output=True,
        text=True,
    )


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want sun.\n")
    b = tmp_path / "box"
    got = subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "init",
            "--box",
            str(b),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "k"),
            *NOW,
        ],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 0, got.stderr
    return b


def repo(tmp_path: Path, clean: bool = True) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=r, check=True)
    (r / "a.txt").write_text("a\n")
    subprocess.run([*GIT, "add", "-A"], cwd=r, check=True)
    subprocess.run([*GIT, "commit", "-q", "-m", "first"], cwd=r, check=True)
    if not clean:
        (r / "a.txt").write_text("changed\n")
    return r


def hook(**fields) -> str:
    return json.dumps({"hook_event_name": "Stop", **fields})


def break_the_chain(b: Path) -> None:
    rec = b / "record.jsonl"
    rec.write_text(rec.read_text().replace("2026", "2025", 1))


def test_a_clean_repo_and_a_sound_record_let_the_turn_end(tmp_path):
    b, r = box(tmp_path), repo(tmp_path)
    got = run("run", "--box", str(b), "--repo", str(r), stdin=hook())
    assert got.returncode == 0 and got.stdout == "" and got.stderr == ""


def test_uncommitted_work_blocks_and_names_the_files(tmp_path):
    b, r = box(tmp_path), repo(tmp_path, clean=False)
    got = run("run", "--box", str(b), "--repo", str(r), stdin=hook())
    assert got.returncode == 2
    assert (
        got.stderr
        == "Not done yet: 1 file has changes that are not committed: a.txt. Commit them, or say why they stay.\n"
    )
    (r / "b.txt").write_text("new\n")
    two = run("run", "--box", str(b), "--repo", str(r), stdin=hook()).stderr
    assert "2 files have changes that are not committed: a.txt, b.txt." in two, (
        "untracked counts"
    )


def test_more_than_five_files_are_counted_not_all_named(tmp_path):
    b, r = box(tmp_path), repo(tmp_path)
    for i in range(7):
        (r / f"f{i}.txt").write_text("x")
    err = run("run", "--box", str(b), "--repo", str(r), stdin=hook()).stderr
    assert (
        "7 files have changes" in err
        and "f0.txt, f1.txt, f2.txt, f3.txt, f4.txt and 2 more." in err
    )
    for i in range(2):
        (r / f"f{i}.txt").unlink()
    (r / "f5.txt").unlink()
    (r / "f6.txt").unlink()
    err = run("run", "--box", str(b), "--repo", str(r), stdin=hook()).stderr
    assert "3 files" in err and "more" not in err


def test_a_record_that_does_not_verify_blocks_and_says_so(tmp_path):
    b, r = box(tmp_path), repo(tmp_path)
    break_the_chain(b)
    got = run("run", "--box", str(b), "--repo", str(r), stdin=hook())
    assert got.returncode == 2 and got.stderr.startswith(
        "Not done yet: the record does not verify ("
    )
    (r / "a.txt").write_text("changed\n")
    both = run(
        "run", "--box", str(b), "--repo", str(r), stdin=hook()
    ).stderr.splitlines()
    assert (
        len(both) == 2
        and "record does not verify" in both[0]
        and "not committed" in both[1]
    )


def test_a_turn_already_stopped_once_is_let_go_so_nothing_loops(tmp_path):
    b, r = box(tmp_path), repo(tmp_path, clean=False)
    break_the_chain(b)
    got = run(
        "run", "--box", str(b), "--repo", str(r), stdin=hook(stop_hook_active=True)
    )
    assert got.returncode == 0 and got.stderr == ""
    assert (
        run(
            "run", "--box", str(b), "--repo", str(r), stdin=hook(stop_hook_active=False)
        ).returncode
        == 2
    )


def test_input_it_cannot_read_is_allowed_and_the_repo_comes_from_cwd(tmp_path):
    b, r = box(tmp_path), repo(tmp_path, clean=False)
    for raw in ("", "not json", "[1]", "7"):
        assert (
            run("run", "--box", str(b), "--repo", str(r), stdin=raw).returncode == 0
        ), raw
    assert run("run", "--box", str(b), stdin=hook(cwd=str(r))).returncode == 2
    clean = tmp_path / "plain"
    clean.mkdir()
    assert run("run", "--box", str(b), stdin=hook(cwd=str(clean))).returncode == 0, (
        "not a repository: not checked"
    )


def test_check_says_both_results_for_a_person(tmp_path):
    b, r = box(tmp_path), repo(tmp_path)
    ok = run("check", "--box", str(b), "--repo", str(r))
    assert (
        ok.returncode == 0
        and ok.stdout == "The record verifies and nothing is uncommitted.\n"
    )
    (r / "a.txt").write_text("changed\n")
    break_the_chain(b)
    bad = run("check", "--box", str(b), "--repo", str(r))
    assert bad.returncode == 42 and len(bad.stdout.splitlines()) == 2


def test_it_writes_nothing_and_a_bad_command_line_is_refused(tmp_path):
    b, r = box(tmp_path), repo(tmp_path, clean=False)
    before = {
        p: p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file() and ".git" not in p.parts
    }
    run("run", "--box", str(b), "--repo", str(r), stdin=hook())
    run("check", "--box", str(b), "--repo", str(r))
    assert {
        p: p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file() and ".git" not in p.parts
    } == before
    for argv in (
        [],
        ["run"],
        ["go", "--box", str(b)],
        ["run", "--box"],
        ["run", "--box", str(b), "x"],
        ["run", "--box", str(b), "--repo"],
        ["check", "--box", str(tmp_path)],
    ):
        assert run(*argv).returncode == 2, argv
    assert "hook_stop.py" in run().stderr
    assert "not a kernel box" in run("check", "--box", str(tmp_path)).stderr
