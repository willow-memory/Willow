"""report.py: the full report and its checks are what the committed files
make, the same bytes twice, and every count it holds is found in the README."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import report  # noqa: E402


def test_the_report_is_what_its_files_make():
    once, again = report.render(), report.render()
    assert once == again
    assert report.REPORT.read_text(encoding="utf-8") == once, "run report.py write"


def test_the_checks_are_what_the_tools_say():
    assert report.CHECKS.read_text(encoding="utf-8") == report.render_checks(), (
        "run report.py write"
    )


def test_the_record_holds_and_names_each_run():
    rows, breaks = report.record()
    assert not breaks
    assert not [r for r in rows if r["kind"] == "seal"]
    for r, x in report.runs().items():
        assert len(x["rows"]) == len(report.RULES), r
        assert x["freeze"] == r


def test_every_count_is_found_in_the_readme():
    assert (
        report.render_checks()
        .rstrip()
        .endswith(f"{len(report.claims())} of {len(report.claims())} found whole.")
    )
