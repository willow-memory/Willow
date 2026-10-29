"""bibtex: each reference as a passage that begins with its key; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "bibtex.py"
spec = importlib.util.spec_from_file_location("bibtex", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE = (
    b'% a comment\n@string{jms = "Journal of Made-Up Studies"}\n@article{smith2020,\n  author = {Example, Ada and Sample, Cy},\n'
    b"  title = {Tides of the {E}stuary},\n  journal = jms,\n  year = 2020, volume = {12}, number = {3}, pages = {45--67},\n"
    b'  doi = "10.1000/xyz123", keywords = {tides, estuaries},\n  abstract = {We measure the tide at six harbours.}\n}\n'
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


def convert(text: str) -> str | None:
    return mod.convert(text.encode())


def test_a_reference_starts_with_its_key_and_title_and_carries_the_rest():
    out = mod.convert(SAMPLE)
    assert out.startswith(
        "smith2020 (article): Tides of the Estuary, 2020\nby Example, Ada; Sample, Cy\n"
    )
    assert "in Journal of Made-Up Studies, 12(3), pages 45--67" in out
    assert (
        "doi: 10.1000/xyz123" in out
        and "keywords: tides, estuaries" in out
        and "abstract: We measure the tide at six harbours." in out
    )


def test_a_macro_a_hash_join_and_a_quoted_value_are_filled_in():
    out = convert(
        '@string{a = "Alpha"}\n@book{k, title = a # " and " # {Beta}, publisher = "Press {Co}", year = 2001}'
    )
    assert "k (book): Alpha and Beta, 2001" in out and "in Press Co" in out
    assert "May" in convert("@misc{m, title = {t}, note = may}")


def test_latex_accents_and_letters_are_read_as_the_letters_they_make():
    assert (
        mod.unlatex(r"M{\"u}ller, Jos\'e, Stra\ss e \& Co~Ltd, \o{}re")
        == "Müller, José, Straße & Co Ltd, øre"
    )


def test_comment_and_preamble_are_skipped_and_text_outside_entries_ignored():
    out = convert(
        'junk @comment{x = y}\n@preamble{"\\\\newcommand"}\nmore junk\n@misc{only, title = {One}}'
    )
    assert out.count("(") == 1 and out.startswith("only (misc): One")


def test_parentheses_can_delimit_an_entry_and_braces_nest():
    assert "p (misc): A {B} C" not in convert(
        "@misc(p, title = {A {B} C})"
    ) and "p (misc): A B C" in convert("@misc(p, title = {A {B} C})")


def test_many_authors_and_an_editor_are_listed():
    out = convert(
        "@inproceedings{c, author = {A One and B Two and C Three}, editor = {E Ed}, booktitle = {Proc}, title = {T}}"
    )
    assert (
        "by A One; B Two; C Three" in out
        and "edited by E Ed" in out
        and "in Proc" in out
    )


def test_a_file_with_no_reference_or_a_broken_one_is_not_a_reader_result():
    assert mod.convert(b"just words, no entries") is None
    for broken in (
        b"@article{k, title = {never closed",
        b'@article{k, title = "never closed',
        b"@article{k, title}",
        b"@article{k, = {x}}",
    ):
        try:
            mod.convert(broken)
        except mod.ERRORS:
            continue
        raise AssertionError(broken)


def test_a_command_that_starts_with_c_or_v_is_not_an_accent():
    bs = chr(92)
    assert (
        mod.unlatex(
            f"{bs}cite{{x}} {bs}vspace{{1cm}} Fran{{{bs}c c}}ois {bs}v{{S}}koda"
        )
        == "x 1cm François Škoda"
    )


def test_a_logo_command_keeps_its_name():
    assert (
        mod.unlatex(r"{\LaTeX}: a system for \BibTeX and \TeX users")
        == "LaTeX: a system for BibTeX and TeX users"
    )


def test_a_byte_order_mark_is_ignored():
    assert mod.convert(b"\xef\xbb\xbf@misc{k, title = {T}}").startswith("k (misc): T")


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"refs/paper.bib": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "refs/paper.bib.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "refs/paper.bib": SAMPLE,
            ".hid/refs/paper.bib": SAMPLE,
            ".refs/paper.bib": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["refs/paper.bib.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"refs/paper.bib": SAMPLE})
    before = (tmp_path / "src" / "refs/paper.bib").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "refs/paper.bib.txt").read_bytes() == (
        out / "refs/paper.bib.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "refs/paper.bib").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path, {"good.bib": SAMPLE, "bad.bib": b"@article{k, title = {never closed"}
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.bib.txt").is_file() and not (out / "bad.bib.txt").exists()


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
        assert got.returncode == 2 and "bibtex.py" in got.stderr
