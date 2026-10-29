"""jupyter: a notebook as text, one block for each cell; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "jupyter.py"
spec = importlib.util.spec_from_file_location("jupyter", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE = (
    b'{"nbformat": 4, "nbformat_minor": 5, "metadata": {"kernelspec": {"name": "python3", "display_name": "Tide analysis"}, "language_info": {"name": "python"}},'
    b' "cells": [{"cell_type": "markdown", "source": ["# Tides at the estuary\\n", "Six harbours."]},'
    b' {"cell_type": "code", "source": "df = load(\\"harbours.csv\\")\\nprint(len(df))", "outputs": [{"output_type": "stream", "name": "stdout", "text": ["6 rows\\n"]},'
    b' {"output_type": "display_data", "data": {"image/png": "iVBORw0KGgo=", "text/plain": ["<Figure size 640x480>"]}}]}]}'
)


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


def nb(*cells, **meta) -> bytes:
    return json.dumps({"nbformat": 4, "metadata": meta, "cells": list(cells)}).encode()


def test_each_cell_is_a_block_headed_by_its_number_and_kind():
    out = mod.convert(SAMPLE)
    assert out.startswith(
        "notebook: Tide analysis (python3, python)\n\ncell 1 (markdown)\n# Tides at the estuary\nSix harbours.\n\ncell 2 (code)\n"
    )
    assert (
        'df = load("harbours.csv")\nprint(len(df))\noutput:\n6 rows\noutput:\n<Figure size 640x480>\n'
        in out
    )


def test_a_picture_is_left_out_and_only_its_text_form_kept():
    out = mod.convert(
        nb(
            {
                "cell_type": "code",
                "source": "plot()",
                "outputs": [
                    {"output_type": "display_data", "data": {"image/png": "AAAA"}}
                ],
            }
        )
    )
    assert "AAAA" not in out and "output:" not in out and "cell 1 (code)\nplot()" in out


def test_an_error_is_its_name_and_message_and_a_result_is_its_plain_form():
    out = mod.convert(
        nb(
            {
                "cell_type": "code",
                "source": "1/0",
                "outputs": [
                    {
                        "output_type": "error",
                        "ename": "ZeroDivisionError",
                        "evalue": "division by zero",
                        "traceback": ["\x1b[0;31m"],
                    }
                ],
            },
            {
                "cell_type": "code",
                "source": "x",
                "outputs": [
                    {
                        "output_type": "execute_result",
                        "data": {"text/plain": "42"},
                        "execution_count": 2,
                    }
                ],
            },
        )
    )
    assert (
        "output:\nZeroDivisionError: division by zero\n" in out
        and "output:\n42\n" in out
        and "\x1b" not in out
    )


def test_a_long_output_keeps_its_first_twenty_lines_and_says_how_many_more():
    big = "\n".join(f"line {i}" for i in range(30)) + "\n"
    out = mod.convert(
        nb(
            {
                "cell_type": "code",
                "source": "x",
                "outputs": [{"output_type": "stream", "name": "stdout", "text": big}],
            }
        )
    )
    assert "line 19\n... 10 more lines\n" in out and "line 20\n" not in out


def test_raw_cells_and_empty_cells_and_a_missing_kernel_are_handled():
    out = mod.convert(
        nb(
            {"cell_type": "raw", "source": "keep me"},
            {"cell_type": "code", "source": "", "outputs": []},
            {"cell_type": "markdown", "source": "after"},
        )
    )
    assert out.startswith(
        "notebook: notebook\n\ncell 1 (raw)\nkeep me\n\ncell 3 (markdown)\nafter\n"
    )


def test_a_title_in_the_metadata_names_the_notebook():
    assert mod.convert(
        nb({"cell_type": "markdown", "source": "x"}, title="My title")
    ).startswith("notebook: My title\n")


def test_the_older_nbformat_3_is_read():
    old = json.dumps(
        {
            "nbformat": 3,
            "worksheets": [
                {
                    "cells": [
                        {
                            "cell_type": "code",
                            "input": ["print(1)"],
                            "outputs": [
                                {
                                    "output_type": "stream",
                                    "stream": "stdout",
                                    "text": ["1\n"],
                                }
                            ],
                        },
                        {"cell_type": "markdown", "source": ["Old"]},
                    ]
                }
            ],
        }
    ).encode()
    out = mod.convert(old)
    assert (
        "cell 1 (code)\nprint(1)\noutput:\n1\n" in out
        and "cell 2 (markdown)\nOld\n" in out
    )


def test_something_that_is_not_a_notebook_or_has_no_cells_is_not_a_result():
    assert (
        mod.convert(b"[1, 2]") is None
        and mod.convert(b'{"cells": []}') is None
        and mod.convert(nb({"cell_type": "code", "source": ""})) is None
    )
    try:
        mod.convert(b"not json")
    except mod.ERRORS:
        return
    raise AssertionError


def test_the_checkpoint_folders_jupyter_keeps_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path, {"a.ipynb": SAMPLE, ".ipynb_checkpoints/a-checkpoint.ipynb": SAMPLE}
    )
    assert sorted(p.name for p in out.rglob("*") if p.is_file()) == ["a.ipynb.txt"]


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"nbs/tides.ipynb": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "nbs/tides.ipynb.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "nbs/tides.ipynb": SAMPLE,
            ".hid/nbs/tides.ipynb": SAMPLE,
            ".nbs/tides.ipynb": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["nbs/tides.ipynb.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"nbs/tides.ipynb": SAMPLE})
    before = (tmp_path / "src" / "nbs/tides.ipynb").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "nbs/tides.ipynb.txt").read_bytes() == (
        out / "nbs/tides.ipynb.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "nbs/tides.ipynb").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(tmp_path, {"good.ipynb": SAMPLE, "bad.ipynb": b"{not json"})
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.ipynb.txt").is_file() and not (out / "bad.ipynb.txt").exists()


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
        assert got.returncode == 2 and "jupyter.py" in got.stderr
