"""say-check: a sentence is held to the boxes it was said about by four
checks (each cite served, each box cited, no word or number the boxes lack,
the person's words exact); one that fails any is struck, exit 42, and each
check says what failed; nothing is written."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "say_check.py"
sys.path.insert(0, str(HERE))
import say_check as sc  # noqa: E402

B5 = {"id": "b5", "text": "needs you: Ratify the work order (local-flow-and-ui §7)"}
B4 = {"id": "b4", "text": "blocked: PR 712 waiting (broker verb · 126 tests pass)"}
BOXES = [B5, B4]
GOOD = "Morning. You need to ratify the work order [b5]. PR 712's still waiting, 126 tests pass [b4]."


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, argv)], capture_output=True, text=True
    )


def held(sentence: str, boxes=BOXES, human: str = "", earlier=None) -> list:
    return [ok for _, ok, _ in sc.run_checks(sentence, boxes, human, earlier)]


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    got = run()
    assert got.returncode == 2 and "say_check.py" in got.stderr
    f = tmp_path / "b.json"
    f.write_text(json.dumps(BOXES))
    for argv in (
        ["--boxes", f],  # no sentence
        ["--sentence", "  ", "--boxes", f],
        ["--sentence", GOOD],  # no boxes
        ["--sentence", GOOD, "--boxes", f, "--earlier"],
        ["--sentence", GOOD, "--boxes", f, "--nope"],
        ["--sentence", GOOD, "--boxes", f, "extra"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and got.stderr.startswith("usage: say_check.py"), (
            argv
        )
        assert got.stdout == ""


def test_boxes_that_cant_be_read_are_refused_and_say_why(tmp_path):
    f = tmp_path / "b.json"
    for text, why in (
        ("not json", "could not be read"),
        ('{"a": 1}', "not a list"),
        ('[{"id": "b1"}]', "each box is"),
        ('[{"id": "b 1", "text": "x"}]', "each box is"),
        (
            '[{"id": "b1", "text": "x"}, {"id": "b1", "text": "y"}]',
            "two boxes are both [b1]",
        ),
        ("[]", "holds no box"),
        ('{"groups": [{"rows": [{"where": "a"}]}]}', "a where and a what"),
    ):
        f.write_text(text)
        got = run("--sentence", "x [b1]", "--boxes", f)
        assert got.returncode == 2 and why in got.stderr, text
    got = run("--sentence", "x", "--boxes", tmp_path / "gone")
    assert got.returncode == 2 and "could not be read" in got.stderr


def test_a_sentence_that_uses_only_the_boxes_stands(tmp_path):
    assert held(GOOD) == [True, True, True, None]
    assert sc.passed(sc.run_checks(GOOD, BOXES))
    f = tmp_path / "b.json"
    f.write_text(json.dumps(BOXES))
    got = run("--sentence", GOOD, "--boxes", f, "--json")
    assert got.returncode == 0, got.stderr
    doc = json.loads(got.stdout)
    assert doc["addon"] == "say-check" and doc["state"] == "populated"
    assert doc["said"] == "the sentence stands: no check failed"
    assert doc["groups"] == [{"name": None, "rows": [
        {"where": "every cite was served", "what": "held"},
        {"where": "every box cited", "what": "held"},
        {"where": "nothing the boxes lack", "what": "held"},
        {"where": "your words quoted exactly", "what": "nothing quoted"},
    ]}]  # fmt: skip


def test_an_invented_number_is_struck_and_named(tmp_path):
    bad = GOOD.replace("126", "140")
    assert held(bad) == [True, True, False, None]
    assert sc.lacking(bad, BOXES) == ["140"]
    f = tmp_path / "b.json"
    f.write_text(json.dumps(BOXES))
    got = run("--sentence", bad, "--boxes", f)
    assert got.returncode == 42
    assert got.stdout.splitlines() == [
        "say-check: populated, struck: 1 of 4 checks failed",
        "  every cite was served      held",
        "  every box cited            held",
        "  nothing the boxes lack     failed: 140 is no box's",
        "  your words quoted exactly  nothing quoted",
    ]


def test_a_cite_to_a_box_never_given_fails_and_an_earlier_one_was_given():
    s = "You need to ratify the work order [b5], still waiting [b4] [b9]."
    assert sc.unserved(s, BOXES) == ["b9"]
    assert held(s)[0] is False
    b9 = {"id": "b9", "text": "decided: phone only proposes"}
    assert sc.unserved(s, BOXES, [b9]) == []
    assert "[b9] was never given" in sc.run_checks(s, BOXES)[0][2]
    two = sc.run_checks("The work order [b5] is waiting [b4] [b8] [b9].", BOXES)[0][2]
    assert two == "failed: [b8], [b9] were never given"
    assert sc.run_checks("Waiting.", BOXES)[1][2] == "failed: [b5], [b4] are not cited"


def test_every_box_given_now_must_be_cited_and_earlier_ones_need_not_be():
    s = "You need to ratify the work order [b5]."
    assert sc.uncited(s, BOXES) == ["b4"]
    assert held(s)[1] is False and "[b4] is not cited" in sc.run_checks(s, BOXES)[1][2]
    earlier = [{"id": "b1", "text": "decided: phone only proposes"}]
    assert held(GOOD, earlier=earlier) == [True, True, True, None]


def test_a_word_the_boxes_lack_fails_and_glue_and_function_words_dont():
    assert sc.lacking("Heads up, the work order is waiting [b5] [b4].", BOXES) == []
    assert sc.lacking("The work order is urgent [b5] [b4].", BOXES) == ["urgent"]
    # any form of a box's word is the box's word
    assert sc.lacking("The orders waited, tested and passing [b5] [b4].", BOXES) == []
    # but only by its ending: ratified is not read as ratify
    assert sc.lacking("The ratified order waits [b5] [b4].", BOXES) == ["ratified"]
    # a possessive and a cite tag are not words
    assert sc.lacking("PR 712's waiting [b4].", [B4]) == []
    got = sc.run_checks("Urgent and overdue: the work order [b5] [b4].", BOXES)[2]
    assert got[1] is False and got[2] == "failed: urgent, overdue are no box's"


def test_accents_fold_and_a_script_the_boxes_dont_hold_fails():
    cafe = [{"id": "b1", "text": "open: the café on Main, 9 to 5"}]
    assert sc.lacking("The cafe on Main is open [b1].", cafe) == []
    assert sc.lacking("The CAFÉ is open 9 to 5 [b1].", cafe) == []
    assert sc.lacking("The café is открыто [b1].", cafe) == ["открыто"]
    assert sc.lacking("The café 是 open [b1].", cafe) == ["是"], "one letter, not ASCII"


def test_a_sentence_with_no_word_is_not_one():
    assert sc.lacking("[b5] [b4].", BOXES) == ["(no word)"]
    assert sc.lacking("126 [b4]", [B4]) == ["(no word)"]


def test_an_earlier_boxs_words_count_only_when_it_is_cited():
    earlier = [{"id": "b1", "text": "decided: phone only proposes"}]
    s = "The work order [b5] is waiting [b4], and the phone only proposes"
    assert sc.lacking(s + ".", BOXES, earlier=earlier) == ["phone", "only", "proposes"]
    assert sc.lacking(s + " [b1].", BOXES, earlier=earlier) == []


def test_your_words_are_quoted_exactly_or_the_quote_fails():
    you = "She meant the damage. Leave it for now"
    s = 'The work order [b5] is waiting [b4]: "she meant the damage".'
    assert sc.misquoted(s, you) == []
    assert held(s, human=you) == [True, True, True, True]
    wrong = (
        'The work order [b5] is waiting [b4]: "she meant the destruction she caused".'
    )
    assert sc.misquoted(wrong, you) == ["she meant the destruction she caused"]
    got = sc.run_checks(wrong, BOXES, you)
    assert got[3][1] is False
    assert got[3][2] == 'failed: not your words: "she meant the destruction she caused"'
    # a span that isn't yours gets no pass on its words either
    assert got[2][1] is False and "destruction" in got[2][2]
    assert sc.misquoted("The work order waits [b5] [b4].", you) is None
    # curly quotes are quotes
    assert sc.misquoted("Waiting [b5] [b4]: “leave it for now”.", you) == []


def test_your_quoted_words_arent_held_to_the_boxes_but_a_number_in_them_is():
    you = "I counted 140 of them yesterday"
    s = 'The work order [b5] is waiting [b4], "counted 140 of them" you said.'
    # "counted" and "them" are yours, so not scanned; "said" is no box's word
    assert sc.lacking(s, BOXES, you) == ["140", "said"]
    assert sc.lacking(s, BOXES, "") == ["140", "counted", "them", "said"]


def test_a_reports_rows_are_the_boxes_in_order(tmp_path):
    doc = {"addon": "invoices", "state": "populated", "said": "1 overdue",
           "groups": [{"name": None, "rows": [
               {"where": "work/log.csv:98", "what": "overdue Theatre $640.00"}]},
               {"name": "paid", "rows": [{"where": "work/log.csv:12", "what": "paid Hall $85"}]}]}  # fmt: skip
    boxes, why = sc.boxes_of(doc)
    assert why == "" and boxes == [
        {"id": "b1", "text": "work/log.csv:98 overdue Theatre $640.00"},
        {"id": "b2", "text": "work/log.csv:12 paid Hall $85"},
    ]
    f = tmp_path / "r.json"
    f.write_text(json.dumps(doc))
    assert run("--sentence", "The Theatre is overdue, 640.00 [b1], and the Hall paid 85 [b2].",
               "--boxes", f).returncode == 0  # fmt: skip
    got = run("--sentence", "The Theatre owes 700 [b1] [b2].", "--boxes", f)
    assert got.returncode == 42 and "700, owes are no box's" in got.stdout


def test_earlier_boxes_come_from_a_file_too(tmp_path):
    f, e = tmp_path / "b.json", tmp_path / "e.json"
    f.write_text(json.dumps(BOXES))
    e.write_text(json.dumps([{"id": "b1", "text": "decided: phone only proposes"}]))
    s = "The work order [b5] is waiting [b4], and the phone only proposes [b1]."
    assert run("--sentence", s, "--boxes", f).returncode == 42
    assert run("--sentence", s, "--boxes", f, "--earlier", e).returncode == 0
    e.write_text("nope")
    assert run("--sentence", s, "--boxes", f, "--earlier", e).returncode == 2


def test_the_example_boxes_are_the_ones_the_card_shows():
    f = HERE / "example-boxes.json"
    assert json.loads(f.read_text()) == BOXES
    assert run("--sentence", GOOD, "--boxes", f).returncode == 0


def test_nothing_is_written(tmp_path):
    f = tmp_path / "b.json"
    f.write_text(json.dumps(BOXES))
    before = {p: p.read_bytes() for p in sorted(tmp_path.rglob("*")) if p.is_file()}
    run("--sentence", GOOD.replace("126", "140"), "--boxes", f, "--you", "hello")
    assert {
        p: p.read_bytes() for p in sorted(tmp_path.rglob("*")) if p.is_file()
    } == before
