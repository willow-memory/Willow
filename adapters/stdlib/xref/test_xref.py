"""xref: each link and file:line in a person's files checked, from the
folder it's written in; the web, mail and anchors left alone; out of the
folder counted, never followed; nothing written."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("xref_addon", HERE / "xref.py")
xr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(xr)


def make(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    for d in ("notes", "trips", "care", "letters", "web"):
        (pile / d).mkdir(parents=True)
    (pile / "trips" / "2018.md").write_text("Lisbon.\n")
    (pile / "care" / "log.txt").write_text("".join(f"day {i}\n" for i in range(1, 32)))
    (pile / "notes" / "index.md").write_text(
        "# Index\n[2018](../trips/2018.md) and [2019](../trips/2019.md)\n"
        "[site](https://example.org) [mail](mailto:a@b.c) [top](#index)\n"
        "[escape](../../secret.txt) [anchor](../trips/2018.md#day-2)\n"
    )
    (pile / "letters" / "reply.txt").write_text(
        "As care/log.txt:12 says, and care/log.txt:40 too.\nSee elsewhere.txt:3, not ours.\n"
    )
    (pile / "web" / "page.html").write_text(
        '<a href="../trips/2018.md">ok</a> <img src="photo.jpg"> <a href="https://x.org">w</a>\n'
    )
    return pile


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "xref.py"), *argv], capture_output=True, text=True
    )


def test_what_doesnt_hold_is_listed_where_it_is_written(tmp_path):
    got = xr.check(make(tmp_path))
    assert sorted(got["broken"]) == [
        (
            "letters/reply.txt:1",
            "file:line",
            "care/log.txt:40",
            "past the end (31 lines)",
        ),
        ("notes/index.md:2", "link", "../trips/2019.md", "not there"),
        ("web/page.html:1", "link", "photo.jpg", "not there"),
    ]
    assert got["held"] == 4 and got["outside"] == 1


def test_the_command_line_prints_each_and_a_count_and_exits_42(tmp_path):
    pile = make(tmp_path)
    before = {p: p.read_bytes() for p in pile.rglob("*") if p.is_file()}
    got = run("--from", str(pile))
    assert got.returncode == 42
    assert (
        "notes/index.md:2" in got.stdout and "../trips/2019.md: not there" in got.stdout
    )
    assert (
        "7 references checked, 3 don't hold; 1 leading out of your folder, not checked."
        in got.stdout
    )
    assert {p: p.read_bytes() for p in pile.rglob("*") if p.is_file()} == before


def test_every_reference_holding_exits_0_and_a_box_reads_its_own_files(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("[b](b.md), and b.md:1\n")
    (pile / "b.md").write_text("one line\n")
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key", str(tmp_path / "k")],
                   check=True, capture_output=True)  # fmt: skip
    got = run("--box", str(b))
    assert got.returncode == 0 and "2 references checked, 0 don't hold." in got.stdout
    (pile / "b.md").unlink()
    got = run("--box", str(b))
    assert got.returncode == 42 and "1 reference checked, 1 doesn't hold." in got.stdout


def test_a_file_line_is_found_from_its_folder_first_then_the_top(tmp_path):
    pile = tmp_path / "pile"
    (pile / "d").mkdir(parents=True)
    (pile / "d" / "x.txt").write_text("1\n2\n")
    (pile / "x.txt").write_text("1\n")
    (pile / "d" / "note.txt").write_text("x.txt:2\n")
    assert xr.check(pile)["broken"] == []  # d/x.txt has 2 lines; the top's has 1
    (pile / "top.txt").write_text("x.txt:2\n")
    assert [b[0] for b in xr.check(pile)["broken"]] == ["top.txt:1"]


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    for argv in (
        [],
        ["--box"],
        ["--from", str(tmp_path), "--box", str(tmp_path)],
        ["--from", str(tmp_path), "x"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "xref.py" in got.stderr
    assert "not a kernel box" in run("--box", str(tmp_path)).stderr
    assert "isn't a folder" in run("--from", str(tmp_path / "nope")).stderr


def test_hidden_folders_and_binary_files_are_left_out_as_the_kernel_leaves_them(
    tmp_path,
):
    pile = tmp_path / "pile"
    (pile / ".obsidian").mkdir(parents=True)
    (pile / ".obsidian" / "cache.md").write_text("[gone](nowhere.md)\n")
    (pile / "blob.md").write_bytes(b"[gone](nowhere.md)\n\0binary")
    (pile / "real.md").write_text("[gone](nowhere.md)\n")
    assert [b[0] for b in xr.check(pile)["broken"]] == ["real.md:1"]
