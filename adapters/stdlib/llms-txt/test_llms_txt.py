"""llms-txt: an llms.txt written from what is in a folder (a title, a summary, a
section for each folder, a link and a note for each text file, big files under
Optional) and one checked against the format, each departure at its line; hidden
and binary files left out; written once and private; the same bytes twice; a
bad command line refused; the folder unchanged."""

from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "llms_txt.py"
spec = importlib.util.spec_from_file_location("llms_txt", SCRIPT)
lt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lt)

GOOD = "# notes\n\n> A folder of notes.\n\n## garden\n\n- [Tomatoes](garden/tomatoes.md): Six hours of sun.\n- [Beans](garden/beans.md)\n\n## Optional\n\n- [Log](log.txt): old\n"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def folder(tmp_path: Path, files: dict[str, str | bytes]) -> Path:
    d = tmp_path / "notes"
    for rel, data in files.items():
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_bytes(data if isinstance(data, bytes) else data.encode())
    return d


def written(
    tmp_path: Path, files: dict[str, str | bytes], *extra: str
) -> tuple[subprocess.CompletedProcess, str]:
    d = folder(tmp_path, files)
    to = tmp_path / "llms.txt"
    to.unlink(missing_ok=True)
    got = run("write", "--from", str(d), "--to", str(to), *extra)
    return got, to.read_text() if to.exists() else ""


def test_a_folder_is_a_title_a_summary_a_section_for_each_folder_and_a_link_for_each_file(
    tmp_path,
):
    got, text = written(
        tmp_path,
        {
            "garden/tomatoes.md": "# Tomatoes\n\nTomatoes want six hours of sun.\n",
            "garden/beans.md": "Beans like it cooler.\n",
            "readme.txt": "Plain notes.\n",
        },
    )
    assert got.returncode == 0, got.stderr
    assert text == (
        "# notes\n\n> 3 files from notes: text and Markdown, listed by folder.\n\n## garden\n\n"
        "- [beans.md](garden/beans.md): Beans like it cooler.\n- [Tomatoes](garden/tomatoes.md): Tomatoes want six hours of sun.\n\n## Files\n\n- [readme.txt](readme.txt): Plain notes.\n"
    )
    assert f"wrote {tmp_path / 'llms.txt'}: 3 files listed" in got.stdout


def test_title_summary_and_base_are_taken_and_the_path_is_made_safe(tmp_path):
    _, text = written(
        tmp_path,
        {"my notes/a b.md": "# A\n\nx\n"},
        "--title",
        "Allotment",
        "--summary",
        "What  I grew.",
        "--base",
        "https://example.org/n/",
    )
    assert (
        text.startswith("# Allotment\n\n> What I grew.\n")
        and "- [A](https://example.org/n/my%20notes/a%20b.md): x\n" in text
    )


def test_a_big_file_goes_under_optional_with_its_size(tmp_path):
    _, text = written(
        tmp_path,
        {
            "small.md": "# Small\n\nfine\n",
            "big.txt": "line of text\n" * 6000,
            "bare.log": "x\n" * 30000,
        },
    )
    assert text.endswith(
        "## Optional\n\n- [bare.log](bare.log): x, 60 KB\n- [big.txt](big.txt): line of text, 78 KB\n"
    )
    assert "## Files\n\n- [Small](small.md): fine\n" in text


def test_a_big_file_with_no_prose_note_is_just_its_size(tmp_path):
    _, text = written(tmp_path, {"data.md": "<table>\n" + "<tr/>\n" * 12000})
    assert "- [data.md](data.md): 72 KB\n" in text


def test_hidden_binary_and_unreadable_files_are_left_out(tmp_path):
    _, text = written(
        tmp_path,
        {
            ".hid/x.md": "# no\n",
            ".secret.md": "# no\n",
            "pic.png": b"\x89PNG\0\0",
            "latin.txt": b"caf\xe9 \xff",
            "ok.md": "# Yes\n\nok\n",
        },
    )
    assert (
        "ok.md" in text
        and ".hid" not in text
        and "secret" not in text
        and "pic.png" not in text
        and "latin.txt" not in text
    )


def test_describe_takes_the_first_heading_and_the_first_line_of_prose_outside_a_code_block():
    text = "\n---\n```\ncode\n```\n# Title\n\nFirst prose [with] link.\nsecond\n"
    assert lt.describe(text, "f.md") == ("Title", "First prose with link.")
    assert lt.describe("no heading here\n", "f.md") == ("f.md", "no heading here")
    assert lt.describe("# [Odd] title\n", "f.md") == ("(Odd) title", "")
    assert lt.describe("x" * 150, "f")[1] == "x" * 99 + "…"


