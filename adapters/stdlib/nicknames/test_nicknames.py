"""nicknames: a family word beside a name, in the shapes listed, becomes a line
of the kernel's words list with the file and line it came from; days, months
and a chat's speaker labels are no names; two names for one nickname are said;
the list is written once, readable only by you, and read by the kernel; nothing
is changed; a bad command line is refused."""

from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "nicknames.py"
KERNEL = HERE.parents[2] / "kernel.py"
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

spec = importlib.util.spec_from_file_location("nicknames_under_test", SCRIPT)
nn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nn)

NOTES = """\
Mum (Margaret) has a dentist appointment on Tuesday.

Margaret (Mum) lives in Leeds.

I rang Margaret, my mum, today.
"""


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def pile(tmp_path: Path, files: dict[str, str]) -> Path:
    p = tmp_path / "pile"
    for name, text in files.items():
        (p / name).parent.mkdir(parents=True, exist_ok=True)
        (p / name).write_text(text, encoding="utf-8")
    return p


def listed(
    p: Path, tmp_path: Path, *extra: str
) -> tuple[subprocess.CompletedProcess, dict]:
    to = tmp_path / "words.txt"
    got = run("--from", str(p), "--to", str(to), *extra)
    return got, (kernel.parse_words(to.read_text())[0] if to.exists() else {})


def test_each_shape_is_read_as_the_nickname_for_the_name(tmp_path):
    shapes = {
        "Mum (Margaret) rang.": ("mum", "margaret"), "Margaret (Mum) rang.": ("mum", "margaret"),
        "I rang Margaret, my mum, today.": ("mum", "margaret"), "my dad Robert is 80": ("dad", "robert"),
        "my gran is Dorothy": ("gran", "dorothy"), "Auntie Jean came": ("auntie", "jean"),
        "Grandad was Albert": ("grandad", "albert"), "We saw Uncle Bob": ("uncle", "bob"),
    }  # fmt: skip
    for text, (nick, name) in shapes.items():
        assert {
            (n, m)
            for (n, m), _, _ in nn.mentions(pile(tmp_path / nick, {"a.txt": text}))
        } == {(nick, name)}, text


def test_the_list_names_the_place_of_the_first_mention_and_how_many(tmp_path):
    p = pile(tmp_path, {"family/notes.txt": NOTES})
    got, words = listed(p, tmp_path)
    assert got.returncode == 0, got.stderr
    assert words == {"mum": ["margaret"]}
    text = (tmp_path / "words.txt").read_text()
    assert "# family/notes.txt:1 (3 mentions) mum = margaret" in text
    assert "mum = margaret    family/notes.txt:1  (3 mentions)" in got.stdout
    assert f"wrote {tmp_path / 'words.txt'}: 1 nickname" in got.stdout


def test_both_adds_the_name_reading_as_the_nickname(tmp_path):
    _, words = listed(pile(tmp_path, {"n.txt": NOTES}), tmp_path, "--both")
    assert words == {"mum": ["margaret"], "margaret": ["mum"]}


def test_a_day_a_month_a_chat_label_and_a_title_are_no_names(tmp_path):
    text = "Dad: Thank you son\n[2021-03-21] Mum: Ferris came by\nMum Monday call\nMum March plans\nFather Liam blessed it\nMum Weds\nBrother Thomas\n"
    got, words = listed(pile(tmp_path, {"chat.txt": text}), tmp_path)
    assert got.returncode == 42 and words == {} and "No nickname found" in got.stdout
    assert not (tmp_path / "words.txt").exists()


def test_two_names_for_one_nickname_are_kept_and_said(tmp_path):
    p = pile(
        tmp_path, {"a.txt": "Mum (Margaret) rang.\n", "b.txt": "my mum Mary came.\n"}
    )
    got, words = listed(p, tmp_path)
    assert got.returncode == 0 and words == {"mum": ["margaret", "mary"]}
    assert "'mum' is claimed by more than one name" in got.stderr


