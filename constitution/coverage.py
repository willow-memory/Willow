#!/usr/bin/env python3
"""coverage.py — the generated coverage artifact Appendix A calls for.

Draft 0.8 removed Appendix A's hand-maintained enforcement table. This is what
replaces it: a report built by scanning trees for Trace-ID citations, rebuilt on
demand, never checked in as prose.

The one-direction rule it enforces
----------------------------------
The constitution names no artifact; artifacts name the constitution. So coverage
is discovered by looking for upward references (``CONST-*`` appearing in code,
tests, configs) and never by reading a list the constitution carries. A Trace ID
does not move when a file does, which is the whole point.

What this script will and will not claim
----------------------------------------
It reports two things it can actually see:

  * which clauses this document defines, parsed from the constitution itself;
  * which clauses are cited somewhere in the scanned trees, and where, in any
    of the three spellings an artifact uses: the Trace ID, a link to the
    article's heading, or the eternity clauses' section sign (§0.4). Each row
    says which spellings it was cited in.

It does NOT decide the four verdicts. ``satisfied`` versus ``differently``
requires knowing whether the citing artifact enforces the clause *by the
mechanism the clause describes* — a judgment about meaning, not a fact about
text. Appendix B: *a gate that cannot check its subject is not a weaker gate; it
is no gate.* So verdicts are read from a declarations file a human maintains,
and any clause without a declaration is reported as ``undeclared`` rather than
guessed into one of the four.

Nor does it treat its own green as evidence. Appendix B again: *a gate's own
report about itself is not evidence about that gate.* This script reports what
it scanned and what it could not read; a clause with no citation found is
reported with the reason, never as a bare empty row (IV.5 / Casebook Case 10).

Usage
-----
    python constitution/coverage.py [--root DIR ...] [--json]

Exit codes follow the house convention: 0 the report was produced, 1 the answer
is no (a clause is declared ``failing``), 2 the report could not be produced.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONSTITUTION = REPO_ROOT / "CONSTITUTION.md"
DECLARATIONS = REPO_ROOT / "constitution" / "declarations.json"

EXIT_OK, EXIT_ANSWER_IS_NO, EXIT_CANNOT = 0, 1, 2

VERDICTS = ("satisfied", "differently", "not applicable", "failing")

# A Trace ID as an artifact writes it: CONST-0, CONST-IV, CONST-0-3, CONST-IV-5.
TRACE_RE = re.compile(r"\bCONST-(?:0|[IVX]+)(?:-[0-9A-Za-z]+)*\b")

# The same clause cited under its other names. An upward reference is an
# upward reference whatever it is spelled as, and a report that sees only one
# spelling reports a clause as uncited while files link to it. Two spellings
# map to exactly one clause each, so they are read; anything looser (a bare
# "IV.5", which is also a version number) is not.
#   * A link to an article heading. Its anchor ends in the article's Trace ID,
#     lowercased by the slug: CONSTITUTION.md#article-vi--the-record-const-vi.
#   * The section sign, which only the eternity clauses carry: §0.4.
ANCHOR_RE = re.compile(r"CONSTITUTION\.md#[a-z0-9-]*?-const-(0|[ivx]+)(?![a-z0-9-])")
SECTION_RE = re.compile(r"(?<![\w.§])§0\.([0-9]+[a-z]?)(?![\w.])")
#: How each spelling is named in the report.
FORMS = ("trace-id", "anchor", "section-sign")

# How the constitution declares an article and a clause. Trace IDs are derived
# from these rather than read as literal `CONST-*` strings, because the document
# says clauses INHERIT their article's identifier — "every Article carries a
# stable identifier (CONST-0, CONST-I, …); clauses inherit it (CONST-0-1 …
# CONST-0-6; CONST-I-1 …)". Only Article 0 ever wrote its clause IDs out, so a
# literal scan saw 6 clauses plus whatever that sentence's own examples
# mentioned, and reported ~21 where the charter has 51. Every clause of Articles
# I–XIII was invisible, and so was any artifact citing one.
_ARTICLE_HEADING = re.compile(r"##\s+Article\s+(0|[IVX]+)\s")
#: `**§0.1 — …**`, `**I.1 — …**`, `**V.4a — …**`, `**VII.default — …**`
_CLAUSE_HEADING = re.compile(r"\*\*§?(0|[IVX]+)\.([0-9A-Za-z]+)\s")

SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".ruff_cache",
}
TEXT_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".sh",
    ".sql",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".md",
    ".cfg",
    ".ini",
    ".txt",
}


def clauses_from_constitution(path: Path) -> tuple[list[str], str | None]:
    """Derive the Trace IDs this constitution defines, from its own structure.

    Returns (ids, unreadable_reason). The reason is non-None when the document
    could not be read or yielded no headings at all — reported rather than
    silently returning zero clauses, which would render as a vacuously clean
    sweep.

    Definitions come from article and clause **headings**, in document order,
    de-duplicated. They are deliberately not taken from prose any more: the
    sentence that explains the Trace-ID scheme names `CONST-0-1` and `CONST-I-1`
    as examples, and a literal scan counted those examples as definitions while
    missing the 45 clauses that carry no written ID. Structure is the authority
    here, and it is still only ever this document's own structure.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as err:
        return [], f"could not read {path}: {err}"

    seen: dict[str, None] = {}
    for line in text.splitlines():
        article = _ARTICLE_HEADING.match(line.strip())
        if article:
            seen.setdefault(f"CONST-{article.group(1)}", None)
            continue
        clause = _CLAUSE_HEADING.match(line.strip())
        if clause:
            seen.setdefault(f"CONST-{clause.group(1)}-{clause.group(2)}", None)

    if not seen:
        return (
            [],
            f"{path}: no article or clause headings found — refusing to report a clean sweep",
        )
    return list(seen), None