def test_nothing_to_list_writes_nothing_and_waits_on_you(tmp_path):
    got, text = written(tmp_path, {"pic.png": b"\0\0", ".hid.md": "x"})
    assert got.returncode == 42 and text == "" and "Nothing to list" in got.stdout


def test_the_same_folder_gives_the_same_bytes_and_it_is_not_changed(tmp_path):
    d = folder(tmp_path, {"a/b.md": "# B\n\nx\n"})
    before = {p: p.read_bytes() for p in d.rglob("*") if p.is_file()}
    to = tmp_path / "llms.txt"
    run("write", "--from", str(d), "--to", str(to))
    one = to.read_bytes()
    to.unlink()
    run("write", "--from", str(d), "--to", str(to))
    assert (
        to.read_bytes() == one
        and {p: p.read_bytes() for p in d.rglob("*") if p.is_file()} == before
    )


def test_the_file_is_written_once_and_private(tmp_path):
    d = folder(tmp_path, {"a.md": "# A\n\nx\n"})
    to = tmp_path / "llms.txt"
    assert run("write", "--from", str(d), "--to", str(to)).returncode == 0
    assert stat.S_IMODE(os.stat(to).st_mode) == 0o600
    again = run("write", "--from", str(d), "--to", str(to))
    assert again.returncode == 2 and "could not write" in again.stderr
    assert (
        run(
            "write", "--from", str(d), "--to", str(tmp_path / "nope" / "l.txt")
        ).returncode
        == 2
    )


def checked(tmp_path: Path, text: str) -> list[str]:
    f = tmp_path / "llms.txt"
    f.write_text(text)
    got = run("check", str(f))
    return [
        x.split("  ", 1)[0].rsplit(":", 1)[1] + " " + x.split("  ", 1)[1]
        for x in got.stdout.splitlines()
        if x.startswith(str(f))
    ]


def test_a_file_that_follows_the_format_is_clean(tmp_path):
    f = tmp_path / "llms.txt"
    f.write_text(
        GOOD.replace("(garden/", "(https://x.org/garden/").replace(
            "(log.txt)", "(https://x.org/log.txt)"
        )
    )
    got = run("check", str(f))
    assert got.returncode == 0 and "follows the format" in got.stdout


def test_what_it_writes_it_also_accepts_with_a_base(tmp_path):
    d = folder(tmp_path, {"garden/a.md": "# A\n\nx\n", "big.txt": "y\n" * 30000})
    to = tmp_path / "llms.txt"
    run("write", "--from", str(d), "--to", str(to), "--base", "https://x.org")
    assert run("check", str(to)).returncode == 0


def test_the_departures_are_found_at_their_lines(tmp_path):
    assert checked(tmp_path, "intro first\n# Title\n") == [
        '1 the file must begin with a "# " title',
        '2 a "> " summary should follow the title',
    ]
    got = checked(
        tmp_path,
        "# T\n\n> s\n\n# Second\n\n## A\n\n- [a](https://x.org/a)\nnot an item\n\n### Deep\n\n## B\n\n## Optional\n\n- [o](x.md): n\n\n## After\n\n- [z](https://x.org/z)\n",
    )
    assert '5 only one "# " title is allowed' in got
    assert '10 a list item should be "- [text](url)" with a note after ": "' in got
    assert '12 after the title, headings must be "## " sections' in got
    assert '14 the section "B" is empty' in got
    assert '16 the "Optional" section should be last' in got
    assert any(x.startswith("18 a relative link (x.md)") for x in got)


def test_a_missing_summary_a_bad_section_heading_and_a_tab(tmp_path):
    got = checked(tmp_path, "# T\n\n##NoSpace\n\n## A\n\n-\t[a](https://x.org)\n")
    assert (
        '1 a "> " summary should follow the title' in got
        and '3 a section heading must be "## " and a name' in got
    )
    assert "7 a tab: use spaces" in got


def test_check_on_a_missing_or_binary_file_is_refused(tmp_path):
    assert run("check", str(tmp_path / "missing")).returncode == 2
    (tmp_path / "b").write_bytes(b"\0\1\2")
    assert run("check", str(tmp_path / "b")).returncode == 2


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    d = folder(tmp_path, {"a.md": "x"})
    to = str(tmp_path / "l.txt")
    for argv in ([], ["write"], ["check"], ["write", "--from", str(d)], ["write", "--to", to], ["write", "--from", str(d), "--to", to, "--base", "ftp://x"],
                 ["write", "--from", str(d), "--to", to, "--nope", "x"], ["write", "--from", str(tmp_path / "missing"), "--to", to], ["nope"], ["check", "a", "b"]):  # fmt: skip
        assert run(*argv).returncode == 2, argv
    assert "llms_txt.py" in run().stderr