def test_the_kernel_reads_the_list_and_a_question_with_the_nickname_finds_the_name(
    tmp_path,
):
    p = pile(
        tmp_path,
        {
            "notes.txt": NOTES,
            "diary.txt": "Margaret has a dentist appointment on Tuesday at nine.\n",
        },
    )
    (tmp_path / "w").mkdir()
    to = tmp_path / "w" / "words.txt"
    assert run("--from", str(p), "--to", str(to)).returncode == 0
    b = tmp_path / "box"
    subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "init",
            "--box",
            str(b),
            "--pile",
            str(p),
            "--key",
            str(tmp_path / "k"),
            "--words",
            str(to),
            "--now",
            "2026-10-24T00:00:00Z",
        ],
        check=True,
        capture_output=True,
    )
    got = subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "bite",
            "--box",
            str(b),
            "--now",
            "2026-10-24T00:00:00Z",
            "when is mum's dentist appointment",
        ],
        capture_output=True,
        text=True,
    )
    assert "diary.txt:1" in got.stdout


def test_hidden_binary_and_large_files_are_not_read(tmp_path):
    p = pile(
        tmp_path, {".hidden/a.txt": "Mum (Margaret)\n", "ok.txt": "nothing here\n"}
    )
    (p / "bin.dat").write_bytes(b"Mum (Margaret)\0\0")
    assert run("--from", str(p), "--to", str(tmp_path / "w.txt")).returncode == 42


def test_the_list_is_written_once_private_and_never_over_a_file(tmp_path):
    p = pile(tmp_path, {"n.txt": NOTES})
    to = tmp_path / "w.txt"
    assert run("--from", str(p), "--to", str(to)).returncode == 0
    assert stat.S_IMODE(os.stat(to).st_mode) == 0o600
    again = run("--from", str(p), "--to", str(to))
    assert again.returncode == 2 and "could not write" in again.stderr
    assert (
        run("--from", str(p), "--to", str(tmp_path / "nope" / "w.txt")).returncode == 2
    )


def test_the_files_it_reads_are_not_changed(tmp_path):
    p = pile(tmp_path, {"n.txt": NOTES})
    before = {q: q.read_bytes() for q in p.rglob("*") if q.is_file()}
    run("--from", str(p), "--to", str(tmp_path / "w.txt"))
    assert {q: q.read_bytes() for q in p.rglob("*") if q.is_file()} == before


def test_a_box_is_read_through_its_pile(tmp_path):
    p = pile(tmp_path, {"n.txt": NOTES})
    b = tmp_path / "box"
    subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "init",
            "--box",
            str(b),
            "--pile",
            str(p),
            "--key",
            str(tmp_path / "k"),
            "--now",
            "2026-10-24T00:00:00Z",
        ],
        check=True,
        capture_output=True,
    )
    assert run("--box", str(b), "--to", str(tmp_path / "w.txt")).returncode == 0


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    p = pile(tmp_path, {"n.txt": NOTES})
    to = str(tmp_path / "w.txt")
    for argv in ([], ["--from", str(p)], ["--to", to], ["--from", str(p), "--to", to, "stray"], ["--from", str(p), "--box", str(p), "--to", to],
                 ["--from", str(tmp_path / "missing"), "--to", to], ["--box", str(tmp_path), "--to", to]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2, argv
    assert "nicknames.py" in run().stderr


def test_two_nicknames_are_counted_in_the_plural_and_one_mention_in_the_singular(
    tmp_path,
):
    p = pile(tmp_path, {"a.txt": "Mum (Margaret) rang.\n\nmy dad Robert came.\n"})
    got, words = listed(p, tmp_path)
    assert words == {"mum": ["margaret"], "dad": ["robert"]}
    assert (
        f"wrote {tmp_path / 'words.txt'}: 2 nicknames" in got.stdout
        and "(1 mention)" in got.stdout
    )
