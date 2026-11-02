"""similar: the kernel's search over this repo's list, a refused duplicate,
and a pull request's report that says so when nothing is near."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("willow_similar", HERE / "similar.py")
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)


def cli(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "similar.py"), *argv],
                          capture_output=True, text=True)  # fmt: skip


def idea(name: str, line: str) -> dict:
    return {"name": name, "line": line, "built": False, "kind": "stdlib"}


def test_the_real_list_has_no_two_entries_the_same():
    got = cli("check")
    assert got.returncode == 0, got.stderr
    assert "no two the same" in got.stdout


def test_near_serves_a_built_add_on_and_an_idea_with_the_words_they_share():
    every = sim.entries()
    found = {a["name"]: shared for a, shared in sim.near(every, "Text out of PDFs.")}
    assert "pdf" in found and "ocr" in found and "dictate" in found
    assert {"pdfs", "text"} <= set(found["pdf"])
    lines = cli("near", "Text out of PDFs.").stdout
    assert "[**pdf**](adapters/deps/pdf/), built: connect to it." in lines
    assert "[**ocr**](adapters/deps/ocr/), built: connect to it." in lines
    assert "**dictate**, an idea already on the list." in lines


def test_a_long_line_still_finds_the_short_entry_it_contains():
    """A new line that holds half of an entry's words is near it, though
    the kernel, counting half of the new line's words, serves nothing: the
    symbols idea went on the list twice that way."""
    every = [
        idea("symbols", "Exact definitions and references for Python code: "
             "where a name is defined, and every place it's used."),
        idea("bank", "Bank CSV statements as dated lines."),
    ]  # fmt: skip
    every = [{**a, "tags": ""} for a in every]
    line = ("Exact definitions and references in code from a SCIP index, so where "
            "is this defined is answered by the compiler's view, not by matching words.")  # fmt: skip
    assert sim.kernel.rank(sim.pile(every), line) == []
    found = sim.near(every, line)
    assert [a["name"] for a, _ in found] == ["symbols"]
    assert {"code", "definitions", "exact", "references"} <= set(found[0][1])
    assert sim.near(every, "statements") == [(every[1], ["statements"])]
    assert sim.near(every, "dated sea shells") == []  # one shared word is never near


def test_an_entry_is_never_near_itself():
    every = sim.entries()
    pdf = next(a for a in every if a["name"] == "pdf")
    assert "pdf" not in [a["name"] for a, _ in sim.near(every, pdf["line"], "pdf")]


def test_the_same_line_retyped_is_a_duplicate_and_a_near_one_is_not():
    every = [
        idea("bank", "Bank CSV statements as dated lines."),
        idea("banking", "bank csv STATEMENTS, as dated lines"),
        idea("money", "Bank CSV statements as dated lines, by month."),
    ]
    assert sim.duplicates(every) == [("bank", "banking")]


def test_a_pull_request_report_names_what_it_adds_and_what_is_near():
    every = sim.entries()
    before = {a["name"]: a["line"] for a in every if a["name"] != "pdf"}
    text = sim.report(every, before)
    assert "**pdf** (built): Text out of PDFs." in text
    assert "**dictate**, an idea already on the list." in text
    assert text.count(" (built): ") + text.count(" (idea): ") == 1  # only what changed


def test_nothing_near_is_said_and_nothing_added_is_said():
    every = sim.entries() + [idea("zither", "Zither quokka zymurgy.")]
    before = {a["name"]: a["line"] for a in every if a["name"] != "zither"}
    assert "- Nothing on the list is close." in sim.report(every, before)
    same = {a["name"]: a["line"] for a in every}
    assert "adds no add-on and no idea" in sim.report(every, same)


def test_the_list_at_a_commit_is_read_from_git():
    before = sim.at("HEAD")
    assert before["pdf"] == "Text out of PDFs."
    assert before["bank"].startswith("Bank CSV and OFX statements")


def test_tags_are_worked_out_the_same_every_time_and_never_more_than_five():
    """Never stored, so a card can't carry stale ones: the same cards give
    the same tags, install and network first, the author's own tag last."""
    every = sim.entries()
    got = sim.worked_out(every)
    assert got == sim.worked_out(every)
    for a in every:
        tags = got[a["name"]]["tags"]
        assert len(tags) <= 5 and len(set(tags)) == len(tags), (a["name"], tags)
        assert tags[:2] == sim.facts_tags(a)
        own = sim.readme.split_tags(a["tags"])
        assert tags[len(tags) - len(own):] == own
        assert len(tags) - 2 - len(own) <= 2  # two topics at most
        assert a["name"] not in got[a["name"]]["near"]
    assert got["ocr"]["tags"][:2] == ["needs-install", "offline"]
    assert got["vim"]["near"][0] == "emacs"


def test_a_tag_follows_the_card_when_the_card_changes():
    every = sim.entries()
    vim = next(a for a in every if a["name"] == "vim")
    moved = [a if a is not vim else {**vim, "network": "loopback"} for a in every]
    assert sim.worked_out(moved)["vim"]["tags"][1] == "this-machine"


def test_a_topic_never_says_the_authors_own_tag_again():
    """hook-guard's author tagged it hooks; "hook" beside it would say it twice."""
    tags = sim.worked_out(sim.entries())["hook-guard"]["tags"]
    assert tags[-1] == "hooks" and "hook" not in tags


def test_tags_on_the_command_line():
    got = cli("tags", "vim", "ocr")
    assert got.returncode == 0, got.stderr
    assert got.stdout.startswith("vim: no-install, offline")
    assert "· near: emacs" in got.stdout and "\nocr: needs-install" in got.stdout
    assert cli("tags", "no-such-add-on").returncode == 2
