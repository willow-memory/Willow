"""man-pages: a man page as its title, headings and text; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "man_pages.py"
spec = importlib.util.spec_from_file_location("man_pages", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'.\\" a comment\n.TH LS 1 "March 2024" "coreutils" "User Commands"\n.SH NAME\nls \\- list directory contents\n.SH SYNOPSIS\n.B ls\n[\\fIOPTION\\fR]... [\\fIFILE\\fR]...\n'
    b'.SH DESCRIPTION\nList information about the \\fBFILE\\fRs.\n.TP\n.BR \\-a ", " \\-\\-all\ndo not ignore entries starting with \\&.\n.PP\nSecond \\(em paragraph.\n'
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


def test_a_page_is_its_title_headings_and_text_with_fonts_and_escapes_read():
    assert mod.convert(SAMPLE) == (
        "LS(1)\n\nNAME\nls - list directory contents\n\nSYNOPSIS\nls [OPTION]... [FILE]...\n\n"
        "DESCRIPTION\nList information about the FILEs.\n\n-a, --all\ndo not ignore entries starting with .\n\nSecond \u2014 paragraph.\n"
    )


def test_a_gzipped_page_is_read_and_a_huge_one_is_not():
    import gzip

    assert mod.convert(gzip.compress(SAMPLE)) == mod.convert(SAMPLE)
    huge = gzip.compress(b".TH X 1\n" + b"a" * (mod.BIGGEST + 10))
    assert mod.convert(huge) is None
    just = gzip.compress(b".TH X 1\n.SH NAME\nx\n")
    assert mod.convert(just).startswith("X(1)")


def test_requests_and_macros():
    page = (
        b'.TH FOO 3p\n.SS Sub heading\n.IP "\\(bu" 2\nbullet text\n.RS\n.nf\nkept line\n.fi\n.RE\n.de XX\nmacro body\n.SH IGNORED\n..\n'
        b".SM small\n.BI -n  count\n.IR file (1)\n.br\nafter break\n.so man1/other.1\n.\n'\n"
    )
    assert (
        mod.convert(page)
        == "FOO(3p)\n\nSub heading\n\n\u2022\nbullet text\nkept line\nsmall -ncount file(1)\nafter break\n"
    )


def test_escapes():
    p = mod.plain
    assert p(r"\fBbold\fR \f(CWmono\fP \f[CR]x") == "bold mono x"
    assert p(r"a\-b \- c\ d\e \\ x\&y\|z\^w\%v") == "a-b - c d\\ \\ xyzwv"
    assert (
        p(r"\(em\(en\(aq\(lq\(rq\(co\(bu\(hy \*(lq quoted\*(rq")
        == "\u2014\u2013'\u201c\u201d\u00a9\u2022- \u201c quoted\u201d"
    )


def test_arguments_honour_quotes():
    assert (
        mod.words('a "b c" d') == ["a", "b c", "d"]
        and mod.words('"x ""y"" z"') == ['x "y" z']
        and mod.words("") == []
    )


def test_a_page_with_no_text_is_no_result():
    for empty in (
        b"",
        b'.\\" only a comment\n',
        b".TH X 1\n",
        b".so man1/other.1\n",
        b".de XX\nbody\n..\n",
    ):
        assert mod.convert(empty) is None, empty


def test_only_section_numbered_names_are_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "man1/ls.1": SAMPLE,
            "man3/printf.3.gz": __import__("gzip").compress(SAMPLE),
            "notes.txt": b"hi",
            "README.9": SAMPLE,
            "bad.1": b".so x\n",
        },
    )
    assert "wrote 2 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "man3" / "printf.3.gz.txt").is_file()


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"man1/ls.1": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "man1/ls.1.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path, {"man1/ls.1": SAMPLE, ".hid/man1/ls.1": SAMPLE, ".man1/ls.1": SAMPLE}
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["man1/ls.1.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"man1/ls.1": SAMPLE})
    before = (tmp_path / "src" / "man1/ls.1").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "man1/ls.1.txt").read_bytes() == (
        out / "man1/ls.1.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "man1/ls.1").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(tmp_path, {"good.1": SAMPLE, "bad.1": b"\x1f\x8b not gzip"})
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.1.txt").is_file() and not (out / "bad.1.txt").exists()


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
        assert got.returncode == 2 and "man_pages.py" in got.stderr
