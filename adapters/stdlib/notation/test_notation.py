"""notation: a glossary from where a paper says what its symbols mean, in
both shapes (a name before the symbol, the symbol then "is the"); one
symbol only, accents and arguments read through, generic words and verbs
refused, at most two names a symbol; each equation's symbols line in the
order it uses them, capped, taking its room from the prose so a passage is
still one chunk; a folder's files share one glossary; the kernel serves the
equation to a question in the glossary's words; the command line's
refusals and exit codes, and originals unchanged."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "notation.py"
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

spec = importlib.util.spec_from_file_location("notation", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

PAPER = rb"""\documentclass{article}
\begin{document}
Let $\eta$ be small. The structure factor $S(q)$ of a fluid at
packing fraction $\eta$ follows, where $\eta$ is the packing fraction
and $\hat{c}(k)$ denotes the direct correlation function. The number
density $\rho$ is written $\rho$ here, and $\rho\sigma^3$ is the reduced
density; the coefficient $a$ is fixed later.
The Ornstein-Zernike relation then gives
\begin{equation}
S(q) = \frac{1}{1 - \rho \hat{c}(q)} \label{eq:oz}
\end{equation}
for every $q$.

Nothing is defined for
\[ x + y = z \]
at all.
\end{document}
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


def test_a_paper_says_what_its_symbols_mean_in_both_shapes():
    g = mod.glossary([PAPER])
    assert g["\\eta"] == [
        "packing fraction"
    ]  # "at packing fraction $\eta$" has no article
    assert g["S"] == ["structure factor"]  # a name before the symbol
    assert g["c"] == ["direct correlation function"]  # the symbol, then "denotes the"
    assert "a" not in g  # a lone generic word names nothing
    assert "\\sigma" not in g  # $\rho\sigma^3$ is two symbols


def test_one_symbol_reads_through_accents_subscripts_and_arguments():
    assert mod.symbol(r"\hat{c}(k)") == "c"
    assert mod.symbol(r"S(q)") == "S"
    assert mod.symbol(r"\eta") == "\\eta"
    assert mod.symbol(r"g_{ij}(r)") == "g"
    assert mod.symbol(r"\sigma^3") == "\\sigma"
    assert mod.symbol(r"\widehat{\mathbf{h}}") == "h"
    for many in (r"\rho\sigma^3", "x = 1", r"\frac{1}{2}", "ab", r"\etaa", ""):
        assert mod.symbol(many) is None, many


def test_a_name_is_cut_after_its_last_article_and_refused_when_it_is_no_name():
    assert mod._phrase("fluid the structure factor") == "structure factor"
    assert (
        mod._phrase("Radial Distribution Function of") == "radial distribution function"
    )
    assert mod._phrase("coefficient") is None and mod._phrase("map") is None
    assert mod._phrase("axis represents") is None and mod._phrase("case") is None
    assert mod._phrase("pressure") == "pressure"


def test_a_symbol_keeps_its_first_two_names():
    paper = (
        rb"\begin{document} the pressure $p$, the osmotic pressure $p$, "
        rb"the vapour pressure $p$. \end{document}"
    )
    assert mod.glossary([paper])["p"] == ["pressure", "osmotic pressure"]


def test_an_equation_names_its_symbols_once_in_the_order_it_uses_them():
    assert mod.used(r"S(q) = \frac{1}{1 - \rho \hat{c}(q)} + S") == [
        "S", "q", "\\rho", "c",
    ]  # fmt: skip
    words = {"S": ["structure factor"], "c": ["direct correlation function"]}
    assert mod.line_for(r"S = 1/(1-\rho c)", words) == (
        "symbols: S structure factor; c direct correlation function"
    )
    assert mod.line_for("x + y", words) == ""


def test_the_symbols_line_is_capped_and_drops_the_last_symbols():
    words = {chr(97 + i): ["a rather long name for a symbol"] for i in range(10)}
    line = mod.line_for(" + ".join(chr(97 + i) for i in range(10)), words)
    assert len(line) <= mod.LINE_AT_MOST and line.startswith("symbols: a ")
    assert "; f " not in line and line.count(";") == 4


def test_each_equation_carries_its_symbols_line_after_its_citation():
    got = mod.passages(PAPER, "p/main.tex", mod.glossary([PAPER]))
    first, second = got
    lines = first.split("\n")
    assert lines[0] == "p/main.tex line 9, label eq:oz"
    assert lines[1] == (
        "symbols: S structure factor; \\rho number density; "
        "c direct correlation function"
    )
    assert r"S(q) = \frac{1}{1 - \rho \hat{c}(q)}" in lines  # math as written
    assert "symbols:" not in second and second.startswith("p/main.tex line 15")


def test_the_symbols_line_takes_its_room_from_the_prose(tmp_path):
    long = b"Words go on and on here. " * 40
    paper = (
        rb"\begin{document} the structure factor $S$ and the density $\rho$. "
        + long
        + rb"\begin{equation} S = \rho \end{equation} after. \end{document}"
    )
    (p,) = mod.passages(paper, "x.tex", mod.glossary([paper]))
    assert len(p) <= kernel.MAX_CHUNK
    assert "symbols: S structure factor; \\rho density" in p
    assert "Words go on" in p  # the prose kept what room was left


