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
    files = json.loads(frozen.read_text(encoding="utf-8"))["files"]
    for rel, sha in files.items():
        got = hashlib.sha256((HERE / rel).read_bytes()).hexdigest()
        assert got == sha, (
            f"{rel} changed after it was frozen; a change is a new freeze"
        )
    must = {"sources.json", "steps.json", "score.py", "tally.py", "pipeline.py",
            "arms.py", "rubric.md", "prompt.md", "words.txt", "expectations.json"}  # fmt: skip
    must |= {f"questions/{p.name}" for p in (HERE / "questions").iterdir()}
    must |= {f"models/{p.name}" for p in (HERE / "models").iterdir()}
    assert must <= set(files), sorted(must - set(files))


def test_every_question_names_a_step_and_every_step_is_asked():
    steps = set(score.BY_ID)  # the chain and the extended steps
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


EXT = {
    "e1": r"For r < \sigma the direct correlation function is $c(r) = -\lambda_1 - 6\eta\lambda_2 r$ with $\lambda_2 = -(1+\eta/2)^2/(1-\eta)^4$",
    "e2": r"g(\sigma^+) = \frac{1+\eta/2}{(1-\eta)^2}",
    "e3": r"h(r) = g(r) - 1",
    "e4": r"the cavity function y(r) = e^{\beta u(r)} g(r) is continuous",
    "e5": r"the form factor P(q) = |F(q)|^2 / V^2",
    "e6": r"I(q) \propto n P(q) S(q)",
    "e7": r"hard spheres: S(q) at \eta = 0.3, from the PY solution",
}


def test_each_step_is_held_by_its_own_formula_and_by_no_other():
    assert set(HAND) == set(score.CHAIN) and set(EXT) == set(score.EXTENDED)
    for step, text in HAND.items():
        assert score.steps_held(text) == [step], (step, score.steps_held(text))
        assert score.extended_held(text) == [], (step, score.extended_held(text))
    for step, text in EXT.items():
        assert score.extended_held(text) == [step], (step, score.extended_held(text))
        assert score.steps_held(text) == [], (step, score.steps_held(text))


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


def test_r4s_seed_is_frozen_and_another_is_only_for_a_dry_run(tmp_path, capsys):
    args = ["--stack", "s", "--work", "w", "--out", str(tmp_path / "o.json")]
    assert tally.SEED == 0
    assert pipeline.main([*args, "--seed", "7"]) == 2
    assert "frozen at 0" in capsys.readouterr().err


def test_every_blind_set_is_asked_and_the_prompt_is_not():
    assert pipeline.SETS == ["author", "null", "blind-a"]


import tally  # noqa: E402


def rows_for(
    found: dict[str, str], set_name: str = "author"
) -> tuple[list[dict], dict]:
    """A question per step; one served passage, holding `found[step]` when given."""
    rows, text_of = [], {}
    for step in score.BY_ID:
        pid = f"{set_name}-{step}"
        text_of[pid] = found.get(step, "nothing here")
        rows.append({"set": set_name, "id": f"{step}.1", "served": [{"id": pid}]})
    return rows, text_of


def test_r1_needs_nine_steps_with_baxter_and_the_answer():
    nine = {s: HAND[s] for s in list(HAND) if s not in ("s1a", "s1b")}
    rows, text_of = rows_for(nine)
    v = tally.tally(rows, text_of, None)
    assert v["R1"]["state"] == "satisfied" and v["R1"]["number"].startswith("9 of 11")
    assert "missing s1a, s1b" in v["R1"]["number"]
    no_baxter = {
        s: HAND[s] for s in HAND if s != "s5b"
    }  # ten found, one of them a must
    rows, text_of = rows_for(no_baxter)
    assert tally.tally(rows, text_of, None)["R1"]["state"] == "failing"
    eight = {s: HAND[s] for s in list(HAND) if s not in ("s0", "s1a", "s1b")}
    rows, text_of = rows_for(eight)
    assert tally.tally(rows, text_of, None)["R1"]["state"] == "failing"


def test_r2_is_not_asked_until_there_are_blind_questions_then_needs_seven():
    rows, text_of = rows_for(HAND)
    assert tally.tally(rows, text_of, None)["R2"]["state"] == "not asked"
    seven = {s: HAND[s] for s in ("s0", "s2", "s3", "s4", "s5b", "s6", "s7")}
    rows, text_of = rows_for(seven, "blind-a")
    v = tally.tally(rows, text_of, None)
    assert v["R2"]["state"] == "satisfied" and v["R1"]["state"] == "not asked"
    six = {s: HAND[s] for s in ("s0", "s2", "s3", "s4", "s5b", "s7")}
    rows, text_of = rows_for(six, "blind-a")
    assert tally.tally(rows, text_of, None)["R2"]["state"] == "failing"


def test_r3_counts_null_questions_served_any_chain_step():
    def nulls(k: int):
        rows, text_of = [], {}
        for n in range(10):
            text_of[f"n{n}"] = HAND["s7"] if n < k else "the Debye length"
            rows.append({"set": "null", "id": f"n.{n}", "served": [{"id": f"n{n}"}]})
        return tally.tally(rows, text_of, None)["R3"]

    assert nulls(2)["state"] == "satisfied" and nulls(2)["number"].startswith("2 of 10")
    assert nulls(3)["state"] == "failing"


