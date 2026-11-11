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