def cited_ids(body: str) -> dict[str, set[str]]:
    """Every clause a text cites, by Trace ID, with the spellings it used."""
    found: dict[str, set[str]] = {}
    for match in TRACE_RE.findall(body):
        found.setdefault(match, set()).add("trace-id")
    for match in ANCHOR_RE.findall(body):
        found.setdefault(f"CONST-{match.upper()}", set()).add("anchor")
    for match in SECTION_RE.findall(body):
        found.setdefault(f"CONST-0-{match}", set()).add("section-sign")
    return found


def scan(
    roots: list[Path],
    skip: set[Path],
    forms: dict[str, dict[str, list[str]]] | None = None,
) -> tuple[dict[str, list[str]], list[str]]:
    """Find upward citations, in every spelling. Returns (citations, unreadable);
    if `forms` is given, it is filled with {clause: {spelling: [paths]}}."""
    citations: dict[str, list[str]] = {}
    unreadable: list[str] = []
    for root in roots:
        if not root.exists():
            unreadable.append(f"{root}: not present")
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                fp = Path(dirpath) / name
                if fp.suffix not in TEXT_SUFFIXES or fp in skip:
                    continue
                try:
                    body = fp.read_text(encoding="utf-8", errors="strict")
                except (OSError, UnicodeDecodeError) as err:
                    unreadable.append(f"{fp}: {type(err).__name__}")
                    continue
                for match, spellings in cited_ids(body).items():
                    rel = (
                        str(fp.relative_to(REPO_ROOT))
                        if REPO_ROOT in fp.parents
                        else str(fp)
                    )
                    citations.setdefault(match, []).append(rel)
                    if forms is not None:
                        for spelling in spellings:
                            forms.setdefault(match, {}).setdefault(spelling, []).append(
                                rel
                            )
    return citations, unreadable


def load_declarations(path: Path) -> tuple[dict[str, dict], str | None]:
    if not path.exists():
        return {}, f"no declarations file at {path}"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        return {}, f"could not read {path}: {err}"
    decls = raw.get("clauses", {})
    for cid, entry in decls.items():
        verdict = entry.get("verdict")
        if verdict not in VERDICTS:
            return {}, f"{cid}: verdict {verdict!r} is not one of {VERDICTS}"
    return decls, None


