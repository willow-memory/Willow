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