def test_r4_draws_the_same_passages_from_the_same_seed_and_counts_steps():
    pile = [{"text": HAND[s]} for s in ("s0", "s2", "s7")] + [{"text": "x"}] * 97
    a = tally.draw(pile, 14, seed=7)
    assert a == tally.draw(pile, 14, seed=7)
    assert tally.draw(pile, 14, seed=7, hit=lambda s, t: False) == 0
    assert tally.draw(pile, 200, seed=1) == 3  # enough draws find every planted step
    assert tally.tally([], {}, 2)["R4"]["state"] == "satisfied"
    assert tally.tally([], {}, 3)["R4"]["state"] == "failing"
    assert tally.tally([], {}, None)["R4"]["state"] == "not asked"


def test_r5_fails_a_step_found_only_through_wertheim():
    laplace = dict(HAND, s6=HAND["s6"] + " from the Laplace transform of r g(r)")
    rows, text_of = rows_for(laplace)
    v = tally.tally(rows, text_of, None)
    assert v["R5"]["state"] == "failing" and v["R5"]["number"].endswith(
        "(Wertheim: s6)"
    )
    rows, text_of = rows_for(HAND)
    assert tally.tally(rows, text_of, None)["R5"]["state"] == "satisfied"


def test_r5_fails_a_step_found_only_through_sticky_spheres():
    sticky = dict(
        HAND,
        s5b=HAND["s5b"] + " for Baxter's adhesive spheres as the stickiness vanishes",
    )
    rows, text_of = rows_for(sticky)
    v = tally.tally(rows, text_of, None)
    assert v["R5"]["state"] == "failing" and v["R5"]["number"].endswith(
        "(sticky spheres: s5b)"
    )
    assert not score.through_sticky(
        [HAND["s5b"], "sticky"]
    ) and not score.through_sticky([])


def test_extended_steps_are_reported_and_never_counted_in_r1():
    rows, text_of = rows_for({**{s: HAND[s] for s in ("s5a", "s5b", "s7")}, **EXT})
    v = tally.tally(rows, text_of, None)
    assert v["R1"]["number"].startswith("3 of 11") and v["R1"]["state"] == "failing"
    assert v["extended"]["number"].startswith("7 of 7")


def test_r6_is_left_to_the_rubric_and_no_overall_verdict_is_made():
    rows, text_of = rows_for(HAND)
    v = tally.tally(rows, text_of, None)
    assert v["R6"]["state"] == "judged by hand"
    assert set(v) == {"R1", "R2", "R3", "R4", "R5", "R6", "extended"}
    assert v["extended"]["state"] == "reported"


import arms  # noqa: E402


def test_arms_summary_counts_steps_per_set_and_null_hits_per_question():
    qs = [
        {"set": "author", "id": "s7.1", "step": "s7", "asked": "q"},
        {"set": "author", "id": "s6.1", "step": "s6", "asked": "q"},
        {"set": "null", "id": "n.1", "step": "n", "asked": "q"},
        {"set": "null", "id": "n.2", "step": "n", "asked": "q"},
    ]
    rows = [arms.found_by(qs[0], [HAND["s7"]]), arms.found_by(qs[1], ["nothing"]),
            arms.found_by(qs[2], [HAND["s2"]]), arms.found_by(qs[3], ["the Debye length"])]  # fmt: skip
    got = arms.summary(qs, {"kernel": rows})["kernel"]
    assert got["author"] == "1 of 11 steps found: s7"
    assert got["null"] == "1 of 2 served a chain step"
    unrun = [{"hit": False, "steps": [], "not run": "numpy"}] * 4
    assert arms.summary(qs, {"latent": unrun}) == {
        "latent": {"not run": "latent needs numpy"}
    }


def test_arms_grades_the_expectations_against_the_kernels_finds():
    exp = json.loads((HERE / "expectations.json").read_text(encoding="utf-8"))["steps"]
    assert set(exp) == set(score.CHAIN)
    qs = [
        {"set": "author", "id": f"{s}.1", "step": s, "asked": "q"} for s in score.CHAIN
    ]
    rows = [{"hit": exp[q["step"]]["found"], "steps": []} for q in qs]
    assert arms.expectations(qs, {"kernel": rows}) == {"held": "11 of 11", "missed": []}
    rows[0] = {"hit": not rows[0]["hit"], "steps": []}
    assert arms.expectations(qs, {"kernel": rows})["missed"] == [qs[0]["step"]]


def test_arms_refuses_a_bad_command_line_and_a_work_folder_without_an_index(tmp_path):
    assert arms.main([]) == 2 and arms.main(["--work", "x"]) == 2
    assert arms.main(["--work", str(tmp_path), "--out", str(tmp_path / "o.json")]) == 2


def test_arms_reads_a_model_and_its_reasoning():
    import pytest

    assert arms.variant("qwen3:8b") == ("qwen3:8b", "")
    assert arms.variant("qwen3:8b@none") == ("qwen3:8b", "none")
    with pytest.raises(SystemExit):
        arms.variant("qwen3:8b@off")