def build_report(roots: list[Path]) -> dict:
    clauses, unreadable_const = clauses_from_constitution(CONSTITUTION)
    if unreadable_const:
        return {"error": unreadable_const}
    # This script's own Trace-ID mentions are regex examples and prose, not
    # enforcement. A gate's self-report is not evidence about that gate
    # (Appendix B; Casebook Case 7), so it excludes itself from its own scan,
    # and its own tests, whose Trace IDs are fixture text.
    here = Path(__file__).resolve()
    forms: dict[str, dict[str, list[str]]] = {}
    citations, unreadable = scan(
        roots,
        skip={CONSTITUTION, here, here.parent / "test_coverage.py"},
        forms=forms,
    )
    decls, decl_problem = load_declarations(DECLARATIONS)

    rows = []
    for cid in clauses:
        cites = sorted(set(citations.get(cid, [])))
        decl = decls.get(cid)
        if decl is not None:
            verdict = decl["verdict"]
            note = decl.get("note", "")
        else:
            verdict = "undeclared"
            # Say WHY, never a bare empty row. 'Nothing here' and 'nothing left
            # to do' are different claims (IV.5, Casebook Case 10).
            if decl_problem:
                note = "no verdict recorded — see the declarations line above"
            elif cites:
                note = "cited in the tree but no human verdict recorded"
            else:
                note = "no citation found in the scanned roots and no verdict recorded"
        rows.append(
            {
                "clause": cid,
                "verdict": verdict,
                "citations": cites,
                "forms": {
                    f: sorted(set(forms.get(cid, {}).get(f, [])))
                    for f in FORMS
                    if forms.get(cid, {}).get(f)
                },
                "note": note,
            }
        )

    # The other direction, which nothing checked: an artifact citing a Trace ID
    # no clause defines. Such a citation reads as diligence and enforces
    # nothing — it cannot appear in any row, so the report stayed silent about
    # it. Both known kinds are worth seeing: a clause ID the charter never
    # declares, and a *case* ID shaped like one (`CONST-0-3-II` is the TRACE_ID
    # of a compliance case, not a clause).
    known = set(clauses)
    unknown = [
        {"clause": cid, "citations": sorted(set(paths))}
        for cid, paths in sorted(citations.items())
        if cid not in known
    ]

    return {
        "clauses_defined": len(clauses),
        "roots_scanned": [str(r) for r in roots],
        "unreadable": unreadable,
        "declarations_problem": decl_problem,
        "rows": rows,
        "unknown_citations": unknown,
    }


def render(report: dict) -> str:
    if "error" in report:
        return f"const-coverage: cannot report — {report['error']}"
    out = [
        "const-coverage — generated, not tabled. This is evidence about a checkout",
        "at a moment; the constitution is the law. References point up.",
        "",
        f"clauses defined: {report['clauses_defined']}",
        f"roots scanned:   {', '.join(report['roots_scanned'])}",
    ]
    if report["declarations_problem"]:
        out.append(f"declarations:    {report['declarations_problem']}")
    if report["unreadable"]:
        out.append(
            f"unreadable:      {len(report['unreadable'])} path(s) — listed below"
        )
    out.append("")
    counts: dict[str, int] = {}
    for row in report["rows"]:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    out.append("  " + " · ".join(f"{v}: {counts[v]}" for v in sorted(counts)))
    spelled = {
        f: sum(1 for row in report["rows"] if f in row.get("forms", {})) for f in FORMS
    }
    out.append(
        "  clauses cited by "
        + " · ".join(f"{f}: {spelled[f]}" for f in FORMS)
        + " (one clause can be cited in several spellings)"
    )
    out.append("")
    width = max((len(r["clause"]) for r in report["rows"]), default=10)
    for row in report["rows"]:
        cites = ", ".join(row["citations"][:3]) or "—"
        if len(row["citations"]) > 3:
            cites += f" (+{len(row['citations']) - 3})"
        out.append(f"  {row['clause']:<{width}}  {row['verdict']:<14}  {cites}")
        if row["note"]:
            out.append(f"  {'':<{width}}  └─ {row['note']}")
    if report.get("unknown_citations"):
        out.append("")
        out.append("cited, but no such clause in the constitution:")
        for entry in report["unknown_citations"]:
            where = ", ".join(entry["citations"][:3])
            if len(entry["citations"]) > 3:
                where += f" (+{len(entry['citations']) - 3})"
            out.append(f"  {entry['clause']}  —  {where}")
    if report["unreadable"]:
        out.append("")
        out.append("unreadable paths:")
        out.extend(f"  {u}" for u in report["unreadable"])
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--root",
        action="append",
        default=None,
        help="tree to scan for upward Trace-ID citations (repeatable)",
    )
    ap.add_argument("--json", action="store_true", help="emit the report as JSON")
    args = ap.parse_args()

    roots = [Path(r).resolve() for r in args.root] if args.root else [REPO_ROOT]
    report = build_report(roots)

    if "error" in report:
        print(render(report), file=sys.stderr)
        return EXIT_CANNOT

    print(json.dumps(report, indent=2) if args.json else render(report))
    failing = [r for r in report["rows"] if r["verdict"] == "failing"]
    return EXIT_ANSWER_IS_NO if failing else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
