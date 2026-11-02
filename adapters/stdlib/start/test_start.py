"""start: the kernel's own init over your files, with the key and the
starter words beside the box under one folder, then how to open, launch and
back it up; never inside your files, never over a box already there."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
#: start's siblings, which it uses when they're beside it and says so when
#: they aren't: each test holds it to whichever is true here, so a copy of
#: willow with only some add-ons is checked as strictly as willow itself
BESIDE = {n: (HERE.parent / n).is_dir() for n in ("starter-words", "browse", "backup")}
spec = importlib.util.spec_from_file_location("start_addon", HERE / "start.py")
st = importlib.util.module_from_spec(spec)
spec.loader.exec_module(st)


def files(tmp_path: Path) -> Path:
    pile = tmp_path / "my files"
    pile.mkdir()
    (pile / "dentist.txt").write_text("The dentist is on Tuesday at 3pm.\n")
    return pile


def run(*argv: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "start.py"), *argv], input=stdin,
                          capture_output=True, text=True)  # fmt: skip


def test_one_step_makes_the_box_key_and_words_and_says_what_next(tmp_path):
    pile, home = files(tmp_path), tmp_path / "willow"
    got = run("--pile", str(pile), "--to", str(home))
    assert got.returncode == 0, got.stderr
    cfg = json.loads((home / "box" / "kernel.json").read_text())
    want = {"pile": str(pile.resolve()), "key": str((home / "key").resolve())}
    if BESIDE["starter-words"]:
        want["words"] = str((home / "my-words.txt").resolve())
    assert cfg == want
    assert (home / "my-words.txt").exists() == BESIDE["starter-words"]
    if os.name == "posix":
        assert (home / "key").stat().st_mode & 0o077 == 0
        if BESIDE["starter-words"]:
            assert (home / "my-words.txt").stat().st_mode & 0o077 == 0
    assert (
        subprocess.run(
            [sys.executable, str(KERNEL), "verify", "--box", str(home / "box")]
        ).returncode
        == 0
    )
    bite = subprocess.run([sys.executable, str(KERNEL), "bite", "--box", str(home / "box"), "when is the dentist"],
                          capture_output=True, text=True)  # fmt: skip
    assert json.loads(bite.stdout)["state"] == "populated"
    out = got.stdout
    assert out.startswith("Set up. Your files: ")
    assert ("browse.py --box" in out and "save as" in out) == BESIDE["browse"]
    assert ("backup.py --box" in out) == BESIDE["backup"]
    assert ("no words list yet" in out) != BESIDE["starter-words"]
    assert str(home / "key") in out and "keep a copy somewhere safe" in out


def test_never_inside_your_files_and_never_over_a_box(tmp_path):
    pile = files(tmp_path)
    for home in (pile, pile / "willow"):
        got = run("--pile", str(pile), "--to", str(home))
        assert got.returncode == 2 and "inside your files" in got.stderr
    assert not (pile / "willow").exists()
    home = tmp_path / "willow"
    assert run("--pile", str(pile), "--to", str(home)).returncode == 0
    before = (home / "box" / "record.jsonl").read_bytes()
    again = run("--pile", str(pile), "--to", str(home))
    assert (
        again.returncode == 2
        and "already set up" in again.stderr
        and "browse.py --box" in again.stderr
    )
    assert (home / "box" / "record.jsonl").read_bytes() == before


def test_files_that_arent_a_folder_are_refused(tmp_path):
    got = run("--pile", str(tmp_path / "nowhere"), "--to", str(tmp_path / "w"))
    assert (
        got.returncode == 2
        and "isn't a folder" in got.stderr
        and not (tmp_path / "w").exists()
    )


def test_a_words_list_already_there_is_used_as_it_is(tmp_path):
    pile, home = files(tmp_path), tmp_path / "willow"
    home.mkdir()
    mine = home / "my-words.txt"
    mine.write_text("tooth = dentist\n")
    mine.chmod(0o600)
    got = run("--pile", str(pile), "--to", str(home))
    assert got.returncode == 0
    # used as it is when starter-words is beside start; never touched either way
    assert ("used as it is" in got.stdout) == BESIDE["starter-words"]
    assert mine.read_text() == "tooth = dentist\n"


def test_without_its_siblings_it_still_sets_up(tmp_path, monkeypatch):
    pile, home = files(tmp_path), tmp_path / "willow"
    monkeypatch.setattr(st, "STDLIB", tmp_path / "empty")
    monkeypatch.setattr(
        sys, "argv", ["start.py", "--pile", str(pile), "--to", str(home)]
    )
    code, said = st.start(pile, home)
    assert code == 0 and "no words list yet" in said and "browse.py" not in said
    assert (
        not (home / "my-words.txt").exists() and (home / "box" / "kernel.json").exists()
    )


def test_in_a_terminal_it_asks_and_runs_the_same_command_line(tmp_path, monkeypatch):
    pile, home = files(tmp_path), tmp_path / "willow"
    calls = []
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True, raising=False)
    answers = iter([str(pile), str(home)])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    monkeypatch.setattr(st.subprocess, "call", lambda argv: calls.append(argv) or 0)
    assert st.main([]) == 0
    assert calls[0][-4:] == ["--pile", str(pile), "--to", str(home)]
    answers = iter(["", ""])
    assert st.main([]) == 2  # no folder named
    monkeypatch.setattr(
        "builtins.input", lambda prompt: (_ for _ in ()).throw(EOFError)
    )
    assert st.main([]) == 2
    answers = iter([str(pile), ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    st.main([])
    assert calls[-1][-1] == str(Path(st.DEFAULT).expanduser())


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    for argv in ([], ["--pile", "x"], ["--to", "y"], ["--pile", "x", "--to", "y", "z"]):
        got = run(*argv, stdin="")
        assert got.returncode == 2 and "start.py" in got.stderr
