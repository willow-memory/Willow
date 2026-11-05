"""demo/percus-yevick: the draft hangs together, and its hit rule does what
it says on formulas written by hand, not taken from the stack.

Fetching the sources and running the pipeline go online and are not part of
CI; this is. Once FROZEN.json exists, every file it names is held to it.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fetch  # noqa: E402
import pipeline  # noqa: E402
import score  # noqa: E402

SOURCES = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))["sources"]


def test_frozen_files_are_as_frozen_or_the_study_says_it_is_a_draft():
    frozen = HERE / "FROZEN.json"
    if not frozen.exists():
        assert "DRAFT" in (HERE / "README.md").read_text(encoding="utf-8")
        return
    for rel, sha in json.loads(frozen.read_text(encoding="utf-8"))["files"].items():
        got = hashlib.sha256((HERE / rel).read_bytes()).hexdigest()
        assert got == sha, (
            f"{rel} changed after it was frozen; a change is a new freeze"
        )


def test_every_question_names_a_step_and_every_step_is_asked():
    steps = {s["id"] for s in score.STEPS["steps"]}
    asked = set()
    for name, _ in pipeline.scan.questions(
        (HERE / "questions" / "author.txt").read_text(encoding="utf-8")
    ):
        assert name.split(".")[0] in steps, name
        asked.add(name.split(".")[0])
    assert asked == steps
    for name, _ in pipeline.scan.questions(
        (HERE / "questions" / "null.txt").read_text(encoding="utf-8")
    ):
        assert name.split(".")[0] not in steps, name


def test_every_source_is_pinned_by_address_and_hash():
    assert len({fetch.slug(s["id"]) for s in SOURCES}) == len(SOURCES)
    for s in SOURCES:
        assert s["kind"] in pipeline.READERS, s["id"]
        assert s["url"].startswith("https://") and s["version"], s["id"]
        assert len(s["sha256"]) == 64 and s["bytes"] > 0 and s["fetched"], s["id"]


HAND = {
    "s0": r"\beta P/\rho = 1 + 4\eta + 10\eta^{2} + \dots",
    "s1a": r"The amplitude is the Fourier transform of the electron density, A(q) = \int \rho_e(r) e^{i q r} dr",
    "s1b": r"f(q) = 3\,\frac{\sin(qR) - qR\cos(qR)}{(qR)^3}",
    "s1c": r"For identical spheres the intensity is a form factor times a structure factor.",
    "s2": r"S(q) = 1 + \rho \int \left[ g(r) - 1 \right] e^{i q r}\, dr",
    "s3": r"S(k) = \frac{1}{1-\rho\hat{c}(k)}",
    "s4": r"In the Percus--Yevick approximation for hard spheres, $c(r) = 0$ for $r>\sigma$.",
    "s5a": r"1-\rho\hat{c}(k) = \hat{Q}(k)\,\hat{Q}(-k)",
    "s5b": r"a = \dfrac{1+2\varphi}{(1-\varphi)^2}",
    "s6": r"S(0) = \frac{(1-\eta)^4}{(1+2\eta)^2}",
    "s7": r"\frac{\beta P}{\rho} = \frac{1+\eta+\eta^2}{\left(1-\eta\right)^3}",
}


def test_each_step_is_held_by_its_own_formula_and_by_no_other():
    assert set(HAND) == set(score.BY_ID)
    for step, text in HAND.items():
        assert score.steps_held(text) == [step], (step, score.steps_held(text))


def test_near_misses_hold_nothing():
    for text in (
        r"\frac{1+2\eta}{(1-\eta)^3}",  # the wrong power
        r"\frac{1+\eta+\eta^2}{(1+\eta)^3}",  # the wrong sign
        r"S(q) = 1 + \rho \hat{h}(q)",  # no integral, no g(r) - 1
        "the Percus-Yevick approximation for hard spheres",  # no closure written
        "qqqq zzzz",
    ):
        assert score.steps_held(text) == [], text


def test_the_traps_are_told_apart_from_the_answer():
    assert score.traps(r"Z = \frac{1+\eta+\eta^2-\eta^3}{(1-\eta)^3}") == [
        "carnahan-starling"
    ]
    assert score.steps_held(r"Z = \frac{1+\eta+\eta^2-\eta^3}{(1-\eta)^3}") == []
    assert score.traps(r"\frac{1+2\eta+3\eta^2}{(1-\eta)^2}") == ["virial-route"]
    assert score.traps(HAND["s7"]) == []


def test_normalizing_takes_out_looks_and_nothing_else():
    assert (
        score.normalize(r"\left( 1 - \phi \right)^{2} \, \tfrac{a}{b}")
        == r"(1-\eta)^{2}\frac{a}{b}"
    )
    assert score.normalize(r"\mathrm{e}^{-i q} \xi \varphi") == r"e^{-iq}\eta\eta"
    assert (
        score.normalize(r"\phiX \xin") == r"\phiX\xin"
    )  # a longer command is not the packing fraction


def test_wertheim_is_flagged_only_when_every_hit_says_laplace():
    assert score.through_wertheim(["the Laplace transform of r g(r)", "by Laplace"])
    assert not score.through_wertheim(
        ["the Laplace transform", "Baxter's factorization"]
    )
    assert not score.through_wertheim([])


def test_check_says_missing_unpinned_and_differs(tmp_path, capsys):
    one = [{"id": "arXiv:0000.0001", "sha256": "0" * 64}]
    assert fetch.check(tmp_path, one) == 42
    assert "missing   arXiv:0000.0001" in capsys.readouterr().out
    (tmp_path / "arXiv_0000.0001").mkdir()
    (tmp_path / "arXiv_0000.0001" / "source.bin").write_bytes(b"not it")
    assert fetch.check(tmp_path, one) == 2
    assert "DIFFERS   arXiv:0000.0001" in capsys.readouterr().out
    assert fetch.check(tmp_path, [{"id": "arXiv:0000.0001", "sha256": None}]) == 42
    good = [{"id": "arXiv:0000.0001", "sha256": hashlib.sha256(b"not it").hexdigest()}]
    assert fetch.check(tmp_path, good) == 0


def test_unpack_reads_a_tar_a_gzipped_file_and_a_pdf(tmp_path):
    import gzip
    import io
    import tarfile

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        info = tarfile.TarInfo("paper.tex")
        info.size = 5
        t.addfile(info, io.BytesIO(b"\\[x\\]"))
    for name, data, want in (
        ("tar", buf.getvalue(), "paper.tex"),
        ("gz", gzip.compress(b"\\[y\\]"), "main.tex"),
        ("pdf", b"%PDF-1.4 ...", "paper.pdf"),
    ):
        (tmp_path / name).mkdir()
        fetch.unpack("arxiv", data, tmp_path / name)
        assert (tmp_path / name / "src" / want).is_file(), name
    (tmp_path / "p").mkdir()
    fetch.unpack("pdf", b"%PDF-1.3 scan", tmp_path / "p")
    assert (tmp_path / "p" / "src" / "paper.pdf").read_bytes() == b"%PDF-1.3 scan"
    (tmp_path / "w").mkdir()
    fetch.unpack("wikipedia", b"<mediawiki/>", tmp_path / "w")
    assert (tmp_path / "w" / "export.xml").read_bytes() == b"<mediawiki/>"


def test_a_bad_command_line_is_refused():
    assert fetch.main([]) == 2 and fetch.main(["--to", "x", "--both"]) == 2
    assert pipeline.main(["--stack", "x"]) == 2
