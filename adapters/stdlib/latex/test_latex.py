"""latex: a LaTeX source as its prose, line for line; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "latex.py"
spec = importlib.util.spec_from_file_location("latex", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE = (
    b"\\documentclass{article}\n\\usepackage{amsmath}\n\\title{Tides of the Estuary}\n\\author{Ada Example}\n\\begin{document}\n\\maketitle\n"
    b"\\section{Method}\\label{sec:m}\nWe measure the tide at six harbours \\cite{smith2020}. % a comment\n"
    b"The result is $x = 1$ and\n\\begin{equation}\ny = mx + b\n\\end{equation}\nholds \\emph{everywhere}.\n\\end{document}\n"
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


def tex(body: str) -> str:
    return mod.convert(body.encode())


def test_the_mirror_has_the_sources_lines_so_a_passage_is_cited_by_its_own_line():
    out = mod.convert(SAMPLE)
    src = SAMPLE.decode().split("\n")
    lines = out.split("\n")
    assert len(lines) <= len(src), "never more lines than the source"
    for needle in (
        "Method",
        "We measure the tide at six harbours [smith2020].",
        "holds everywhere.",
    ):
        assert any(needle in x for x in lines)
    assert lines[src.index("\\section{Method}\\label{sec:m}")] == "Method"
    assert (
        lines[
            src.index(
                "We measure the tide at six harbours \\cite{smith2020}. % a comment"
            )
        ]
        == "We measure the tide at six harbours [smith2020]."
    )


def test_the_title_and_author_are_kept_and_the_rest_of_the_preamble_is_not():
    out = mod.convert(SAMPLE)
    assert "title: Tides of the Estuary" in out and "author: Ada Example" in out
    assert "documentclass" not in out and "amsmath" not in out and "article" not in out


def test_math_and_environments_are_dropped_but_their_lines_are_kept():
    out = tex(
        "a $x$ b\n\\[ y = 1 \\]\nc $$z$$ d\n\\begin{align*}\nq\n\\end{align*}\ne\n\\begin{verbatim}\ncode here\n\\end{verbatim}\nf\n"
    )
    assert out.split("\n")[:11] == ["a b", "", "c d", "", "", "", "e", "", "", "", "f"]


def test_arguments_to_keep_and_arguments_to_drop():
    out = tex(
        "\\textbf{bold} \\emph{it} \\caption{A figure} \\label{x} \\ref{y} \\includegraphics[width=3cm]{pic.png} \\href{http://x}{the link}"
    )
    assert out == "bold it A figure the link\n"


def test_citations_footnotes_and_items():
    out = tex(
        "see \\citep[p.~3]{a, b} and \\cite{c}.\nWord\\footnote{a note} here.\n\\item first\n\\item[x] second\n"
    )
    assert out == "see [a,b] and [c].\nWord (a note) here.\n- first\n- x second\n"


def test_escapes_dashes_quotes_and_accents():
    out = tex(
        r"50\% of \$5 \& R\_D, pages 3--5 --- ``quoted'' caf\'e M{\"u}ller Stra\ss e na\"ive"
    )
    assert out == "50% of $5 & R_D, pages 3–5 — “quoted” café Müller Straße naïve\n"


def test_a_comment_is_dropped_but_an_escaped_percent_is_not():
    assert tex("keep this % drop that\nand 5\\% of it\n") == "keep this\nand 5% of it\n"


def test_a_file_with_no_prose_is_not_a_result():
    assert (
        mod.convert(b"\\documentclass{article}\n\\begin{document}\n\\end{document}\n")
        is None
        and mod.convert(b"") is None
    )


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"paper/main.tex": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "paper/main.tex.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "paper/main.tex": SAMPLE,
            ".hid/paper/main.tex": SAMPLE,
            ".paper/main.tex": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["paper/main.tex.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"paper/main.tex": SAMPLE})
    before = (tmp_path / "src" / "paper/main.tex").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "paper/main.tex.txt").read_bytes() == (
        out / "paper/main.tex.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "paper/main.tex").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path, {"good.tex": SAMPLE, "bad.tex": b"\xff\xfe not utf8"}
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.tex.txt").is_file() and not (out / "bad.tex.txt").exists()


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
        assert got.returncode == 2 and "latex.py" in got.stderr


def test_a_cedilla_or_caron_with_braces_or_a_space_but_not_a_command_that_starts_with_c_or_v():
    bs = chr(92)
    out = tex(
        f"Fran{bs}c{{c}}ois {bs}v{{S}}koda Fran{bs}c c. {bs}v S. {bs}vspace{{1cm}} {bs}caption{{Cap}}"
    )
    assert out == "François Škoda Franç. Š. Cap\n"
