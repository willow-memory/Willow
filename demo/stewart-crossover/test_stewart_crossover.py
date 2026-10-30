"""demo/stewart-crossover: what was frozen stays frozen, and the parts that
need no network or other repository do what they say.

The run needs the sources fetch.py saves and the four repositories beside
this one, and is not part of CI; this is.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fetch  # noqa: E402
import run  # noqa: E402

FROZEN = json.loads((HERE / "FROZEN.json").read_text(encoding="utf-8"))
Q = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))


def test_every_frozen_file_is_as_it_was_frozen():
    for rel, sha in FROZEN["files"].items():
        got = hashlib.sha256((HERE / rel).read_bytes()).hexdigest()
        assert got == sha, (
            f"{rel} changed after it was frozen; a change is a new freeze"
        )
    assert {"sources.json", "questions.json", "fetch.py", "run.py"} <= set(
        FROZEN["files"]
    )


def test_each_source_is_pinned_and_held_by_a_hash():
    for s in fetch.SOURCES:
        assert re.fullmatch(r"[0-9a-f]{64}", s["bytes_sha256"]), s["id"]
        if s["kind"] == "html":
            assert len(s["passages"]) >= 20 and len(set(s["passages"])) == len(
                s["passages"]
            )
        elif s["kind"] == "wikitext":
            assert "oldid=" in s["url"], s["id"]  # a revision, not the page
        elif s["kind"] == "text":
            assert re.search(r"/[0-9a-f]{40}/", s["url"]), s["id"]  # a commit
        else:
            assert s["kind"] == "parody" and re.search(r"@[0-9a-f]{40}:", s["url"])
    pubs = {s["publisher"] for s in fetch.SOURCES if s["kind"] != "parody"}
    assert {"wikipedia", "deadline", "variety", "cnn"} <= pubs


def test_every_rule_is_judged_and_every_id_is_once():
    ids = [x["id"] for k in ("facts", "quotes", "traps", "beats") for x in Q[k]]
    assert len(ids) == len(set(ids))
    for rule in Q["pass_rules"]:
        assert f'"{rule}"' in (HERE / "run.py").read_text(encoding="utf-8"), rule


def test_a_news_page_keeps_only_its_frozen_lines_in_order():
    src = {"passages": [fetch.sha(b"one two three"), fetch.sha(b"four five")]}
    page = b"<p>four  five</p>\n<aside>Cause Of Death Revealed</aside>\n<p>one two\tthree</p>"
    assert fetch.lines_kept(src, page) == ["four five", "one two three"]
    assert fetch.lines_kept(src, b"<p>a sidebar only</p>") == []


def test_the_parody_block_is_the_g28_atom_alone():
    text = (
        f"### G27 | x\n\nbefore\n\n{fetch.G28}\n\nStewpott.\n\n### G29 | y\n\nafter\n"
    )
    assert fetch.parody_block(text) == f"{fetch.G28}\n\nStewpott.\n"


def test_nothing_known_about_him_is_unnamed_or_dated_after_her_today():
    names = re.compile(Q["names"])
    for f in Q["facts"]:
        assert names.search(f["sentence"]) or f["id"] == "fact3", f["id"]
    for t in Q["traps"]:
        assert names.search(t["line"]), t["id"]
    assert Q["window"][1] < Q["wren_today"] < "2026-10-28"  # before his death


def test_a_bad_command_line_says_how_to_run_it(capsys):
    for main, argv in (
        (fetch.main, []),
        (fetch.main, ["--to"]),
        (fetch.main, ["--to", "x", "--stray"]),
        (run.main, []),
        (run.main, ["--mirror", "m", "--wren", "w", "--work", "k"]),
    ):
        assert main(argv) == 2
        assert ".py" in capsys.readouterr().err
