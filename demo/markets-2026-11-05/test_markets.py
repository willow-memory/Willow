"""demo/markets-2026-11-05: what fetch.py froze, and the parts that need no
network, do what the README says.

The fetch goes online and is not part of CI; this is.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fetch  # noqa: E402

FROZEN = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))


def test_every_source_is_pinned_once_by_its_sha256():
    rows = FROZEN["sources"]
    assert len(rows) == 944
    assert all(re.fullmatch(r"[0-9a-f]{64}", r["sha256"]) for r in rows)
    places = [(r["folder"], r["file"]) for r in rows]
    assert len(places) == len(set(places))


def test_no_contact_or_source_text_is_kept():
    text = (HERE / "sources.json").read_text(encoding="utf-8")
    assert not re.search(
        r"[\w.+-]+@[\w-]+\.[\w.]+", text
    )  # no email (OECD's "@DF_CLI" is a dataset)
    assert set(FROZEN["sources"][0]) == {"bytes", "file", "folder", "sha256", "url"}


def test_the_hand_listed_sources_need_no_network_to_list():
    listed = fetch.static_sources()
    assert len(listed) == len({(f, n) for f, n, _ in listed})
    assert all(u.startswith("https://") for _, _, u in listed)
    assert not any(fetch.is_sec(u) for _, _, u in listed)  # EDGAR only with --contact


def test_an_error_page_or_a_bls_limit_is_not_data(tmp_path):
    page = tmp_path / "x.csv"
    page.write_text("<!DOCTYPE html><title>Missing Key</title>", encoding="utf-8")
    assert fetch.error_body(page)
    bls = tmp_path / "bls" / "S.json"
    bls.parent.mkdir()
    bls.write_text(
        '{"status": "REQUEST_NOT_PROCESSED", "Results": {}}', encoding="utf-8"
    )
    assert "BLS" in fetch.error_body(bls)
    good = tmp_path / "y.csv"
    good.write_text("observation_date,UNRATE\n2026-09-01,4.2\n", encoding="utf-8")
    assert fetch.error_body(good) is None


def test_a_successor_without_a_10k_reads_its_predecessors():
    assert fetch.PREDECESSOR == {"XOM": 34088}
    tenk = [
        r
        for r in FROZEN["sources"]
        if r["folder"] == "sec/10-k" and r["file"].startswith("XOM")
    ]
    assert tenk and "/data/34088/" in tenk[0]["url"]


def test_the_contact_goes_to_sec_gov_by_host_alone():
    assert fetch.is_sec("https://data.sec.gov/submissions/CIK0000320193.json")
    assert fetch.is_sec("https://www.sec.gov/files/company_tickers.json")
    assert fetch.is_sec("https://sec.gov/")
    for not_sec in (
        "https://evil.example/x.sec.gov/",
        "https://sec.gov.evil.example/",
        "https://notsec.gov/",
        "http://www.sec.gov/",
        "https://evil.example/?u=https://www.sec.gov/",
    ):
        assert not fetch.is_sec(not_sec), not_sec
