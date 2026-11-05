"""equations: each displayed equation a passage of its own, cited by its .tex
line, with its labels and the prose around it, math kept as written; macros
for a display's opening read as what they stand for; inline math, comments,
verbatim and the preamble never an equation; a passage fits one kernel chunk;
hidden files skipped, an unreadable file skipped and counted, the same bytes
twice, originals unchanged, and MIRROR and FOLDER kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "equations.py"
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

spec = importlib.util.spec_from_file_location("equations", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE = rb"""\documentclass{article}
\def\be{\begin{equation}}
\newcommand{\ee}{\end{equation}}
\begin{equation} x = preamble \end{equation}
\begin{document}
\section{Structure}
The intensity scattered by $N$ identical spheres factorizes into a form factor
and the structure factor. The latter is
\be
S(q) = 1 + \rho \int [g(r)-1] e^{i\mathbf{q}\cdot\mathbf{r}}\, d\mathbf{r} \label{eq:S}
\ee
where $g(r)$ is the radial distribution function. More text follows here.

Integrating the compressibility, % a comment, $$ not math $$
\[ \frac{\beta P}{\rho} = \frac{1+\eta+\eta^2}{(1-\eta)^3} \]
which is the PY equation of state.
\begin{verbatim}
\[ verbatim is not math \]
\end{verbatim}
Baxter's coefficients are
\begin{align*}
a &= \frac{1+2\eta}{(1-\eta)^2}, \nonumber \\
b &= -\frac{3\eta\sigma}{2(1-\eta)^2} \notag
\end{align*}
and the price is \$5 or \$\$6.
$$Q(r) = \tfrac12 a (r^2-\sigma^2) + b (r-\sigma)$$
\end{document}
\[ after = the end \]
"""


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


def got() -> list[str]:
    return mod.passages(SAMPLE, "paper/py.tex")


def line_of(needle: bytes) -> int:
    return SAMPLE.split(b"\n").index(needle) + 1


def test_each_displayed_equation_is_one_passage_cited_by_its_own_line():
    ps = got()
    opening = [
        rb"\be",
        rb"\[ \frac{\beta P}{\rho} = \frac{1+\eta+\eta^2}{(1-\eta)^3} \]",
        rb"\begin{align*}",
        rb"$$Q(r) = \tfrac12 a (r^2-\sigma^2) + b (r-\sigma)$$",
    ]
    lines = [line_of(x) for x in opening]
    assert [p.split("\n")[0] for p in ps] == [
        f"paper/py.tex line {lines[0]}, label eq:S",
        f"paper/py.tex line {lines[1]}",
        f"paper/py.tex line {lines[2]}",
        f"paper/py.tex line {lines[3]}",
    ]


def test_the_math_is_kept_as_written_with_labels_and_numbering_taken_out():
    ps = got()
    assert (
        r"S(q) = 1 + \rho \int [g(r)-1] e^{i\mathbf{q}\cdot\mathbf{r}}\, d\mathbf{r}"
        in ps[0].split("\n")
    )
    assert r"\frac{\beta P}{\rho} = \frac{1+\eta+\eta^2}{(1-\eta)^3}" in ps[1].split(
        "\n"
    )
    assert (
        r"a &= \frac{1+2\eta}{(1-\eta)^2}, \\ b &= -\frac{3\eta\sigma}{2(1-\eta)^2}"
        in ps[2].split("\n")
    )
    assert r"Q(r) = \tfrac12 a (r^2-\sigma^2) + b (r-\sigma)" in ps[3].split("\n")
    for p in ps:
        assert "\\label" not in p and "nonumber" not in p and "notag" not in p


def test_the_prose_before_and_after_comes_along():
    ps = got()
    first = ps[0].split("\n")
    assert first[1].endswith("form factor and the structure factor. The latter is")
    assert first[-1] == "where $g(r)$ is the radial distribution function."
    second = ps[1].split("\n")
    assert second[1] == "Integrating the compressibility,"
    assert second[-1] == "which is the PY equation of state."
    assert ps[2].split("\n")[1] == "Baxter's coefficients are"


def test_the_preamble_comments_verbatim_escaped_dollars_and_what_follows_the_document_are_no_equation():
    text = "\n".join(got())
    for absent in (
        "preamble",
        "not math",
        "verbatim is not math",
        "after = the end",
        "\\end{document}",
        "a comment",
    ):
        assert absent not in text
    assert len(got()) == 4


def test_inline_math_is_prose_not_an_equation():
    assert mod.passages(b"Take $x = 1$ and \\(y=2\\) here.\n", "a.tex") == []


def test_a_file_without_a_document_environment_is_read_from_the_top():
    ps = mod.passages(b"Lead in\n\\begin{gather}\nE = mc^2\n\\end{gather}\n", "a.tex")
    assert ps == ["a.tex line 2\nLead in\nE = mc^2"]


def test_an_empty_display_is_no_passage():
    assert mod.passages(b"\\[ \\label{x} \\]\n", "a.tex") == []


def test_every_env_and_its_starred_form_is_a_display():
    for env in (
        "equation",
        "align",
        "gather",
        "multline",
        "eqnarray",
        "displaymath",
        "flalign",
        "alignat",
    ):
        for star in ("", "*"):
            body = f"\\begin{{{env}{star}}}\nk = 1\n\\end{{{env}{star}}}\n".encode()
            assert mod.passages(body, "a.tex") == ["a.tex line 1\nk = 1"], env + star


def test_alignat_takes_its_column_count_off():
    body = b"\\begin{alignat}{2}\nk &= 1\n\\end{alignat}\n"
    assert mod.passages(body, "a.tex") == ["a.tex line 1\nk &= 1"]


def test_a_macro_for_a_display_counts_only_whole_and_only_when_defined():
    body = b"\\newcommand\\beq{\\begin{equation}}\n\\def\\eeq{\\end{equation}}\n\\beq k=1 \\eeq\n\n\\beqx\n"
    assert mod.passages(body, "a.tex") == ["a.tex line 3\nk=1"]
    assert mod.passages(b"\\beq k=1 \\eeq\n", "a.tex") == []
    renew = b"\\renewcommand*{\\be}{\\[}\n\\def\\ee{\\]}\n\\be k=2 \\ee\n"
    assert mod.passages(renew, "a.tex") == ["a.tex line 3\nk=2"]


def test_several_labels_are_named():
    body = (
        b"\\begin{align}\na = 1 \\label{one} \\\\\nb = 2 \\label{ two }\n\\end{align}\n"
    )
    assert (
        mod.passages(body, "a.tex")[0].split("\n")[0] == "a.tex line 1, label one, two"
    )


def test_context_stays_in_its_paragraph_and_its_first_sentence_after():
    body = b"Old paragraph.\n\nNew one leads in\n\\[ k = 1 \\]\nthen ends. And more.\n\nNext paragraph.\n"
    assert mod.passages(body, "a.tex") == [
        "a.tex line 4\nNew one leads in\nk = 1\nthen ends."
    ]


def test_context_between_two_equations_is_not_served_twice_past_its_sentence():
    body = b"\\[ a = 1 \\]\nso that. Then\n\\[ b = 2 \\]\n"
    ps = mod.passages(body, "a.tex")
    assert ps == ["a.tex line 1\na = 1\nso that.", "a.tex line 3\nThen\nb = 2"]


def test_long_context_is_cut_at_a_sentence_so_a_passage_is_one_chunk():
    lead = ("The quick brown fox jumps over the lazy dog. " * 30).encode()
    tail = ("and then " * 60).encode()
    body = lead + b"Finally\n\\[ x = 1 \\]\n" + tail + b"\n"
    (p,) = mod.passages(body, "a.tex")
    assert len(p) <= kernel.MAX_CHUNK
    lines = p.split("\n")
    assert lines[1].startswith("The quick") and lines[1].endswith("Finally")
    assert lines[2] == "x = 1"
    assert lines[3].startswith("and then") and len(lines[3]) <= mod.AFTER


def test_a_cut_with_no_sentence_end_falls_on_a_word():
    body = ("word " * 200).encode() + b"\n\\[ x = 1 \\]\n"
    (p,) = mod.passages(body, "a.tex")
    assert p.split("\n")[1].startswith("word ") and len(p) <= kernel.MAX_CHUNK
    assert mod._before("abc", 2) == "" and mod._after("abcdef", 2) == ""
    assert mod._before("one. two three", 9) == "two three"
    assert mod._after("one two three", 8) == "one two"


def test_the_kernel_serves_the_equation_with_its_words(tmp_path):
    res, out = mirror_of(tmp_path, {"paper/py.tex": SAMPLE})
    assert res.returncode == 0
    pile = kernel.chunks(out)
    assert len(pile) == 4
    (top,) = kernel.rank(pile, "the compressibility PY equation of state", top=1)
    assert r"\frac{1+\eta+\eta^2}{(1-\eta)^3}" in top["text"]
    assert top["path"] == "paper/py.tex.txt"


def test_mirror_writes_each_file_beside_its_path_and_counts(tmp_path):
    files = {
        "paper/py.tex": SAMPLE,
        "notes/none.tex": b"No display here, only $x$.\n",
        "bad.tex": b"\xff\xfe not utf-8 \\[ x \\]",
        ".hidden.tex": b"\\[ h = 1 \\]\n",
        ".dot/in.tex": b"\\[ h = 1 \\]\n",
        "readme.txt": b"\\[ t = 1 \\]\n",
    }
    res, out = mirror_of(tmp_path, files)
    assert res.returncode == 0, res.stderr
    assert res.stdout.strip() == f"wrote 4 equations from 1 files to {out}; skipped 2"
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["paper/py.tex.txt"]
    assert (out / "paper/py.tex.txt").read_text() == "\n\n".join(got()) + "\n"
    for rel, data in files.items():
        assert (tmp_path / "src" / rel).read_bytes() == data
    first = (out / "paper/py.tex.txt").read_bytes()
    again = run("mirror", "--from", str(tmp_path / "src"), "--to", str(out))
    assert again.returncode == 0 and (out / "paper/py.tex.txt").read_bytes() == first


def test_nothing_readable_escalates(tmp_path):
    res, out = mirror_of(tmp_path, {"a.tex": b"just prose\n"})
    assert res.returncode == kernel.ESCALATE
    assert "wrote 0 equations from 0 files" in res.stdout
    assert not out.exists()


def test_a_bad_command_line_is_refused_and_names_the_script():
    got = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    assert got.returncode == 2 and "equations.py" in got.stderr
    for argv in (
        ["mirror", "--from", "x"],
        ["copy", "--from", "a", "--to", "b"],
        ["mirror", "--from", "a", "--into", "b"],
    ):
        res = run(*argv)
        assert res.returncode == kernel.REFUSED and "usage: equations.py" in res.stderr


def test_a_missing_folder_and_nested_folders_are_refused(tmp_path):
    res = run("mirror", "--from", str(tmp_path / "nope"), "--to", str(tmp_path / "out"))
    assert res.returncode == kernel.REFUSED and "not a folder" in res.stderr
    (tmp_path / "src").mkdir()
    for to in (tmp_path / "src", tmp_path / "src" / "out", tmp_path):
        res = run("mirror", "--from", str(tmp_path / "src"), "--to", str(to))
        assert res.returncode == kernel.REFUSED and "inside one another" in res.stderr
