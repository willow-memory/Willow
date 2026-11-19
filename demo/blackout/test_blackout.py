"""blackout: the sources are pinned by address and hash, the contact goes to
sec.gov alone and into no file, and a fetch refuses once the study is frozen."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fetch  # noqa: E402

SOURCES = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))


def test_every_source_is_pinned_by_address_and_hash():
    got = SOURCES["sources"]
    assert not SOURCES["failed"] and len(got) == len(fetch.LIST)
    assert {(s["folder"], s["file"], s["url"]) for s in got} == set(fetch.LIST)
    for s in got:
        assert s["url"].startswith("https://") and len(s["sha256"]) == 64
        assert s["bytes"] > 0


def test_the_rules_the_story_asks_about_are_among_them():
    names = {s["file"] for s in SOURCES["sources"]}
    for wanted in ("17-cfr-240.10b5-1.xml", "17-cfr-243.100.xml", "form8-k.pdf"):
        assert wanted in names


def test_no_file_in_this_folder_holds_an_email_address():
    for p in HERE.iterdir():
        if p.is_file() and p.suffix in (".py", ".json", ".md", ".txt"):
            text = p.read_text(encoding="utf-8")
            assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text), p.name


def test_the_contact_goes_to_sec_gov_alone_judged_by_host():
    assert fetch.is_sec("https://www.sec.gov/files/form8-k.pdf")
    assert fetch.is_sec("https://sec.gov/x")
    for other in (
        "https://www.ecfr.gov/api/x?sec.gov",
        "https://sec.gov.evil.example/x",
        "https://notsec.gov/x",
        "http://www.sec.gov/x",
    ):
        assert not fetch.is_sec(other), other
    contact = "someone" + chr(64) + "example.invalid"  # no address is written out here
    assert contact in fetch.agent("https://www.sec.gov/f", contact)
    assert contact not in fetch.agent("https://www.ecfr.gov/f", contact)
    assert "@" not in fetch.agent("https://www.sec.gov/f", None)


def test_check_says_holds_differs_and_missing_offline(tmp_path, capsys):
    s = SOURCES["sources"]
    assert fetch.check(tmp_path) == 1
    assert capsys.readouterr().out.count("missing") == len(s)
    first = tmp_path / s[0]["folder"]
    first.mkdir(parents=True)
    (first / s[0]["file"]).write_bytes(b"not the rule")
    fetch.check(tmp_path)
    assert f"DIFFERS  {s[0]['folder']}/{s[0]['file']}" in capsys.readouterr().out


def test_a_fetch_is_refused_once_the_study_is_frozen(tmp_path, monkeypatch, capsys):
    frozen = HERE / "FROZEN.json"
    if not frozen.exists():
        monkeypatch.setattr(fetch, "HERE", tmp_path)
        (tmp_path / "FROZEN.json").write_text("{}")
    assert fetch.fetch(tmp_path / "pile", None) == 2
    assert "FROZEN.json exists" in capsys.readouterr().out


# ── the piles ────────────────────────────────────────────────────────────────
import make_life  # noqa: E402


def made(tmp_path, monkeypatch, rules=None):
    monkeypatch.setattr(make_life, "LIFE", tmp_path / "life")
    make_life.write(rules)
    return tmp_path / "life"


def test_the_piles_are_the_same_bytes_every_time(tmp_path, monkeypatch):
    life = made(tmp_path, monkeypatch)
    first = {
        p.relative_to(life): p.read_bytes() for p in life.rglob("*") if p.is_file()
    }
    made(tmp_path, monkeypatch)
    again = {
        p.relative_to(life): p.read_bytes() for p in life.rglob("*") if p.is_file()
    }
    assert first == again and len({r.parts[0] for r in first}) == 8


def test_the_planted_lines_are_held(tmp_path, monkeypatch, capsys):
    made(tmp_path, monkeypatch)
    assert make_life.check() == 0
    assert "11/11 planted lines held" in capsys.readouterr().out


def test_only_the_filing_and_the_release_are_in_every_box(tmp_path, monkeypatch):
    life = made(tmp_path, monkeypatch)
    seen: dict[str, set[str]] = {}
    for p in life.rglob("*.txt"):
        box = p.relative_to(life).parts[0]
        for ln in p.read_text(encoding="utf-8").splitlines():
            if len(ln) > 40:
                seen.setdefault(ln, set()).add(box)
    shared = {ln for ln, boxes in seen.items() if len(boxes) > 1}
    public = {
        ln
        for text in make_life.PUBLIC.values()
        for ln in text.splitlines()
        if len(ln) > 40
    }
    assert shared == public and all(len(seen[ln]) == 8 for ln in shared)


def test_the_story_is_in_the_numbers(tmp_path, monkeypatch):
    life = made(tmp_path, monkeypatch)
    sales = (life / "plan/trades/plan-sales-2026-q4.txt").read_text()
    sold = [ln.split()[0] for ln in sales.splitlines() if ln.startswith("E-")]
    roster = (life / "steward/roster/seniority-list.txt").read_text()
    dept = {ln.split()[0]: ln for ln in roster.splitlines() if ln.startswith("E-")}
    assert len(sold) == 11
    # nine are on the melt shop's or the rolling mill's list, one is a parts
    # clerk, and one (the plant manager) is on no union list at all
    assert sum(("melt shop" in dept.get(e, "")) or ("rolling mill" in dept.get(e, ""))
               for e in sold) == 9  # fmt: skip
    assert [e for e in sold if e not in dept and e != "E-0007"] == []
    # the window moved: 14 days before 2026-11-05 is 10-22, 7 days is 10-29
    from datetime import date, timedelta

    release = date(2026, 11, 5)
    assert release - timedelta(14) == date(2026, 10, 22)
    assert release - timedelta(7) == date(2026, 10, 29)
    assert all(date(2026, 10, 22) <= date.fromisoformat(ln.split()[1]) < date(2026, 10, 29)
               for ln in sales.splitlines() if ln.startswith("E-"))  # fmt: skip


def test_the_rules_are_mirrored_into_every_box_only_when_asked(tmp_path, monkeypatch):
    pile = tmp_path / "rules-pile" / "ecfr"
    pile.mkdir(parents=True)
    (pile / "17-cfr-243.100.xml").write_text(
        "<DIV><HEAD>A rule &amp; its words</HEAD></DIV>"
    )
    plain = made(tmp_path, monkeypatch)
    assert not list(plain.rglob("rules"))
    ruled = made(tmp_path, monkeypatch, tmp_path / "rules-pile")
    got = [ruled / b / "rules/17-cfr-243.100.txt" for b in make_life.BOXES]
    assert all(p.read_text() == "A rule & its words\n" for p in got)
