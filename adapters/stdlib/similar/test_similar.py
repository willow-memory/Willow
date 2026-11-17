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
    assert "pdf" in found and "ocr" in found and "file-kind" in found
    assert {"pdfs", "text"} <= set(found["pdf"])
    lines = cli("near", "Text out of PDFs.").stdout
    assert "[**pdf**](adapters/deps/pdf/), built: connect to it." in lines
    assert "[**ocr**](adapters/deps/ocr/), built: connect to it." in lines
    assert "**file-kind**, an idea already on the list." in lines


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


def wanted(*lines: tuple[str, str]) -> list[dict]:
    return [{**idea(n, ln), "network": "none", "tags": ""} for n, ln in lines]


def test_want_puts_what_a_word_usually_means_first_and_says_when_you_named_one():
    every = wanted(
        ("mail", "Email in eml and mbox files, as text."),
        ("coming-up", "Dates written in your files in the next days."),
        ("renewals", "What renews when, from your files."),
        ("tides", "High and low water, from a tide table."),
    )
    want = sim.Want(every, alias={"due": ["coming", "renewals"]})
    found = want.find("read my mail and tell me when the boiler is due")["found"]
    means = [f for f in found if f["why"] == "what “due” usually means here"]
    assert {f["name"] for f in means} == {"coming-up", "renewals"}
    assert [f["name"] for f in found[:2]] == [f["name"] for f in means]
    assert {"name": "mail", "why": "you named it"} in found
    assert "tides" not in [f["name"] for f in found[:3]]
    assert want.find("   ") == {"state": "empty", "found": []}
    assert len(want.find("mail", top=1)["found"]) == 1


def test_one_part_of_a_name_moves_no_card_and_a_whole_one_is_said():
    """ "count" is one part of noised-count; the card about counting how
    often suggestions were sealed is the one these words mean."""
    every = wanted(
        ("noised-count", "A number of yours, noised before it is sent."),
        (
            "assistant-scores",
            "How often each assistant's suggestions were sealed or set aside.",
        ),
        ("box-health", "What a box needs: rows waiting, files it can't read."),
    )
    want = sim.Want(every, alias={})
    found = want.find("count how often each suggestion was sealed")["found"]
    assert found[0]["name"] == "assistant-scores"
    assert all(f["why"] != "you named it" for f in found)
    health = want.find("the health of my box")["found"]
    assert health[0] == {"name": "box-health", "why": "you named it"}


def test_the_first_five_are_the_same_whatever_is_asked_for():
    want = sim.Want()
    for words in ("check that my tests catch a broken line of code", "my email"):
        five = [f["name"] for f in want.find(words, top=5)["found"]]
        assert [f["name"] for f in want.find(words, top=12)["found"]][:5] == five


def test_want_with_no_words_list_still_searches(tmp_path):
    assert sim.search_words(tmp_path / "absent.txt") == {}
    bad = tmp_path / "words.txt"
    bad.write_text("this is not a words list\n")
    assert sim.search_words(bad) == {}
    every = wanted(("mail", "Email in eml and mbox files, as text."))
    assert sim.Want(every, alias={}).find("my mail")["found"][0]["name"] == "mail"


def test_want_on_the_command_line():
    got = cli("want", "use it from vim")
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines()[0] == "- vim: you named it"
    assert len(got.stdout.splitlines()) <= sim.WANT_TOP


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
        assert tags[len(tags) - len(own) :] == own
        assert len(tags) - 2 - len(own) <= 2  # two topics at most
        assert a["name"] not in got[a["name"]]["near"]
    assert got["ocr"]["tags"][:2] == ["needs-install", "offline"]
    assert got["vim"]["near"][0] == "emacs"


def test_a_tag_follows_the_card_when_the_card_changes():
    every = sim.entries()
    vim = next(a for a in every if a["name"] == "vim")
    moved = [a if a is not vim else {**vim, "network": "loopback"} for a in every]
    assert sim.worked_out(moved)["vim"]["tags"][1] == "this-machine"


def test_an_add_on_that_hands_on_to_a_model_is_never_tagged_offline():
    """It reaches nothing itself, but what it hands an assistant's model may
    leave: the card's hands line says so, and the tag says it too (CONST-III-5)."""
    got = sim.worked_out(sim.entries())
    assert got["mcp-sampling"]["tags"][1] == "to-a-model"
    assert got["claude-code"]["tags"][1] == "to-a-model"
    assert got["vim"]["tags"][1] == "offline"  # it shows answers to the person
    online = {"name": "x", "kind": "deps", "network": "api.example.com", "hands": "h"}
    assert sim.facts_tags(online)[1] == "online"  # what it reaches comes first


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


def test_one_entry_worked_out_alone_is_its_line_in_the_whole_list():
    every = sim.entries()
    whole = sim.worked_out(every)
    for name in (every[0]["name"], every[len(every) // 2]["name"], every[-1]["name"]):
        assert sim.worked_out(every, only={name}) == {name: whole[name]}
