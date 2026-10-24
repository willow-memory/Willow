"""demo/google-privacy-2026-10-16: what was frozen stays frozen, and the
study's rules do what they say.

The run needs the pile fetch.py saves, and is not part of CI; this is.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fetch  # noqa: E402
import study  # noqa: E402

FROZEN = json.loads((HERE / "FROZEN.json").read_text(encoding="utf-8"))


def test_every_frozen_file_is_as_it_was_frozen():
    for rel, sha in FROZEN["files"].items():
        got = hashlib.sha256((HERE / rel).read_bytes()).hexdigest()
        assert got == sha, (
            f"{rel} changed after it was frozen; a change is a new freeze"
        )
    frozen = set(FROZEN["files"])
    assert {"sources.json", "targets.json", "study.py", "fetch.py"} <= frozen
    assert {f"questions/{p.name}" for p in (HERE / "questions").iterdir()} <= frozen


def test_the_sources_are_whole_and_match_what_fetch_asks_for():
    doc = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))
    got = [(s["folder"], s["file"], s["url"]) for s in doc["sources"]]
    assert sorted(got) == sorted(fetch.SOURCES)
    for s in doc["sources"]:
        assert len(s["sha256"]) == 64 and s["status"] == 200 and s["bytes"] > 0
        assert s["fetched"].startswith("2026-10-24T") and s["url"].startswith(
            "https://"
        )
    assert doc["wayback"]["exit"] == 42  # said, not left out


def test_check_says_missing_and_differs(tmp_path, capsys):
    assert fetch.check(tmp_path) == 42
    assert "missing  policy-old/google_privacy_policy_en.pdf" in capsys.readouterr().out
    (tmp_path / "policy-old").mkdir()
    (tmp_path / "policy-old" / "google_privacy_policy_en.pdf").write_bytes(b"not it")
    assert fetch.check(tmp_path) == 2
    assert "DIFFERS  policy-old/google_privacy_policy_en.pdf" in capsys.readouterr().out


def test_the_question_files_are_named_and_whole():
    names = set()
    for p in sorted((HERE / "questions").iterdir()):
        qs = study.questions(p.name)
        assert qs and all(n and t.strip() for n, t in qs), p.name
        assert not names & {n for n, _ in qs}, p.name
        names |= {n for n, _ in qs}
    claims = {n for n, _ in study.questions("claims.txt")}
    assert (
        claims
        == set(study.TARGETS["support"]["needs"])
        == set(study.TARGETS["support"]["absent"])
    )
    blind = {n.rsplit("-v", 1)[0] for n, _ in study.questions("blind-claims.txt")}
    assert blind == claims
    reps = {n for n, _ in study.questions("reporters.txt")}
    assert {
        n.rsplit("-v", 1)[0] for n, _ in study.questions("blind-reporters.txt")
    } == reps


def test_a_question_lands_only_on_its_versions_clause():
    exc, dflt = study.TARGETS["exception"]["text"], study.TARGETS["default"]["text"]
    opt = study.TARGETS["opt-in"]["texts"][1]
    other = {"text": "We use cookies."}
    assert study.level([other, {"text": exc}], "new") == "exception"
    assert study.level([{"text": opt}, other], "new") == "opt-in"
    assert study.level([{"text": dflt}], "new") == "miss"
    assert study.level([{"text": dflt}], "old") == "default"
    assert study.level([{"text": exc}], "old") == "miss"
    assert "unless you choose" in exc and "unless" not in dflt


def test_support_needs_every_group_in_one_passage():
    needs = ["read", "mail", "ads"]
    assert study.supports("Google scans your Gmail to show ads.", needs)
    assert study.supports("We analyze email messages for advertising.", needs)
    assert not study.supports(study.TARGETS["exception"]["text"], needs)  # no reading
    assert not study.supports(study.TARGETS["analyze"]["text"], needs)  # no mail word
    assert study.supports("Gmail ads are on by default.", ["mail", "ads", "default"])
    assert not study.supports("Gmail ads are on.", ["mail", "ads", "default"])


def test_the_binomial_tail_and_the_pass_rule():
    assert abs(study.tail(10, 0, 0.2) - 1.0) < 1e-12
    assert abs(study.tail(2, 2, 0.5) - 0.25) < 1e-12
    assert abs(study.tail(3, 2, 0.5) - 0.5) < 1e-12
    rows = [{"level": "exception"}] * 6 + [{"level": "miss"}] * 4
    got = study.test(rows, "exception", 6, 15)
    assert got["lands"] == 6 and got["random_rate"] == 0.2 and got["pass"]
    assert not study.test(rows, "exception", 7, 15)["pass"]  # the floor
    assert not study.test(rows, "exception", 6, 4)["pass"]  # chance would do it
