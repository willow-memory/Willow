"""words-layers: one list made from several, in order, remade only when one
changed; someone's own list is never written over."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TOOL = HERE / "words_layers.py"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), *map(str, argv)],
                          capture_output=True, text=True)  # fmt: skip


def lists(tmp: Path) -> tuple[Path, Path, Path]:
    master, layer, made = tmp / "master.txt", tmp / "project.txt", tmp / "words.txt"
    master.write_text(
        "# what is true everywhere\ndeadline = due, expires\nlicence = license\n"
    )
    layer.write_text("# this project\ndeadline = timeline\nstep = instruction\n")
    return master, layer, made


def test_make_writes_the_layers_in_order_and_the_kernel_reads_it(tmp_path):
    import kernel

    master, layer, made = lists(tmp_path)
    got = run("make", "--from", master, "--from", layer, "--to", made)
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines()[0] == (
        f"made: {made}, 3 words from 2 layers; changed: master.txt, project.txt"
    )
    text = made.read_text()
    assert text.startswith(
        "# made by words-layers: edit the layers below, never this file.\n"
    )
    assert text.index("licence = license") < text.index("step = instruction")
    assert f"# layer {master.resolve()} sha256 " in text
    assert os.stat(made).st_mode & 0o777 == 0o600
    # the kernel takes it as a words list, and a word on two layers means both
    box = tmp_path / "box"
    box.mkdir()
    alias, _sha, why = kernel.read_words(made, box)
    assert why is None
    assert alias == {"deadline": ["due", "expires", "timeline"], "licence": ["license"],
                     "step": ["instruction"]}  # fmt: skip
    assert (
        "  in more than one layer, read together: deadline (master.txt, project.txt)"
        in got.stdout
    )
    assert "licence" not in got.stdout  # on one layer only: nothing to say
    assert sorted(p.name for p in tmp_path.iterdir() if p.is_file()) == [
        "master.txt", "project.txt", "words.txt"]  # fmt: skip


def test_made_again_only_when_a_layer_changed_and_it_says_which(tmp_path):
    master, layer, made = lists(tmp_path)
    ask = ("--from", master, "--from", layer, "--to", made)
    run("make", *ask)
    before = (made.read_bytes(), os.stat(made).st_mtime_ns)
    again = run("make", *ask)
    assert again.stdout.startswith(f"current: {made}, 3 words from 2 layers\n")
    assert (made.read_bytes(), os.stat(made).st_mtime_ns) == before
    layer.write_text(layer.read_text() + "target = targets\n")
    got = run("make", *ask)
    assert got.stdout.startswith(
        f"remade: {made}, 4 words from 2 layers; changed: project.txt\n"
    )
    assert "target = targets" in made.read_text()
    # a layer taken out is said, and its words go
    got = run("make", "--from", master, "--to", made)
    assert got.stdout.startswith(
        f"remade: {made}, 2 words from 1 layers; changed: project.txt (taken out)\n"
    )
    assert "step" not in made.read_text()


def test_check_says_current_stale_or_not_made_and_writes_nothing(tmp_path):
    master, layer, made = lists(tmp_path)
    ask = ("--from", master, "--from", layer, "--to", made)
    got = run("check", *ask)
    assert got.returncode == 42 and got.stdout.startswith("not made yet: ")
    assert not made.exists()
    run("make", *ask)
    got = run("check", *ask)
    assert got.returncode == 0 and got.stdout.startswith("current: ")
    master.write_text(master.read_text() + "goal = aim\n")
    was = made.read_bytes()
    got = run("check", *ask)
    assert got.returncode == 42
    assert got.stdout.startswith(
        f"stale: {made}, 4 words from 2 layers; changed: master.txt\n"
    )
    assert made.read_bytes() == was


def test_someones_own_list_is_never_written_over(tmp_path):
    master, layer, made = lists(tmp_path)
    made.write_text("# my own list\nmum = margaret\n")
    for verb in ("make", "check"):
        got = run(verb, "--from", master, "--to", made)
        assert got.returncode == 2 and got.stdout == ""
        assert (
            "is there and was not made by words-layers; it is left as it is"
            in got.stderr
        )
    assert made.read_text() == "# my own list\nmum = margaret\n"


def test_a_layer_that_is_not_a_words_list_is_refused_and_named(tmp_path):
    master, layer, made = lists(tmp_path)
    layer.write_text("step = an instruction\n")  # two words on the right
    got = run("make", "--from", master, "--from", layer, "--to", made)
    assert got.returncode == 2 and not made.exists()
    assert f"refused: {layer}: words list line 1:" in got.stderr
    got = run("make", "--from", tmp_path / "gone.txt", "--to", made)
    assert (
        got.returncode == 2
        and "gone.txt could not be read: FileNotFoundError" in got.stderr
    )
    layer.write_bytes(b"\xff\xfe not text")
    got = run("make", "--from", layer, "--to", made)
    assert got.returncode == 2 and "could not be read" in got.stderr


def test_a_to_that_is_a_folder_or_in_no_folder_is_refused(tmp_path):
    master, _layer, _made = lists(tmp_path)
    for bad in (tmp_path, tmp_path / "nowhere" / "words.txt"):
        got = run("make", "--from", master, "--to", bad)
        assert (
            got.returncode == 2 and "a file, in a folder that is there" in got.stderr
        ), bad
    assert not (tmp_path / "nowhere").exists()


def test_a_bad_command_line_is_refused(tmp_path):
    master, layer, made = lists(tmp_path)
    for argv in ([], ["made"], ["make"], ["make", "--from", master], ["make", "--to", made],
                 ["make", "--from", master, "--to", made, "--to", made],
                 ["make", "--from", master, "--to"], ["make", "--from", master, "--into", made],
                 ["make", master, "--to", made]):  # fmt: skip
        got = run(*argv)
        assert (
            got.returncode == 2 and "words_layers.py make --from LIST" in got.stderr
        ), argv
    assert not made.exists()


def test_layers_in_reads_only_its_own_lines():
    import words_layers

    text = ("# made by words-layers: edit the layers below, never this file.\n\n"
            "# layer /a/master.txt sha256 abc\nx = y\n# layer of paint\n# layer /b sha256\n")  # fmt: skip
    assert words_layers.layers_in(text) == {"/a/master.txt": "abc"}
    assert words_layers.layers_in("") == {}
