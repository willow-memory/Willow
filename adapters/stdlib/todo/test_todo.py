"""todo: marked lines across the folder, oldest first by the kernel's own
passage dates, undated last."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def test_oldest_first_undated_last_and_every_marker(tmp_path):
    pile = tmp_path / "pile"
    (pile / "memos").mkdir(parents=True)
    (pile / "memos" / "2021-05-14.txt").write_text(
        "Sold the van. Need to call the insurer.\n"
    )
    (pile / "memos" / "2025-02-07.txt").write_text("Remember to check the mites.\n")
    (pile / "README.md").write_text(
        "TODO: fix the install step\n\n- [ ] buy strings\n\nAll done here.\n"
    )
    (pile / "code.py").write_text("x = 1  # FIXME: off by one\n")
    b = tmp_path / "box"
    run(
        str(KERNEL),
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    )
    got = run(str(HERE / "todo.py"), "--box", str(b))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "todo: populated, 5 lines marked to do, the oldest from 2021-05-14",
        "  memos/2021-05-14.txt:1  2021-05-14  Sold the van. Need to call the insurer.",
        "  memos/2025-02-07.txt:1  2025-02-07  Remember to check the mites.",
        "## undated",
        "  README.md:1             TODO: fix the install step",
        "  README.md:3             - [ ] buy strings",
        "  code.py:1               x = 1  # FIXME: off by one",
    ]
    doc = json.loads(run(str(HERE / "todo.py"), "--box", str(b), "--json").stdout)
    assert doc["addon"] == "todo" and doc["state"] == "populated"
    assert [g["name"] for g in doc["groups"]] == [None, "undated"]
    assert doc["groups"][0]["rows"][0] == {
        "where": "memos/2021-05-14.txt:1",
        "what": "2021-05-14  Sold the van. Need to call the insurer.",
    }
    assert doc["groups"][1]["rows"][2] == {
        "where": "code.py:1",
        "what": "x = 1  # FIXME: off by one",
    }


def marked(tmp_path, *lines: str) -> list[str]:
    """The lines of one file the report takes as marked to do, in order."""
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("\n\n".join(lines) + "\n")
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key",
        str(tmp_path / "k"), *NOW)  # fmt: skip
    doc = json.loads(run(str(HERE / "todo.py"), "--box", str(b), "--json").stdout)
    # as a set: the report orders rows by their place, which isn't the point here
    return {r["what"] for g in doc["groups"] for r in g["rows"]}


def test_todo_and_fixme_count_as_written_in_capitals_and_not_as_a_files_name(tmp_path):
    assert marked(
        tmp_path,
        "TODO: water the beans",
        "x = 1  # FIXME off by one",
        "the todo add-on prints a report",
        "Todo lists are kept in the kitchen",
        "see TODO.md for the rest",
        "a fixme in lower case is prose too",
        "TODO. And then the next thing",
    ) == {"TODO: water the beans", "x = 1  # FIXME off by one",
          "TODO. And then the next thing"}  # fmt: skip


def test_need_to_counts_where_a_thing_to_do_is_said(tmp_path):
    assert marked(
        tmp_path,
        "Need to call the insurer.",
        "need to call the vet",
        "- need to buy strings",
        "Sold the van. Need to call the insurer too.",
        "Note: need to renew the passport",
        "I need to book the MOT",
        "we still need to pay the fencer",
        "The file is read as a stream, so it does not need to fit in memory.",
        "You need to restart the server after that.",
        "There is no need to hurry.",
        "They will need to ask twice.",
    ) == {
        "Need to call the insurer.",
        "need to call the vet",
        "- need to buy strings",
        "Sold the van. Need to call the insurer too.",
        "Note: need to renew the passport",
        "I need to book the MOT",
        "we still need to pay the fencer",
    }


def test_a_mark_inside_quotation_marks_is_words_quoted_not_a_thing_to_do(tmp_path):
    assert marked(
        tmp_path,
        '- **The ask.** "I still need to sign the py stuff on github"',
        "- **Local first.** \u201cBack to the local, where I need to be working first.\u201d",
        '**Asked:** the operator, that morning: "we need to get that into rat?"',
        'We need to focus on the 0, and yes there is a demo for that too."',
        '| `todo` | every line marked "need to", "remember to", an open checkbox |',
        '"target_text": "Correct the status. TODO: keep them in lockstep"',
        'Mum: "don\'t forget the bins on Tuesday"',
        "- Walt: \u201cremember to bring the ladder\u201d",
        'need to buy "milk" today',
        '- [ ] reply to the "need to renew" email',
        'Wrote "done" on it, but I need to post it.',
        '- [ ] **the demos of sharing** (the owner: "a few demos in Willow as',
    ) == {
        '- [ ] **the demos of sharing** (the owner: "a few demos in Willow as',
        'Mum: "don\'t forget the bins on Tuesday"',
        "- Walt: \u201cremember to bring the ladder\u201d",
        'need to buy "milk" today',
        '- [ ] reply to the "need to renew" email',
        'Wrote "done" on it, but I need to post it.',
    }


def test_the_other_marks_count_anywhere_in_a_line_in_any_case(tmp_path):
    assert marked(
        tmp_path,
        "And DON'T FORGET the milk",
        "dont forget the bread",
        "I must remember to lock the shed",
        "- [ ] buy strings",
        "* [ ] tune the fiddle",
        "- [x] done already",
        "text with a [ ] in the middle of it",
    ) == {"And DON'T FORGET the milk", "dont forget the bread",
          "I must remember to lock the shed", "- [ ] buy strings",
          "* [ ] tune the fiddle"}  # fmt: skip


def test_a_checkbox_that_opens_with_a_templates_blank_is_nothing_to_do(tmp_path):
    assert marked(
        tmp_path,
        "- [ ] {item}",
        "- [ ] {step} — {owner} — {due}",
        "* [ ]   {item not done}  ← if any are unchecked, explain",
        "- [ ] fill in {owner} before Friday",
        "- [ ] {unclosed blank",
        "- [ ] {} has nothing in it but is a blank still",
    ) == {"- [ ] fill in {owner} before Friday", "- [ ] {unclosed blank"}


def test_nothing_marked(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("Nothing to see.\n")
    b = tmp_path / "box"
    run(
        str(KERNEL),
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    )
    got = run(str(HERE / "todo.py"), "--box", str(b))
    assert got.returncode == 0  # empty is 0: 42 never means found nothing
    assert got.stdout == "todo: empty, nothing in your folder is marked to do\n"
    got = run(str(HERE / "todo.py"), "--box", str(b), "--json")
    assert got.returncode == 0
    assert json.loads(got.stdout) == {
        "addon": "todo",
        "state": "empty",
        "said": "nothing in your folder is marked to do",
        "groups": [],
    }


def test_all_undated_says_so(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("TODO: water\n")
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key",
        str(tmp_path / "k"), *NOW)  # fmt: skip
    got = run(str(HERE / "todo.py"), "--box", str(b))
    assert got.stdout.splitlines() == [
        "todo: populated, 1 line marked to do, none dated",
        "## undated",
        "  a.md:1  TODO: water",
    ]


def test_a_long_marked_line_is_cut_at_120(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("TODO: " + "y" * 200 + "\n")
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key",
        str(tmp_path / "k"), *NOW)  # fmt: skip
    line = run(str(HERE / "todo.py"), "--box", str(b)).stdout.splitlines()[-1]
    assert line.endswith("TODO: " + "y" * 114)


def test_a_day_no_calendar_has_is_no_date(tmp_path):
    """June has 30 days, and the kernel knows it: a line under 1984-06-31 is
    never the oldest, it's undated, and the report is the plain populated."""
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "old.md").write_text("1984-06-31\nTODO: file the claim\n")
    (pile / "real.md").write_text("2021-05-14\nNeed to call the insurer.\n")
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key",
        str(tmp_path / "k"), *NOW)  # fmt: skip
    got = run(str(HERE / "todo.py"), "--box", str(b))
    assert got.returncode == 0
    assert got.stdout.splitlines() == [
        "todo: populated, 2 lines marked to do, the oldest from 2021-05-14",
        "  real.md:2  2021-05-14  Need to call the insurer.",
        "## undated",
        "  old.md:2   TODO: file the claim",
    ]
