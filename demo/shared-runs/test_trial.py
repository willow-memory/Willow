"""shared-runs, trial 1: the strike takes out a sentence whose figure the
report lacks and no other, an answer is right, not said or wrong by the
key, and what the trial's page says is what its kept files score to."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRIAL = HERE / "trial-1"
sys.path.insert(0, str(HERE))
import trial  # noqa: E402

REPORT = "done: 6 of 29 steps flagged\nthe chain holds: 2 rows, 0 sealed\nfirst mention: 1959-04-17\n"


def test_a_sentence_with_a_figure_the_report_lacks_is_struck_and_no_other():
    account = "It ran 29 steps and 6 were flagged. It took 204 seconds.\nNothing was sealed. First said on 1959-04-17."
    kept, struck = trial.strike(REPORT, account)
    assert struck == ["It took 204 seconds."]
    assert (
        kept
        == "It ran 29 steps and 6 were flagged.\nNothing was sealed.\nFirst said on 1959-04-17.\n"
    )
    assert trial.strike(REPORT, "It ran 1,959 steps.")[1] == ["It ran 1,959 steps."], (
        "1959 is not 1959-04-17"
    )
    assert trial.strike(REPORT, "It ran 29 steps.")[1] == []


def test_an_answer_is_right_not_said_or_wrong_by_the_key():
    key = {
        "steps": "29",
        "flagged": "07 11",
        "same": "yes",
        "when": "1959-04-17",
        "time": trial.NOT_SAID,
    }
    marks = trial.score(
        key,
        "steps: 29.\nflagged: 7, 11\nsame: Yes\nwhen: not said\ntime: 204\nother: 3\n",
    )
    assert marks == {
        "steps": "right",
        "flagged": "right",
        "same": "right",
        "when": "not said",
        "time": "wrong",
    }
    marks = trial.score(key, "steps: 30\ntime: Not said.\n")
    assert marks["steps"] == "wrong" and marks["time"] == "right"
    assert marks["flagged"] == marks["same"] == marks["when"] == "unanswered"


def test_what_the_trials_page_says_is_what_its_files_score_to():
    key = json.loads((TRIAL / "key.json").read_text())
    assert len(key) == 12 and sum(1 for v in key.values() if v == trial.NOT_SAID) == 2
    asked = [
        ln.split(":")[0] for ln in (TRIAL / "questions.txt").read_text().splitlines()
    ]
    assert asked == list(key)
    report = (TRIAL / "report.txt").read_text()
    account = (TRIAL / "a-account.txt").read_text()
    kept, struck = trial.strike(report, account)
    assert struck == [] and kept == (TRIAL / "a-account-struck.txt").read_text()
    assert len(account.split()) <= 150
    b = trial.score(key, (TRIAL / "b-answers.txt").read_text())
    c = trial.score(key, (TRIAL / "c-answers.txt").read_text())
    assert sorted(k for k, v in b.items() if v == "not said") == [
        "first-mention",
        "same-bytes",
    ]
    assert list(b.values()).count("right") == 10 and "wrong" not in b.values()
    assert set(c.values()) == {"right"}
    assert b["seconds"] == b["machines"] == c["seconds"] == c["machines"] == "right"
    page = (TRIAL / "RESULTS.md").read_text()
    assert (
        "10 right, 2 `not said`, 0 wrong" in page
        and "12 right, 0 `not said`, 0 wrong" in page
    )


def test_the_report_and_briefs_name_no_machine_and_hold_no_answer_key():
    for name in ("report.txt", "brief-a.txt", "brief-b.txt", "questions.txt"):
        text = (TRIAL / name).read_text()
        assert "/tmp/" not in text and "/home/" not in text, name
    assert "not said" not in (TRIAL / "report.txt").read_text()


def test_the_chain_refuses_what_a_step_may_not_be_and_passes_what_it_may():
    import chain

    stack = "## a\n- scan -- scan --index x\n- glance -- --of {01}\n"
    passes = [("ids", "--box {box} kernel.py"), ("fixity", "--box {box}"),
              ("glance", "--of {02} --questions <scratch>/questions.txt"),
              ("fair-merge", '--from <pile> "kept so it is not computed again"')]  # fmt: skip
    for name, args in passes:
        assert chain.refusal(name, args, stack) is None, (name, args)
    refused = {
        ("nope", "--box {box}"): "not a built add-on",
        ("kinds", "count"): "not a built add-on",  # a repo tool, not a stack's step
        ("scan", "scan --index x"): "already on the stack",
        ("backup", "--box {box} --to /media/usb"): "no path of its own",
        ("ids", "--box {box} ../x"): "no path of its own",
        ("ids", "--box {box} ~/x"): "no path of its own",
        ("ids", "--box {box} <repo>/kernel.py"): "the only folders",
        ("glance", "--of {03}"): "not an earlier step",
        ("glance", "--of {00}"): "not an earlier step",
        ("share", "send --box {box} --id <scratch>/a.key"): "may not name .key",
        ("fixity", "--box {box} --key x"): "may not name",
        ("session-seal", "--box {box}"): "may not name seal",
    }
    for (name, args), why in refused.items():
        got = chain.refusal(name, args, stack)
        assert got and why in got, (name, args, got)


def test_a_reply_is_read_by_its_three_lines_and_the_catalog_is_what_a_stack_can_run():
    import chain

    said = chain.read_reply(
        "want: a thing\nstep: - ids -- --box {box} kernel.py\nwhy: because\ncards: none\n"
    )
    assert said == {
        "want": ["a thing"],
        "step": ["- ids -- --box {box} kernel.py"],
        "why": ["because"],
    }
    assert chain.steps_of("## a\n- ids -- --box {box}\n# - no -- x\n- scan -- scan\n") == [
        ("ids", "--box {box}"), ("scan", "scan")]  # fmt: skip
    cards = chain.catalog()
    assert "scan" in cards and "fixity" in cards and "star-system" in cards
    assert (
        "kinds" not in cards
        and "hook-handoff" not in cards
        and "starter-words" not in cards
    )
    page = (TRIAL.parent / "trial-2" / "handoff-1.txt").read_text()
    assert page.startswith(
        (TRIAL.parent / "trial-2" / "brief.txt").read_text().rstrip()
    )
    assert "/tmp/" not in page and "/home/" not in page
    assert "hook-handoff: no session before this one." in page


def test_what_trial_twos_page_says_is_what_its_kept_files_hold():
    import chain

    two = TRIAL.parent / "trial-2"
    turns = [
        json.loads(line) for line in (two / "chain.jsonl").read_text().splitlines()
    ]
    assert [(t["link"], t["model"]) for t in turns] == [
        ("link-1", "haiku"), ("link-2", "sonnet"), ("link-3", "haiku")]  # fmt: skip
    assert [t["refused"] for t in turns] == [None, None, None]
    assert [t["ended"] for t in turns] == ["exit 0", "exit 2", "exit 42"]
    assert [t["place"] for t in turns] == [8, 9, 10]
    stack = (two / "stack-at-the-end.txt").read_text()
    steps = chain.steps_of(stack)
    assert len(steps) == 10 and [name for name, _ in steps[7:]] == [
        "again",
        "why-not",
        "box-health",
    ]
    assert len(set(steps)) == len(steps), "no step is on the stack twice"
    cards = chain.catalog()
    for n, turn in enumerate(turns, 1):
        reply = (two / f"reply-{n}.txt").read_text()
        said = chain.read_reply(reply)
        assert (
            said["step"] == [turn["step"]]
            and turn["step"] == f"- {steps[6 + n][0]} -- {steps[6 + n][1]}"
        )
        page = (two / f"handoff-{n}.txt").read_text()
        assert steps[6 + n][0] in cards and f"\n{steps[6 + n][0]}: " in page, (
            "chosen from the page"
        )
        figures = set(trial.figures(" ".join(said["want"] + said["why"])))
        assert figures <= set(trial.figures(page)), (
            n,
            figures - set(trial.figures(page)),
        )
        assert "/tmp/" not in page and "/home/" not in page
    assert "no session before this one" in (two / "handoff-1.txt").read_text()
    assert "session link-1 ended" in (two / "handoff-2.txt").read_text()
    assert "session link-2 ended" in (two / "handoff-3.txt").read_text()
    assert "why-not: refused: not a kernel box" in (two / "handoff-3.txt").read_text()
    log = (two / "log-at-the-end.txt").read_text()
    assert (
        "09 why-not: exit 2" in log
        and "08 again: exit 0" in log
        and "10 box-health: exit 42" in log
    )