def test_a_folders_files_share_one_glossary_and_another_folder_does_not(tmp_path):
    defs = rb"\begin{document} the packing fraction $\eta$. \end{document}"
    eq = rb"\begin{document} \[ \eta^2 \] \end{document}"
    res, out = mirror_of(tmp_path, {"a/defs.tex": defs, "a/eq.tex": eq, "b/eq.tex": eq})
    assert res.returncode == kernel.ALIVE
    assert "symbols: \\eta packing fraction" in (out / "a/eq.tex.txt").read_text()
    assert "symbols:" not in (out / "b/eq.tex.txt").read_text()
    assert not (out / "a/defs.tex.txt").exists()  # no equation: skipped
    assert "found 2 equations; 1 given the words" in res.stdout
    assert "wrote 2 files" in res.stdout and "skipped 1" in res.stdout
    assert (tmp_path / "src/a/defs.tex").read_bytes() == defs  # originals unchanged


def test_the_kernel_serves_the_equation_to_a_question_in_the_glossarys_words(tmp_path):
    paper = (
        rb"\begin{document} The structure factor $S(q)$ is measured, and $\hat{c}$ "
        rb"denotes the direct correlation function." + b"\n\n" + rb"Then "
        rb"\begin{equation} S(q) = 1/(1 - \rho \hat{c}(q)) \end{equation} holds."
        rb" \end{document}"
    )
    question = (
        "What is the structure factor in terms of the direct correlation function?"
    )
    res, out = mirror_of(tmp_path, {"paper/main.tex": paper})
    assert res.returncode == kernel.ALIVE
    (top,) = kernel.rank(kernel.chunks(out), question, top=1)
    assert "S(q) = 1/(1 - \\rho \\hat{c}(q))" in top["text"]
    assert top["path"] == "paper/main.tex.txt"
    plain = tmp_path / "plain"  # the same equation as the equations add-on writes it
    plain.mkdir()
    eqs = mod.equations.passages(paper, "paper/main.tex")
    (plain / "main.tex.txt").write_text("\n\n".join(eqs) + "\n", encoding="utf-8")
    assert kernel.rank(kernel.chunks(plain), question, top=1) == []


def test_nothing_readable_escalates(tmp_path):
    res, _ = mirror_of(tmp_path, {"notes.tex": b"no equations here", "a.txt": b"x"})
    assert res.returncode == kernel.ESCALATE and "wrote 0 files" in res.stdout


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    for argv in ([], ["mirror"], ["mirror", "--from", "x"], ["copy", "--from", "a", "--to", "b"],
                 ["mirror", "--from", "a", "--into", "b"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == kernel.REFUSED and "notation.py" in got.stderr, argv


def test_a_missing_folder_and_nested_folders_are_refused(tmp_path):
    (tmp_path / "src").mkdir()
    got = run("mirror", "--from", str(tmp_path / "nope"), "--to", str(tmp_path / "o"))
    assert got.returncode == kernel.REFUSED and "not a folder" in got.stderr
    for to in (tmp_path / "src" / "out", tmp_path / "src", tmp_path):
        got = run("mirror", "--from", str(tmp_path / "src"), "--to", str(to))
        assert got.returncode == kernel.REFUSED and "inside one another" in got.stderr


def test_a_tight_passage_gives_the_prose_after_half_the_room_left():
    eq = "q = " + " + ".join(["x"] * 90)  # long math, no symbol the paper defines
    after = " ".join(["word"] * 60)  # no sentence end: cut on a word
    paper = (
        rb"\begin{document} Before it comes a sentence. \[ " + eq.encode()
        + rb" \] " + after.encode() + rb" \end{document}"
    )  # fmt: skip
    (p,) = mod.passages(paper, "x.tex", {})
    head, *_, last = p.split("\n")
    room = kernel.MAX_CHUNK - len(head) - len(eq) - 5
    assert last.startswith("word") and room // 2 - 5 < len(last) <= room // 2
    assert len(p) <= kernel.MAX_CHUNK


def test_a_long_equation_shortens_its_symbols_line_to_stay_one_chunk():
    words = {c: [f"the name of {c} in words"] for c in "abcdefgh"}
    eq = "a + b + c + d + e + f + g + h = " + " + ".join(["1"] * 95)
    paper = rb"\begin{document} \[ " + eq.encode() + rb" \] \end{document}"
    (p,) = mod.passages(paper, "x.tex", words)
    assert len(p) <= kernel.MAX_CHUNK and "symbols: a the name of a" in p
    assert "h the name" not in p  # the last symbols left out to fit
    huge = rb"\begin{document} \[ a = " + b" + 1" * 200 + rb" \] \end{document}"
    (p,) = mod.passages(huge, "x.tex", words)
    assert "symbols:" not in p  # an equation longer than a chunk: no room at all
