"""The coverage report has to be able to see the whole charter.

Appendix B: *a gate's own report about itself is not evidence about that gate*,
so coverage.py's coverage is established here rather than by its own
green.
"""

import importlib.util
from pathlib import Path


_HERE = Path(__file__).resolve().parent


def _load_const_coverage():
    """Import ``constitution/coverage.py`` by path.

    It is a script rather than a package module, so importlib is the honest
    way to get at it.
    """
    path = _HERE / "coverage.py"
    spec = importlib.util.spec_from_file_location("willow_coverage_probe", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cc = _load_const_coverage()


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "CONSTITUTION.md"
    path.write_text(body, encoding="utf-8")
    return path


def test_a_clause_with_no_written_id_is_still_defined(tmp_path):
    """The defect. Only Article 0 ever wrote its clause IDs out, so every clause
    of Articles I-XIII was invisible and so was any artifact citing one."""
    doc = _write(
        tmp_path,
        "## Article X — Supremacy *(CONST-X)*\n"
        "\n"
        "**X.4 — The Concurrence Rule.** No precedence hierarchy exists.\n",
    )
    ids, problem = cc.clauses_from_constitution(doc)
    assert problem is None
    assert ids == ["CONST-X", "CONST-X-4"]


def test_article_zero_keeps_its_section_sign_form(tmp_path):
    doc = _write(
        tmp_path,
        "## Article 0 — The Eternity Clause *(CONST-0)*\n"
        "\n"
        "**§0.1 — No self-attestation.** *(CONST-0-1)*\n",
    )
    ids, _ = cc.clauses_from_constitution(doc)
    assert ids == ["CONST-0", "CONST-0-1"]


def test_irregular_clause_labels_survive(tmp_path):
    """`V.4a` was added by amendment and `VII.default` is a named default."""
    doc = _write(
        tmp_path,
        "## Article V — The Human *(CONST-V)*\n"
        "**V.4a — Declaration of Incapacity.** Standing agents allege.\n"
        "## Article VII — The Interpreter *(CONST-VII)*\n"
        "**VII.default — Escalation holds the seat.** Per §0.6.\n",
    )
    ids, _ = cc.clauses_from_constitution(doc)
    assert "CONST-V-4a" in ids
    assert "CONST-VII-default" in ids


def test_prose_examples_no_longer_define_clauses(tmp_path):
    """The sentence explaining the scheme names CONST-0-1 and CONST-I-1 as
    examples. Counting those as definitions is how the old scan reported 21
    clauses for a charter that has 65 identifiers."""
    doc = _write(
        tmp_path,
        "> **Trace IDs:** every Article carries a stable identifier (`CONST-0`,\n"
        "> `CONST-I`); clauses inherit it (`CONST-0-1`; `CONST-I-1`).\n"
        "\n"
        "## Article I — Identity *(CONST-I)*\n"
        "**I.1 — Identity is the manifest.** An agent's identity is its manifest.\n",
    )
    ids, _ = cc.clauses_from_constitution(doc)
    assert ids == ["CONST-I", "CONST-I-1"], "only the headings define"


def test_a_document_with_no_headings_refuses_rather_than_sweeping_clean(tmp_path):
    """Zero clauses would render as a report with nothing to answer for."""
    doc = _write(tmp_path, "Some prose, mentioning CONST-0-3 but declaring nothing.\n")
    ids, problem = cc.clauses_from_constitution(doc)
    assert ids == []
    assert problem is not None
    assert "refusing" in problem


def test_an_unreadable_document_says_so(tmp_path):
    ids, problem = cc.clauses_from_constitution(tmp_path / "absent.md")
    assert ids == []
    assert problem is not None and "could not read" in problem


def test_a_citation_to_no_clause_is_surfaced(tmp_path, monkeypatch):
    """The direction nothing checked. A Trace ID that matches no clause cannot
    appear in any row, so the report used to stay silent about it — and a
    citation that enforces nothing reads exactly like diligence."""
    doc = _write(
        tmp_path,
        "## Article X — Supremacy *(CONST-X)*\n**X.4 — The Concurrence Rule.** Text.\n",
    )
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "artifact.py").write_text(
        'GOOD = "CONST-X-4"\nBAD = "CONST-0-3-II"  # a compliance case ID, not a clause\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(cc, "CONSTITUTION", doc)
    monkeypatch.setattr(cc, "DECLARATIONS", tmp_path / "no-declarations.json")

    report = cc.build_report([tree])

    unknown = {entry["clause"] for entry in report["unknown_citations"]}
    assert unknown == {"CONST-0-3-II"}
    assert "cited, but no such clause" in cc.render(report)

    cited = {row["clause"]: row["citations"] for row in report["rows"]}
    assert cited["CONST-X-4"], "the real citation still lands on its clause"


def test_the_real_charter_parses_to_every_article_and_clause():
    """Against the document itself: 14 articles and 64 clauses (Draft 0.9 adds 13)."""
    ids, problem = cc.clauses_from_constitution(cc.CONSTITUTION)
    assert problem is None
    articles = [i for i in ids if i.count("-") == 1]
    clauses = [i for i in ids if i.count("-") >= 2]
    assert len(articles) == 14, articles
    assert len(clauses) == 64, len(clauses)
    assert "CONST-X-4" in clauses, "the clause that started this"


def test_a_clause_is_cited_under_each_of_its_names(tmp_path, monkeypatch):
    """A link to an article's heading and the eternity clauses' section sign
    are upward references too. A report that reads only the Trace ID calls a
    clause uncited while files link to it."""
    doc = _write(
        tmp_path,
        "## Article 0 — The Eternity Clause *(CONST-0)*\n"
        "**§0.4 — The human key is required.** Text.\n"
        "## Article VI — The Record *(CONST-VI)*\n"
        "**VI.1 — Append and read.** Text.\n",
    )
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "rules.md").write_text(
        "See [the record](governance/CONSTITUTION.md#article-vi--the-record-const-vi).\n"
        "The human seals (§0.4).\n",
        encoding="utf-8",
    )
    (tree / "gate.py").write_text('CLAUSE = "CONST-0-4"\n', encoding="utf-8")
    (tree / "other.md").write_text(
        "INVARIANTS.md §11 and §12. Version 0.4. IV.5 of something else.\n"
        "A link elsewhere: OTHER.md#article-vi--x-const-vi.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cc, "CONSTITUTION", doc)
    monkeypatch.setattr(cc, "DECLARATIONS", tmp_path / "no-declarations.json")

    rows = {r["clause"]: r for r in cc.build_report([tree])["rows"]}

    assert rows["CONST-VI"]["forms"] == {"anchor": [str(tree / "rules.md")]}
    assert rows["CONST-0-4"]["forms"] == {
        "trace-id": [str(tree / "gate.py")],
        "section-sign": [str(tree / "rules.md")],
    }
    assert rows["CONST-0-4"]["citations"] == sorted(
        [str(tree / "gate.py"), str(tree / "rules.md")]
    )
    assert rows["CONST-VI-1"]["citations"] == [], "nothing loose is read as a citation"
    assert "clauses cited by trace-id: 1 · anchor: 1 · section-sign: 1" in cc.render(
        cc.build_report([tree])
    )


def test_an_articles_answer_stands_for_its_clauses_unless_one_has_its_own(
    tmp_path, monkeypatch
):
    cc = _load_const_coverage()
    law = _write(tmp_path, "## Article I — X\n\n**I.1 — One.**\n\n**I.2 — Two.**\n")
    reach = tmp_path / "reach.json"
    reach.write_text('{"answers": {"CONST-I": {"answer": "out of reach", "why": "a"},'
                     ' "CONST-I-2": {"answer": "open", "why": "b"}}}')  # fmt: skip
    monkeypatch.setattr(cc, "CONSTITUTION", law)
    got = cc.load_reach(reach)
    assert got["CONST-I-1"]["why"] == "a" and got["CONST-I-2"]["why"] == "b"
    assert cc.load_reach(tmp_path / "missing.json") == {}
